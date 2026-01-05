"""Planned purchase service for managing shopping lists and purchase planning."""

from decimal import Decimal
from datetime import date, timedelta, datetime
from typing import Optional


class PlannedPurchaseService:
    """Service for planned purchase management and affordability analysis."""

    # Priority level mappings
    PRIORITY_LABELS = {
        1: "Critical/Necessity",
        2: "High Priority",
        3: "Moderate",
        4: "Low Priority",
        5: "Want/Luxury"
    }

    def __init__(self, planned_purchase_repo, account_service, budget_service, decision_support_service):
        """
        Initialize planned purchase service.

        Args:
            planned_purchase_repo: PlannedPurchaseRepository instance
            account_service: AccountService instance
            budget_service: BudgetService instance
            decision_support_service: DecisionSupportService instance
        """
        self.repo = planned_purchase_repo
        self.account_service = account_service
        self.budget_service = budget_service
        self.decision_support_service = decision_support_service

    def create_purchase(
        self,
        user_id: int,
        name: str,
        estimated_cost: Decimal,
        priority: int = 3,
        description: Optional[str] = None,
        category: Optional[str] = None,
        deadline: Optional[date] = None,
        notes: Optional[str] = None,
        url: Optional[str] = None,
    ) -> dict:
        """
        Create a new planned purchase.

        Args:
            user_id: User ID
            name: Purchase name
            estimated_cost: Estimated cost
            priority: Priority level (1-5)
            description: Description
            category: Category
            deadline: Target purchase date
            notes: Additional notes
            url: Product URL

        Returns:
            Created purchase dict

        Raises:
            ValueError: If inputs are invalid
        """
        if estimated_cost <= 0:
            raise ValueError("Estimated cost must be positive")

        if priority < 1 or priority > 5:
            raise ValueError("Priority must be between 1 (critical) and 5 (want)")

        if deadline and deadline < date.today():
            raise ValueError("Deadline cannot be in the past")

        purchase_id = self.repo.create(
            user_id=user_id,
            name=name,
            estimated_cost=estimated_cost,
            priority=priority,
            description=description,
            category=category,
            deadline=deadline,
            notes=notes,
            url=url
        )

        return self.repo.get_by_id(purchase_id)

    def list_purchases(
        self,
        user_id: int,
        status: str = "planned",
        priority: Optional[int] = None,
        sort_by: str = "priority",
        show_affordability: bool = False
    ) -> list[dict]:
        """
        List planned purchases with optional affordability info.

        Args:
            user_id: User ID
            status: Status filter
            priority: Priority filter
            sort_by: Sort field
            show_affordability: Include affordability analysis

        Returns:
            List of purchase dicts with optional affordability data
        """
        purchases = self.repo.get_all(user_id, status, priority, sort_by)

        if show_affordability:
            # Get total available balance
            accounts = self.account_service.list_accounts(user_id)
            total_balance = sum(Decimal(str(acc["current_balance"])) for acc in accounts)

            running_balance = total_balance

            for purchase in purchases:
                cost = Decimal(str(purchase["estimated_cost"]))
                purchase["can_afford"] = running_balance >= cost
                purchase["balance_after"] = running_balance - cost
                running_balance -= cost if purchase["can_afford"] else Decimal("0")

        return purchases

    def get_purchase(self, purchase_id: int) -> Optional[dict]:
        """
        Get a single planned purchase.

        Args:
            purchase_id: Purchase ID

        Returns:
            Purchase dict or None
        """
        return self.repo.get_by_id(purchase_id)

    def update_purchase(self, purchase_id: int, **kwargs) -> dict:
        """
        Update a planned purchase.

        Args:
            purchase_id: Purchase ID
            **kwargs: Fields to update

        Returns:
            Updated purchase dict
        """
        # Validate priority if being updated
        if "priority" in kwargs:
            priority = kwargs["priority"]
            if priority < 1 or priority > 5:
                raise ValueError("Priority must be between 1 and 5")

        # Validate deadline if being updated
        if "deadline" in kwargs and kwargs["deadline"]:
            if kwargs["deadline"] < date.today():
                raise ValueError("Deadline cannot be in the past")

        self.repo.update(purchase_id, **kwargs)
        return self.repo.get_by_id(purchase_id)

    def mark_purchased(
        self,
        purchase_id: int,
        actual_cost: Decimal,
        transaction_id: Optional[int] = None
    ) -> dict:
        """
        Mark a purchase as completed.

        Args:
            purchase_id: Purchase ID
            actual_cost: Actual amount paid
            transaction_id: Optional linked transaction

        Returns:
            Updated purchase dict
        """
        self.repo.mark_purchased(purchase_id, actual_cost, transaction_id)
        return self.repo.get_by_id(purchase_id)

    def cancel_purchase(self, purchase_id: int) -> None:
        """
        Cancel a planned purchase.

        Args:
            purchase_id: Purchase ID
        """
        self.repo.cancel(purchase_id)

    def delete_purchase(self, purchase_id: int) -> None:
        """
        Delete a planned purchase.

        Args:
            purchase_id: Purchase ID
        """
        self.repo.delete(purchase_id)

    def get_affordability_analysis(self, user_id: int) -> dict:
        """
        Analyze which planned purchases can be afforded.

        Args:
            user_id: User ID

        Returns:
            Dict with affordability analysis
        """
        purchases = self.repo.get_all(user_id, status="planned", sort_by="priority")

        # Get current balance
        accounts = self.account_service.list_accounts(user_id)
        total_balance = sum(Decimal(str(acc["current_balance"])) for acc in accounts)

        analysis = {
            "total_balance": total_balance,
            "total_planned": self.repo.get_total_planned_cost(user_id),
            "can_afford_all": False,
            "by_priority": {},
            "affordable": [],
            "unaffordable": []
        }

        # Analyze by priority
        running_balance = total_balance
        for priority in range(1, 6):
            priority_items = [p for p in purchases if p["priority"] == priority]
            priority_cost = sum(Decimal(str(p["estimated_cost"])) for p in priority_items)

            analysis["by_priority"][priority] = {
                "label": self.PRIORITY_LABELS[priority],
                "count": len(priority_items),
                "total_cost": priority_cost,
                "can_afford_all": running_balance >= priority_cost,
                "balance_after": running_balance - priority_cost
            }

            running_balance -= priority_cost if running_balance >= priority_cost else Decimal("0")

        # Categorize individual items
        running_balance = total_balance
        for purchase in purchases:
            cost = Decimal(str(purchase["estimated_cost"]))
            if running_balance >= cost:
                analysis["affordable"].append(purchase)
                running_balance -= cost
            else:
                analysis["unaffordable"].append(purchase)

        analysis["can_afford_all"] = len(analysis["unaffordable"]) == 0

        return analysis

    def get_purchase_recommendations(self, user_id: int) -> dict:
        """
        Get AI-powered recommendations for purchase timing.

        Args:
            user_id: User ID

        Returns:
            Dict with recommendations
        """
        purchases = self.repo.get_all(user_id, status="planned", sort_by="priority")

        if not purchases:
            return {
                "recommendations": [],
                "summary": "No planned purchases found"
            }

        analysis = self.get_affordability_analysis(user_id)

        recommendations = {
            "now": [],
            "soon": [],
            "later": [],
            "skip": []
        }

        # Categorize based on priority, affordability, and deadline
        for purchase in purchases:
            cost = Decimal(str(purchase["estimated_cost"]))
            priority = purchase["priority"]
            deadline = purchase.get("deadline")

            # Check if affordable
            affordable = purchase in analysis["affordable"]

            # Check deadline urgency
            urgent = False
            if deadline:
                # Parse deadline string to date object
                deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
                days_until = (deadline_date - date.today()).days
                urgent = days_until <= 7

            # Make recommendation
            if priority <= 2:  # Critical/High priority
                if affordable and urgent:
                    recommendations["now"].append(purchase)
                elif affordable:
                    recommendations["soon"].append(purchase)
                elif urgent:
                    recommendations["now"].append(purchase)  # Critical even if not affordable
                else:
                    recommendations["later"].append(purchase)
            elif priority == 3:  # Moderate
                if affordable and urgent:
                    recommendations["now"].append(purchase)
                elif affordable:
                    recommendations["soon"].append(purchase)
                else:
                    recommendations["later"].append(purchase)
            else:  # Low priority/Wants
                if affordable and not analysis["by_priority"][1]["can_afford_all"]:
                    # Can afford but have higher priorities
                    recommendations["skip"].append(purchase)
                elif affordable:
                    recommendations["later"].append(purchase)
                else:
                    recommendations["skip"].append(purchase)

        summary_parts = []
        if recommendations["now"]:
            summary_parts.append(f"{len(recommendations['now'])} to buy now")
        if recommendations["soon"]:
            summary_parts.append(f"{len(recommendations['soon'])} to buy soon")
        if recommendations["skip"]:
            summary_parts.append(f"{len(recommendations['skip'])} to skip/delay")

        return {
            "recommendations": recommendations,
            "summary": ", ".join(summary_parts) if summary_parts else "No recommendations",
            "analysis": analysis
        }

    def get_overdue_purchases(self, user_id: int) -> list[dict]:
        """
        Get purchases past their deadline.

        Args:
            user_id: User ID

        Returns:
            List of overdue purchases
        """
        return self.repo.get_overdue(user_id)

    @staticmethod
    def get_priority_label(priority: int) -> str:
        """Get human-readable label for priority level."""
        return PlannedPurchaseService.PRIORITY_LABELS.get(priority, "Unknown")
