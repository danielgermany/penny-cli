"""Transaction repository for database operations."""

from datetime import date
from decimal import Decimal
from typing import Optional
from .base import BaseRepository


class TransactionRepository(BaseRepository):
    """Repository for transaction database operations."""

    def create(
        self,
        user_id: int,
        account_id: int,
        date: date,
        amount: Decimal,
        type: str,
        merchant: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None,
        to_account_id: Optional[int] = None,
        transfer_pair_id: Optional[int] = None,
        status: str = "posted",
    ) -> int:
        """
        Create a new transaction.

        Args:
            user_id: User ID
            account_id: Account ID
            date: Transaction date
            amount: Transaction amount (always positive)
            type: Transaction type ('expense', 'income', 'transfer')
            merchant: Merchant name
            category: Category name
            subcategory: Subcategory name
            description: Transaction description
            notes: Additional notes
            to_account_id: Destination account for transfers
            transfer_pair_id: ID of paired transfer transaction
            status: Transaction status

        Returns:
            ID of created transaction
        """
        query = """
            INSERT INTO transactions
            (user_id, account_id, date, amount, type, merchant, category, subcategory,
             description, notes, to_account_id, transfer_pair_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self._execute(
            query,
            (
                user_id,
                account_id,
                date,
                float(amount),
                type,
                merchant,
                category,
                subcategory,
                description,
                notes,
                to_account_id,
                transfer_pair_id,
                status,
            ),
        )
        return cursor.lastrowid

    def get_by_id(self, tx_id: int) -> Optional[dict]:
        """
        Get transaction by ID.

        Args:
            tx_id: Transaction ID

        Returns:
            Transaction dict or None if not found
        """
        query = "SELECT * FROM transactions WHERE id = ?"
        return self._fetchone(query, (tx_id,))

    def get_recent(self, user_id: int, limit: int = 10) -> list[dict]:
        """
        Get most recent transactions for user.

        Args:
            user_id: User ID
            limit: Maximum number of transactions to return

        Returns:
            List of transaction dicts
        """
        query = """
            SELECT * FROM transactions
            WHERE user_id = ?
            ORDER BY date DESC, id DESC
            LIMIT ?
        """
        return self._fetchall(query, (user_id, limit))

    def get_by_month(self, user_id: int, year: int, month: int) -> list[dict]:
        """
        Get all transactions for a specific month.

        Args:
            user_id: User ID
            year: Year
            month: Month (1-12)

        Returns:
            List of transaction dicts
        """
        query = """
            SELECT * FROM transactions
            WHERE user_id = ?
            AND strftime('%Y', date) = ?
            AND strftime('%m', date) = ?
            ORDER BY date DESC, id DESC
        """
        return self._fetchall(query, (user_id, str(year), f"{month:02d}"))

    def get_by_category(
        self, user_id: int, category: str, year: Optional[int] = None, month: Optional[int] = None
    ) -> list[dict]:
        """
        Get transactions by category.

        Args:
            user_id: User ID
            category: Category name
            year: Optional year filter
            month: Optional month filter (1-12)

        Returns:
            List of transaction dicts
        """
        if year and month:
            query = """
                SELECT * FROM transactions
                WHERE user_id = ? AND category = ?
                AND strftime('%Y', date) = ?
                AND strftime('%m', date) = ?
                ORDER BY date DESC
            """
            return self._fetchall(query, (user_id, category, str(year), f"{month:02d}"))
        else:
            query = """
                SELECT * FROM transactions
                WHERE user_id = ? AND category = ?
                ORDER BY date DESC
            """
            return self._fetchall(query, (user_id, category))

    def update(self, tx_id: int, **kwargs) -> None:
        """
        Update transaction fields.

        Args:
            tx_id: Transaction ID
            **kwargs: Fields to update
        """
        if not kwargs:
            return

        # Build SET clause
        set_clause = ", ".join(f"{key} = ?" for key in kwargs.keys())
        query = f"UPDATE transactions SET {set_clause} WHERE id = ?"

        # Execute with values plus tx_id
        self._execute(query, tuple(kwargs.values()) + (tx_id,))

    def delete(self, tx_id: int) -> None:
        """
        Delete transaction.

        Args:
            tx_id: Transaction ID
        """
        query = "DELETE FROM transactions WHERE id = ?"
        self._execute(query, (tx_id,))

    def get_total_by_type(
        self, user_id: int, type: str, year: Optional[int] = None, month: Optional[int] = None
    ) -> Decimal:
        """
        Get total amount for transaction type.

        Args:
            user_id: User ID
            type: Transaction type ('expense', 'income')
            year: Optional year filter
            month: Optional month filter

        Returns:
            Total amount
        """
        if year and month:
            query = """
                SELECT COALESCE(SUM(amount), 0) as total
                FROM transactions
                WHERE user_id = ? AND type = ?
                AND strftime('%Y', date) = ?
                AND strftime('%m', date) = ?
            """
            result = self._fetchone(query, (user_id, type, str(year), f"{month:02d}"))
        else:
            query = """
                SELECT COALESCE(SUM(amount), 0) as total
                FROM transactions
                WHERE user_id = ? AND type = ?
            """
            result = self._fetchone(query, (user_id, type))

        return Decimal(str(result["total"])) if result else Decimal("0")

    def search(
        self,
        user_id: int,
        search_text: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        category: Optional[str] = None,
        account_id: Optional[int] = None,
        transaction_type: Optional[str] = None,
        tags: Optional[list[str]] = None,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """
        Search and filter transactions.

        Args:
            user_id: User ID
            search_text: Search in merchant, description, notes
            start_date: Start date filter
            end_date: End date filter
            min_amount: Minimum amount filter
            max_amount: Maximum amount filter
            category: Category filter
            account_id: Account filter
            transaction_type: Transaction type filter
            tags: Filter by tag names (returns transactions with ANY of these tags)
            limit: Maximum results to return

        Returns:
            List of matching transaction dicts
        """
        # Build dynamic query
        conditions = ["user_id = ?"]
        params = [user_id]

        if search_text:
            conditions.append(
                "(merchant LIKE ? OR description LIKE ? OR notes LIKE ?)"
            )
            search_pattern = f"%{search_text}%"
            params.extend([search_pattern, search_pattern, search_pattern])

        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)

        if min_amount is not None:
            conditions.append("amount >= ?")
            params.append(float(min_amount))

        if max_amount is not None:
            conditions.append("amount <= ?")
            params.append(float(max_amount))

        if category:
            conditions.append("category = ?")
            params.append(category)

        if account_id:
            conditions.append("account_id = ?")
            params.append(account_id)

        if transaction_type:
            conditions.append("type = ?")
            params.append(transaction_type)

        # Filter by tags (transactions with ANY of the specified tags)
        if tags:
            placeholders = ",".join("?" * len(tags))
            conditions.append(f"""
                id IN (
                    SELECT tt.transaction_id
                    FROM transaction_tags tt
                    JOIN tags t ON tt.tag_id = t.id
                    WHERE t.name IN ({placeholders})
                )
            """)
            # Normalize tag names to lowercase
            params.extend([tag.lower() for tag in tags])

        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT * FROM transactions
            WHERE {where_clause}
            ORDER BY date DESC, id DESC
        """

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        return self._fetchall(query, tuple(params))
