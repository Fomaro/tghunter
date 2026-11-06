"""
Telegram Username Hunter PRO
SQLite Database Management
"""
import json
import logging
import sqlite3
import threading
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

from telegram_username_hunter.config.settings import (
    DEFAULT_SETTINGS,
    BotStatus,
    PremiumBotStatus,
    UsernameStatus,
)
from telegram_username_hunter.database.models import (
    BotRecord,
    DashboardStats,
    PremiumAliasRecord,
    UsernameRecord,
)

logger = logging.getLogger(__name__)

ALLOWED_SORT_COLUMNS = {
    "score": "score",
    "length": "LENGTH(username)",
    "date": "last_checked_at",
    "username": "username"
}


class DatabaseManager:
    """Thread-safe SQLite database manager for Telegram Username Hunter PRO."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or DEFAULT_SETTINGS.db_path
        self._lock = threading.RLock()
        self._init_db()

    @contextmanager
    def _connection_context(self) -> Generator[sqlite3.Connection, None, None]:
        """Provides a connection with WAL mode and guarantees connection closure."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Create necessary tables and indices if they do not exist."""
        with self._lock:
            with self._connection_context() as conn:
                cursor = conn.cursor()

                # 1. Regular usernames
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS usernames (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        category TEXT NOT NULL,
                        status TEXT NOT NULL,
                        score INTEGER NOT NULL DEFAULT 0,
                        auction_eligibility TEXT NOT NULL,
                        fragment_url TEXT,
                        generated_at TIMESTAMP NOT NULL,
                        last_checked_at TIMESTAMP,
                        check_source TEXT,
                        notes TEXT
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_un_username ON usernames(username);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_un_status ON usernames(status);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_un_score ON usernames(score);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_un_category ON usernames(category);")

                # 2. Bot usernames
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bot_usernames (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        category TEXT NOT NULL,
                        status TEXT NOT NULL,
                        score INTEGER NOT NULL DEFAULT 0,
                        auction_eligibility TEXT NOT NULL,
                        fragment_url TEXT,
                        generated_at TIMESTAMP NOT NULL,
                        last_checked_at TIMESTAMP,
                        check_source TEXT,
                        notes TEXT
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_bot_username ON bot_usernames(username);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_bot_status ON bot_usernames(status);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_bot_score ON bot_usernames(score);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_bot_category ON bot_usernames(category);")

                # 3. Premium bot aliases
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS premium_bot_aliases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        suffix TEXT NOT NULL,
                        category TEXT NOT NULL,
                        status TEXT NOT NULL,
                        score INTEGER NOT NULL DEFAULT 0,
                        auction_eligibility TEXT NOT NULL,
                        fragment_url TEXT,
                        generated_at TIMESTAMP NOT NULL,
                        last_checked_at TIMESTAMP,
                        check_source TEXT,
                        notes TEXT
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pba_username ON premium_bot_aliases(username);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pba_status ON premium_bot_aliases(status);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pba_score ON premium_bot_aliases(score);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pba_suffix ON premium_bot_aliases(suffix);")

                # 4. Check history log
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS checks_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        target_type TEXT NOT NULL,
                        username TEXT NOT NULL,
                        previous_status TEXT,
                        new_status TEXT NOT NULL,
                        response_code INTEGER,
                        checked_at TIMESTAMP NOT NULL,
                        check_source TEXT,
                        details TEXT
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ch_username ON checks_history(username);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ch_time ON checks_history(checked_at);")

                # 5. Scoring history
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scoring_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        target_type TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        breakdown TEXT,
                        scored_at TIMESTAMP NOT NULL
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_sh_username ON scoring_history(username);")

                # 6. Settings key-value
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP NOT NULL
                    );
                """)

                # 7. Search sessions
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS search_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_type TEXT NOT NULL,
                        started_at TIMESTAMP NOT NULL,
                        ended_at TIMESTAMP,
                        total_generated INTEGER DEFAULT 0,
                        total_checked INTEGER DEFAULT 0,
                        total_available INTEGER DEFAULT 0,
                        total_errors INTEGER DEFAULT 0,
                        status TEXT NOT NULL
                    );
                """)
                logger.info(f"Database initialized at {self.db_path}")

    # ================= USERNAME METHODS =================

    def upsert_username(self, record: UsernameRecord) -> int:
        """Insert or update a regular username record."""
        with self._lock, self._connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                    INSERT INTO usernames (
                        username, category, status, score, auction_eligibility,
                        fragment_url, generated_at, last_checked_at, check_source, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(username) DO UPDATE SET
                        category = excluded.category,
                        status = excluded.status,
                        score = excluded.score,
                        auction_eligibility = excluded.auction_eligibility,
                        fragment_url = excluded.fragment_url,
                        last_checked_at = excluded.last_checked_at,
                        check_source = excluded.check_source,
                        notes = excluded.notes;
                """, (
                record.username, record.category, record.status, record.score,
                record.auction_eligibility, record.fragment_url, record.generated_at,
                record.last_checked_at, record.check_source, record.notes
            ))
            return cursor.lastrowid or 0

    def get_usernames(
        self,
        limit: int = 500,
        offset: int = 0,
        status: str | None = None,
        min_score: int = 0,
        category: str | None = None,
        auction_eligibility: str | None = None,
        sort_by: str = "score",
        sort_asc: bool = False
    ) -> list[UsernameRecord]:
        """Fetch regular usernames with parameterized filters and whitelisted sorting."""
        order_col = ALLOWED_SORT_COLUMNS.get(sort_by, "score")
        direction = "ASC" if sort_asc else "DESC"

        query_parts = ["SELECT * FROM usernames WHERE score >= ?"]
        params: list[Any] = [min_score]

        if status:
            if status in ("AVAILABLE", "AVAILABLE_TO_CLAIM"):
                query_parts.append("AND status IN ('AVAILABLE', 'AVAILABLE_TO_CLAIM')")
            elif status in ("OCCUPIED", "TAKEN"):
                query_parts.append("AND status IN ('OCCUPIED', 'TAKEN')")
            elif status in ("RESTRICTED", "RESERVED", "COLLECTIBLE"):
                query_parts.append("AND status IN ('RESTRICTED', 'RESERVED', 'COLLECTIBLE')")
            else:
                query_parts.append("AND status = ?")
                params.append(status)
        if category:
            query_parts.append("AND category = ?")
            params.append(category)
        if auction_eligibility:
            if auction_eligibility in ("AUCTION_SUPPORTED", "AUCTION_ELIGIBLE"):
                query_parts.append("AND auction_eligibility IN ('AUCTION_SUPPORTED', 'AUCTION_ELIGIBLE')")
            else:
                query_parts.append("AND auction_eligibility = ?")
                params.append(auction_eligibility)

        # Safe order column from static dictionary mapping
        query_parts.append(f"ORDER BY {order_col} {direction} LIMIT ? OFFSET ?")
        params.extend([limit, offset])

        full_query = " ".join(query_parts)

        with self._lock, self._connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute(full_query, params)
            rows = cursor.fetchall()
            return [
                UsernameRecord(
                    id=r["id"],
                    username=r["username"],
                    category=r["category"],
                    status=r["status"],
                    score=r["score"],
                    auction_eligibility=r["auction_eligibility"],
                    fragment_url=r["fragment_url"],
                    generated_at=r["generated_at"],
                    last_checked_at=r["last_checked_at"],
                    check_source=r["check_source"],
                    notes=r["notes"]
                )
                for r in rows
            ]

    # ================= BOT METHODS =================

    def upsert_bot(self, record: BotRecord) -> int:
        """Insert or update a bot username record."""
        with self._lock, self._connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                    INSERT INTO bot_usernames (
                        username, category, status, score, auction_eligibility,
                        fragment_url, generated_at, last_checked_at, check_source, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(username) DO UPDATE SET
                        category = excluded.category,
                        status = excluded.status,
                        score = excluded.score,
                        auction_eligibility = excluded.auction_eligibility,
                        fragment_url = excluded.fragment_url,
                        last_checked_at = excluded.last_checked_at,
                        check_source = excluded.check_source,
                        notes = excluded.notes;
                """, (
                record.username, record.category, record.status, record.score,
                record.auction_eligibility, record.fragment_url, record.generated_at,
                record.last_checked_at, record.check_source, record.notes
            ))
            return cursor.lastrowid or 0

    def get_bots(
        self,
        limit: int = 500,
        offset: int = 0,
        status: str | None = None,
        min_score: int = 0,
        category: str | None = None,
        sort_by: str = "score",
        sort_asc: bool = False
    ) -> list[BotRecord]:
        """Fetch bot usernames with filters and sorting."""
        order_col = ALLOWED_SORT_COLUMNS.get(sort_by, "score")
        direction = "ASC" if sort_asc else "DESC"

        query_parts = ["SELECT * FROM bot_usernames WHERE score >= ?"]
        params: list[Any] = [min_score]

        if status:
            query_parts.append("AND status = ?")
            params.append(status)
        if category:
            query_parts.append("AND category = ?")
            params.append(category)

        query_parts.append(f"ORDER BY {order_col} {direction} LIMIT ? OFFSET ?")
        params.extend([limit, offset])

        full_query = " ".join(query_parts)

        with self._lock, self._connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute(full_query, params)
            rows = cursor.fetchall()
            return [
                BotRecord(
                    id=r["id"],
                    username=r["username"],
                    category=r["category"],
                    status=r["status"],
                    score=r["score"],
                    auction_eligibility=r["auction_eligibility"],
                    fragment_url=r["fragment_url"],
                    generated_at=r["generated_at"],
                    last_checked_at=r["last_checked_at"],
                    check_source=r["check_source"],
                    notes=r["notes"]
                )
                for r in rows
            ]

    # ================= PREMIUM BOT ALIAS METHODS =================

    def upsert_premium_alias(self, record: PremiumAliasRecord) -> int:
        """Insert or update a premium bot alias record."""
        with self._lock:
            with self._connection_context() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO premium_bot_aliases (
                        username, suffix, category, status, score, auction_eligibility,
                        fragment_url, generated_at, last_checked_at, check_source, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(username) DO UPDATE SET
                        suffix = excluded.suffix,
                        category = excluded.category,
                        status = excluded.status,
                        score = excluded.score,
                        auction_eligibility = excluded.auction_eligibility,
                        fragment_url = excluded.fragment_url,
                        last_checked_at = excluded.last_checked_at,
                        check_source = excluded.check_source,
                        notes = excluded.notes;
                """, (
                    record.username, record.suffix, record.category, record.status, record.score,
                    record.auction_eligibility, record.fragment_url, record.generated_at,
                    record.last_checked_at, record.check_source, record.notes
                ))
                return cursor.lastrowid or 0

    def get_premium_aliases(
        self,
        limit: int = 500,
        offset: int = 0,
        status: str | None = None,
        min_score: int = 0,
        suffix: str | None = None,
        sort_by: str = "score",
        sort_asc: bool = False
    ) -> list[PremiumAliasRecord]:
        """Fetch premium bot aliases with filters and sorting."""
        order_col = ALLOWED_SORT_COLUMNS.get(sort_by, "score")
        direction = "ASC" if sort_asc else "DESC"

        query_parts = ["SELECT * FROM premium_bot_aliases WHERE score >= ?"]
        params: list[Any] = [min_score]

        if status:
            query_parts.append("AND status = ?")
            params.append(status)
        if suffix:
            query_parts.append("AND suffix = ?")
            params.append(suffix)

        query_parts.append(f"ORDER BY {order_col} {direction} LIMIT ? OFFSET ?")
        params.extend([limit, offset])

        full_query = " ".join(query_parts)

        with self._lock, self._connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute(full_query, params)
            rows = cursor.fetchall()
            return [
                PremiumAliasRecord(
                    id=r["id"],
                    username=r["username"],
                    suffix=r["suffix"],
                    category=r["category"],
                    status=r["status"],
                    score=r["score"],
                    auction_eligibility=r["auction_eligibility"],
                    fragment_url=r["fragment_url"],
                    generated_at=r["generated_at"],
                    last_checked_at=r["last_checked_at"],
                    check_source=r["check_source"],
                    notes=r["notes"]
                )
                for r in rows
            ]

    # ================= HISTORY & LOGGING =================

    def log_check(
        self,
        target_type: str,
        username: str,
        previous_status: str | None,
        new_status: str,
        response_code: int | None = None,
        check_source: str = "",
        details: str = ""
    ) -> None:
        """Record check history event."""
        with self._lock, self._connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                    INSERT INTO checks_history (
                        target_type, username, previous_status, new_status,
                        response_code, checked_at, check_source, details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                target_type, username, previous_status, new_status,
                response_code, datetime.now(UTC).isoformat(), check_source, details
            ))

    def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Retrieve recent check history."""
        with self._lock, self._connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                    SELECT * FROM checks_history ORDER BY id DESC LIMIT ?
                """, (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def record_scoring(
        self,
        username: str,
        target_type: str,
        score: int,
        breakdown: dict[str, Any]
    ) -> None:
        with self._lock, self._connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                    INSERT INTO scoring_history (
                        username, target_type, score, breakdown, scored_at
                    ) VALUES (?, ?, ?, ?, ?);
                """, (
                username, target_type, score, json.dumps(breakdown),
                datetime.now(UTC).isoformat()
            ))

    # ================= SETTINGS PERSISTENCE =================

    def save_setting(self, key: str, value: str) -> None:
        """Save or update setting key-value pair."""
        with self._lock, self._connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at;
            """, (key, value, datetime.now(UTC).isoformat()))

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve setting value by key."""
        with self._lock, self._connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    # ================= SESSIONS & STATS =================

    def create_session(self, session_type: str) -> int:
        with self._lock, self._connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                    INSERT INTO search_sessions (
                        session_type, started_at, status
                    ) VALUES (?, ?, 'RUNNING');
                """, (session_type, datetime.now(UTC).isoformat()))
            return cursor.lastrowid or 0

    def update_session(
        self,
        session_id: int,
        total_generated: int,
        total_checked: int,
        total_available: int,
        total_errors: int,
        status: str = "FINISHED"
    ) -> None:
        with self._lock, self._connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                    UPDATE search_sessions SET
                        ended_at = ?,
                        total_generated = ?,
                        total_checked = ?,
                        total_available = ?,
                        total_errors = ?,
                        status = ?
                    WHERE id = ?;
                """, (
                datetime.now(UTC).isoformat(), total_generated, total_checked,
                total_available, total_errors, status, session_id
            ))

    def get_dashboard_stats(self, min_promising_score: int = 70) -> DashboardStats:
        """Calculate aggregated stats for the dashboard using parameterized queries."""
        stats = DashboardStats()
        with self._lock:
            with self._connection_context() as conn:
                cursor = conn.cursor()

                # Total generated (all 3 tables)
                cursor.execute("SELECT COUNT(*) FROM usernames")
                un_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM bot_usernames")
                bot_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM premium_bot_aliases")
                alias_count = cursor.fetchone()[0]
                stats.total_generated = un_count + bot_count + alias_count

                # Total checked (status != UNKNOWN) - parameterized
                cursor.execute("SELECT COUNT(*) FROM usernames WHERE status != ?", (UsernameStatus.UNKNOWN.value,))
                un_checked = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM bot_usernames WHERE status != ?", (BotStatus.UNKNOWN.value,))
                bot_checked = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM premium_bot_aliases WHERE status != ?", (PremiumBotStatus.UNKNOWN.value,))
                alias_checked = cursor.fetchone()[0]
                stats.total_checked = un_checked + bot_checked + alias_checked

                # Available regular usernames - parameterized
                cursor.execute("SELECT COUNT(*) FROM usernames WHERE status = ?", (UsernameStatus.AVAILABLE_TO_CLAIM.value,))
                stats.available_usernames = cursor.fetchone()[0]

                # Available bot usernames - parameterized
                cursor.execute("SELECT COUNT(*) FROM bot_usernames WHERE status = ?", (BotStatus.AVAILABLE_FOR_BOT.value,))
                stats.available_bot_names = cursor.fetchone()[0]

                # Premium bot aliases (eligible) - parameterized
                cursor.execute("SELECT COUNT(*) FROM premium_bot_aliases WHERE status = ?", (PremiumBotStatus.ELIGIBLE_FOR_ASSIGNMENT.value,))
                stats.premium_bot_aliases = cursor.fetchone()[0]

                # Promising regular usernames - parameterized
                cursor.execute(
                    "SELECT COUNT(*) FROM usernames WHERE status = ? AND score >= ?",
                    (UsernameStatus.AVAILABLE_TO_CLAIM.value, min_promising_score)
                )
                stats.promising_usernames = cursor.fetchone()[0]

                # Promising bots - parameterized
                cursor.execute(
                    "SELECT COUNT(*) FROM bot_usernames WHERE status = ? AND score >= ?",
                    (BotStatus.AVAILABLE_FOR_BOT.value, min_promising_score)
                )
                stats.promising_bot_names = cursor.fetchone()[0]

                # Errors - parameterized
                cursor.execute("SELECT COUNT(*) FROM usernames WHERE status = ?", (UsernameStatus.ERROR.value,))
                un_err = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM bot_usernames WHERE status = ?", (BotStatus.ERROR.value,))
                bot_err = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM premium_bot_aliases WHERE status = ?", (PremiumBotStatus.ERROR.value,))
                alias_err = cursor.fetchone()[0]
                stats.check_errors = un_err + bot_err + alias_err

                # Last activity
                cursor.execute("SELECT checked_at, username, new_status FROM checks_history ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()
                if row:
                    stats.last_activity = f"{row[0][:19]}: @{row[1]} -> {row[2]}"
                else:
                    stats.last_activity = "No activity yet"

        return stats

    def clear_all_tables(self) -> None:
        """Clear all stored data."""
        with self._lock, self._connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usernames;")
            cursor.execute("DELETE FROM bot_usernames;")
            cursor.execute("DELETE FROM premium_bot_aliases;")
            cursor.execute("DELETE FROM checks_history;")
            cursor.execute("DELETE FROM scoring_history;")
            cursor.execute("DELETE FROM search_sessions;")
