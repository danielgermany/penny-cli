"""Transaction service for business logic."""

from decimal import Decimal
from datetime import date, datetime
from typing import Optional
from ..exceptions import TransactionNotFoundError, InvalidTransactionError


class TransactionService:
    """Service for transaction operations."""

    def __init__(self, transaction_repo, account_service, category_rule_repo, ai_client):
        """
        Initialize transaction service.

        Args:
            transaction_repo: Transaction repository instance
            account_service: Account service instance
            category_rule_repo: Category rule repository instance
            ai_client: AI client for categorization
        """
        self.repo = transaction_repo
        self.account_service = account_service
        self.category_rule_repo = category_rule_repo
        self.ai = ai_client

    def create_from_text(
        self,
        user_id: int,
        account_id: int,
        description: str,
        transaction_date: Optional[date] = None,
        override_category: Optional[str] = None,
    ) -> dict:
        """
        Create transaction from natural language description.

        Args:
            user_id: User ID
            account_id: Account ID
            description: Transaction description (e.g., "coffee $5")
            transaction_date: Optional transaction date (defaults to today)
            override_category: Override AI categorization

        Returns:
            Created transaction dict

        Example:
            create_from_text(1, 1, "Starbucks $5.50")
            create_from_text(1, 1, "Grocery shopping at Whole Foods $87.32")
        """
        # Parse with AI
        parsed = self.ai.parse_transaction(description)

        merchant = parsed["merchant"]
        amount = Decimal(str(parsed["amount"]))
        category = override_category or parsed["category"]
        confidence = parsed.get("confidence", 0.8)

        # Check for cached rule first
        if not override_category:
            cached_rule = self.category_rule_repo.get_by_merchant(user_id, merchant)
            if cached_rule:
                category = cached_rule["category"]
                self.category_rule_repo.update_usage(cached_rule["id"])
            elif confidence >= 0.8:
                # Cache AI categorization if confident
                self.category_rule_repo.upsert(
                    user_id=user_id,
                    merchant=merchant,
                    category=category,
                    confidence=Decimal(str(confidence)),
                    source="ai",
                )

        # Create transaction
        tx_date = transaction_date or date.today()
        tx_id = self.repo.create(
            user_id=user_id,
            account_id=account_id,
            date=tx_date,
            amount=amount,
            merchant=merchant,
            category=category,
            description=description,
            type="expense",
        )

        # Update account balance
        self.account_service.adjust_balance(account_id, -amount)

        return self.repo.get_by_id(tx_id)

    def create_transaction(
        self,
        user_id: int,
        account_id: int,
        amount: Decimal,
        type: str,
        transaction_date: Optional[date] = None,
        merchant: Optional[str] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """
        Create transaction with explicit fields.

        Args:
            user_id: User ID
            account_id: Account ID
            amount: Transaction amount (always positive)
            type: Transaction type ('expense', 'income', 'transfer')
            transaction_date: Transaction date
            merchant: Merchant name
            category: Category
            description: Description
            notes: Additional notes

        Returns:
            Created transaction dict
        """
        if amount <= 0:
            raise InvalidTransactionError("Amount must be positive")

        valid_types = ["expense", "income", "transfer"]
        if type not in valid_types:
            raise InvalidTransactionError(f"Invalid type. Must be one of: {', '.join(valid_types)}")

        tx_date = transaction_date or date.today()
        tx_id = self.repo.create(
            user_id=user_id,
            account_id=account_id,
            date=tx_date,
            amount=amount,
            type=type,
            merchant=merchant,
            category=category,
            description=description,
            notes=notes,
        )

        # Update account balance
        if type == "expense":
            self.account_service.adjust_balance(account_id, -amount)
        elif type == "income":
            self.account_service.adjust_balance(account_id, amount)

        return self.repo.get_by_id(tx_id)

    def create_transfer(
        self,
        user_id: int,
        from_account_id: int,
        to_account_id: int,
        amount: Decimal,
        transaction_date: Optional[date] = None,
        description: str = "Transfer",
    ) -> tuple[dict, dict]:
        """
        Create transfer between accounts.

        Args:
            user_id: User ID
            from_account_id: Source account ID
            to_account_id: Destination account ID
            amount: Transfer amount
            transaction_date: Transaction date
            description: Transfer description

        Returns:
            Tuple of (outgoing transaction, incoming transaction)
        """
        if amount <= 0:
            raise InvalidTransactionError("Amount must be positive")

        if from_account_id == to_account_id:
            raise InvalidTransactionError("Cannot transfer to same account")

        # Verify accounts exist
        from_account = self.account_service.get_account(from_account_id)
        to_account = self.account_service.get_account(to_account_id)

        tx_date = transaction_date or date.today()

        # Create outgoing transaction
        tx_out_id = self.repo.create(
            user_id=user_id,
            account_id=from_account_id,
            date=tx_date,
            amount=amount,
            type="transfer",
            to_account_id=to_account_id,
            description=f"{description} (to {to_account['name']})",
        )

        # Create incoming transaction
        tx_in_id = self.repo.create(
            user_id=user_id,
            account_id=to_account_id,
            date=tx_date,
            amount=amount,
            type="transfer",
            description=f"{description} (from {from_account['name']})",
            transfer_pair_id=tx_out_id,
        )

        # Link them
        self.repo.update(tx_out_id, transfer_pair_id=tx_in_id)

        # Update balances
        self.account_service.adjust_balance(from_account_id, -amount)
        self.account_service.adjust_balance(to_account_id, amount)

        return (self.repo.get_by_id(tx_out_id), self.repo.get_by_id(tx_in_id))

    def get_transaction(self, tx_id: int) -> dict:
        """
        Get transaction by ID.

        Args:
            tx_id: Transaction ID

        Returns:
            Transaction dict

        Raises:
            TransactionNotFoundError: If transaction not found
        """
        tx = self.repo.get_by_id(tx_id)
        if not tx:
            raise TransactionNotFoundError(f"Transaction with ID {tx_id} not found")
        return tx

    def list_recent(self, user_id: int, limit: int = 10) -> list[dict]:
        """
        Get recent transactions.

        Args:
            user_id: User ID
            limit: Maximum number of transactions

        Returns:
            List of transaction dicts
        """
        return self.repo.get_recent(user_id, limit)

    def list_by_month(self, user_id: int, year: Optional[int] = None, month: Optional[int] = None) -> list[dict]:
        """
        Get transactions for a specific month.

        Args:
            user_id: User ID
            year: Year (defaults to current year)
            month: Month 1-12 (defaults to current month)

        Returns:
            List of transaction dicts
        """
        now = datetime.now()
        year = year or now.year
        month = month or now.month

        return self.repo.get_by_month(user_id, year, month)

    def delete_transaction(self, tx_id: int) -> None:
        """
        Delete transaction and reverse balance changes.

        Args:
            tx_id: Transaction ID

        Raises:
            TransactionNotFoundError: If transaction not found
        """
        tx = self.get_transaction(tx_id)

        # Reverse balance change
        amount = Decimal(str(tx["amount"]))
        if tx["type"] == "expense":
            self.account_service.adjust_balance(tx["account_id"], amount)
        elif tx["type"] == "income":
            self.account_service.adjust_balance(tx["account_id"], -amount)
        elif tx["type"] == "transfer":
            # Reverse both sides
            self.account_service.adjust_balance(tx["account_id"], amount)
            if tx["to_account_id"]:
                self.account_service.adjust_balance(tx["to_account_id"], -amount)

        self.repo.delete(tx_id)

    def get_monthly_total(
        self, user_id: int, type: str = "expense", year: Optional[int] = None, month: Optional[int] = None
    ) -> Decimal:
        """
        Get total for transaction type in month.

        Args:
            user_id: User ID
            type: Transaction type ('expense' or 'income')
            year: Year (defaults to current)
            month: Month (defaults to current)

        Returns:
            Total amount
        """
        now = datetime.now()
        year = year or now.year
        month = month or now.month

        return self.repo.get_total_by_type(user_id, type, year, month)

    def search_transactions(
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
            limit: Maximum results to return

        Returns:
            List of matching transaction dicts
        """
        return self.repo.search(
            user_id=user_id,
            search_text=search_text,
            start_date=start_date,
            end_date=end_date,
            min_amount=min_amount,
            max_amount=max_amount,
            category=category,
            account_id=account_id,
            transaction_type=transaction_type,
            limit=limit,
        )
