"""Recurring charge service for business logic."""

from decimal import Decimal
from datetime import date, timedelta
from typing import Optional
from collections import defaultdict
from ..exceptions import RecurringChargeNotFoundError


class RecurringService:
    """Service for recurring charge operations."""

    def __init__(self, recurring_repo, transaction_repo):
        """
        Initialize recurring service.

        Args:
            recurring_repo: Recurring repository instance
            transaction_repo: Transaction repository instance
        """
        self.repo = recurring_repo
        self.transaction_repo = transaction_repo

    def create_recurring_charge(
        self,
        user_id: int,
        merchant: str,
        category: str,
        typical_amount: Decimal,
        frequency: str,
        day_of_period: Optional[int] = None,
        first_seen: Optional[date] = None,
        last_seen: Optional[date] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """
        Create a new recurring charge.

        Args:
            user_id: User ID
            merchant: Merchant name
            category: Transaction category
            typical_amount: Typical transaction amount
            frequency: Frequency ('weekly', 'monthly', 'annual')
            day_of_period: Day of week (0-6) or day of month (1-31)
            first_seen: First occurrence date (defaults to today)
            last_seen: Most recent occurrence date (defaults to today)
            notes: Additional notes

        Returns:
            Created recurring charge dict

        Raises:
            ValueError: If frequency is invalid or amount is not positive
        """
        # Validate frequency
        valid_frequencies = ["weekly", "monthly", "annual"]
        if frequency not in valid_frequencies:
            raise ValueError(f"Invalid frequency. Must be one of: {', '.join(valid_frequencies)}")

        # Validate amount
        if typical_amount <= 0:
            raise ValueError("Typical amount must be positive")

        # Default dates to today
        today = date.today()
        first_seen = first_seen or today
        last_seen = last_seen or today

        # Calculate next expected date
        next_expected = self._calculate_next_date(last_seen, frequency, day_of_period)

        recurring_id = self.repo.create(
            user_id=user_id,
            merchant=merchant,
            category=category,
            typical_amount=typical_amount,
            frequency=frequency,
            day_of_period=day_of_period,
            first_seen=first_seen,
            last_seen=last_seen,
            next_expected_date=next_expected,
            occurrence_count=1,
            confidence=Decimal("1.0"),  # Manual entries are 100% confident
            notes=notes,
        )

        return self.repo.get_by_id(recurring_id)

    def get_recurring_charge(self, recurring_id: int) -> dict:
        """
        Get recurring charge by ID.

        Args:
            recurring_id: Recurring charge ID

        Returns:
            Recurring charge dict

        Raises:
            RecurringChargeNotFoundError: If not found
        """
        recurring = self.repo.get_by_id(recurring_id)
        if not recurring:
            raise RecurringChargeNotFoundError(f"Recurring charge with ID {recurring_id} not found")
        return recurring

    def list_recurring_charges(self, user_id: int, status: Optional[str] = None) -> list[dict]:
        """
        Get all recurring charges for user.

        Args:
            user_id: User ID
            status: Filter by status ('active', 'paused', 'cancelled')

        Returns:
            List of recurring charge dicts
        """
        return self.repo.get_all(user_id, status=status)

    def get_upcoming_charges(self, user_id: int, days_ahead: int = 7) -> list[dict]:
        """
        Get recurring charges due within specified days.

        Args:
            user_id: User ID
            days_ahead: Number of days to look ahead

        Returns:
            List of upcoming recurring charge dicts
        """
        return self.repo.get_upcoming(user_id, days_ahead)

    def update_recurring_charge(self, recurring_id: int, **kwargs) -> dict:
        """
        Update recurring charge fields.

        Args:
            recurring_id: Recurring charge ID
            **kwargs: Fields to update

        Returns:
            Updated recurring charge dict

        Raises:
            RecurringChargeNotFoundError: If not found
        """
        # Verify exists
        self.get_recurring_charge(recurring_id)

        # Validate frequency if being updated
        if "frequency" in kwargs:
            valid_frequencies = ["weekly", "monthly", "annual"]
            if kwargs["frequency"] not in valid_frequencies:
                raise ValueError(f"Invalid frequency. Must be one of: {', '.join(valid_frequencies)}")

        # Update recurring charge
        self.repo.update(recurring_id, **kwargs)
        return self.get_recurring_charge(recurring_id)

    def cancel_recurring_charge(self, recurring_id: int) -> None:
        """
        Cancel a recurring charge (mark as cancelled).

        Args:
            recurring_id: Recurring charge ID

        Raises:
            RecurringChargeNotFoundError: If not found
        """
        # Verify exists
        self.get_recurring_charge(recurring_id)
        self.repo.update_status(recurring_id, "cancelled")

    def pause_recurring_charge(self, recurring_id: int) -> None:
        """
        Pause a recurring charge.

        Args:
            recurring_id: Recurring charge ID

        Raises:
            RecurringChargeNotFoundError: If not found
        """
        # Verify exists
        self.get_recurring_charge(recurring_id)
        self.repo.update_status(recurring_id, "paused")

    def resume_recurring_charge(self, recurring_id: int) -> None:
        """
        Resume a paused recurring charge.

        Args:
            recurring_id: Recurring charge ID

        Raises:
            RecurringChargeNotFoundError: If not found
        """
        # Verify exists
        self.get_recurring_charge(recurring_id)
        self.repo.update_status(recurring_id, "active")

    def delete_recurring_charge(self, recurring_id: int) -> None:
        """
        Delete a recurring charge.

        Args:
            recurring_id: Recurring charge ID

        Raises:
            RecurringChargeNotFoundError: If not found
        """
        # Verify exists
        self.get_recurring_charge(recurring_id)
        self.repo.delete(recurring_id)

    def detect_recurring_patterns(self, user_id: int, min_occurrences: int = 2) -> list[dict]:
        """
        Analyze transactions to detect recurring charge patterns.

        Args:
            user_id: User ID
            min_occurrences: Minimum number of occurrences to consider as recurring

        Returns:
            List of detected pattern dicts with merchant, category, frequency, etc.
        """
        # Get all transactions for the user
        transactions = self.transaction_repo.search(user_id)

        # Group by merchant
        merchant_txs = defaultdict(list)
        for tx in transactions:
            if tx["type"] == "expense" and tx.get("merchant"):
                merchant_txs[tx["merchant"]].append(tx)

        patterns = []

        for merchant, txs in merchant_txs.items():
            # Need at least min_occurrences
            if len(txs) < min_occurrences:
                continue

            # Sort by date
            txs.sort(key=lambda x: x["date"])

            # Calculate intervals between transactions
            intervals = []
            for i in range(len(txs) - 1):
                date1 = date.fromisoformat(txs[i]["date"]) if isinstance(txs[i]["date"], str) else txs[i]["date"]
                date2 = date.fromisoformat(txs[i + 1]["date"]) if isinstance(txs[i + 1]["date"], str) else txs[i + 1]["date"]
                interval = (date2 - date1).days
                intervals.append(interval)

            if not intervals:
                continue

            # Check if intervals are consistent
            avg_interval = sum(intervals) / len(intervals)
            max_deviation = max(abs(i - avg_interval) for i in intervals)

            # Determine frequency based on average interval
            frequency = None
            confidence = Decimal("0.0")

            # Weekly (7 days ± 2 days)
            if 5 <= avg_interval <= 9 and max_deviation <= 3:
                frequency = "weekly"
                confidence = min(Decimal("0.9"), Decimal(str(1.0 - (max_deviation / avg_interval))))

            # Monthly (28-31 days ± 3 days)
            elif 25 <= avg_interval <= 34 and max_deviation <= 4:
                frequency = "monthly"
                confidence = min(Decimal("0.9"), Decimal(str(1.0 - (max_deviation / avg_interval))))

            # Annual (365 days ± 7 days)
            elif 358 <= avg_interval <= 372 and max_deviation <= 10:
                frequency = "annual"
                confidence = min(Decimal("0.9"), Decimal(str(1.0 - (max_deviation / avg_interval))))

            if frequency and confidence >= Decimal("0.5"):
                # Calculate typical amount
                amounts = [Decimal(str(tx["amount"])) for tx in txs]
                typical_amount = sum(amounts) / len(amounts)

                # Get first and last seen dates
                first_seen = date.fromisoformat(txs[0]["date"]) if isinstance(txs[0]["date"], str) else txs[0]["date"]
                last_seen = date.fromisoformat(txs[-1]["date"]) if isinstance(txs[-1]["date"], str) else txs[-1]["date"]

                # Check if already exists
                existing = self.repo.get_by_merchant(user_id, merchant)
                if existing:
                    continue

                patterns.append({
                    "merchant": merchant,
                    "category": txs[0].get("category", "Uncategorized"),
                    "typical_amount": typical_amount,
                    "frequency": frequency,
                    "occurrence_count": len(txs),
                    "confidence": confidence,
                    "first_seen": first_seen,
                    "last_seen": last_seen,
                })

        return patterns

    def confirm_pattern(self, user_id: int, pattern: dict) -> dict:
        """
        Confirm a detected pattern and create a recurring charge.

        Args:
            user_id: User ID
            pattern: Pattern dict from detect_recurring_patterns()

        Returns:
            Created recurring charge dict
        """
        return self.create_recurring_charge(
            user_id=user_id,
            merchant=pattern["merchant"],
            category=pattern["category"],
            typical_amount=pattern["typical_amount"],
            frequency=pattern["frequency"],
            first_seen=pattern["first_seen"],
            last_seen=pattern["last_seen"],
        )

    def _calculate_next_date(
        self,
        last_date: date,
        frequency: str,
        day_of_period: Optional[int]
    ) -> date:
        """
        Calculate next expected date based on frequency.

        Args:
            last_date: Last occurrence date
            frequency: Frequency ('weekly', 'monthly', 'annual')
            day_of_period: Day of week (0-6) or day of month (1-31)

        Returns:
            Next expected date
        """
        if frequency == "weekly":
            return last_date + timedelta(days=7)
        elif frequency == "monthly":
            # Add one month
            next_month = last_date.month + 1
            next_year = last_date.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            # Use day_of_period if provided, otherwise use last_date's day
            day = day_of_period or last_date.day
            # Handle month end edge cases
            try:
                return date(next_year, next_month, min(day, 28))
            except ValueError:
                # Day doesn't exist in month, use last day of month
                if next_month == 2:
                    return date(next_year, next_month, 28)
                elif next_month in [4, 6, 9, 11]:
                    return date(next_year, next_month, 30)
                else:
                    return date(next_year, next_month, 31)
        elif frequency == "annual":
            return date(last_date.year + 1, last_date.month, last_date.day)
        else:
            return last_date
