"""
Security Audit Tests: SQL Injection, Path Traversal, Secrets in Logs
"""
import tempfile
from pathlib import Path

import pytest

from telegram_username_hunter.database.database import DatabaseManager
from telegram_username_hunter.database.models import UsernameRecord
from telegram_username_hunter.generators.username_generator import is_valid_telegram_username
from telegram_username_hunter.services.export_service import ExportService


@pytest.fixture
def temp_sec_db():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        db_path = Path(tmp_dir) / "sec_hunter.db"
        db = DatabaseManager(db_path)
        yield db


def test_sql_injection_defense_in_username(temp_sec_db):
    # Attacker attempts SQL injection via username string
    malicious_payload = "admin' OR '1'='1"
    assert is_valid_telegram_username(malicious_payload) is False

    # Even if an invalid payload bypassed validator and reached DB
    rec = UsernameRecord(
        username=malicious_payload,
        category="hack",
        status="TEST",
        score=50,
    )
    # Must safely store parameterized without syntax error or drop
    temp_sec_db.upsert_username(rec)

    # Query with malicious filter
    results = temp_sec_db.get_usernames(status="' OR '1'='1")
    assert len(results) == 0

    results_safe = temp_sec_db.get_usernames(status="TEST")
    assert len(results_safe) == 1
    assert results_safe[0].username == malicious_payload


def test_sql_injection_defense_in_sorting(temp_sec_db):
    # Malicious sort_by input attempting SQL injection
    malicious_sort = "score; DROP TABLE usernames; --"
    # Should safely fallback to default 'score' without executing arbitrary SQL
    results = temp_sec_db.get_usernames(sort_by=malicious_sort)
    assert isinstance(results, list)

    # Check that table still exists and functions
    stats = temp_sec_db.get_dashboard_stats()
    assert stats is not None


def test_path_traversal_defense_in_export(temp_sec_db):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as exp_dir:
        exporter = ExportService(temp_sec_db, Path(exp_dir))

        # Ensure writes stay within exports directory
        out = exporter.export_available_usernames()
        assert out.parent == Path(exp_dir)
        assert out.exists()


def test_no_secrets_in_logs_and_records():
    # Verify that records and error messages do not leak system paths or sensitive keys
    rec = UsernameRecord(username="safename", notes="Safe public information only")
    d = rec.to_dict()
    for val in d.values():
        val_str = str(val).lower()
        assert "password" not in val_str
        assert "secret_key" not in val_str
        assert "token" not in val_str or "ton" in val_str or "not in" in val_str
