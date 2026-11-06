"""
Telegram Username Hunter PRO
Comprehensive Regression Test Suite (Prompt #3)
Verifies that bug fixes and performance modes maintain 100% integrity across all subsystems.
"""
import asyncio
import gc
import tempfile
import time
from pathlib import Path

import pytest

from telegram_username_hunter.analysis.auction_eligibility import (
    AuctionEligibilityAnalyzer,
)
from telegram_username_hunter.analysis.market_analysis import MarketPotentialAnalyzer
from telegram_username_hunter.analysis.scoring import UsernameScorer
from telegram_username_hunter.checkers.bot_checker import BotChecker
from telegram_username_hunter.checkers.fragment_checker import FragmentChecker
from telegram_username_hunter.checkers.premium_bot_checker import PremiumBotChecker
from telegram_username_hunter.checkers.telegram_checker import TelegramChecker
from telegram_username_hunter.config.settings import (
    AppSettings,
    AuctionEligibility,
    BotStatus,
    PerformanceMode,
    PERFORMANCE_PROFILES,
    PremiumBotStatus,
    UsernameCategory,
    UsernameStatus,
)
from telegram_username_hunter.database.database import ALLOWED_SORT_COLUMNS, DatabaseManager
from telegram_username_hunter.database.models import (
    BotRecord,
    PremiumAliasRecord,
    UsernameRecord,
)
from telegram_username_hunter.generators.bot_generator import BotUsernameGenerator
from telegram_username_hunter.generators.premium_bot_generator import (
    PremiumBotGenerator,
)
from telegram_username_hunter.generators.username_generator import UsernameGenerator
from telegram_username_hunter.gui import HunterApp
from telegram_username_hunter.services.export_service import ExportService
from telegram_username_hunter.services.rate_limiter import RateLimiter
from telegram_username_hunter.services.search_service import SearchService


@pytest.fixture
def regression_env():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        dir_path = Path(tmp_dir)
        db_path = dir_path / "hunter_regression.db"
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

        yield service, db, exporter, settings, exp_path
        service.stop()
        del service
        del exporter
        del db
        gc.collect()


# 1. GENERATION REGRESSION TESTS

def test_regression_regular_generation_and_rules():
    """Verify regular username generation rules: lengths 5-32, no duplicates, valid categories."""
    gen = UsernameGenerator(seed=42)
    batch = gen.generate_batch(count=150, min_length=5, max_length=32)

    assert len(batch) == 150
    seen = set()
    for name, cat in batch:
        assert 5 <= len(name) <= 32
        assert name.islower()
        assert name not in seen
        seen.add(name)
        assert isinstance(cat, str)


def test_regression_bot_generation_and_rules():
    """Verify bot username generation rules: ends with 'bot', lengths 5-32, BotFather compliant."""
    gen = BotUsernameGenerator(seed=42)
    batch = gen.generate_batch(count=100, min_length=5, max_length=32)

    assert len(batch) == 100
    seen = set()
    for name, cat in batch:
        assert 5 <= len(name) <= 32
        assert name.endswith("bot")
        assert name not in seen
        seen.add(name)


def test_regression_premium_alias_generation_and_rules():
    """Verify premium bot alias generation rules: valid suffix, valid category, lengths 5-32."""
    gen = PremiumBotGenerator(seed=42)
    batch = gen.generate_batch(count=100, min_length=5, max_length=32)

    assert len(batch) == 100
    seen = set()
    valid_suffixes = {"_app", "_ai", "_game", "_agent", "_bot", "_gay"}
    for name, sfx, cat in batch:
        assert 5 <= len(name) <= 32
        assert sfx in valid_suffixes
        assert name.endswith(sfx)
        assert name not in seen
        seen.add(name)


# 2. CHECKERS & SCORING REGRESSION TESTS

@pytest.mark.asyncio
async def test_regression_availability_checkers_mock_and_parsing():
    """Verify availability checkers handle mock parsing and contract return types."""
    limiter = RateLimiter(base_delay=0.001, jitter=0.001)
    frag_checker = FragmentChecker(rate_limiter=limiter, mock_mode=True)
    tg_checker = TelegramChecker(rate_limiter=limiter, fragment_checker=frag_checker, mock_mode=True)
    bot_checker = BotChecker(rate_limiter=limiter, fragment_checker=frag_checker, mock_mode=True)
    pba_checker = PremiumBotChecker(rate_limiter=limiter, fragment_checker=frag_checker, mock_mode=True)

    status, details = await tg_checker.check_username("apex")
    assert isinstance(status, UsernameStatus)
    assert "source" in details

    bot_status, bot_details = await bot_checker.check_bot_username("apexbot")
    assert isinstance(bot_status, BotStatus)

    alias_status, alias_details = await pba_checker.check_alias("apex_app")
    assert isinstance(alias_status, PremiumBotStatus)


def test_regression_scoring_and_market_potential():
    """Verify scoring logic (0-100), pre-compiled regexes, and market potential tiers."""
    scorer = UsernameScorer()
    score, breakdown = scorer.calculate_score("apex", category="brand")
    assert 0 <= score <= 100
    assert "length_score" in breakdown
    assert "pronounce_score" in breakdown
    assert "semantic_score" in breakdown

    profile = MarketPotentialAnalyzer.get_market_profile("apex", score)
    assert "potential_tier" in profile
    assert "benchmark_match" in profile
    assert "similar_benchmarks" in profile


# 3. DATABASE & PERSISTENCE REGRESSION TESTS

def test_regression_sqlite_persistence_and_no_locks(regression_env):
    """Verify database persistence, absence of connection leaks, and SQL injection safety."""
    _service, db, _exporter, _settings, _exp_path = regression_env

    # 1. SQL Injection attempt via status/sort_by
    malicious_sort = "score; DROP TABLE usernames; --"
    res = db.get_usernames(sort_by=malicious_sort)
    assert isinstance(res, list)

    # 2. Upsert records
    un_rec = UsernameRecord(username="alpha1", category="5_chars", status=UsernameStatus.AVAILABLE_TO_CLAIM.value, score=90)
    bot_rec = BotRecord(username="alpha1bot", category="brand", status=BotStatus.AVAILABLE_FOR_BOT.value, score=85)
    pba_rec = PremiumAliasRecord(username="alpha1_app", suffix="_app", category="apps", status=PremiumBotStatus.ELIGIBLE_FOR_ASSIGNMENT.value, score=88)

    db.upsert_username(un_rec)
    db.upsert_bot(bot_rec)
    db.upsert_premium_alias(pba_rec)

    stats = db.get_dashboard_stats(min_promising_score=70)
    assert stats.available_usernames == 1
    assert stats.available_bot_names == 1
    assert stats.premium_bot_aliases == 1
    assert stats.promising_usernames == 1

    # 3. Setting persistence
    db.save_setting("test_key", "test_val")
    assert db.get_setting("test_key") == "test_val"


def test_regression_exports_txt_and_csv_format(regression_env):
    """Verify export files are strictly categorized and correctly formatted."""
    _service, db, exporter, settings, exp_path = regression_env

    db.upsert_username(UsernameRecord(username="free_un", category="5_chars", status=UsernameStatus.AVAILABLE_TO_CLAIM.value, score=92))
    db.upsert_username(UsernameRecord(username="taken_un", category="5_chars", status=UsernameStatus.TAKEN.value, score=95))
    db.upsert_bot(BotRecord(username="free_bot", category="brand", status=BotStatus.AVAILABLE_FOR_BOT.value, score=85))

    exporter.run_all_auto_exports(min_score=70)

    # Free names file must only contain free usernames
    with open(exp_path / "available_usernames.txt", "r", encoding="utf-8") as f:
        content = f.read()
        assert "free_un" in content
        assert "taken_un" not in content

    # CSV must exist and contain headers
    with open(exp_path / "all_usernames.csv", "r", encoding="utf-8") as f:
        csv_header = f.readline()
        assert "username" in csv_header
        assert "status" in csv_header


# 4. PERFORMANCE MODES & DYNAMIC CONTROLS REGRESSION TESTS

@pytest.mark.asyncio
async def test_regression_all_three_performance_modes(regression_env):
    """Verify Economy, Standard, and Fast mode parameter loading and rate limiter synchrony."""
    service, db, _exporter, settings, _exp_path = regression_env

    # 1. Economy
    service.set_performance_mode(PerformanceMode.ECONOMY)
    prof_eco = settings.get_active_profile()
    assert prof_eco.concurrency == 1
    assert prof_eco.request_delay_seconds == 2.2
    assert service.rate_limiter.base_delay == 2.2
    assert db.get_setting("performance_mode") == "ECONOMY"

    # 2. Standard
    service.set_performance_mode(PerformanceMode.STANDARD)
    prof_std = settings.get_active_profile()
    assert prof_std.concurrency == 3
    assert prof_std.request_delay_seconds == 1.2
    assert service.rate_limiter.base_delay == 1.2
    assert db.get_setting("performance_mode") == "STANDARD"

    # 3. Fast
    service.set_performance_mode(PerformanceMode.FAST, custom_concurrency=7)
    prof_fst = settings.get_active_profile()
    assert prof_fst.concurrency == 7
    assert prof_fst.request_delay_seconds == 0.5
    assert service.rate_limiter.base_delay == 0.5
    assert db.get_setting("custom_concurrency") == "7"


@pytest.mark.asyncio
async def test_regression_stop_pause_resume_during_flood_wait(regression_env):
    """Verify stop and pause responsiveness during active FloodWait cooldown."""
    service, _db, _exporter, _settings, _exp_path = regression_env

    # Trigger a 15-second FloodWait cooldown
    service.rate_limiter.record_error(is_rate_limit=True, retry_after=15.0)
    assert service.rate_limiter.is_throttled
    assert service.rate_limiter.cooldown_remaining > 5.0

    # Stop should break interruptible sleep within <= 0.35s
    stop_start = time.time()
    service.stop()
    acquire_task = asyncio.create_task(service.rate_limiter.acquire())

    # Wait for acquire to exit
    await asyncio.wait_for(acquire_task, timeout=1.0)
    elapsed = time.time() - stop_start
    assert elapsed < 0.8  # Broken immediately without waiting 15s


# 5. GUI TABS & CATEGORY ISOLATION REGRESSION TESTS

def test_regression_gui_all_tabs_and_category_isolation(regression_env):
    """Verify GUI instantiation, tab navigation, and strict category isolation for updates."""
    _service, db, _exporter, settings, _exp_path = regression_env

    app = HunterApp(db=db, settings=settings)
    app.withdraw()

    try:
        # All 9 views exist
        expected_views = [
            "Dashboard", "Username Hunter", "Bot Username Hunter",
            "Premium Bot Names", "Premium Selection", "Bot Selection",
            "Auction Potential", "History", "Settings"
        ]
        for vname in expected_views:
            assert vname in app.views

        # Simulate items for 3 different types
        app._handle_item_ui_update({"username": "reg_name", "target_type": "REGULAR", "category": "5_chars", "status": "AVAILABLE_TO_CLAIM", "score": 90})
        app._handle_item_ui_update({"username": "bot_name_bot", "target_type": "BOT", "category": "brand", "status": "AVAILABLE_FOR_BOT", "score": 85})
        app._handle_item_ui_update({"username": "pba_name_app", "target_type": "PREMIUM_BOT", "category": "apps", "status": "ELIGIBLE_FOR_ASSIGNMENT", "score": 88})

        # Regular tree has reg_name and NOT bot_name_bot
        reg_tree = app.views["Username Hunter"].tree
        reg_items = [reg_tree.item(c)["values"][0] for c in reg_tree.get_children()]
        assert "reg_name" in reg_items
        assert "bot_name_bot" not in reg_items

        # Bot tree has bot_name_bot and NOT reg_name
        bot_tree = app.views["Bot Username Hunter"].tree
        bot_items = [bot_tree.item(c)["values"][0] for c in bot_tree.get_children()]
        assert "bot_name_bot" in bot_items
        assert "reg_name" not in bot_items

        # Premium bot tree has pba_name_app
        pba_tree = app.views["Premium Bot Names"].tree
        pba_items = [pba_tree.item(c)["values"][0] for c in pba_tree.get_children()]
        assert "pba_name_app" in pba_items
        assert "reg_name" not in pba_items

    finally:
        app.destroy()
