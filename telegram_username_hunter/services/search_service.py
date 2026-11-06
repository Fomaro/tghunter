"""
Telegram Username Hunter PRO
Search and Pipeline Orchestration Service with Adaptive Worker Pool
"""
import asyncio
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Optional

import psutil

from telegram_username_hunter.analysis.auction_eligibility import (
    AuctionEligibilityAnalyzer,
)
from telegram_username_hunter.analysis.scoring import UsernameScorer
from telegram_username_hunter.checkers.bot_checker import BotChecker
from telegram_username_hunter.checkers.fragment_checker import FragmentChecker
from telegram_username_hunter.checkers.premium_bot_checker import PremiumBotChecker
from telegram_username_hunter.checkers.telegram_checker import TelegramChecker
from telegram_username_hunter.config.settings import (
    AppSettings,
    BotStatus,
    PerformanceMode,
    PerformanceProfile,
    PremiumBotStatus,
    UsernameCategory,
    UsernameStatus,
)
from telegram_username_hunter.database.database import DatabaseManager
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
from telegram_username_hunter.services.cache_service import CacheService
from telegram_username_hunter.services.export_service import ExportService
from telegram_username_hunter.services.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class SearchService:
    """Coordinates generation, checking, scoring, and persistence with thread-safe controls and dynamic worker pool."""

    def __init__(
        self,
        db: DatabaseManager,
        settings: AppSettings,
        export_service: ExportService | None = None
    ):
        self.db = db
        self.settings = settings
        self.export_service = export_service or ExportService(db=db, export_dir=settings.exports_dir)

        # Restore persisted performance settings if available
        saved_mode = self.db.get_setting("performance_mode")
        if saved_mode:
            try:
                self.settings.performance_mode = PerformanceMode(saved_mode)
            except ValueError:
                pass
        saved_concurrency = self.db.get_setting("custom_concurrency")
        if saved_concurrency:
            try:
                self.settings.custom_concurrency = int(saved_concurrency)
            except ValueError:
                pass

        profile = self.settings.get_active_profile()

        # State flags
        self.is_running: bool = False
        self.is_paused: bool = False
        self._stop_requested: bool = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()

        # Worker Pool & Concurrency
        self._target_concurrency: int = profile.concurrency
        self._is_throttled: bool = False
        self._workers: set[asyncio.Task] = set()
        self._work_queue: asyncio.Queue = asyncio.Queue()
        self._db_lock = asyncio.Lock()
        self._stats_lock = asyncio.Lock()
        self._active_session_type: str = ""
        self._active_session_id: int = 0
        self._total_candidates: int = 0
        self._checked_count: int = 0
        self._available_count: int = 0
        self._error_count: int = 0
        self._start_time: float = 0.0

        # Components
        self.rate_limiter = RateLimiter(
            base_delay=profile.request_delay_seconds,
            jitter=profile.request_jitter_seconds,
            backoff_factor=settings.backoff_factor,
            flood_wait_padding=settings.flood_wait_padding_seconds
        )
        self.rate_limiter.is_stopped_check = lambda: self._stop_requested
        self.rate_limiter.is_paused_check = lambda: self.is_paused
        self.rate_limiter.pause_event = self._pause_event
        self.rate_limiter.on_throttle_change = self._handle_throttle_change

        self.cache = CacheService()
        self.scorer = UsernameScorer()

        self.fragment_checker = FragmentChecker(
            rate_limiter=self.rate_limiter,
            mock_mode=settings.mock_mode,
            timeout=settings.timeout_seconds
        )
        self.telegram_checker = TelegramChecker(
            rate_limiter=self.rate_limiter,
            fragment_checker=self.fragment_checker,
            mock_mode=settings.mock_mode,
            timeout=settings.timeout_seconds
        )
        self.bot_checker = BotChecker(
            rate_limiter=self.rate_limiter,
            fragment_checker=self.fragment_checker,
            mock_mode=settings.mock_mode,
            timeout=settings.timeout_seconds
        )
        self.premium_bot_checker = PremiumBotChecker(
            rate_limiter=self.rate_limiter,
            fragment_checker=self.fragment_checker,
            mock_mode=settings.mock_mode,
            timeout=settings.timeout_seconds
        )

        # Generators
        self.un_generator = UsernameGenerator()
        self.bot_generator = BotUsernameGenerator()
        self.pba_generator = PremiumBotGenerator()

        # Callbacks
        self.on_item_checked: Callable[[dict[str, Any]], None] | None = None
        self.on_progress: Callable[[int, int, float, int, int], None] | None = None
        self.on_log: Callable[[str], None] | None = None
        self.on_throttle_event: Callable[[bool, float, str], None] | None = None

    # ================= CONCURRENCY & MODE MANAGEMENT =================

    @property
    def active_workers_count(self) -> int:
        return len([t for t in self._workers if not t.done()])

    def _effective_target_concurrency(self) -> int:
        """During active FloodWait/429 throttling, drop to 1 worker; otherwise use target."""
        if self._is_throttled:
            return 1
        return max(1, self._target_concurrency)

    def set_performance_mode(
        self,
        mode: PerformanceMode,
        custom_concurrency: Optional[int] = None
    ) -> None:
        """Switch performance mode dynamically and adapt worker pool on the fly."""
        self.settings.performance_mode = mode
        if custom_concurrency is not None:
            self.settings.custom_concurrency = custom_concurrency

        profile = self.settings.get_active_profile()
        self._target_concurrency = profile.concurrency

        # Update rate limiter timings
        self.rate_limiter.update_profile(
            base_delay=profile.request_delay_seconds,
            jitter=profile.request_jitter_seconds
        )

        # Persist settings to database
        self.db.save_setting("performance_mode", mode.value)
        if custom_concurrency is not None:
            self.db.save_setting("custom_concurrency", str(custom_concurrency))

        self._emit_log(
            f"Performance mode set to: {profile.name_ru} "
            f"(Concurrency: {profile.concurrency}, Delay: {profile.request_delay_seconds}s)"
        )

        # Dynamically scale workers if pipeline is active
        if self.is_running:
            self._adjust_workers()

    def _adjust_workers(self) -> None:
        """Spawn extra workers or allow excess workers to retire dynamically."""
        self._workers = {t for t in self._workers if not t.done()}
        target = self._effective_target_concurrency()

        if len(self._workers) < target and not self._stop_requested:
            needed = target - len(self._workers)
            for _ in range(needed):
                worker_task = asyncio.create_task(self._worker_loop())
                self._workers.add(worker_task)
                worker_task.add_done_callback(lambda t: self._workers.discard(t))

    def _handle_throttle_change(self, is_throttled: bool, duration: float, reason: str) -> None:
        """Callback from RateLimiter when FloodWait or recovery triggers."""
        self._is_throttled = is_throttled
        if is_throttled:
            self._emit_log(f"⚠️ Adaptive Throttle Activated: {reason} (Cooldown {duration:.1f}s, dropping concurrency to 1)")
        else:
            self._emit_log("🟢 Normal Rate Restored: Resuming standard worker concurrency.")

        if self.on_throttle_event:
            try:
                self.on_throttle_event(is_throttled, duration, reason)
            except Exception as e:
                logger.error(f"Error in on_throttle_event callback: {e}")

        if self.is_running:
            self._adjust_workers()

    def get_metrics(self) -> dict[str, Any]:
        """Collect live operational telemetry for UI and reports."""
        profile = self.settings.get_active_profile()
        now = time.time()
        elapsed = max(0.1, now - self._start_time) if (self._start_time > 0 and self.is_running) else 1.0
        speed_per_min = (self._checked_count / (elapsed / 60.0)) if (self.is_running and elapsed > 0) else 0.0

        try:
            proc = psutil.Process()
            ram_mb = proc.memory_info().rss / (1024 * 1024)
            cpu_pct = psutil.cpu_percent(interval=None)
        except Exception:
            ram_mb = 0.0
            cpu_pct = 0.0

        return {
            "mode": self.settings.performance_mode.value,
            "mode_name": profile.name_ru,
            "target_concurrency": self._target_concurrency,
            "active_workers": self.active_workers_count,
            "speed_per_min": round(speed_per_min, 1),
            "checked_count": self._checked_count,
            "available_count": self._available_count,
            "error_count": self._error_count,
            "ram_mb": round(ram_mb, 1),
            "memory_mb": round(ram_mb, 1),
            "cpu_percent": round(cpu_pct, 1),
            "is_throttled": self.rate_limiter.is_throttled,
            "cooldown_remaining": round(self.rate_limiter.cooldown_remaining, 1),
            "throttle_status": "THROTTLED" if self.rate_limiter.is_throttled else "NORMAL",
        }

    # ================= LIFECYCLE CONTROLS =================

    def pause(self) -> None:
        self.is_paused = True
        self._pause_event.clear()
        self._emit_log("Search paused by user.")

    def resume(self) -> None:
        self.is_paused = False
        self._pause_event.set()
        self._emit_log("Search resumed.")

    def stop(self) -> None:
        self._stop_requested = True
        self.is_running = False
        self.is_paused = False
        self._pause_event.set()
        self._emit_log("Search stopping...")

    def _emit_log(self, msg: str) -> None:
        logger.info(msg)
        if self.on_log:
            try:
                self.on_log(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
            except Exception as e:
                logger.error(f"Error in on_log callback: {e}")

    # ================= PIPELINE ORCHESTRATION =================

    async def _worker_loop(self) -> None:
        """Concurrent worker pulling items from queue and executing check."""
        profile = self.settings.get_active_profile()

        while not self._stop_requested:
            await self._pause_event.wait()

            # Dynamic scale down: if too many workers for target, exit gracefully
            self._workers = {t for t in self._workers if not t.done()}
            if len(self._workers) > self._effective_target_concurrency():
                break

            try:
                item = await asyncio.wait_for(self._work_queue.get(), timeout=0.25)
            except asyncio.TimeoutError:
                if self._work_queue.empty():
                    break
                continue

            try:
                if self._stop_requested:
                    break

                target_type = self._active_session_type
                await self._process_single_candidate(item, target_type, profile)

            except Exception as e:
                logger.error(f"Error processing candidate {item}: {e}", exc_info=True)
                async with self._stats_lock:
                    self._error_count += 1
            finally:
                self._work_queue.task_done()

    async def _process_single_candidate(
        self,
        item: tuple,
        target_type: str,
        profile: PerformanceProfile
    ) -> None:
        """Process one candidate through scoring, checking, DB write and notifications."""
        record: UsernameRecord | BotRecord | PremiumAliasRecord
        if target_type == "REGULAR_USERNAMES":
            username, cat = item
            score, breakdown = self.scorer.calculate_score(username, category=cat)
            reg_status, details = await self.telegram_checker.check_username(username)
            fragment_url = AuctionEligibilityAnalyzer.get_fragment_url(username)
            _, auction_elig, _ = AuctionEligibilityAnalyzer.analyze_regular_username(
                username, reg_status.value, details.get("fragment_data", {})
            )
            record = UsernameRecord(
                username=username,
                category=cat,
                status=reg_status.value,
                score=score,
                auction_eligibility=auction_elig,
                fragment_url=fragment_url,
                last_checked_at=datetime.now(UTC).isoformat(),
                check_source=details.get("source", "unknown"),
                notes=details.get("details", "")
            )
            is_free = (reg_status == UsernameStatus.AVAILABLE_TO_CLAIM)
            is_err = (reg_status == UsernameStatus.ERROR)
            target_key = "REGULAR"

            async with self._db_lock:
                self.db.record_scoring(username, "username", score, breakdown)
                self.db.upsert_username(record)
                self.db.log_check("username", username, None, reg_status.value, check_source=details.get("source", ""))

        elif target_type == "BOT_USERNAMES":
            username, cat = item
            score, breakdown = self.scorer.calculate_score(username, category=cat, is_bot=True)
            bot_status, details = await self.bot_checker.check_bot_username(username)
            fragment_url = AuctionEligibilityAnalyzer.get_fragment_url(username)
            _, auction_elig, _ = AuctionEligibilityAnalyzer.analyze_bot_username(
                username, bot_status.value, details.get("fragment_data", {})
            )
            record = BotRecord(
                username=username,
                category=cat,
                status=bot_status.value,
                score=score,
                auction_eligibility=auction_elig,
                fragment_url=fragment_url,
                last_checked_at=datetime.now(UTC).isoformat(),
                check_source=details.get("source", "unknown"),
                notes=details.get("details", "")
            )
            is_free = (bot_status == BotStatus.AVAILABLE_FOR_BOT)
            is_err = (bot_status == BotStatus.ERROR)
            target_key = "BOT"

            async with self._db_lock:
                self.db.record_scoring(username, "bot", score, breakdown)
                self.db.upsert_bot(record)
                self.db.log_check("bot", username, None, bot_status.value, check_source=details.get("source", ""))

        elif target_type == "PREMIUM_BOT_ALIASES":
            username, suffix, cat = item
            score, breakdown = self.scorer.calculate_score(username, category=cat, is_premium_alias=True)
            prem_status, details = await self.premium_bot_checker.check_alias(username)
            fragment_url = AuctionEligibilityAnalyzer.get_fragment_url(username)
            _, auction_elig, _ = AuctionEligibilityAnalyzer.analyze_premium_alias(
                username, prem_status.value, details.get("fragment_data", {})
            )
            record = PremiumAliasRecord(
                username=username,
                suffix=suffix,
                category=cat,
                status=prem_status.value,
                score=score,
                auction_eligibility=auction_elig,
                fragment_url=fragment_url,
                last_checked_at=datetime.now(UTC).isoformat(),
                check_source=details.get("source", "unknown"),
                notes=details.get("details", "")
            )
            is_free = (prem_status == PremiumBotStatus.ELIGIBLE_FOR_ASSIGNMENT)
            is_err = (prem_status == PremiumBotStatus.ERROR)
            target_key = "PREMIUM_BOT"

            async with self._db_lock:
                self.db.record_scoring(username, "premium_bot", score, breakdown)
                self.db.upsert_premium_alias(record)
                self.db.log_check("premium_bot", username, None, prem_status.value, check_source=details.get("source", ""))
        else:
            return

        # Atomically update counters
        async with self._stats_lock:
            self._checked_count += 1
            if is_free:
                self._available_count += 1
                self._emit_log(f"FOUND FREE: @{username} | Score: {score}/100 | {target_key}")
            elif is_err:
                self._error_count += 1

            curr_checked = self._checked_count
            curr_avail = self._available_count
            curr_err = self._error_count

        elapsed = max(0.1, time.time() - self._start_time)
        speed = curr_checked / elapsed

        if self.on_progress:
            self.on_progress(curr_checked, self._total_candidates, speed, curr_avail, curr_err)

        if self.on_item_checked:
            item_dict = record.to_dict()
            item_dict["target_type"] = target_key
            self.on_item_checked(item_dict)

        # Batch pacing delay
        if curr_checked % profile.batch_size == 0 and profile.batch_delay_seconds > 0:
            await asyncio.sleep(profile.batch_delay_seconds)

    async def _execute_pipeline(
        self,
        session_type: str,
        candidates: list[Any]
    ) -> None:
        """Run the multi-worker pipeline for a given candidate set."""
        self.is_running = True
        self._stop_requested = False
        self.is_paused = False
        self._pause_event.set()

        self._active_session_type = session_type
        self._total_candidates = len(candidates)
        self._checked_count = 0
        self._available_count = 0
        self._error_count = 0
        self._start_time = time.time()

        session_id = self.db.create_session(session_type)
        self._active_session_id = session_id

        # Enqueue all candidates
        # Clear out any leftover queue items
        while not self._work_queue.empty():
            try:
                self._work_queue.get_nowait()
                self._work_queue.task_done()
            except Exception:
                break

        for item in candidates:
            await self._work_queue.put(item)

        # Launch workers matching initial effective target
        target = self._effective_target_concurrency()
        self._workers.clear()
        for _ in range(target):
            worker_task = asyncio.create_task(self._worker_loop())
            self._workers.add(worker_task)
            worker_task.add_done_callback(lambda t: self._workers.discard(t))

        # Wait until queue is completely processed or stop was requested
        while not self._work_queue.empty() and not self._stop_requested:
            await asyncio.sleep(0.1)

        if self._stop_requested:
            # Drain remaining items in queue so tasks unblock
            while not self._work_queue.empty():
                try:
                    self._work_queue.get_nowait()
                    self._work_queue.task_done()
                except Exception:
                    break

        await self._work_queue.join()

        # Await remaining workers
        if self._workers:
            for w in list(self._workers):
                if not w.done():
                    w.cancel()
            await asyncio.gather(*list(self._workers), return_exceptions=True)
            self._workers.clear()

        # Finalize session
        self.db.update_session(
            session_id,
            self._total_candidates,
            self._checked_count,
            self._available_count,
            self._error_count,
            "FINISHED" if not self._stop_requested else "STOPPED"
        )

        if self.settings.auto_save_results:
            self.export_service.run_all_auto_exports(min_score=self.settings.min_score_threshold)
            self._emit_log("Auto-export completed.")

        self.is_running = False
        self._emit_log(
            f"{session_type} finished. Checked: {self._checked_count}, "
            f"Available: {self._available_count}, Errors: {self._error_count}"
        )

    # ================= PIPELINE RUNNERS =================

    async def run_regular_hunter(
        self,
        count: int = 100,
        categories: list[UsernameCategory] | None = None
    ) -> None:
        """Run username search pipeline."""
        self._emit_log(f"Starting Regular Username Hunter. Target: {count} names.")
        candidates = self.un_generator.generate_batch(
            count=count,
            categories=categories,
            min_length=self.settings.min_length,
            max_length=self.settings.max_length
        )
        await self._execute_pipeline("REGULAR_USERNAMES", candidates)

    async def run_bot_hunter(
        self,
        count: int = 100,
        categories: list[UsernameCategory] | None = None
    ) -> None:
        """Run bot username search pipeline."""
        self._emit_log(f"Starting Bot Username Hunter. Target: {count} bot names.")
        candidates = self.bot_generator.generate_batch(
            count=count,
            categories=categories,
            min_length=self.settings.min_length,
            max_length=self.settings.max_length
        )
        await self._execute_pipeline("BOT_USERNAMES", candidates)

    async def run_premium_bot_hunter(
        self,
        count: int = 100,
        categories: list[UsernameCategory] | None = None,
        suffixes: list[str] | None = None
    ) -> None:
        """Run premium bot aliases search pipeline."""
        self._emit_log(f"Starting Premium Bot Names Hunter. Target: {count} aliases.")
        candidates = self.pba_generator.generate_batch(
            count=count,
            categories=categories,
            suffixes=suffixes,
            min_length=self.settings.min_length,
            max_length=self.settings.max_length
        )
        await self._execute_pipeline("PREMIUM_BOT_ALIASES", candidates)
