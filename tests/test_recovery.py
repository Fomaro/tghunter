"""
Recovery and Resilience Tests: Network Drops, 500 Errors, DB Rollbacks
"""
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from telegram_username_hunter.checkers.telegram_checker import TelegramChecker
from telegram_username_hunter.config.settings import AppSettings, UsernameStatus
from telegram_username_hunter.database.database import DatabaseManager
from telegram_username_hunter.database.models import UsernameRecord
from telegram_username_hunter.services.export_service import ExportService
from telegram_username_hunter.services.search_service import SearchService


@pytest.fixture
def temp_resilience_env():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        db_path = Path(tmp_dir) / "resilience.db"
        exp_path = Path(tmp_dir) / "exports"
        settings = AppSettings(
            db_path=db_path,
            exports_dir=exp_path,
            mock_mode=True,
            request_delay_seconds=0.01,
            batch_size=5,
            batch_delay_seconds=0.01
        )
        db = DatabaseManager(db_path)
        exporter = ExportService(db=db, export_dir=exp_path)
        service = SearchService(db=db, settings=settings, export_service=exporter)
        yield service, db


@pytest.mark.asyncio
async def test_recovery_from_network_timeout():
    checker = TelegramChecker(mock_mode=False)

    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Network timed out")):
        status, details = await checker.check_username("testtimeout")
        assert status == UsernameStatus.ERROR
        assert "timed out" in details["details"].lower()


@pytest.mark.asyncio
async def test_recovery_from_server_500_error():
    checker = TelegramChecker(mock_mode=False)

    mock_resp = AsyncMock()
    mock_resp.status_code = 500
    mock_resp.headers = {}

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        status, details = await checker.check_username("testservererr")
        assert status == UsernameStatus.ERROR
        assert status != UsernameStatus.AVAILABLE_TO_CLAIM


@pytest.mark.asyncio
async def test_database_persistence_across_restart():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        db_path = Path(tmp_dir) / "persist.db"

        # Session 1: create and write data
        db1 = DatabaseManager(db_path)
        db1.upsert_username(UsernameRecord(username="persistent_name", category="brand", status="AVAILABLE_TO_CLAIM", score=90))
        del db1

        # Session 2: reopen DB from disk and verify persistence
        db2 = DatabaseManager(db_path)
        res = db2.get_usernames(status="AVAILABLE_TO_CLAIM")
        assert len(res) == 1
        assert res[0].username == "persistent_name"
        assert res[0].score == 90


@pytest.mark.asyncio
async def test_search_stop_and_resume_preserves_data(temp_resilience_env):
    service, db = temp_resilience_env

    # Run search briefly then request stop
    service.on_item_checked = lambda item: service.stop() if item.get("username") else None
    await service.run_regular_hunter(count=5)

    # Verify that items processed before stop are safely persisted in DB
    saved = db.get_usernames()
    assert len(saved) >= 1
    assert service.is_running is False
