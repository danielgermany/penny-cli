"""User repository for database operations."""

from typing import Optional
from datetime import datetime
from .base import BaseRepository


class UserRepository(BaseRepository):
    """Repository for user database operations."""

    def create(
        self,
        username: str,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
        password_hash: Optional[str] = None,
        require_password: bool = False
    ) -> int:
        """
        Create a new user.

        Args:
            username: Username (unique)
            email: Email address (unique)
            display_name: Display name
            password_hash: Hashed password
            require_password: Whether this user requires password authentication

        Returns:
            ID of created user
        """
        query = """
            INSERT INTO users (username, email, display_name, password_hash, require_password)
            VALUES (?, ?, ?, ?, ?)
        """
        cursor = self._execute(query, (username, email, display_name, password_hash, require_password))
        return cursor.lastrowid

    def get_by_id(self, user_id: int) -> Optional[dict]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User dict or None if not found
        """
        query = "SELECT * FROM users WHERE id = ?"
        return self._fetchone(query, (user_id,))

    def get_by_username(self, username: str) -> Optional[dict]:
        """
        Get user by username.

        Args:
            username: Username

        Returns:
            User dict or None if not found
        """
        query = "SELECT * FROM users WHERE username = ?"
        return self._fetchone(query, (username,))

    def get_by_email(self, email: str) -> Optional[dict]:
        """
        Get user by email.

        Args:
            email: Email address

        Returns:
            User dict or None if not found
        """
        query = "SELECT * FROM users WHERE email = ?"
        return self._fetchone(query, (email,))

    def get_all(self, active_only: bool = True) -> list[dict]:
        """
        Get all users.

        Args:
            active_only: Only return active users

        Returns:
            List of user dicts
        """
        if active_only:
            query = "SELECT * FROM users WHERE is_active = 1 ORDER BY username"
        else:
            query = "SELECT * FROM users WHERE is_active = 0 ORDER BY username"
        return self._fetchall(query)

    def update(self, user_id: int, **kwargs) -> None:
        """
        Update user fields.

        Args:
            user_id: User ID
            **kwargs: Fields to update
        """
        if not kwargs:
            return

        set_clause = ", ".join(f"{key} = ?" for key in kwargs.keys())
        query = f"UPDATE users SET {set_clause} WHERE id = ?"

        self._execute(query, tuple(kwargs.values()) + (user_id,))

    def update_last_login(self, user_id: int) -> None:
        """
        Update user's last login timestamp.

        Args:
            user_id: User ID
        """
        query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?"
        self._execute(query, (user_id,))

    def deactivate(self, user_id: int) -> None:
        """
        Deactivate user (soft delete).

        Args:
            user_id: User ID
        """
        query = "UPDATE users SET is_active = 0 WHERE id = ?"
        self._execute(query, (user_id,))

    def activate(self, user_id: int) -> None:
        """
        Activate user.

        Args:
            user_id: User ID
        """
        query = "UPDATE users SET is_active = 1 WHERE id = ?"
        self._execute(query, (user_id,))

    def delete(self, user_id: int) -> None:
        """
        Permanently delete user.

        WARNING: This will cascade delete all user data.

        Args:
            user_id: User ID
        """
        query = "DELETE FROM users WHERE id = ?"
        self._execute(query, (user_id,))

    def count_users(self) -> int:
        """
        Get total number of active users.

        Returns:
            User count
        """
        query = "SELECT COUNT(*) as count FROM users WHERE is_active = 1"
        result = self._fetchone(query)
        return result["count"] if result else 0
