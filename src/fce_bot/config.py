"""Configuration management for FCE Bot using pydantic-settings."""

import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env", override=True)
load_dotenv(BASE_DIR / ".env.local", override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(BASE_DIR / ".env"), str(BASE_DIR / ".env.local")),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # Project metadata
    PROJECT_NAME: str = "FCE Circumetnea Bot"
    DEBUG: bool = False
    BASE_DIR: Path = BASE_DIR

    # Telegram configuration
    TELEGRAM_BOT_TOKEN: str = Field(
        default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""),
        description="Telegram Bot API Token"
    )
    NEWS_BOT_TOKEN: Optional[str] = Field(
        default_factory=lambda: os.getenv("NEWS_BOT_TOKEN"),
        description="Optional separate token for news announcements"
    )
    TELEGRAM_CHANNEL_ID: Optional[str] = Field(
        default_factory=lambda: os.getenv("TELEGRAM_CHANNEL_ID"),
        description="Telegram channel ID / @handle for news broadcasts"
    )
    ADMIN_USER_IDS_RAW: str = Field(
        default_factory=lambda: os.getenv("ADMIN_USER_IDS", ""),
        validation_alias=AliasChoices("ADMIN_USER_IDS", "ADMIN_USER_IDS_RAW"),
        description="Comma-separated Telegram user IDs of administrators"
    )

    # Database configuration
    DATABASE_PATH: Path = BASE_DIR / "fce_lines.db"
    USERS_DATABASE_PATH: Path = BASE_DIR / "users.db"

    # Circumetnea data endpoints
    CIRCUMETNEA_BASE_URL: str = "https://www.circumetnea.it"
    CIRCUMETNEA_LINES_URL: str = "https://www.circumetnea.it/le-nostre-linee/"
    CIRCUMETNEA_GTFS_URL: str = (
        "https://www.circumetnea.it/download/general-transit-feed-specification-fce-01-02-2025-28-02-2028/?wpdmdl=17798"
    )
    CIRCUMETNEA_RSS_URL: str = "https://www.circumetnea.it/category/news/feed/"

    # AI Trip Assistant (Exclusively Google Gemini)
    GEMINI_API_KEY: Optional[str] = Field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY") or os.getenv("AI_API_KEY"),
        validation_alias=AliasChoices("GEMINI_API_KEY", "AI_API_KEY")
    )
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    # Vercel & Webhook configuration
    WEBHOOK_URL: Optional[str] = None  # e.g. https://my-fce-bot.vercel.app/api/webhook
    WEBHOOK_SECRET: Optional[str] = None
    CRON_SECRET: Optional[str] = None

    @property
    def admin_user_ids(self) -> List[int]:
        """Parsed integer list of admin IDs."""
        ids: List[int] = []
        if not self.ADMIN_USER_IDS_RAW:
            return ids
        for item in self.ADMIN_USER_IDS_RAW.replace(";", ",").split(","):
            cleaned = item.strip()
            if cleaned.isdigit() or (cleaned.startswith("-") and cleaned[1:].isdigit()):
                ids.append(int(cleaned))
        return ids

    @property
    def effective_news_token(self) -> str:
        """Returns NEWS_BOT_TOKEN or falls back to TELEGRAM_BOT_TOKEN."""
        return self.NEWS_BOT_TOKEN or self.TELEGRAM_BOT_TOKEN


settings = Settings()
