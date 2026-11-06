"""
Telegram Username Hunter PRO
In-Memory Cache for Recent Checks
"""
import time
from typing import Any


class CacheService:
    """Thread-safe in-memory cache to prevent redundant network calls within a session."""

    def __init__(self, ttl_seconds: float = 3600.0):
        self.ttl = ttl_seconds
        self._cache: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        now = time.time()
        entry = self._cache.get(key)
        if not entry:
            return None
        timestamp, value = entry
        if now - timestamp > self.ttl:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = (time.time(), value)

    def clear(self) -> None:
        self._cache.clear()
