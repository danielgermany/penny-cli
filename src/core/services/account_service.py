"""Account service for business logic."""

from decimal import Decimal
from typing import Optional
from ..exceptions import AccountNotFoundError


class AccountService:
    """Service for account operations."""

    def __init__(self, account_repo):
        """
        Initialize account service.

        Args:
            account_repo: Account repository instance
        """
        self.repo = account_repo

    def create_account(
        self,
        user_id: int,
        name: str,
        type: str,
        institution: Optional[str] = None,
        initial_balance: Decimal = Decimal("0"),
        notes: Optional[str] = None,
    ) -> dict:
        """
        Create a new account.

        Args:
            user_id: User ID
            name: Account name
            type: Account type ('checking', 'savings', 'credit_card', 'investment')
            institution: Financial institution name
            initial_balance: Starting balance
            notes: Additional notes

        Returns:
            Created account dict

        Raises:
            ValueError: If account with name already exists
        """
        # Check if account with same name exists
        existing = self.repo.get_by_name(user_id, name)
        if existing:
            raise ValueError(f"Account with name '{name}' already exists")

        # Validate type
        valid_types = ["checking", "savings", "credit_card", "investment"]
        if type not in valid_types:
            raise ValueError(f"Invalid account type. Must be one of: {', '.join(valid_types)}")

        account_id = self.repo.create(
            user_id=user_id,
            name=name,
            type=type,
            institution=institution,
            current_balance=initial_balance,
            notes=notes,
        )

        return self.repo.get_by_id(account_id)

    def get_account(self, account_id: int) -> dict:
        """
        Get account by ID.

        Args:
            account_id: Account ID

        Returns:
            Account dict

        Raises:
            AccountNotFoundError: If account not found
        """
        account = self.repo.get_by_id(account_id)
        if not account:
            raise AccountNotFoundError(f"Account with ID {account_id} not found")
        return account

    def get_account_by_name(self, user_id: int, name: str) -> dict:
        """
        Get account by name.

        Args:
            user_id: User ID
            name: Account name

        Returns:
            Account dict

        Raises:
            AccountNotFoundError: If account not found
        """
        account = self.repo.get_by_name(user_id, name)
        if not account:
            raise AccountNotFoundError(f"Account '{name}' not found")
        return account

    def list_accounts(self, user_id: int, active_only: bool = True) -> list[dict]:
        """
        Get all accounts for user.

        Args:
            user_id: User ID
            active_only: Only return active accounts

        Returns:
            List of account dicts
        """
        return self.repo.get_all(user_id, active_only=active_only)

    def update_balance(self, account_id: int, new_balance: Decimal) -> dict:
        """
        Update account balance.

        Args:
            account_id: Account ID
            new_balance: New balance

        Returns:
            Updated account dict
        """
        self.repo.update_balance(account_id, new_balance)
        return self.get_account(account_id)

    def adjust_balance(self, account_id: int, amount: Decimal) -> dict:
        """
        Adjust account balance by amount.

        Args:
            account_id: Account ID
            amount: Amount to add (positive) or subtract (negative)

        Returns:
            Updated account dict
        """
        self.repo.adjust_balance(account_id, amount)
        return self.get_account(account_id)

    def get_total_balance(self, user_id: int) -> Decimal:
        """
        Get total balance across all active accounts.

        Args:
            user_id: User ID

        Returns:
            Total balance
        """
        return self.repo.get_total_balance(user_id)

    def update_account(self, account_id: int, **kwargs) -> dict:
        """
        Update account fields.

        Args:
            account_id: Account ID
            **kwargs: Fields to update (name, type, institution, notes)

        Returns:
            Updated account dict

        Raises:
            AccountNotFoundError: If account not found
        """
        # Verify account exists
        self.get_account(account_id)

        # Validate type if being updated
        if "type" in kwargs:
            valid_types = ["checking", "savings", "credit_card", "investment"]
            if kwargs["type"] not in valid_types:
                raise ValueError(f"Invalid account type. Must be one of: {', '.join(valid_types)}")

        # Update account
        self.repo.update(account_id, **kwargs)
        return self.get_account(account_id)

    def delete_account(self, account_id: int) -> None:
        """
        Delete account (soft delete).

        Args:
            account_id: Account ID

        Raises:
            AccountNotFoundError: If account not found
        """
        # Verify account exists
        self.get_account(account_id)

        # Soft delete
        self.repo.delete(account_id)
