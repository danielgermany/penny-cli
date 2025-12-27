"""Configuration management."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Application configuration."""

    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            env_file: Path to .env file (defaults to .env in current directory)
        """
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        # API Settings
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.ai_model = os.getenv("AI_MODEL", "claude-sonnet-4-5-20250929")

        # Database Settings
        self.db_path = os.getenv("DATABASE_PATH", "data/finance.db")

        # User Settings
        self.default_currency = os.getenv("DEFAULT_CURRENCY", "USD")
        self.user_id = int(os.getenv("USER_ID", "1"))

        # Paths
        self.config_dir = Path(__file__).parent.parent.parent / "config"
        self.categories_file = self.config_dir / "categories.yaml"
        self.prompts_file = self.config_dir / "prompts.yaml"

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.api_key:
            return False, "ANTHROPIC_API_KEY not set. Please set it in .env file."

        if not self.db_path:
            return False, "DATABASE_PATH not set."

        return True, None

    @property
    def is_initialized(self) -> bool:
        """Check if database is initialized."""
        return Path(self.db_path).exists()
