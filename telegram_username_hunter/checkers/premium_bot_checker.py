"""
Telegram Username Hunter PRO
Premium Bot Aliases Checker
"""
import asyncio
import logging
from typing import Any

import httpx

from telegram_username_hunter.checkers.fragment_checker import FragmentChecker
from telegram_username_hunter.config.settings import PremiumBotStatus
from telegram_username_hunter.generators.premium_bot_generator import (
    is_valid_premium_bot_alias,
)
from telegram_username_hunter.services.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class PremiumBotChecker:
    """
    Verifies availability and assignment eligibility for Premium Bot Aliases
    (_app, _ai, _game, _agent, _gay).
    """

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

    async def check_alias(self, alias_username: str) -> tuple[PremiumBotStatus, dict[str, Any]]:
        """
        Check premium bot alias.
        Returns (PremiumBotStatus, details_dict).
        """
        clean_name = alias_username.lstrip("@").lower()

        # 1. Validation check
        if not is_valid_premium_bot_alias(clean_name):
            return PremiumBotStatus.INVALID, {
                "source": "validator",
                "details": "Invalid premium alias format or unsupported suffix."
            }

        # 2. Fragment check
        fragment_res = await self.fragment_checker.check_fragment(clean_name)
        if fragment_res.get("exists_on_fragment") and fragment_res.get("status") in ("sold", "in_auction", "taken", "unavailable"):
            return PremiumBotStatus.ALREADY_ASSIGNED, {
                "source": "fragment",
                "details": f"Alias is registered or occupied on Fragment ({fragment_res.get('status')})",
                "fragment_data": fragment_res
            }

        # 3. Mock mode check
        if self.mock_mode:
            await asyncio.sleep(0.05)
            if clean_name.startswith("taken") or "assigned" in clean_name:
                return PremiumBotStatus.ALREADY_ASSIGNED, {
                    "source": "mock_alias",
                    "details": "Mock: Alias already assigned to a bot",
                    "fragment_data": fragment_res
                }
            elif clean_name.startswith("error"):
                return PremiumBotStatus.ERROR, {
                    "source": "mock_alias",
                    "details": "Mock: Connection error",
                    "fragment_data": fragment_res
                }
            elif clean_name.startswith("unknown"):
                return PremiumBotStatus.UNKNOWN, {
                    "source": "mock_alias",
                    "details": "Mock: Inconclusive check. Final confirmation requires Telegram assignment.",
                    "fragment_data": fragment_res
                }
            else:
                return PremiumBotStatus.ELIGIBLE_FOR_ASSIGNMENT, {
                    "source": "mock_alias",
                    "details": "Mock: Unassigned namespace. Final confirmation requires assignment via Telegram.",
                    "fragment_data": fragment_res
                }

        # 4. Live t.me endpoint check
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
                        return PremiumBotStatus.UNKNOWN, {
                            "source": "tme",
                            "details": "Telegram FloodWait 429. Final check pending.",
                            "fragment_data": fragment_res
                        }

                    if resp.status_code in (404, 302):
                        self.rate_limiter.record_success()
                        return PremiumBotStatus.ELIGIBLE_FOR_ASSIGNMENT, {
                            "source": "tme",
                            "details": "Namespace unoccupied. Final assignment subject to Telegram bot settings.",
                            "fragment_data": fragment_res
                        }

                    if resp.status_code == 200:
                        self.rate_limiter.record_success()
                        text = resp.text
                        text_lower = text.lower()

                        has_title = 'class="tgme_page_title"' in text
                        has_extra = 'class="tgme_page_extra"' in text
                        has_photo = 'class="tgme_page_photo' in text or 'tgme_page_photo_image' in text
                        has_desc = 'class="tgme_page_description"' in text

                        is_free_phrase = any(
                            p in text_lower for p in [
                                "if you have", "you can contact", "right away",
                                "если у вас есть", "вы можете связаться", "прямо сейчас",
                                "si tienes telegram", "puedes contactar",
                                "wenn sie telegram haben", "können sie"
                            ]
                        )

                        is_free = (
                            (has_desc and is_free_phrase and not has_title and not has_photo)
                            or (has_desc and ('class="tgme_username_link"' in text or 'tgme_icon_user' in text) and not has_title and not has_photo)
                            or (not has_title and not has_extra and not has_photo and (fragment_res.get("status") == "not_found" or not fragment_res.get("exists_on_fragment")))
                        )
                        if is_free:
                            return PremiumBotStatus.ELIGIBLE_FOR_ASSIGNMENT, {
                                "source": "tme_and_fragment",
                                "details": "Public endpoints show unassigned. Final confirmation is executed when linking alias to bot in Telegram.",
                                "fragment_data": fragment_res
                            }

                        has_action_btn = 'class="tgme_action_button_new"' in text or 'class="tgme_page_action"' in text

                        if has_title or has_extra or has_photo or (has_action_btn and not has_desc):
                            return PremiumBotStatus.ALREADY_ASSIGNED, {
                                "source": "tme",
                                "details": "Alias is already occupied and attached to an existing bot or channel.",
                                "fragment_data": fragment_res
                            }

                        return PremiumBotStatus.ELIGIBLE_FOR_ASSIGNMENT, {
                            "source": "tme_and_fragment",
                            "details": "Public endpoints show unassigned. Final confirmation is executed when linking alias to bot in Telegram.",
                            "fragment_data": fragment_res
                        }

                    else:
                        if attempt < max_attempts and resp.status_code in (500, 502, 503, 504):
                            await asyncio.sleep(0.3)
                            continue
                        self.rate_limiter.record_error()
                        return PremiumBotStatus.ERROR, {
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
                return PremiumBotStatus.ERROR, {
                    "source": "tme",
                    "details": "HTTP request timed out" if is_timeout else f"Network exception: {last_error_details}",
                    "fragment_data": fragment_res
                }
            except Exception as e:
                self.rate_limiter.record_error()
                return PremiumBotStatus.ERROR, {
                    "source": "tme",
                    "details": f"Network exception: {e!s}",
                    "fragment_data": fragment_res
                }

        return PremiumBotStatus.ERROR, {
            "source": "tme",
            "details": last_error_details or "Request failed without response",
            "fragment_data": fragment_res
        }
