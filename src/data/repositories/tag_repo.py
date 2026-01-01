"""Tag repository for database operations."""

from typing import Optional
from .base import BaseRepository


class TagRepository(BaseRepository):
    """Repository for tag database operations."""

    def create(self, name: str, description: Optional[str] = None, color: Optional[str] = None) -> int:
        """
        Create a new tag.

        Args:
            name: Tag name (unique)
            description: Tag description
            color: Optional color for display

        Returns:
            ID of created tag
        """
        query = """
            INSERT INTO tags (name, description, color)
            VALUES (?, ?, ?)
        """
        cursor = self._execute(query, (name.lower(), description, color))
        return cursor.lastrowid

    def get_by_id(self, tag_id: int) -> Optional[dict]:
        """
        Get tag by ID.

        Args:
            tag_id: Tag ID

        Returns:
            Tag dict or None if not found
        """
        query = "SELECT * FROM tags WHERE id = ?"
        return self._fetchone(query, (tag_id,))

    def get_by_name(self, name: str) -> Optional[dict]:
        """
        Get tag by name.

        Args:
            name: Tag name

        Returns:
            Tag dict or None if not found
        """
        query = "SELECT * FROM tags WHERE name = ?"
        return self._fetchone(query, (name.lower(),))

    def get_all(self) -> list[dict]:
        """
        Get all tags.

        Returns:
            List of tag dicts
        """
        query = "SELECT * FROM tags ORDER BY name"
        return self._fetchall(query)

    def update(self, tag_id: int, **kwargs) -> None:
        """
        Update tag fields.

        Args:
            tag_id: Tag ID
            **kwargs: Fields to update
        """
        if not kwargs:
            return

        # Normalize name to lowercase
        if "name" in kwargs:
            kwargs["name"] = kwargs["name"].lower()

        set_clause = ", ".join(f"{key} = ?" for key in kwargs.keys())
        query = f"UPDATE tags SET {set_clause} WHERE id = ?"

        self._execute(query, tuple(kwargs.values()) + (tag_id,))

    def delete(self, tag_id: int) -> None:
        """
        Delete tag and all associations.

        Args:
            tag_id: Tag ID
        """
        # Foreign key constraint will cascade delete transaction_tags
        query = "DELETE FROM tags WHERE id = ?"
        self._execute(query, (tag_id,))

    def get_or_create(self, name: str, description: Optional[str] = None, color: Optional[str] = None) -> dict:
        """
        Get existing tag or create new one.

        Args:
            name: Tag name
            description: Tag description (only used if creating)
            color: Tag color (only used if creating)

        Returns:
            Tag dict
        """
        tag = self.get_by_name(name)
        if tag:
            return tag

        tag_id = self.create(name, description, color)
        return self.get_by_id(tag_id)

    # Transaction tag associations

    def add_tag_to_transaction(self, transaction_id: int, tag_id: int) -> None:
        """
        Associate a tag with a transaction.

        Args:
            transaction_id: Transaction ID
            tag_id: Tag ID
        """
        query = """
            INSERT OR IGNORE INTO transaction_tags (transaction_id, tag_id)
            VALUES (?, ?)
        """
        self._execute(query, (transaction_id, tag_id))

    def remove_tag_from_transaction(self, transaction_id: int, tag_id: int) -> None:
        """
        Remove tag association from a transaction.

        Args:
            transaction_id: Transaction ID
            tag_id: Tag ID
        """
        query = "DELETE FROM transaction_tags WHERE transaction_id = ? AND tag_id = ?"
        self._execute(query, (transaction_id, tag_id))

    def get_transaction_tags(self, transaction_id: int) -> list[dict]:
        """
        Get all tags for a transaction.

        Args:
            transaction_id: Transaction ID

        Returns:
            List of tag dicts
        """
        query = """
            SELECT t.*
            FROM tags t
            JOIN transaction_tags tt ON t.id = tt.tag_id
            WHERE tt.transaction_id = ?
            ORDER BY t.name
        """
        return self._fetchall(query, (transaction_id,))

    def get_transactions_by_tag(self, tag_id: int) -> list[int]:
        """
        Get all transaction IDs with a specific tag.

        Args:
            tag_id: Tag ID

        Returns:
            List of transaction IDs
        """
        query = """
            SELECT transaction_id
            FROM transaction_tags
            WHERE tag_id = ?
            ORDER BY transaction_id DESC
        """
        results = self._fetchall(query, (tag_id,))
        return [r["transaction_id"] for r in results]

    def get_tag_stats(self) -> list[dict]:
        """
        Get usage statistics for all tags.

        Returns:
            List of dicts with tag info and usage counts
        """
        query = """
            SELECT
                t.*,
                COUNT(tt.transaction_id) as usage_count
            FROM tags t
            LEFT JOIN transaction_tags tt ON t.id = tt.tag_id
            GROUP BY t.id
            ORDER BY usage_count DESC, t.name
        """
        return self._fetchall(query)

    def clear_transaction_tags(self, transaction_id: int) -> None:
        """
        Remove all tags from a transaction.

        Args:
            transaction_id: Transaction ID
        """
        query = "DELETE FROM transaction_tags WHERE transaction_id = ?"
        self._execute(query, (transaction_id,))
