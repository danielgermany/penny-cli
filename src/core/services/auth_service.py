"""Authentication service for user management."""

import hashlib
import os
from pathlib import Path
from typing import Optional


class AuthService:
    """Service for user authentication and session management."""

    def __init__(self, user_repo, config):
        """
        Initialize authentication service.

        Args:
            user_repo: User repository instance
            config: Config instance
        """
        self.user_repo = user_repo
        self.config = config
        self.session_file = Path.home() / ".finance_tracker_session"

    def hash_password(self, password: str) -> str:
        """
        Hash a password using SHA-256.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            password: Plain text password
            password_hash: Stored password hash

        Returns:
            True if password matches
        """
        return self.hash_password(password) == password_hash

    def create_user(
        self,
        username: str,
        password: Optional[str] = None,
        email: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> dict:
        """
        Create a new user.

        Args:
            username: Username
            password: Optional password
            email: Optional email
            display_name: Optional display name

        Returns:
            Created user dict

        Raises:
            ValueError: If username already exists
        """
        # Check if username exists
        existing = self.user_repo.get_by_username(username)
        if existing:
            raise ValueError(f"Username '{username}' already exists")

        # Check if email exists
        if email:
            existing_email = self.user_repo.get_by_email(email)
            if existing_email:
                raise ValueError(f"Email '{email}' already in use")

        # Hash password if provided
        password_hash = None
        require_password = False
        if password:
            password_hash = self.hash_password(password)
            require_password = True

        # Create user
        user_id = self.user_repo.create(
            username=username,
            email=email,
            display_name=display_name,
            password_hash=password_hash,
            require_password=require_password
        )

        return self.user_repo.get_by_id(user_id)

    def authenticate(self, username: str, password: Optional[str] = None) -> Optional[dict]:
        """
        Authenticate a user.

        Args:
            username: Username
            password: Password (required if user has password set)

        Returns:
            User dict if authentication successful, None otherwise
        """
        user = self.user_repo.get_by_username(username)
        if not user:
            return None

        if not user["is_active"]:
            return None

        # Check if password is required
        if user["require_password"]:
            if not password:
                return None
            if not self.verify_password(password, user["password_hash"]):
                return None

        # Update last login
        self.user_repo.update_last_login(user["id"])

        return user

    def get_current_user(self) -> Optional[dict]:
        """
        Get currently logged in user from session.

        Returns:
            User dict or None if no session
        """
        if not self.session_file.exists():
            return None

        try:
            with open(self.session_file, "r") as f:
                user_id = int(f.read().strip())
            return self.user_repo.get_by_id(user_id)
        except (ValueError, IOError):
            return None

    def set_current_user(self, user_id: int) -> None:
        """
        Set the current user session.

        Args:
            user_id: User ID to set as current
        """
        with open(self.session_file, "w") as f:
            f.write(str(user_id))

    def clear_session(self) -> None:
        """Clear the current user session."""
        if self.session_file.exists():
            os.remove(self.session_file)

    def login(self, username: str, password: Optional[str] = None) -> dict:
        """
        Log in a user and create session.

        Args:
            username: Username
            password: Password (if required)

        Returns:
            User dict

        Raises:
            ValueError: If authentication fails
        """
        user = self.authenticate(username, password)
        if not user:
            if password:
                raise ValueError("Invalid username or password")
            else:
                # Check if password is required
                user_check = self.user_repo.get_by_username(username)
                if user_check and user_check["require_password"]:
                    raise ValueError(f"Password required for user '{username}'")
                raise ValueError(f"User '{username}' not found or inactive")

        # Set session
        self.set_current_user(user["id"])

        return user

    def logout(self) -> None:
        """Log out the current user."""
        self.clear_session()

    def list_users(self, include_inactive: bool = False) -> list[dict]:
        """
        List all users.

        Args:
            include_inactive: Include inactive users

        Returns:
            List of user dicts (without password hashes)
        """
        users = self.user_repo.get_all(active_only=not include_inactive)

        # Remove password hashes from output
        for user in users:
            if "password_hash" in user:
                del user["password_hash"]

        return users

    def change_password(self, user_id: int, new_password: str) -> None:
        """
        Change user password.

        Args:
            user_id: User ID
            new_password: New password
        """
        password_hash = self.hash_password(new_password)
        self.user_repo.update(user_id, password_hash=password_hash, require_password=True)

    def remove_password(self, user_id: int) -> None:
        """
        Remove password requirement for a user.

        Args:
            user_id: User ID
        """
        self.user_repo.update(user_id, password_hash=None, require_password=False)

    def update_user(self, user_id: int, **kwargs) -> dict:
        """
        Update user fields.

        Args:
            user_id: User ID
            **kwargs: Fields to update (email, display_name)

        Returns:
            Updated user dict
        """
        # Don't allow updating password through this method
        if "password" in kwargs:
            del kwargs["password"]
        if "password_hash" in kwargs:
            del kwargs["password_hash"]

        self.user_repo.update(user_id, **kwargs)
        return self.user_repo.get_by_id(user_id)

    def delete_user(self, user_id: int) -> None:
        """
        Deactivate a user (soft delete).

        Args:
            user_id: User ID
        """
        # Don't allow deleting the last user
        if self.user_repo.count_users() <= 1:
            raise ValueError("Cannot delete the last active user")

        self.user_repo.deactivate(user_id)
