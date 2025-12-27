"""Budget service for business logic."""

from decimal import Decimal
from datetime import datetime
from typing import Optional
from ..exceptions import BudgetNotFoundError


class BudgetService:
    """Service for budget operations."""

    def __init__(self, budget_repo, transaction_repo):
        """
        Initialize budget service.

        Args:
            budget_repo: Budget repository instance
            transaction_repo: Transaction repository instance
        """
        self.budget_repo = budget_repo
        self.transaction_repo = transaction_repo

    def create_budget(
        self,
        user_id: int,
        category: str,
        monthly_limit: Decimal,
        alert_threshold: Decimal = Decimal("0.9"),
    ) -> dict:
        """
        Create a new budget.

        Args:
            user_id: User ID
            category: Category name
            monthly_limit: Monthly spending limit
            alert_threshold: Alert when spending reaches this % of limit

        Returns:
            Created budget dict

        Raises:
            ValueError: If budget already exists for category
        """
        # Check if budget already exists
        existing = self.budget_repo.get_by_category(user_id, category)
        if existing:
            raise ValueError(f"Budget for category '{category}' already exists")

        budget_id = self.budget_repo.create(
            user_id=user_id,
            category=category,
            monthly_limit=monthly_limit,
            alert_threshold=alert_threshold,
        )

        return self.budget_repo.get_by_id(budget_id)

    def get_budget(self, budget_id: int) -> dict:
        """
        Get budget by ID.

        Args:
            budget_id: Budget ID

        Returns:
            Budget dict

        Raises:
            BudgetNotFoundError: If budget not found
        """
        budget = self.budget_repo.get_by_id(budget_id)
        if not budget:
            raise BudgetNotFoundError(f"Budget with ID {budget_id} not found")
        return budget

    def list_budgets(self, user_id: int) -> list[dict]:
        """
        Get all budgets for user.

        Args:
            user_id: User ID

        Returns:
            List of budget dicts
        """
        return self.budget_repo.get_all(user_id)

    def get_budget_status(
        self, user_id: int, category: str, year: Optional[int] = None, month: Optional[int] = None
    ) -> dict:
        """
        Get budget status for category in specific month.

        Args:
            user_id: User ID
            category: Category name
            year: Year (defaults to current)
            month: Month (defaults to current)

        Returns:
            Dict with budget status:
                - budget: Budget dict
                - spent: Amount spent
                - remaining: Amount remaining
                - percentage: Percentage of budget used
                - is_over: Whether over budget
                - should_alert: Whether alert threshold reached
        """
        now = datetime.now()
        year = year or now.year
        month = month or now.month

        # Get budget
        budget = self.budget_repo.get_by_category(user_id, category)
        if not budget:
            return None

        # Get spending for category
        transactions = self.transaction_repo.get_by_category(user_id, category, year, month)
        spent = sum(Decimal(str(tx["amount"])) for tx in transactions if tx["type"] == "expense")

        limit = Decimal(str(budget["monthly_limit"]))
        remaining = limit - spent
        percentage = (spent / limit * 100) if limit > 0 else Decimal("0")
        alert_threshold = Decimal(str(budget["alert_threshold"])) * 100

        return {
            "budget": budget,
            "spent": spent,
            "remaining": remaining,
            "limit": limit,
            "percentage": percentage,
            "is_over": spent > limit,
            "should_alert": percentage >= alert_threshold,
        }

    def get_all_budget_status(self, user_id: int, year: Optional[int] = None, month: Optional[int] = None) -> list[dict]:
        """
        Get budget status for all budgets.

        Args:
            user_id: User ID
            year: Year (defaults to current)
            month: Month (defaults to current)

        Returns:
            List of budget status dicts
        """
        budgets = self.list_budgets(user_id)
        return [self.get_budget_status(user_id, budget["category"], year, month) for budget in budgets]

    def update_budget(self, budget_id: int, **kwargs) -> dict:
        """
        Update budget.

        Args:
            budget_id: Budget ID
            **kwargs: Fields to update

        Returns:
            Updated budget dict
        """
        self.budget_repo.update(budget_id, **kwargs)
        return self.get_budget(budget_id)

    def delete_budget(self, budget_id: int) -> None:
        """
        Delete budget.

        Args:
            budget_id: Budget ID
        """
        self.budget_repo.delete(budget_id)
