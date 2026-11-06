"""
Telegram Username Hunter PRO
Telegram Username Checker
"""
import asyncio
import logging
from typing import Any

import httpx

from telegram_username_hunter.checkers.fragment_checker import FragmentChecker
from telegram_username_hunter.config.settings import UsernameStatus
from telegram_username_hunter.generators.username_generator import (
    is_valid_telegram_username,
)
from telegram_username_hunter.services.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class TelegramChecker:
    """Verifies regular Telegram usernames via t.me and Fragment endpoints."""

    TELEGRAM_BASE_URL = "https://t.me"

    def __init__(
        self,
        rate_limiter: RateLimiter | None = None,
        fragment_checker: FragmentChecker | None = None,
        mock_mode: bool = False,
        timeout: float = 10.0
    ):
        self.rate_limiter = rate_limiter or RateLimiter()
        self.fragment_checker = fragment_checker or FragmentChecker(
            rate_limiter=self.rate_limiter,
            mock_mode=mock_mode,
            timeout=timeout
        )
        self.mock_mode = mock_mode
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def check_username(self, username: str) -> tuple[UsernameStatus, dict[str, Any]]:
        """
        Check username availability.
        Returns (UsernameStatus, details_dict).
        """
        clean_name = username.lstrip("@").lower()

        # 1. Validation check
        if not is_valid_telegram_username(clean_name):
            return UsernameStatus.INVALID, {
                "source": "validator",
                "details": "Username fails Telegram format requirements (5-32 chars, a-z0-9_, no double __)"
            }

        # 2. Check Fragment first for collectibles
        fragment_res = await self.fragment_checker.check_fragment(clean_name)
        if fragment_res.get("is_collectible"):
            return UsernameStatus.COLLECTIBLE, {
                "source": "fragment",
                "details": f"Collectible username registered on Fragment ({fragment_res.get('status')})",
                "fragment_data": fragment_res
            }

        # 3. Mock mode check
        if self.mock_mode:
            await asyncio.sleep(0.05)
            if clean_name.startswith("taken") or clean_name in ("admin", "telegram", "durov"):
                return UsernameStatus.TAKEN, {
                    "source": "mock_tme",
                    "details": "Mock: Profile exists and is taken",
                    "fragment_data": fragment_res
                }
            elif clean_name.startswith("reserved"):
                return UsernameStatus.RESERVED, {
                    "source": "mock_tme",
                    "details": "Mock: Reserved by system",
                    "fragment_data": fragment_res
                }
            elif clean_name.startswith("error"):
                return UsernameStatus.ERROR, {
                    "source": "mock_tme",
                    "details": "Mock: Connection error",
                    "fragment_data": fragment_res
                }
            elif clean_name.startswith("unknown"):
                return UsernameStatus.UNKNOWN, {
                    "source": "mock_tme",
                    "details": "Mock: Inconclusive check",
                    "fragment_data": fragment_res
                }
            else:
                return UsernameStatus.AVAILABLE_TO_CLAIM, {
                    "source": "mock_tme",
                    "details": "Mock: Username is free to claim",
                    "fragment_data": fragment_res
                }

        url = f"{self.TELEGRAM_BASE_URL}/{clean_name}"
        await self.rate_limiter.acquire()

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers=self.headers)

                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("Retry-After", 30))
                    self.rate_limiter.record_error(is_rate_limit=True, retry_after=retry_after)
                    return UsernameStatus.UNKNOWN, {
                        "source": "tme",
                        "details": f"Telegram FloodWait 429. Retry after {retry_after}s",
                        "fragment_data": fragment_res
                    }

                if resp.status_code in (404, 302):
                    self.rate_limiter.record_success()
                    return UsernameStatus.AVAILABLE_TO_CLAIM, {
                        "source": "tme",
                        "details": f"Telegram returned HTTP {resp.status_code} (Resource not found). Free to claim.",
                        "fragment_data": fragment_res
                    }

                if resp.status_code == 200:
                    self.rate_limiter.record_success()
                    text = resp.text

                    # Signatures of free unclaimed namespaces on t.me
                    is_free = 'class="tgme_page_description"' in text and (
                        "if you have" in text.lower() and "you can contact" in text.lower()
                    )
                    if is_free:
                        return UsernameStatus.AVAILABLE_TO_CLAIM, {
                            "source": "tme",
                            "details": "Empty profile placeholder on t.me. Available to claim.",
                            "fragment_data": fragment_res
                        }

                    # Signatures of existing active profiles on t.me
                    has_title = 'class="tgme_page_title"' in text
                    has_extra = 'class="tgme_page_extra"' in text
                    has_photo = 'class="tgme_page_photo' in text
                    has_action_btn = 'class="tgme_action_button_new"' in text or 'class="tgme_page_action"' in text

                    if has_title or has_extra or has_photo or has_action_btn:
                        return UsernameStatus.TAKEN, {
                            "source": "tme",
                            "details": "Profile/Channel/Bot exists on Telegram",
                            "fragment_data": fragment_res
                        }

                    # If not taken on t.me and not on Fragment
                    if fragment_res.get("status") == "not_found" or not fragment_res.get("exists_on_fragment"):
                        return UsernameStatus.AVAILABLE_TO_CLAIM, {
                            "source": "tme_and_fragment",
                            "details": "No active profile found on t.me and not listed on Fragment. Available to claim.",
                            "fragment_data": fragment_res
                        }

                    return UsernameStatus.UNKNOWN, {
                        "source": "tme",
                        "details": "t.me page returned non-standard structure",
                        "fragment_data": fragment_res
                    }

                else:
                    self.rate_limiter.record_error()
                    return UsernameStatus.ERROR, {
                        "source": "tme",
                        "details": f"HTTP status error: {resp.status_code}",
                        "fragment_data": fragment_res
                    }

        except httpx.TimeoutException:
            self.rate_limiter.record_error()
            return UsernameStatus.ERROR, {
                "source": "tme",
                "details": "HTTP request timed out",
                "fragment_data": fragment_res
            }
        except Exception as e:
            self.rate_limiter.record_error()
            return UsernameStatus.ERROR, {
                "source": "tme",
                "details": f"Network exception: {e!s}",
                "fragment_data": fragment_res
            }
