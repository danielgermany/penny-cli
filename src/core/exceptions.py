"""Custom exceptions for the finance tracker."""


class FinanceTrackerError(Exception):
    """Base exception for finance tracker errors."""

    pass


class AccountNotFoundError(FinanceTrackerError):
    """Raised when account is not found."""

    pass


class TransactionNotFoundError(FinanceTrackerError):
    """Raised when transaction is not found."""

    pass


class BudgetNotFoundError(FinanceTrackerError):
    """Raised when budget is not found."""

    pass


class InsufficientFundsError(FinanceTrackerError):
    """Raised when account has insufficient funds for operation."""

    pass


class InvalidTransactionError(FinanceTrackerError):
    """Raised when transaction data is invalid."""

    pass


class CategoryNotFoundError(FinanceTrackerError):
    """Raised when category is not found."""

    pass


class RecurringChargeNotFoundError(FinanceTrackerError):
    """Raised when recurring charge is not found."""

    pass
