"""
Telegram Username Hunter PRO
Rate Limiter & Adaptive FloodWait Controller
"""
import asyncio
import logging
import random
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """Controls request pacing, backoff, and FloodWait safety delays."""

    def __init__(
        self,
        base_delay: float = 1.2,
        jitter: float = 0.3,
        backoff_factor: float = 2.0,
        flood_wait_padding: float = 10.0
    ):
        self.base_delay = base_delay
        self.jitter = jitter
        self.backoff_factor = backoff_factor
        self.flood_wait_padding = flood_wait_padding

        self._consecutive_errors = 0
        self._consecutive_successes = 0
        self._last_request_time = 0.0
        self._flood_wait_until = 0.0
        self._lock = asyncio.Lock()
        self.is_stopped_check: Optional[Callable[[], bool]] = None
        self.is_paused_check: Optional[Callable[[], bool]] = None
        self.pause_event: Optional[asyncio.Event] = None
        self.on_throttle_change: Optional[Callable[[bool, float, str], None]] = None

    @property
    def is_throttled(self) -> bool:
        return time.time() < self._flood_wait_until

    @property
    def cooldown_remaining(self) -> float:
        remaining = self._flood_wait_until - time.time()
        return max(0.0, remaining)

    def update_profile(self, base_delay: float, jitter: float) -> None:
        """Dynamically update rate limiter parameters on mode switch."""
        self.base_delay = base_delay
        self.jitter = jitter
        logger.info(f"RateLimiter updated: base_delay={base_delay}s, jitter={jitter}s")

    async def _interruptible_sleep(self, duration: float) -> None:
        """Sleep in small slices so stopping or cancellation is responsive."""
        end_time = time.time() + duration
        while True:
            if self.is_stopped_check and self.is_stopped_check():
                break
            if self.is_paused_check and self.is_paused_check():
                if self.pause_event:
                    await self.pause_event.wait()
                if self.is_stopped_check and self.is_stopped_check():
                    break
            remaining = end_time - time.time()
            if remaining <= 0:
                break
            step = min(remaining, 0.25)
            await asyncio.sleep(step)

    async def acquire(self) -> None:
        """Wait until it is safe to issue the next request."""
        async with self._lock:
            now = time.time()

            # 1. FloodWait penalty
            if now < self._flood_wait_until:
                wait_time = self._flood_wait_until - now
                logger.warning(f"Active FloodWait in effect. Pausing for {wait_time:.1f}s...")
                if self.on_throttle_change:
                    self.on_throttle_change(True, wait_time, "FloodWait Cooldown")

                await self._interruptible_sleep(wait_time)
                now = time.time()

                if now >= self._flood_wait_until and self.on_throttle_change:
                    self.on_throttle_change(False, 0.0, "Normal Operation")

            # 2. Base delay + exponential backoff if errors occurred
            backoff = (self.backoff_factor ** min(self._consecutive_errors, 5)) - 1.0 if self._consecutive_errors > 0 else 0.0
            jitter_amount = random.uniform(0, self.jitter)
            target_delay = self.base_delay + backoff + jitter_amount

            elapsed = now - self._last_request_time
            if elapsed < target_delay:
                wait_needed = target_delay - elapsed
                await self._interruptible_sleep(wait_needed)

            self._last_request_time = time.time()

    def record_success(self) -> None:
        """Reset consecutive error count on successful request and track recovery."""
        self._consecutive_errors = 0
        self._consecutive_successes += 1
        if self._consecutive_successes >= 5 and not self.is_throttled and self.on_throttle_change:
            self.on_throttle_change(False, 0.0, "Normal Operation")

    def record_error(self, is_rate_limit: bool = False, retry_after: Optional[float] = None) -> None:
        """Adjust backoff on error or handle 429 FloodWait."""
        self._consecutive_errors += 1
        self._consecutive_successes = 0
        if is_rate_limit:
            wait_seconds = (retry_after or 30.0) + self.flood_wait_padding
            self._flood_wait_until = time.time() + wait_seconds
            logger.warning(f"Rate limit triggered. Enforcing cooldown until {self._flood_wait_until} (+{wait_seconds}s)")
            if self.on_throttle_change:
                self.on_throttle_change(True, wait_seconds, f"FloodWait 429 (+{wait_seconds:.1f}s)")
        else:
            logger.info(f"Temporary error logged. Consecutive errors: {self._consecutive_errors}")
