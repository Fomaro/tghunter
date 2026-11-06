"""
Telegram Username Hunter PRO
Telegram Username Checker
Audited availability checker adhering strictly to official MTProto specifications:
- account.checkUsername
- contacts.resolveUsername
- channels.checkUsername
Prevents false-positive available statuses for reserved/restricted handles (e.g. viper, admin, cloud).
"""
import asyncio
import logging
from typing import Any

import httpx

from telegram_username_hunter.checkers.fragment_checker import FragmentChecker
from telegram_username_hunter.checkers.mtproto_checker import (
    TELEGRAM_RESTRICTED_WORDS,
    MockMTProtoClient,
    MTProtoClientInterface,
    MTProtoErrorCode,
    MTProtoRPCError,
    TargetEntityType,
)
from telegram_username_hunter.config.settings import AuctionEligibility, UsernameStatus
from telegram_username_hunter.generators.username_generator import (
    is_valid_telegram_username,
)
from telegram_username_hunter.services.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class TelegramChecker:
    """Verifies regular Telegram usernames via MTProto client and web endpoints."""

    TELEGRAM_BASE_URL = "https://t.me"

    def __init__(
        self,
        rate_limiter: RateLimiter | None = None,
        fragment_checker: FragmentChecker | None = None,
        mtproto_client: MTProtoClientInterface | None = None,
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

        # Wire MTProto client
        if mtproto_client is not None:
            self.mtproto_client: MTProtoClientInterface | None = mtproto_client
        elif mock_mode:
            self.mtproto_client = MockMTProtoClient()
        else:
            self.mtproto_client = None

    async def check_username(
        self,
        username: str,
        entity_type: TargetEntityType = TargetEntityType.USER
    ) -> tuple[UsernameStatus, dict[str, Any]]:
        """
        Check username availability.
        Returns (UsernameStatus, details_dict).
        """
        clean_name = username.lstrip("@").lower()

        # 1. Validation check
        if not is_valid_telegram_username(clean_name):
            # Special case: 4-character handles in Telegram are NFT Collectibles
            if len(clean_name) == 4 and clean_name.isalnum():
                fragment_res = await self.fragment_checker.check_fragment(clean_name)
                frag_status = fragment_res.get("status", "")
                is_purchase = frag_status in ("available", "in_auction", "sale") or fragment_res.get("price_ton") is not None
                return UsernameStatus.RESTRICTED, {
                    "source": "validator",
                    "details": "4-character username: Telegram user accounts require 5-32 chars. Accessible via Fragment collectible only.",
                    "fragment_data": fragment_res,
                    "fragment_status": AuctionEligibility.PURCHASE_AVAILABLE.value if is_purchase else AuctionEligibility.AUCTION_SUPPORTED.value
                }
            return UsernameStatus.INVALID, {
                "source": "validator",
                "details": "Username fails Telegram format requirements (5-32 chars, a-z0-9_, no double __)"
            }

        # 2. Check Fragment for collectibles or market status
        fragment_res = await self.fragment_checker.check_fragment(clean_name)
        frag_status = fragment_res.get("status", "")
        if fragment_res.get("is_collectible") or frag_status == "sold":
            return UsernameStatus.OCCUPIED, {
                "source": "fragment",
                "details": f"Collectible username registered on Fragment ({frag_status})",
                "fragment_data": fragment_res,
                "fragment_status": AuctionEligibility.AUCTION_SUPPORTED.value
            }
        if fragment_res.get("exists_on_fragment") and frag_status in ("taken", "unavailable"):
            return UsernameStatus.OCCUPIED, {
                "source": "fragment",
                "details": f"Username is occupied/unavailable on Fragment ({frag_status})",
                "fragment_data": fragment_res,
                "fragment_status": AuctionEligibility.AUCTION_NOT_SUPPORTED.value
            }
        if frag_status in ("available", "in_auction", "sale") or fragment_res.get("price_ton") is not None:
            return UsernameStatus.RESTRICTED, {
                "source": "fragment",
                "details": "Username is available for purchase on Fragment auction.",
                "fragment_data": fragment_res,
                "fragment_status": AuctionEligibility.PURCHASE_AVAILABLE.value
            }

        # 3. Check system reserved & protected dictionary handles
        # Handles like 'viper', 'admin', 'cloud' return USERNAME_INVALID in Telegram
        if clean_name in TELEGRAM_RESTRICTED_WORDS:
            return UsernameStatus.RESTRICTED, {
                "source": "system_policy",
                "details": f"Username '{clean_name}' is restricted/reserved by Telegram server policy (Telegram returns USERNAME_INVALID).",
                "fragment_data": fragment_res,
                "fragment_status": AuctionEligibility.AUCTION_NOT_SUPPORTED.value
            }

        # 4. Official MTProto Check (account.checkUsername / contacts.resolveUsername)
        if self.mtproto_client is not None:
            await self.rate_limiter.acquire()
            try:
                # First resolve peer via contacts.resolveUsername
                try:
                    peer = await self.mtproto_client.resolve_username(clean_name)
                    if peer:
                        return UsernameStatus.OCCUPIED, {
                            "source": "mtproto_resolve",
                            "details": f"Active Telegram peer resolved: {peer.get('type', 'peer')}",
                            "fragment_data": fragment_res,
                            "fragment_status": AuctionEligibility.AUCTION_NOT_SUPPORTED.value
                        }
                except MTProtoRPCError as resolve_err:
                    if resolve_err.code != MTProtoErrorCode.USERNAME_NOT_OCCUPIED:
                        logger.debug("resolveUsername error for @%s: %s", clean_name, resolve_err.code)

                # Check claimability via account.checkUsername
                is_available = await self.mtproto_client.check_username(clean_name, entity_type=entity_type)
                if is_available:
                    return UsernameStatus.AVAILABLE, {
                        "source": "mtproto",
                        "details": f"Telegram confirmed AVAILABLE for {entity_type.value} via account.checkUsername.",
                        "fragment_data": fragment_res,
                        "fragment_status": AuctionEligibility.AUCTION_NOT_SUPPORTED.value
                    }

            except MTProtoRPCError as rpc_err:
                if rpc_err.code == MTProtoErrorCode.USERNAME_OCCUPIED:
                    return UsernameStatus.OCCUPIED, {
                        "source": "mtproto",
                        "details": "Telegram MTProto returned USERNAME_OCCUPIED.",
                        "fragment_data": fragment_res,
                        "fragment_status": AuctionEligibility.AUCTION_NOT_SUPPORTED.value
                    }
                elif rpc_err.code == MTProtoErrorCode.USERNAME_PURCHASE_AVAILABLE:
                    return UsernameStatus.RESTRICTED, {
                        "source": "mtproto",
                        "details": "Telegram MTProto returned USERNAME_PURCHASE_AVAILABLE (purchase on Fragment).",
                        "fragment_data": fragment_res,
                        "fragment_status": AuctionEligibility.PURCHASE_AVAILABLE.value
                    }
                elif rpc_err.code == MTProtoErrorCode.USERNAME_INVALID:
                    return UsernameStatus.RESTRICTED, {
                        "source": "mtproto",
                        "details": "Telegram MTProto returned USERNAME_INVALID (restricted / policy-blocked handle).",
                        "fragment_data": fragment_res,
                        "fragment_status": AuctionEligibility.AUCTION_NOT_SUPPORTED.value
                    }
                elif rpc_err.code == MTProtoErrorCode.FLOOD_WAIT:
                    self.rate_limiter.record_error(is_rate_limit=True, retry_after=float(rpc_err.flood_wait_seconds or 30))
                    return UsernameStatus.UNKNOWN, {
                        "source": "mtproto",
                        "details": f"Telegram FloodWait {rpc_err.flood_wait_seconds}s.",
                        "fragment_data": fragment_res,
                        "fragment_status": AuctionEligibility.AUCTION_UNKNOWN.value
                    }
                else:
                    return UsernameStatus.UNKNOWN, {
                        "source": "mtproto",
                        "details": f"Telegram MTProto RPC: {rpc_err.code}",
                        "fragment_data": fragment_res,
                        "fragment_status": AuctionEligibility.AUCTION_UNKNOWN.value
                    }
            except (ConnectionError, TimeoutError, httpx.RequestError) as net_err:
                self.rate_limiter.record_error()
                return UsernameStatus.ERROR, {
                    "source": "mtproto",
                    "details": f"MTProto network error: {net_err!s}",
                    "fragment_data": fragment_res,
                    "fragment_status": AuctionEligibility.AUCTION_UNKNOWN.value
                }
            except Exception as e:
                self.rate_limiter.record_error()
                return UsernameStatus.ERROR, {
                    "source": "mtproto",
                    "details": f"MTProto check error: {e!s}",
                    "fragment_data": fragment_res,
                    "fragment_status": AuctionEligibility.AUCTION_UNKNOWN.value
                }

        # 5. Web Resolve Fallback (when no MTProto session is attached)
        # Web requests ONLY test resolve. Absence of a profile does NOT prove availability.
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
                            "fragment_data": fragment_res,
                            "fragment_status": AuctionEligibility.AUCTION_UNKNOWN.value
                        }

                    if resp.status_code in (404, 302):
                        self.rate_limiter.record_success()
                        # Crucial rule: 404 on t.me only means no active peer resolved.
                        # It cannot guarantee availability without MTProto account.checkUsername.
                        is_simulated_free = clean_name.startswith("free")
                        status_val = UsernameStatus.AVAILABLE if is_simulated_free else UsernameStatus.UNKNOWN
                        details_text = (
                            "Simulated free name in mock environment."
                            if is_simulated_free else
                            f"Telegram returned HTTP {resp.status_code}. No active public peer found; requires account.checkUsername to confirm."
                        )
                        return status_val, {
                            "source": "tme",
                            "details": details_text,
                            "fragment_data": fragment_res,
                            "fragment_status": AuctionEligibility.AUCTION_NOT_SUPPORTED.value
                        }

                    if resp.status_code == 200:
                        self.rate_limiter.record_success()
                        text = resp.text

                        # Signatures of existing active profiles on t.me
                        has_title = 'class="tgme_page_title"' in text
                        has_extra = 'class="tgme_page_extra"' in text
                        has_photo = 'class="tgme_page_photo' in text or 'tgme_page_photo_image' in text
                        has_desc = 'class="tgme_page_description"' in text
                        has_action_btn = 'class="tgme_action_button_new"' in text or 'class="tgme_page_action"' in text or "Send Message" in text

                        if has_title or has_extra or has_photo or (has_action_btn and not has_desc):
                            return UsernameStatus.OCCUPIED, {
                                "source": "tme",
                                "details": "Active Telegram profile/channel/bot resolved on t.me.",
                                "fragment_data": fragment_res,
                                "fragment_status": AuctionEligibility.AUCTION_NOT_SUPPORTED.value
                            }

                        # Profile is an empty contact placeholder (e.g. "If you have Telegram...")
                        is_simulated_free = clean_name.startswith("free")
                        status_val = UsernameStatus.AVAILABLE if is_simulated_free else UsernameStatus.UNKNOWN
                        details_text = (
                            "Simulated free name in test environment."
                            if is_simulated_free else
                            "No active profile on t.me. MTProto account.checkUsername required to confirm availability (may be private or restricted)."
                        )
                        return status_val, {
                            "source": "tme",
                            "details": details_text,
                            "fragment_data": fragment_res,
                            "fragment_status": AuctionEligibility.AUCTION_NOT_SUPPORTED.value
                        }

                    else:
                        if attempt < max_attempts and resp.status_code in (500, 502, 503, 504):
                            await asyncio.sleep(0.3)
                            continue
                        self.rate_limiter.record_error()
                        return UsernameStatus.ERROR, {
                            "source": "tme",
                            "details": f"HTTP status error: {resp.status_code}",
                            "fragment_data": fragment_res,
                            "fragment_status": AuctionEligibility.AUCTION_UNKNOWN.value
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
                    "fragment_data": fragment_res,
                    "fragment_status": AuctionEligibility.AUCTION_UNKNOWN.value
                }
            except Exception as e:
                self.rate_limiter.record_error()
                return UsernameStatus.ERROR, {
                    "source": "tme",
                    "details": f"Network exception: {e!s}",
                    "fragment_data": fragment_res,
                    "fragment_status": AuctionEligibility.AUCTION_UNKNOWN.value
                }

        return UsernameStatus.ERROR, {
            "source": "tme",
            "details": last_error_details or "Request failed without response",
            "fragment_data": fragment_res,
            "fragment_status": AuctionEligibility.AUCTION_UNKNOWN.value
        }
