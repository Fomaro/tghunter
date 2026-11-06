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


TELEGRAM_SYSTEM_RESERVED = {
    "admin", "administrator", "root", "support", "help", "service", "security",
    "telegram", "durov", "channel", "group", "contact", "settings", "privacy",
    "terms", "wallet", "status", "update", "updates", "news", "official", "system",
    "verify", "verification", "moderator", "staff", "founder", "ceo", "fragment",
    "ton", "blockchain", "premium", "stickers", "themes", "proxy", "desktop",
    "web", "android", "ios", "login", "auth", "oauth", "token", "connect",
    "account", "profile", "notification", "notifications", "alerts", "securitybot",
    "spam", "spambot", "botfather", "cloud"
}


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

        # 2. Check Fragment first for collectibles or taken status
        fragment_res = await self.fragment_checker.check_fragment(clean_name)
        if fragment_res.get("is_collectible"):
            return UsernameStatus.COLLECTIBLE, {
                "source": "fragment",
                "details": f"Collectible username registered on Fragment ({fragment_res.get('status')})",
                "fragment_data": fragment_res
            }
        if fragment_res.get("exists_on_fragment") and fragment_res.get("status") in ("taken", "unavailable"):
            return UsernameStatus.TAKEN, {
                "source": "fragment",
                "details": f"Username is occupied/unavailable on Fragment ({fragment_res.get('status')})",
                "fragment_data": fragment_res
            }

        # 3. Check system reserved handles
        if clean_name in TELEGRAM_SYSTEM_RESERVED:
            return UsernameStatus.RESERVED, {
                "source": "system_policy",
                "details": f"Username '{clean_name}' is reserved by Telegram or official systems.",
                "fragment_data": fragment_res
            }

        # 4. Mock mode check
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
        max_attempts = 2
        last_error_details = ""

        for attempt in range(1, max_attempts + 1):
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
                        text_lower = text.lower()

                        # Signatures of existing active profiles on t.me
                        has_title = 'class="tgme_page_title"' in text
                        has_extra = 'class="tgme_page_extra"' in text
                        has_photo = 'class="tgme_page_photo' in text or 'tgme_page_photo_image' in text
                        has_desc = 'class="tgme_page_description"' in text

                        has_action_btn = 'class="tgme_action_button_new"' in text or 'class="tgme_page_action"' in text or "Send Message" in text

                        if has_title or has_extra or has_photo or (has_action_btn and not has_desc):
                            return UsernameStatus.TAKEN, {
                                "source": "tme",
                                "details": "Profile/Channel/Bot exists on Telegram",
                                "fragment_data": fragment_res
                            }

                        # Multilingual phrases for free username invitation
                        is_free_phrase = any(
                            p in text_lower for p in [
                                "if you have", "you can contact", "right away",
                                "если у вас есть", "вы можете связаться", "прямо сейчас",
                                "si tienes telegram", "puedes contactar",
                                "wenn sie telegram haben", "können sie"
                            ]
                        )

                        # A username is available to claim when:
                        # 1) It has page description or username link, and NO profile title, extra, or photo
                        # 2) Or has empty profile placeholder without profile elements
                        is_free = (
                            (has_desc and is_free_phrase and not has_title and not has_photo)
                            or (has_desc and ('class="tgme_username_link"' in text or 'tgme_icon_user' in text) and not has_title and not has_photo)
                            or (not has_title and not has_extra and not has_photo and not has_action_btn and (fragment_res.get("status") == "not_found" or not fragment_res.get("exists_on_fragment")))
                        )
                        if is_free:
                            return UsernameStatus.AVAILABLE_TO_CLAIM, {
                                "source": "tme",
                                "details": "Empty profile placeholder on t.me. Available to claim.",
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
                        if attempt < max_attempts and resp.status_code in (500, 502, 503, 504):
                            await asyncio.sleep(0.3)
                            continue
                        self.rate_limiter.record_error()
                        return UsernameStatus.ERROR, {
                            "source": "tme",
                            "details": f"HTTP status error: {resp.status_code}",
                            "fragment_data": fragment_res
                        }

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_error_details = str(e)
                if attempt < max_attempts:
                    await asyncio.sleep(0.3)
                    continue
                self.rate_limiter.record_error()
                is_timeout = isinstance(e, httpx.TimeoutException) or "timed out" in last_error_details.lower()
                return UsernameStatus.ERROR, {
                    "source": "tme",
                    "details": "HTTP request timed out" if is_timeout else f"Network exception: {last_error_details}",
                    "fragment_data": fragment_res
                }
            except Exception as e:
                self.rate_limiter.record_error()
                return UsernameStatus.ERROR, {
                    "source": "tme",
                    "details": f"Network exception: {e!s}",
                    "fragment_data": fragment_res
                }

        return UsernameStatus.ERROR, {
            "source": "tme",
            "details": last_error_details or "Request failed without response",
            "fragment_data": fragment_res
        }
