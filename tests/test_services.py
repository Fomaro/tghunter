"""
Tests for Search Pipeline & Export Services
"""
import tempfile
import gc
from pathlib import Path
import pytest
from telegram_username_hunter.config.settings import (
    AppSettings,
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
from telegram_username_hunter.services.export_service import ExportService
from telegram_username_hunter.services.search_service import SearchService
from telegram_username_hunter.services.cache_service import CacheService


@pytest.fixture
def test_env():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        dir_path = Path(tmp_dir)
        db_path = dir_path / "hunter.db"
        exp_path = dir_path / "exports"

        settings = AppSettings(
            db_path=db_path,
            exports_dir=exp_path,
            mock_mode=True,
            request_delay_seconds=0.01,
            batch_size=5,
            batch_delay_seconds=0.01,
        )
        db = DatabaseManager(db_path)
        exporter = ExportService(db=db, export_dir=exp_path)
        service = SearchService(db=db, settings=settings, export_service=exporter)
        yield service, db, exporter, exp_path
        del service
        del exporter
        del db
        gc.collect()


@pytest.mark.asyncio
async def test_search_service_regular_run(test_env):
    service, db, _exporter, _exp_path = test_env

    items_checked = []
    service.on_item_checked = lambda item: items_checked.append(item)

    await service.run_regular_hunter(count=10)

    assert len(items_checked) == 10
    saved = db.get_usernames(limit=50)
    assert len(saved) >= 10


@pytest.mark.asyncio
async def test_search_service_bot_run(test_env):
    service, db, _exporter, _exp_path = test_env

    items_checked = []
    service.on_item_checked = lambda item: items_checked.append(item)

    await service.run_bot_hunter(count=8)

    assert len(items_checked) == 8
    saved = db.get_bots(limit=50)
    assert len(saved) >= 8


@pytest.mark.asyncio
async def test_search_service_premium_alias_run(test_env):
    service, db, _exporter, _exp_path = test_env

    items_checked = []
    service.on_item_checked = lambda item: items_checked.append(item)

    await service.run_premium_bot_hunter(count=8)

    assert len(items_checked) == 8
    saved = db.get_premium_aliases(limit=50)
    assert len(saved) >= 8


@pytest.mark.asyncio
async def test_search_service_pause_resume_stop(test_env):
    service, _db, _exporter, _exp_path = test_env

    service.pause()
    assert service.is_paused is True

    service.resume()
    assert service.is_paused is False

    service.stop()
    assert service.is_running is False


def test_export_service_files_generated(test_env):
    _service, db, exporter, exp_path = test_env

    # Populate dummy data
    db.upsert_username(UsernameRecord(username="avail1", category="5_chars", status=UsernameStatus.AVAILABLE_TO_CLAIM.value, score=85))
    db.upsert_username(UsernameRecord(username="taken1", category="5_chars", status=UsernameStatus.TAKEN.value, score=90))
    db.upsert_username(UsernameRecord(username="unknown1", category="5_chars", status=UsernameStatus.UNKNOWN.value, score=70))

    db.upsert_bot(BotRecord(username="freebot", category="brand", status=BotStatus.AVAILABLE_FOR_BOT.value, score=88))
    db.upsert_premium_alias(PremiumAliasRecord(username="free_app", suffix="_app", category="apps", status=PremiumBotStatus.ELIGIBLE_FOR_ASSIGNMENT.value, score=92))

    # Run auto exports
    exporter.run_all_auto_exports(min_score=70)

    # Markdown reports verification
    md_reports = exporter.export_all_markdown_reports()
    assert (exp_path / "1_available.md").exists()
    assert (exp_path / "2_fragment_purchase.md").exists()
    assert (exp_path / "3_occupied.md").exists()
    assert (exp_path / "4_restricted.md").exists()
    assert (exp_path / "5_invalid.md").exists()
    assert (exp_path / "6_unknown.md").exists()
    assert (exp_path / "7_errors.md").exists()
    assert (exp_path / "8_all_statuses.md").exists()

    with open(exp_path / "1_available.md", "r", encoding="utf-8") as f:
        avail_md = f.read()
        assert "avail1" in avail_md
        assert "taken1" not in avail_md
        assert "## 👤 Юзернеймы Telegram" in avail_md

    with open(exp_path / "3_occupied.md", "r", encoding="utf-8") as f:
        occ_md = f.read()
        assert "taken1" in occ_md
        assert "avail1" not in occ_md

    # Check that expected files are created
    assert (exp_path / "available_usernames.txt").exists()
    assert (exp_path / "premium_selection.txt").exists()
    assert (exp_path / "available_bot_names.txt").exists()
    assert (exp_path / "bot_selection.txt").exists()
    assert (exp_path / "premium_bot_names.txt").exists()
    assert (exp_path / "premium_bot_selection.txt").exists()
    assert (exp_path / "unknown_names.txt").exists()
    assert (exp_path / "all_usernames.csv").exists()
    assert (exp_path / "all_bot_names.csv").exists()
    assert (exp_path / "premium_aliases.csv").exists()

    # Rule check: available_usernames.txt should NOT contain taken or unknown names
    with open(exp_path / "available_usernames.txt", "r", encoding="utf-8") as f:
        content = f.read()
        assert "avail1" in content
        assert "taken1" not in content
        assert "unknown1" not in content

    # unknown_names.txt should contain unknown1
    with open(exp_path / "unknown_names.txt", "r", encoding="utf-8") as f:
        unknown_content = f.read()
        assert "unknown1" in unknown_content


def test_cache_service():
    cache = CacheService(ttl_seconds=1.0)
    assert cache.get("none") is None

    cache.set("key1", "val1")
    assert cache.get("key1") == "val1"

    cache.clear()
    assert cache.get("key1") is None
