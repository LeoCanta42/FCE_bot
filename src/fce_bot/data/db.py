"""Database initialization and connection management for SQLite."""

import sqlite3
import re
import os
import shutil
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from fce_bot.config import settings


def normalize_stop_name(s: str) -> str:
    """Normalize station names for robust fuzzy and exact matching."""
    if not s:
        return ""
    s = s.upper()
    s = s.replace("P.ZZA", "PIAZZA").replace("Ù", "U").replace("Ò", "O").replace("È", "E").replace("À", "A").replace("Ì", "I")
    s = s.replace("’", "").replace("'", "")
    # Remove punctuation and parentheses
    s = re.sub(r"[().,\-–_/\\]", " ", s)
    # Remove extra spaces
    s = re.sub(r"\s+", " ", s).strip()
    return s


def get_db_path() -> Path:
    """Return database file path, ensuring writable copy in /tmp on Vercel/serverless environments."""
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        tmp_db = Path("/tmp/fce_lines.db")
        if not tmp_db.exists():
            orig_db = settings.DATABASE_PATH
            if orig_db.exists():
                try:
                    shutil.copy2(orig_db, tmp_db)
                except Exception as err:
                    # Fallback to original if copy fails
                    pass
        if tmp_db.exists():
            return tmp_db

    path = settings.DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def get_db(path: Path = None) -> Generator[sqlite3.Connection, None, None]:
    """Provide a transactional database connection."""
    target_path = path or get_db_path()
    conn = sqlite3.connect(target_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(path: Path = None) -> None:
    """Initialize database tables and performance indexes."""
    with get_db(path) as conn:
        cursor = conn.cursor()

        # Transit tables (GTFS backed)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stops (
                stop_id TEXT PRIMARY KEY,
                stop_name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                lat REAL DEFAULT 0.0,
                lon REAL DEFAULT 0.0,
                has_bus INTEGER DEFAULT 0,
                has_train INTEGER DEFAULT 0,
                has_metro INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routes (
                route_id TEXT PRIMARY KEY,
                route_short_name TEXT,
                route_long_name TEXT,
                route_type INTEGER,
                transport_type TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                trip_id TEXT PRIMARY KEY,
                route_id TEXT NOT NULL,
                service_id TEXT,
                trip_headsign TEXT,
                trip_short_name TEXT,
                direction_id INTEGER DEFAULT 0,
                FOREIGN KEY (route_id) REFERENCES routes(route_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stop_times (
                trip_id TEXT NOT NULL,
                arrival_time TEXT NOT NULL,
                departure_time TEXT NOT NULL,
                stop_id TEXT NOT NULL,
                stop_sequence INTEGER NOT NULL,
                PRIMARY KEY (trip_id, stop_sequence),
                FOREIGN KEY (trip_id) REFERENCES trips(trip_id),
                FOREIGN KEY (stop_id) REFERENCES stops(stop_id)
            )
        """)

        # User management & news caching tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id TEXT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_subscribed INTEGER DEFAULT 0,
                ai_allowed INTEGER DEFAULT 0
            )
        """)

        # Migration: ensure ai_allowed column exists on existing databases
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN ai_allowed INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_cache (
                guid TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                pub_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Performance indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stops_norm ON stops(normalized_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stops_name ON stops(stop_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_st_stop_dep ON stop_times(stop_id, departure_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_st_trip_seq ON stop_times(trip_id, stop_sequence)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_route ON trips(route_id)")
