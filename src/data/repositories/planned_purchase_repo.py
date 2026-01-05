"""Planned purchase repository for database operations."""

from decimal import Decimal
from typing import Optional
from datetime import date
from .base import BaseRepository


class PlannedPurchaseRepository(BaseRepository):
    """Repository for planned purchase database operations."""

    def create(
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
    ) -> int:
        """
        Create a new planned purchase.

        Args:
            user_id: User ID
            name: Purchase name
            estimated_cost: Estimated cost
            priority: Priority level (1-5)
            description: Purchase description
            category: Category
            deadline: Target purchase date
            notes: Additional notes
            url: Product URL

        Returns:
            ID of created planned purchase
        """
        query = """
            INSERT INTO planned_purchases
            (user_id, name, estimated_cost, priority, description, category, deadline, notes, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self._execute(
            query,
            (user_id, name, float(estimated_cost), priority, description, category, deadline, notes, url),
        )
        return cursor.lastrowid

    def get_by_id(self, purchase_id: int) -> Optional[dict]:
        """
        Get planned purchase by ID.

        Args:
            purchase_id: Purchase ID

        Returns:
            Purchase dict or None if not found
        """
        query = "SELECT * FROM planned_purchases WHERE id = ?"
        return self._fetchone(query, (purchase_id,))

    def get_all(
        self,
        user_id: int,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        sort_by: str = "priority"
    ) -> list[dict]:
        """
        Get all planned purchases for user.

        Args:
            user_id: User ID
            status: Filter by status
            priority: Filter by priority level
            sort_by: Sort field (priority, deadline, created_at, cost)

        Returns:
            List of purchase dicts
        """
        conditions = ["user_id = ?"]
        params = [user_id]

        if status:
            conditions.append("status = ?")
            params.append(status)

        if priority is not None:
            conditions.append("priority = ?")
            params.append(priority)

        where_clause = " AND ".join(conditions)

        # Build ORDER BY clause
        if sort_by == "priority":
            order = "priority ASC, deadline ASC NULLS LAST, created_at DESC"
        elif sort_by == "deadline":
            order = "deadline ASC NULLS LAST, priority ASC"
        elif sort_by == "cost":
            order = "estimated_cost DESC"
        else:  # created_at
            order = "created_at DESC"

        query = f"""
            SELECT * FROM planned_purchases
            WHERE {where_clause}
            ORDER BY {order}
        """
        return self._fetchall(query, tuple(params))

    def update(self, purchase_id: int, **kwargs) -> None:
        """
        Update planned purchase fields.

        Args:
            purchase_id: Purchase ID
            **kwargs: Fields to update
        """
        if not kwargs:
            return

        # Convert Decimal values to float for SQLite
        for key in ["estimated_cost", "actual_cost"]:
            if key in kwargs and isinstance(kwargs[key], Decimal):
                kwargs[key] = float(kwargs[key])

        # Update updated_at timestamp
        kwargs["updated_at"] = "CURRENT_TIMESTAMP"

        set_clause = ", ".join(f"{key} = ?" for key in kwargs.keys())
        query = f"UPDATE planned_purchases SET {set_clause} WHERE id = ?"

        # Handle CURRENT_TIMESTAMP specially
        params = []
        for key, value in kwargs.items():
            if value == "CURRENT_TIMESTAMP":
                # Need to reconstruct query to handle SQL functions
                continue
            params.append(value)

        # Rebuild query properly for CURRENT_TIMESTAMP
        set_parts = []
        params = []
        for key, value in kwargs.items():
            if value == "CURRENT_TIMESTAMP":
                set_parts.append(f"{key} = CURRENT_TIMESTAMP")
            else:
                set_parts.append(f"{key} = ?")
                params.append(value)

        set_clause = ", ".join(set_parts)
        query = f"UPDATE planned_purchases SET {set_clause} WHERE id = ?"
        params.append(purchase_id)

        self._execute(query, tuple(params))

    def mark_purchased(
        self,
        purchase_id: int,
        actual_cost: Decimal,
        transaction_id: Optional[int] = None
    ) -> None:
        """
        Mark a planned purchase as purchased.

        Args:
            purchase_id: Purchase ID
            actual_cost: Actual cost paid
            transaction_id: Optional linked transaction ID
        """
        query = """
            UPDATE planned_purchases
            SET status = 'purchased',
                actual_cost = ?,
                purchased_transaction_id = ?,
                purchased_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        self._execute(query, (float(actual_cost), transaction_id, purchase_id))

    def cancel(self, purchase_id: int) -> None:
        """
        Cancel a planned purchase.

        Args:
            purchase_id: Purchase ID
        """
        query = """
            UPDATE planned_purchases
            SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        self._execute(query, (purchase_id,))

    def delete(self, purchase_id: int) -> None:
        """
        Delete a planned purchase.

        Args:
            purchase_id: Purchase ID
        """
        query = "DELETE FROM planned_purchases WHERE id = ?"
        self._execute(query, (purchase_id,))

    def get_total_planned_cost(self, user_id: int, status: str = "planned") -> Decimal:
        """
        Get total cost of planned purchases.

        Args:
            user_id: User ID
            status: Status filter

        Returns:
            Total estimated cost
        """
        query = """
            SELECT COALESCE(SUM(estimated_cost), 0) as total
            FROM planned_purchases
            WHERE user_id = ? AND status = ?
        """
        result = self._fetchone(query, (user_id, status))
        return Decimal(str(result["total"])) if result else Decimal("0")

    def get_by_priority(self, user_id: int, priority: int, status: str = "planned") -> list[dict]:
        """
        Get all planned purchases of a specific priority.

        Args:
            user_id: User ID
            priority: Priority level (1-5)
            status: Status filter

        Returns:
            List of purchase dicts
        """
        query = """
            SELECT * FROM planned_purchases
            WHERE user_id = ? AND priority = ? AND status = ?
            ORDER BY deadline ASC NULLS LAST, created_at DESC
        """
        return self._fetchall(query, (user_id, priority, status))

    def get_overdue(self, user_id: int) -> list[dict]:
        """
        Get planned purchases past their deadline.

        Args:
            user_id: User ID

        Returns:
            List of overdue purchase dicts
        """
        query = """
            SELECT * FROM planned_purchases
            WHERE user_id = ?
            AND status = 'planned'
            AND deadline IS NOT NULL
            AND deadline < date('now')
            ORDER BY deadline ASC
        """
        return self._fetchall(query, (user_id,))
