"""Savings goal service for managing financial goals."""

from decimal import Decimal
from datetime import date, timedelta
from typing import Optional


class SavingsGoalService:
    """Service for savings goal management."""

    def __init__(self, savings_goal_repo, transaction_repo, analytics_service):
        """
        Initialize savings goal service.

        Args:
            savings_goal_repo: Savings goal repository instance
            transaction_repo: Transaction repository instance
            analytics_service: Analytics service instance
        """
        self.savings_goal_repo = savings_goal_repo
        self.transaction_repo = transaction_repo
        self.analytics_service = analytics_service

    def create_goal(
        self,
        user_id: int,
        name: str,
        target_amount: Decimal,
        description: Optional[str] = None,
        deadline: Optional[date] = None,
        category: Optional[str] = None,
        priority: int = 5,
        notes: Optional[str] = None,
    ) -> dict:
        """
        Create a new savings goal.

        Args:
            user_id: User ID
            name: Goal name
            target_amount: Target amount to save
            description: Goal description
            deadline: Target completion date
            category: Goal category
            priority: Priority level (1-10)
            notes: Additional notes

        Returns:
            Created savings goal dict
        """
        if target_amount <= 0:
            raise ValueError("Target amount must be positive")

        if priority < 1 or priority > 10:
            raise ValueError("Priority must be between 1 and 10")

        if deadline and deadline < date.today():
            raise ValueError("Deadline cannot be in the past")

        goal_id = self.savings_goal_repo.create(
            user_id=user_id,
            name=name,
            target_amount=target_amount,
            description=description,
            deadline=deadline,
            category=category,
            priority=priority,
            notes=notes,
        )

        return self.savings_goal_repo.get_by_id(goal_id)

    def get_goal(self, goal_id: int) -> Optional[dict]:
        """
        Get savings goal by ID.

        Args:
            goal_id: Savings goal ID

        Returns:
            Savings goal dict or None
        """
        return self.savings_goal_repo.get_by_id(goal_id)

    def get_goal_by_name(self, user_id: int, name: str) -> Optional[dict]:
        """
        Get savings goal by name.

        Args:
            user_id: User ID
            name: Goal name

        Returns:
            Savings goal dict or None
        """
        return self.savings_goal_repo.get_by_name(user_id, name)

    def list_goals(self, user_id: int, status: Optional[str] = None) -> list[dict]:
        """
        List all savings goals for user.

        Args:
            user_id: User ID
            status: Filter by status

        Returns:
            List of savings goal dicts with progress info
        """
        goals = self.savings_goal_repo.get_all(user_id, status)

        # Enhance with progress calculations
        for goal in goals:
            goal["progress"] = self._calculate_progress(goal)

        return goals

    def update_goal(self, goal_id: int, **kwargs) -> dict:
        """
        Update savings goal.

        Args:
            goal_id: Savings goal ID
            **kwargs: Fields to update

        Returns:
            Updated savings goal dict
        """
        # Validate updates
        if "target_amount" in kwargs and kwargs["target_amount"] <= 0:
            raise ValueError("Target amount must be positive")

        if "priority" in kwargs:
            priority = kwargs["priority"]
            if priority < 1 or priority > 10:
                raise ValueError("Priority must be between 1 and 10")

        if "deadline" in kwargs and kwargs["deadline"]:
            if kwargs["deadline"] < date.today():
                raise ValueError("Deadline cannot be in the past")

        self.savings_goal_repo.update(goal_id, **kwargs)
        return self.savings_goal_repo.get_by_id(goal_id)

    def add_contribution(self, goal_id: int, amount: Decimal, description: Optional[str] = None) -> dict:
        """
        Add contribution to savings goal.

        Args:
            goal_id: Savings goal ID
            amount: Amount to contribute
            description: Optional description

        Returns:
            Updated savings goal dict with progress
        """
        if amount <= 0:
            raise ValueError("Contribution amount must be positive")

        goal = self.savings_goal_repo.get_by_id(goal_id)
        if not goal:
            raise ValueError(f"Savings goal {goal_id} not found")

        if goal["status"] != "active":
            raise ValueError(f"Cannot contribute to {goal['status']} goal")

        # Add contribution
        self.savings_goal_repo.add_contribution(goal_id, amount)

        # Check if goal is now complete
        updated_goal = self.savings_goal_repo.get_by_id(goal_id)
        current = Decimal(str(updated_goal["current_amount"]))
        target = Decimal(str(updated_goal["target_amount"]))

        if current >= target:
            self.savings_goal_repo.update_status(goal_id, "completed")
            updated_goal = self.savings_goal_repo.get_by_id(goal_id)

        # Add progress info
        updated_goal["progress"] = self._calculate_progress(updated_goal)

        return updated_goal

    def withdraw(self, goal_id: int, amount: Decimal, reason: Optional[str] = None) -> dict:
        """
        Withdraw from savings goal.

        Args:
            goal_id: Savings goal ID
            amount: Amount to withdraw
            reason: Optional reason for withdrawal

        Returns:
            Updated savings goal dict
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")

        goal = self.savings_goal_repo.get_by_id(goal_id)
        if not goal:
            raise ValueError(f"Savings goal {goal_id} not found")

        current = Decimal(str(goal["current_amount"]))
        if amount > current:
            raise ValueError(f"Cannot withdraw ${amount}. Current balance is ${current}")

        # Set new amount
        new_amount = current - amount
        self.savings_goal_repo.set_amount(goal_id, new_amount)

        updated_goal = self.savings_goal_repo.get_by_id(goal_id)
        updated_goal["progress"] = self._calculate_progress(updated_goal)

        return updated_goal

    def update_status(self, goal_id: int, status: str) -> dict:
        """
        Update savings goal status.

        Args:
            goal_id: Savings goal ID
            status: New status

        Returns:
            Updated savings goal dict
        """
        valid_statuses = ["active", "completed", "paused", "cancelled"]
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")

        self.savings_goal_repo.update_status(goal_id, status)
        return self.savings_goal_repo.get_by_id(goal_id)

    def delete_goal(self, goal_id: int) -> None:
        """
        Delete savings goal.

        Args:
            goal_id: Savings goal ID
        """
        goal = self.savings_goal_repo.get_by_id(goal_id)
        if not goal:
            raise ValueError(f"Savings goal {goal_id} not found")

        self.savings_goal_repo.delete(goal_id)

    def get_recommendations(self, user_id: int, goal_id: int) -> dict:
        """
        Get savings recommendations for a goal.

        Args:
            user_id: User ID
            goal_id: Savings goal ID

        Returns:
            Dict with recommendations and projections
        """
        goal = self.savings_goal_repo.get_by_id(goal_id)
        if not goal:
            raise ValueError(f"Savings goal {goal_id} not found")

        progress = self._calculate_progress(goal)

        recommendations = {
            "goal": goal,
            "progress": progress,
            "suggestions": []
        }

        # Calculate required monthly/weekly savings
        if goal["deadline"] and progress["remaining"] > 0:
            # Parse deadline if it's a string (from SQLite)
            deadline_date = goal["deadline"]
            if isinstance(deadline_date, str):
                from datetime import datetime
                deadline_date = datetime.strptime(deadline_date, "%Y-%m-%d").date()

            days_left = (deadline_date - date.today()).days

            if days_left > 0:
                daily_needed = progress["remaining"] / Decimal(str(days_left))
                weekly_needed = daily_needed * 7
                monthly_needed = daily_needed * 30

                recommendations["required_savings"] = {
                    "daily": daily_needed,
                    "weekly": weekly_needed,
                    "monthly": monthly_needed,
                    "days_remaining": days_left
                }

                # Add suggestions based on spending patterns
                try:
                    trends = self.analytics_service.get_spending_trends(user_id, weeks=4)
                    avg_weekly_spending = sum(w["total"] for w in trends["weekly_data"]) / len(trends["weekly_data"])

                    savings_percentage = (weekly_needed / avg_weekly_spending) * 100 if avg_weekly_spending > 0 else 0

                    if savings_percentage > 0:
                        recommendations["suggestions"].append(
                            f"Save {savings_percentage:.1f}% of your weekly spending (${weekly_needed:.2f}/week)"
                        )

                    if savings_percentage > 30:
                        recommendations["suggestions"].append(
                            "Consider extending deadline or reducing discretionary spending"
                        )
                except:
                    pass

        # Suggest contribution frequency based on progress
        if progress["percentage"] < 25:
            recommendations["suggestions"].append("Get started! Make your first contribution to build momentum")
        elif progress["percentage"] < 50:
            recommendations["suggestions"].append("You're making progress! Consider automating weekly contributions")
        elif progress["percentage"] < 75:
            recommendations["suggestions"].append("Great progress! You're over halfway there")
        else:
            recommendations["suggestions"].append("Almost there! Just a bit more to reach your goal")

        return recommendations

    def _calculate_progress(self, goal: dict) -> dict:
        """
        Calculate progress metrics for a goal.

        Args:
            goal: Savings goal dict

        Returns:
            Dict with progress metrics
        """
        current = Decimal(str(goal["current_amount"]))
        target = Decimal(str(goal["target_amount"]))

        remaining = max(Decimal("0"), target - current)
        percentage = min(Decimal("100"), (current / target * 100)) if target > 0 else Decimal("0")

        progress = {
            "current": current,
            "target": target,
            "remaining": remaining,
            "percentage": float(percentage),
            "is_complete": current >= target
        }

        # Calculate projected completion date if deadline exists
        if goal["deadline"] and not progress["is_complete"]:
            # Parse deadline if it's a string (from SQLite)
            deadline_date = goal["deadline"]
            if isinstance(deadline_date, str):
                from datetime import datetime
                deadline_date = datetime.strptime(deadline_date, "%Y-%m-%d").date()

            days_until_deadline = (deadline_date - date.today()).days
            progress["days_until_deadline"] = days_until_deadline

            if days_until_deadline > 0:
                progress["on_track"] = True  # We'll enhance this with historical data later
            else:
                progress["on_track"] = False
                progress["overdue_days"] = abs(days_until_deadline)

        return progress
