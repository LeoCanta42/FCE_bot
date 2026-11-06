"""User repository for tracking interactions and subscriptions."""

import logging
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fce_bot.data.db import get_db

logger = logging.getLogger(__name__)


class UsersRepository:
    """Manages bot user interactions and broadcast subscriptions."""

    def __init__(self, db_path=None):
        self.db_path = db_path

    def register_or_update(
        self,
        chat_id: int | str,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> None:
        """Register a user interaction or update last active timestamp."""
        try:
            with get_db(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO users (chat_id, username, first_name, last_active, is_subscribed)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1)
                    ON CONFLICT(chat_id) DO UPDATE SET
                        username = coalesce(excluded.username, users.username),
                        first_name = coalesce(excluded.first_name, users.first_name),
                        last_active = CURRENT_TIMESTAMP
                """, (str(chat_id), username, first_name))
        except Exception as e:
            logger.warning("Could not persist user %s: %s", chat_id, e)

    def get_subscribed_chat_ids(self) -> List[str]:
        """Return list of active subscribed chat IDs."""
        try:
            with get_db(self.db_path) as conn:
                cur = conn.cursor()
                rows = cur.execute("""
                    SELECT chat_id FROM users
                    WHERE is_subscribed = 1
                """).fetchall()
                return [row["chat_id"] for row in rows]
        except Exception as e:
            logger.warning("Error fetching subscribed users: %s", e)
            return []

    def get_stats(self) -> dict:
        """Return user count statistics."""
        try:
            with get_db(self.db_path) as conn:
                cur = conn.cursor()
                total = cur.execute("SELECT count(*) as cnt FROM users").fetchone()["cnt"]
                subscribed = cur.execute("SELECT count(*) as cnt FROM users WHERE is_subscribed = 1").fetchone()["cnt"]
                cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
                active_30d = cur.execute("SELECT count(*) as cnt FROM users WHERE last_active >= ?", (cutoff,)).fetchone()["cnt"]
                return {
                    "total_users": total,
                    "subscribed_users": subscribed,
                    "active_last_30_days": active_30d
                }
        except Exception as e:
            logger.warning("Error reading user stats: %s", e)
            return {"total_users": 0, "subscribed_users": 0, "active_last_30_days": 0}

    def prune_inactive(self, days: int = 60) -> int:
        """Clean up old users not seen in N days."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            with get_db(self.db_path) as conn:
                cur = conn.cursor()
                res = cur.execute("DELETE FROM users WHERE last_active < ?", (cutoff,))
                return res.rowcount
        except Exception as e:
            logger.warning("Error pruning inactive users: %s", e)
            return 0
