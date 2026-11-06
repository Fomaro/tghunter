"""
Tests for SQLite Database Manager & Persistence
"""
import gc
import tempfile
from pathlib import Path

import pytest

from telegram_username_hunter.config.settings import (
    AuctionEligibility,
    BotStatus,
    PremiumBotStatus,
    UsernameStatus,
)
from telegram_username_hunter.database.database import DatabaseManager
from telegram_username_hunter.database.models import (
    BotRecord,
    PremiumAliasRecord,
    UsernameRecord,
)


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        db_path = Path(tmp_dir) / "test_hunter.db"
        db = DatabaseManager(db_path)
        yield db
        del db
        gc.collect()


def test_upsert_and_query_usernames(temp_db):
    rec1 = UsernameRecord(
        username="qevro",
        category="5_chars",
        status=UsernameStatus.AVAILABLE_TO_CLAIM.value,
        score=85,
        auction_eligibility=AuctionEligibility.AUCTION_NOT_SUPPORTED.value
    )
    temp_db.upsert_username(rec1)

    # Duplicate upsert with update
    rec1.score = 88
    temp_db.upsert_username(rec1)

    results = temp_db.get_usernames(status=UsernameStatus.AVAILABLE_TO_CLAIM.value)
    assert len(results) == 1
    assert results[0].username == "qevro"
    assert results[0].score == 88


def test_upsert_and_query_bots(temp_db):
    bot_rec = BotRecord(
        username="qevrobot",
        category="brand",
        status=BotStatus.AVAILABLE_FOR_BOT.value,
        score=90
    )
    temp_db.upsert_bot(bot_rec)

    results = temp_db.get_bots(status=BotStatus.AVAILABLE_FOR_BOT.value)
    assert len(results) == 1
    assert results[0].username == "qevrobot"


def test_upsert_and_query_premium_aliases(temp_db):
    alias_rec = PremiumAliasRecord(
        username="qevro_app",
        suffix="_app",
        category="apps",
        status=PremiumBotStatus.ELIGIBLE_FOR_ASSIGNMENT.value,
        score=82
    )
    temp_db.upsert_premium_alias(alias_rec)

    results = temp_db.get_premium_aliases(status=PremiumBotStatus.ELIGIBLE_FOR_ASSIGNMENT.value)
    assert len(results) == 1
    assert results[0].username == "qevro_app"
    assert results[0].suffix == "_app"


def test_dashboard_stats(temp_db):
    temp_db.upsert_username(UsernameRecord(username="alpha", category="5_chars", status=UsernameStatus.AVAILABLE_TO_CLAIM.value, score=75))
    temp_db.upsert_bot(BotRecord(username="alphabot", category="brand", status=BotStatus.AVAILABLE_FOR_BOT.value, score=85))
    temp_db.upsert_premium_alias(PremiumAliasRecord(username="alpha_ai", suffix="_ai", category="ai", status=PremiumBotStatus.ELIGIBLE_FOR_ASSIGNMENT.value, score=80))

    stats = temp_db.get_dashboard_stats(min_promising_score=70)
    assert stats.total_generated == 3
    assert stats.available_usernames == 1
    assert stats.available_bot_names == 1
    assert stats.premium_bot_aliases == 1
    assert stats.promising_usernames == 1
    assert stats.promising_bot_names == 1
