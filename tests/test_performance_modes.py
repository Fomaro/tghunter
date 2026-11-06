"""
Telegram Username Hunter PRO
Comprehensive Performance Modes & Adaptive Load Management Tests
"""
import asyncio
import gc
import tempfile
import time
from pathlib import Path

import psutil
import pytest

from telegram_username_hunter.config.settings import (
    AppSettings,
    PerformanceMode,
    PERFORMANCE_PROFILES,
    UsernameCategory,
)
from telegram_username_hunter.database.database import DatabaseManager
from telegram_username_hunter.services.export_service import ExportService
from telegram_username_hunter.services.search_service import SearchService


@pytest.fixture
def test_env():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        dir_path = Path(tmp_dir)
        db_path = dir_path / "hunter_perf.db"
        exp_path = dir_path / "exports"

        settings = AppSettings(
            db_path=db_path,
            exports_dir=exp_path,
            mock_mode=True,
            performance_mode=PerformanceMode.STANDARD
        )
        db = DatabaseManager(db_path)
        exporter = ExportService(db=db, export_dir=exp_path)
        service = SearchService(db=db, settings=settings, export_service=exporter)
        yield service, db, settings, dir_path
        service.stop()
        del service
        del exporter
        del db
        gc.collect()


# ================= 1. ECONOMY MODE TEST =================

@pytest.mark.asyncio
async def test_economy_mode_execution(test_env):
    """Test 1: Economy Mode verifies 1 worker, reduced resource usage, sequential processing."""
    service, db, settings, _ = test_env
    service.set_performance_mode(PerformanceMode.ECONOMY)

    profile = settings.get_active_profile()
    assert profile.mode == PerformanceMode.ECONOMY
    assert profile.concurrency == 1
    assert profile.request_delay_seconds == 2.2
    assert service.rate_limiter.base_delay == 2.2

    # Override delay temporarily for fast test execution
    service.rate_limiter.base_delay = 0.02
    service.rate_limiter.jitter = 0.005

    max_workers_seen = 0

    def on_progress(checked, total, speed, avail, err):
        nonlocal max_workers_seen
        max_workers_seen = max(max_workers_seen, service.active_workers_count)

    service.on_progress = on_progress

    # Run check of 10 usernames
    await service.run_regular_hunter(count=10, categories=[UsernameCategory.FIVE_CHAR])

    assert max_workers_seen <= 1
    saved = db.get_usernames(limit=50)
    assert len(saved) == 10

    metrics = service.get_metrics()
    assert metrics["mode"] == "ECONOMY"
    assert metrics["memory_mb"] < 250.0


# ================= 2. STANDARD MODE TEST =================

@pytest.mark.asyncio
async def test_standard_mode_execution(test_env):
    """Test 2: Standard Mode verifies 3 workers, balanced throughput and resource stability."""
    service, db, settings, _ = test_env
    service.set_performance_mode(PerformanceMode.STANDARD)

    profile = settings.get_active_profile()
    assert profile.mode == PerformanceMode.STANDARD
    assert profile.concurrency == 3
    assert profile.request_delay_seconds == 1.2

    service.rate_limiter.base_delay = 0.01
    service.rate_limiter.jitter = 0.005

    max_workers_seen = 0

    def on_progress(checked, total, speed, avail, err):
        nonlocal max_workers_seen
        max_workers_seen = max(max_workers_seen, service.active_workers_count)

    service.on_progress = on_progress

    await service.run_bot_hunter(count=15, categories=[UsernameCategory.BRAND])

    assert max_workers_seen <= 3
    saved = db.get_bots(limit=50)
    assert len(saved) == 15

    metrics = service.get_metrics()
    assert metrics["mode"] == "STANDARD"
    assert metrics["checked_count"] == 15


# ================= 3. FAST MODE & ADAPTIVE THROTTLING TEST =================

@pytest.mark.asyncio
async def test_fast_mode_and_adaptive_throttle(test_env):
    """Test 3: Fast Mode verifies up to 6 workers and adaptive backoff during 429/FloodWait."""
    service, db, settings, _ = test_env
    service.set_performance_mode(PerformanceMode.FAST, custom_concurrency=6)

    profile = settings.get_active_profile()
    assert profile.mode == PerformanceMode.FAST
    assert profile.concurrency == 6

    # Test FloodWait / 429 rate limiter response
    service.rate_limiter.flood_wait_padding = 0.2
    assert not service.rate_limiter.is_throttled

    # Trigger a 429 error on the rate limiter
    service.rate_limiter.record_error(is_rate_limit=True, retry_after=0.8)

    assert service.rate_limiter.is_throttled
    assert service.rate_limiter.cooldown_remaining > 0
    # SearchService must adapt target concurrency down to 1 during throttling
    assert service._effective_target_concurrency() == 1

    metrics = service.get_metrics()
    assert metrics["is_throttled"] is True
    assert metrics["throttle_status"] == "THROTTLED"

    # Wait for cooldown to expire
    await asyncio.sleep(1.2)

    # Record successful request to reset backoff
    for _ in range(5):
        service.rate_limiter.record_success()

    assert not service.rate_limiter.is_throttled
    assert service._effective_target_concurrency() == 6


# ================= 4. DYNAMIC MODE SWITCHING TEST =================

@pytest.mark.asyncio
async def test_dynamic_mode_switching_live(test_env):
    """Test 4: Switch modes on-the-fly without restarting or dropping data."""
    service, db, settings, _ = test_env

    service.set_performance_mode(PerformanceMode.STANDARD)
    service.rate_limiter.base_delay = 0.01
    service.rate_limiter.jitter = 0.002

    modes_seen = []

    def on_item_checked(item):
        modes_seen.append(service.settings.performance_mode)

    service.on_item_checked = on_item_checked

    # Start hunter task in background
    hunter_task = asyncio.create_task(
        service.run_premium_bot_hunter(count=20, categories=[UsernameCategory.AI])
    )

    await asyncio.sleep(0.05)
    # Live switch to ECONOMY
    service.set_performance_mode(PerformanceMode.ECONOMY)
    assert service.settings.performance_mode == PerformanceMode.ECONOMY
    assert service.db.get_setting("performance_mode") == "ECONOMY"

    await asyncio.sleep(0.05)
    # Live switch to FAST
    service.set_performance_mode(PerformanceMode.FAST, custom_concurrency=5)
    assert service.settings.performance_mode == PerformanceMode.FAST
    assert service.settings.custom_concurrency == 5
    assert service.db.get_setting("custom_concurrency") == "5"

    await hunter_task

    # Verify all items processed without loss
    saved = db.get_premium_aliases(limit=50)
    assert len(saved) == 20
    assert len(modes_seen) == 20


# ================= 5. EXTENDED LOAD & MEMORY STABILITY TEST =================

@pytest.mark.asyncio
async def test_extended_load_and_memory_stability(test_env):
    """Test 5: Process 200 items under continuous load, checking for memory leaks and db integrity."""
    service, db, settings, _ = test_env
    service.set_performance_mode(PerformanceMode.FAST, custom_concurrency=4)
    service.rate_limiter.base_delay = 0.005
    service.rate_limiter.jitter = 0.001

    proc = psutil.Process()
    ram_before = proc.memory_info().rss / (1024 * 1024)

    await service.run_regular_hunter(count=150, categories=[UsernameCategory.TECH, UsernameCategory.CRYPTO])

    ram_after = proc.memory_info().rss / (1024 * 1024)
    ram_delta = ram_after - ram_before

    # Memory growth should remain very low (< 50MB delta during test)
    assert ram_delta < 50.0

    # Verify DB integrity
    with db._connection_context() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        res = cursor.fetchone()
        assert res[0] == "ok"

    stats = db.get_dashboard_stats()
    assert stats.total_checked >= 150
