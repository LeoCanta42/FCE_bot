"""User repository for tracking interactions and subscriptions (GDPR Compliant)."""

import logging
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fce_bot.config import settings
from fce_bot.data.db import get_db

logger = logging.getLogger(__name__)


class UsersRepository:
    """Manages bot user interactions and broadcast subscriptions with GDPR compliance."""

    def __init__(self, db_path=None):
        self.db_path = db_path

    @staticmethod
    def _is_valid_chat_id(chat_id: int | str) -> bool:
        """Ensure chat_id is a valid numeric Telegram ID (never a mock string or exceed 64-bit int)."""
        if isinstance(chat_id, bool) or chat_id is None:
            return False
        if isinstance(chat_id, int):
            return True
        if isinstance(chat_id, str):
            s = chat_id.strip()
            return bool(s) and (s.isdigit() or (s.startswith("-") and s[1:].isdigit()))
        return False

    def register_or_update(
        self,
        chat_id: int | str,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        is_subscribed: bool = False
    ) -> None:
        """Register a user chat interaction or update activity timestamp.
        
        New users are saved with notifications disabled (is_subscribed=0) and AI disabled (ai_allowed=0)
        by default, while preserving any existing subscription/AI permissions on subsequent messages.
        """
        if not self._is_valid_chat_id(chat_id):
            return
        clean_user = str(username) if isinstance(username, str) else None
        clean_first = str(first_name) if isinstance(first_name, str) else None
        try:
            with get_db(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO users (chat_id, username, first_name, last_active, is_subscribed, ai_allowed)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, 0)
                    ON CONFLICT(chat_id) DO UPDATE SET
                        username = coalesce(excluded.username, users.username),
                        first_name = coalesce(excluded.first_name, users.first_name),
                        last_active = CURRENT_TIMESTAMP
                """, (str(chat_id).strip(), clean_user, clean_first, 1 if is_subscribed else 0))
        except Exception as e:
            logger.warning("Could not persist user %s: %s", chat_id, e)

    def is_user_subscribed(self, chat_id: int | str) -> bool:
        """Check if user has explicitly subscribed to service announcements."""
        try:
            with get_db(self.db_path) as conn:
                cur = conn.cursor()
                row = cur.execute(
                    "SELECT is_subscribed FROM users WHERE chat_id = ?",
                    (str(chat_id),)
                ).fetchone()
                return bool(row and row["is_subscribed"] == 1)
        except Exception as e:
            logger.warning("Error checking subscription for %s: %s", chat_id, e)
            return False

    def subscribe_user(
        self,
        chat_id: int | str,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> bool:
        """Explicit opt-in: register user for news and service broadcasts."""
        if not self._is_valid_chat_id(chat_id):
            return False
        clean_user = str(username) if isinstance(username, str) else None
        clean_first = str(first_name) if isinstance(first_name, str) else None
        try:
            with get_db(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO users (chat_id, username, first_name, last_active, is_subscribed)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1)
                    ON CONFLICT(chat_id) DO UPDATE SET
                        is_subscribed = 1,
                        username = coalesce(excluded.username, users.username),
                        first_name = coalesce(excluded.first_name, users.first_name),
                        last_active = CURRENT_TIMESTAMP
                """, (str(chat_id).strip(), clean_user, clean_first))
                return True
        except Exception as e:
            logger.error("Error subscribing user %s: %s", chat_id, e)
            return False

    def unsubscribe_user(self, chat_id: int | str) -> bool:
        """Explicit opt-out: stop receiving news and service broadcasts."""
        try:
            with get_db(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE users SET is_subscribed = 0 WHERE chat_id = ?",
                    (str(chat_id),)
                )
                return True
        except Exception as e:
            logger.error("Error unsubscribing user %s: %s", chat_id, e)
            return False

    def delete_user(self, chat_id: int | str) -> bool:
        """Permanently delete user data (GDPR Art. 17 - Right to Erasure)."""
        try:
            with get_db(self.db_path) as conn:
                cur = conn.cursor()
                res = cur.execute("DELETE FROM users WHERE chat_id = ?", (str(chat_id),))
                return res.rowcount > 0
        except Exception as e:
            logger.error("Error deleting user %s: %s", chat_id, e)
            return False

    def set_subscription(self, chat_id: int | str, is_subscribed: bool) -> bool:
        """Toggle user news broadcast subscription state (creating record if needed)."""
        if not self._is_valid_chat_id(chat_id):
            return False
        try:
            with get_db(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO users (chat_id, is_subscribed, ai_allowed, last_active)
                    VALUES (?, ?, 0, CURRENT_TIMESTAMP)
                    ON CONFLICT(chat_id) DO UPDATE SET
                        is_subscribed = ?
                """, (str(chat_id).strip(), 1 if is_subscribed else 0, 1 if is_subscribed else 0))
                return True
        except Exception as e:
            logger.error("Error setting subscription for user %s: %s", chat_id, e)
            return False

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

    def is_ai_allowed(self, chat_id: int | str) -> bool:
        """Check if user has permission to use the AI assistant.
        
        Configured admins in settings.admin_user_ids are always authorized by default.
        Other users require explicit authorization by an admin via /allow_ai.
        """
        try:
            cid_int = int(chat_id)
            if cid_int in settings.admin_user_ids:
                return True
        except (ValueError, TypeError):
            pass

        try:
            with get_db(self.db_path) as conn:
                cur = conn.cursor()
                row = cur.execute(
                    "SELECT ai_allowed FROM users WHERE chat_id = ?",
                    (str(chat_id),)
                ).fetchone()
                return bool(row and row["ai_allowed"] == 1)
        except Exception as e:
            logger.warning("Error checking AI allowance for %s: %s", chat_id, e)
            return False

    def set_ai_allowed(self, chat_id: int | str, allowed: bool) -> bool:
        """Enable or revoke AI usage permission for a chat ID."""
        if not self._is_valid_chat_id(chat_id):
            return False
        try:
            with get_db(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO users (chat_id, ai_allowed, is_subscribed)
                    VALUES (?, ?, 0)
                    ON CONFLICT(chat_id) DO UPDATE SET
                        ai_allowed = ?
                """, (str(chat_id).strip(), 1 if allowed else 0, 1 if allowed else 0))
                return True
        except Exception as e:
            logger.error("Error setting AI allowance for user %s: %s", chat_id, e)
            return False

    def get_ai_allowed_chat_ids(self) -> List[str]:
        """Return list of chat IDs authorized to use AI."""
        try:
            with get_db(self.db_path) as conn:
                cur = conn.cursor()
                rows = cur.execute("""
                    SELECT chat_id FROM users
                    WHERE ai_allowed = 1
                """).fetchall()
                return [row["chat_id"] for row in rows]
        except Exception as e:
            logger.warning("Error fetching AI allowed users: %s", e)
            return []

    def get_user(self, identifier: int | str) -> Optional[dict]:
        """Find a single user by chat_id or username (case-insensitive, with or without @)."""
        if identifier is None:
            return None
        ident_str = str(identifier).strip()
        if not ident_str:
            return None
        clean_uname = ident_str.lstrip("@")
        try:
            with get_db(self.db_path) as conn:
                cur = conn.cursor()
                row = cur.execute("""
                    SELECT chat_id, username, first_name, last_active, is_subscribed, ai_allowed
                    FROM users
                    WHERE chat_id = ?
                       OR (username IS NOT NULL AND LOWER(username) = LOWER(?))
                    LIMIT 1
                """, (ident_str, clean_uname)).fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.warning("Error fetching user %s: %s", identifier, e)
            return None

    def search_users(self, query: str = "", limit: int = 50) -> List[dict]:
        """Search users by username, first_name, or chat_id (or list all if query is empty)."""
        q = (query or "").strip().lstrip("@")
        try:
            with get_db(self.db_path) as conn:
                cur = conn.cursor()
                if not q:
                    rows = cur.execute("""
                        SELECT chat_id, username, first_name, last_active, is_subscribed, ai_allowed
                        FROM users
                        ORDER BY last_active DESC
                        LIMIT ?
                    """, (limit,)).fetchall()
                else:
                    like_q = f"%{q}%"
                    rows = cur.execute("""
                        SELECT chat_id, username, first_name, last_active, is_subscribed, ai_allowed
                        FROM users
                        WHERE chat_id LIKE ?
                           OR (username IS NOT NULL AND LOWER(username) LIKE LOWER(?))
                           OR (first_name IS NOT NULL AND LOWER(first_name) LIKE LOWER(?))
                        ORDER BY last_active DESC
                        LIMIT ?
                    """, (like_q, like_q, like_q, limit)).fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning("Error searching users with query '%s': %s", query, e)
            return []

    def get_all_users(self, filter_mode: str = "all", limit: int = 100) -> List[dict]:
        """Return list of user dicts filtered by 'all', 'sub', or 'ai'."""
        try:
            with get_db(self.db_path) as conn:
                cur = conn.cursor()
                if filter_mode == "sub":
                    sql = """
                        SELECT chat_id, username, first_name, last_active, is_subscribed, ai_allowed
                        FROM users WHERE is_subscribed = 1
                        ORDER BY last_active DESC LIMIT ?
                    """
                elif filter_mode == "ai":
                    sql = """
                        SELECT chat_id, username, first_name, last_active, is_subscribed, ai_allowed
                        FROM users WHERE ai_allowed = 1
                        ORDER BY last_active DESC LIMIT ?
                    """
                else:
                    sql = """
                        SELECT chat_id, username, first_name, last_active, is_subscribed, ai_allowed
                        FROM users
                        ORDER BY last_active DESC LIMIT ?
                    """
                rows = cur.execute(sql, (limit,)).fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning("Error listing users (mode=%s): %s", filter_mode, e)
            return []

    def resolve_chat_id(self, identifier: int | str) -> Optional[str]:
        """Resolve a username (e.g. @mario or mario) or chat_id to a target chat_id string."""
        if identifier is None:
            return None
        ident_str = str(identifier).strip()
        if not ident_str:
            return None
        user = self.get_user(ident_str)
        if user:
            return str(user["chat_id"])
        # If numeric chat_id not yet in DB, allow direct ID targeting
        if ident_str.lstrip("-").isdigit():
            return ident_str
        return None

    def get_stats(self) -> dict:
        """Return user count statistics."""
        try:
            with get_db(self.db_path) as conn:
                cur = conn.cursor()
                total = cur.execute("SELECT count(*) as cnt FROM users").fetchone()["cnt"]
                subscribed = cur.execute("SELECT count(*) as cnt FROM users WHERE is_subscribed = 1").fetchone()["cnt"]
                ai_allowed = cur.execute("SELECT count(*) as cnt FROM users WHERE ai_allowed = 1").fetchone()["cnt"]
                cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                active_30d = cur.execute("SELECT count(*) as cnt FROM users WHERE last_active >= ?", (cutoff,)).fetchone()["cnt"]
                return {
                    "total_users": total,
                    "subscribed_users": subscribed,
                    "ai_allowed_users": ai_allowed,
                    "active_last_30_days": active_30d
                }
        except Exception as e:
            logger.warning("Error reading user stats: %s", e)
            return {"total_users": 0, "subscribed_users": 0, "ai_allowed_users": 0, "active_last_30_days": 0}

    def prune_inactive(self, days: int = 60) -> int:
        """Clean up old users not seen in N days (Data retention limit)."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            with get_db(self.db_path) as conn:
                cur = conn.cursor()
                res = cur.execute("DELETE FROM users WHERE last_active < ?", (cutoff,))
                return res.rowcount
        except Exception as e:
            logger.warning("Error pruning inactive users: %s", e)
            return 0
