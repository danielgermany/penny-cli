"""Recurring charge repository for database operations."""

from decimal import Decimal
from typing import Optional
from datetime import date
from .base import BaseRepository


class RecurringRepository(BaseRepository):
    """Repository for recurring charge database operations."""

    def create(
        self,
        user_id: int,
        merchant: str,
        category: str,
        typical_amount: Decimal,
        frequency: str,
        day_of_period: Optional[int],
        first_seen: date,
        last_seen: date,
        next_expected_date: Optional[date] = None,
        occurrence_count: int = 1,
        confidence: Decimal = Decimal("0.5"),
        notes: Optional[str] = None,
    ) -> int:
        """
        Create a new recurring charge.

        Args:
            user_id: User ID
            merchant: Merchant name
            category: Transaction category
            typical_amount: Typical transaction amount
            frequency: Frequency ('weekly', 'monthly', 'annual')
            day_of_period: Day of week (0-6) or day of month (1-31)
            first_seen: First occurrence date
            last_seen: Most recent occurrence date
            next_expected_date: Next expected date
            occurrence_count: Number of times seen
            confidence: Pattern detection confidence (0.0-1.0)
            notes: Additional notes

        Returns:
            ID of created recurring charge
        """
        query = """
            INSERT INTO recurring_charges
            (user_id, merchant, category, typical_amount, frequency, day_of_period,
             first_seen, last_seen, next_expected_date, occurrence_count, confidence, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self._execute(
            query,
            (
                user_id,
                merchant,
                category,
                float(typical_amount),
                frequency,
                day_of_period,
                first_seen,
                last_seen,
                next_expected_date,
                occurrence_count,
                float(confidence),
                notes,
            ),
        )
        return cursor.lastrowid

    def get_by_id(self, recurring_id: int) -> Optional[dict]:
        """
        Get recurring charge by ID.

        Args:
            recurring_id: Recurring charge ID

        Returns:
            Recurring charge dict or None if not found
        """
        query = "SELECT * FROM recurring_charges WHERE id = ?"
        return self._fetchone(query, (recurring_id,))

    def get_by_merchant(self, user_id: int, merchant: str) -> Optional[dict]:
        """
        Get recurring charge by merchant name.

        Args:
            user_id: User ID
            merchant: Merchant name

        Returns:
            Recurring charge dict or None if not found
        """
        query = """
            SELECT * FROM recurring_charges
            WHERE user_id = ? AND merchant = ? AND status = 'active'
        """
        return self._fetchone(query, (user_id, merchant))

    def get_all(self, user_id: int, status: Optional[str] = None) -> list[dict]:
        """
        Get all recurring charges for user.

        Args:
            user_id: User ID
            status: Filter by status ('active', 'paused', 'cancelled')

        Returns:
            List of recurring charge dicts
        """
        if status:
            query = """
                SELECT * FROM recurring_charges
                WHERE user_id = ? AND status = ?
                ORDER BY next_expected_date ASC, merchant ASC
            """
            return self._fetchall(query, (user_id, status))
        else:
            query = """
                SELECT * FROM recurring_charges
                WHERE user_id = ?
                ORDER BY status ASC, next_expected_date ASC, merchant ASC
            """
            return self._fetchall(query, (user_id,))

    def get_upcoming(self, user_id: int, days_ahead: int = 7) -> list[dict]:
        """
        Get recurring charges due within specified days.

        Args:
            user_id: User ID
            days_ahead: Number of days to look ahead

        Returns:
            List of upcoming recurring charge dicts
        """
        query = """
            SELECT * FROM recurring_charges
            WHERE user_id = ?
            AND status = 'active'
            AND next_expected_date IS NOT NULL
            AND next_expected_date <= date('now', '+' || ? || ' days')
            ORDER BY next_expected_date ASC
        """
        return self._fetchall(query, (user_id, days_ahead))

    def update(self, recurring_id: int, **kwargs) -> None:
        """
        Update recurring charge fields.

        Args:
            recurring_id: Recurring charge ID
            **kwargs: Fields to update
        """
        if not kwargs:
            return

        # Convert Decimal values to float for SQLite
        for key in ["typical_amount", "confidence"]:
            if key in kwargs and isinstance(kwargs[key], Decimal):
                kwargs[key] = float(kwargs[key])

        set_clause = ", ".join(f"{key} = ?" for key in kwargs.keys())
        query = f"UPDATE recurring_charges SET {set_clause} WHERE id = ?"

        self._execute(query, tuple(kwargs.values()) + (recurring_id,))

    def delete(self, recurring_id: int) -> None:
        """
        Delete recurring charge.

        Args:
            recurring_id: Recurring charge ID
        """
        query = "DELETE FROM recurring_charges WHERE id = ?"
        self._execute(query, (recurring_id,))

    def update_status(self, recurring_id: int, status: str) -> None:
        """
        Update recurring charge status.

        Args:
            recurring_id: Recurring charge ID
            status: New status ('active', 'paused', 'cancelled')
        """
        query = "UPDATE recurring_charges SET status = ? WHERE id = ?"
        self._execute(query, (status, recurring_id))
