"""Dependency injection container."""

from ..data.database import Database
from ..data.repositories.transaction_repo import TransactionRepository
from ..data.repositories.account_repo import AccountRepository
from ..data.repositories.budget_repo import BudgetRepository
from ..data.repositories.category_rule_repo import CategoryRuleRepository
from ..data.repositories.recurring_repo import RecurringRepository
from ..core.services.transaction_service import TransactionService
from ..core.services.account_service import AccountService
from ..core.services.budget_service import BudgetService
from ..core.services.recurring_service import RecurringService
from ..core.services.analytics_service import AnalyticsService
from ..core.services.decision_support_service import DecisionSupportService
from ..ai.claude_client import ClaudeClient


class ServiceContainer:
    """Dependency injection container for services and repositories."""

    def __init__(self, config):
        """
        Initialize service container.

        Args:
            config: Configuration instance
        """
        self.config = config
        self._db = None
        self._ai_client = None

        # Repository instances (cached)
        self._transaction_repo = None
        self._account_repo = None
        self._budget_repo = None
        self._category_rule_repo = None
        self._recurring_repo = None

        # Service instances (cached)
        self._transaction_service = None
        self._account_service = None
        self._budget_service = None
        self._recurring_service = None
        self._analytics_service = None
        self._decision_support_service = None

    @property
    def db(self):
        """Get database instance (singleton)."""
        if not self._db:
            self._db = Database(self.config.db_path)
        return self._db

    @property
    def ai_client(self):
        """Get AI client instance (singleton)."""
        if not self._ai_client:
            self._ai_client = ClaudeClient(api_key=self.config.api_key, model=self.config.ai_model)
        return self._ai_client

    # Repositories

    def transaction_repo(self):
        """Get transaction repository."""
        if not self._transaction_repo:
            self._transaction_repo = TransactionRepository(self.db)
        return self._transaction_repo

    def account_repo(self):
        """Get account repository."""
        if not self._account_repo:
            self._account_repo = AccountRepository(self.db)
        return self._account_repo

    def budget_repo(self):
        """Get budget repository."""
        if not self._budget_repo:
            self._budget_repo = BudgetRepository(self.db)
        return self._budget_repo

    def category_rule_repo(self):
        """Get category rule repository."""
        if not self._category_rule_repo:
            self._category_rule_repo = CategoryRuleRepository(self.db)
        return self._category_rule_repo

    def recurring_repo(self):
        """Get recurring charge repository."""
        if not self._recurring_repo:
            self._recurring_repo = RecurringRepository(self.db)
        return self._recurring_repo

    # Services

    def transaction_service(self):
        """Get transaction service."""
        if not self._transaction_service:
            self._transaction_service = TransactionService(
                self.transaction_repo(), self.account_service(), self.category_rule_repo(), self.ai_client
            )
        return self._transaction_service

    def account_service(self):
        """Get account service."""
        if not self._account_service:
            self._account_service = AccountService(self.account_repo())
        return self._account_service

    def budget_service(self):
        """Get budget service."""
        if not self._budget_service:
            self._budget_service = BudgetService(self.budget_repo(), self.transaction_repo())
        return self._budget_service

    def recurring_service(self):
        """Get recurring service."""
        if not self._recurring_service:
            self._recurring_service = RecurringService(self.recurring_repo(), self.transaction_repo())
        return self._recurring_service

    def analytics_service(self):
        """Get analytics service."""
        if not self._analytics_service:
            self._analytics_service = AnalyticsService(self.transaction_repo(), self.account_repo())
        return self._analytics_service

    def decision_support_service(self):
        """Get decision support service."""
        if not self._decision_support_service:
            self._decision_support_service = DecisionSupportService(
                self.budget_service(),
                self.recurring_service(),
                self.analytics_service(),
                self.account_service(),
                self.ai_client
            )
        return self._decision_support_service
