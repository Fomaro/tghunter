"""
Telegram Username Hunter PRO
Fragment Marketplace Checker
"""
import asyncio
import logging
import re
from typing import Any

import httpx

from telegram_username_hunter.services.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class FragmentChecker:
    """Checks username status on the official Fragment platform."""

    BASE_URL = "https://fragment.com/username"

    def __init__(
        self,
        rate_limiter: RateLimiter | None = None,
        mock_mode: bool = False,
        timeout: float = 10.0
    ):
        self.rate_limiter = rate_limiter or RateLimiter()
        self.mock_mode = mock_mode
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def check_fragment(self, username: str) -> dict[str, Any]:
        """
        Query Fragment for username status.
        Returns dictionary with:
        - exists_on_fragment: bool
        - is_collectible: bool
        - status: str ('sold', 'in_auction', 'available', 'taken', 'not_found', 'error')
        - price_ton: Optional[float]
        - fragment_url: str
        """
        clean_name = username.lstrip("@").lower()
        url = f"{self.BASE_URL}/{clean_name}"

        if self.mock_mode:
            # Deterministic simulation for tests/offline
            await asyncio.sleep(0.05)
            if clean_name in ("news", "crypto", "ton", "bank", "gold"):
                return {
                    "exists_on_fragment": True,
                    "is_collectible": True,
                    "status": "sold",
                    "price_ton": 250000.0,
                    "fragment_url": url,
                    "raw_details": "Mock: Sold Collectible"
                }
            elif clean_name.startswith("taken"):
                return {
                    "exists_on_fragment": True,
                    "is_collectible": False,
                    "status": "taken",
                    "price_ton": None,
                    "fragment_url": url,
                    "raw_details": "Mock: Taken username"
                }
            elif clean_name.startswith("error"):
                return {
                    "exists_on_fragment": False,
                    "is_collectible": False,
                    "status": "error",
                    "price_ton": None,
                    "fragment_url": url,
                    "raw_details": "Mock: Simulated error"
                }
            else:
                return {
                    "exists_on_fragment": False,
                    "is_collectible": False,
                    "status": "not_found",
                    "price_ton": None,
                    "fragment_url": url,
                    "raw_details": "Mock: Not found on Fragment"
                }

        await self.rate_limiter.acquire()
        try:
            # Use follow_redirects=False: unlisted Fragment names return HTTP 302 redirecting to /?query=...
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
                resp = await client.get(url, headers=self.headers)

                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("Retry-After", 30))
                    self.rate_limiter.record_error(is_rate_limit=True, retry_after=retry_after)
                    return {
                        "exists_on_fragment": False,
                        "is_collectible": False,
                        "status": "rate_limited",
                        "price_ton": None,
                        "fragment_url": url,
                        "raw_details": f"HTTP 429 FloodWait: retry after {retry_after}s"
                    }

                if resp.status_code in (301, 302, 404):
                    self.rate_limiter.record_success()
                    return {
                        "exists_on_fragment": False,
                        "is_collectible": False,
                        "status": "not_found",
                        "price_ton": None,
                        "fragment_url": url,
                        "raw_details": f"Fragment HTTP {resp.status_code} (Not listed on Fragment)"
                    }

                if resp.status_code == 200:
                    self.rate_limiter.record_success()
                    text = resp.text
                    text_lower = text.lower()

                    # Extract meta tags if present
                    og_title_m = re.findall(r'<meta property="og:title" content="(.*?)"', text)
                    og_desc_m = re.findall(r'<meta property="og:description" content="(.*?)"', text)
                    title_str = og_title_m[0].lower() if og_title_m else ""
                    desc_str = og_desc_m[0].lower() if og_desc_m else ""

                    is_sold = ("sold for" in text_lower) or ("sold" in title_str) or ("sold" in desc_str) or ("status-sold" in text_lower)
                    is_auction = ("in auction" in text_lower) or ("auction" in title_str) or ("auction" in desc_str) or ("buy @" in title_str)
                    is_taken = ("is taken" in desc_str) or ("make an offer" in title_str) or ("unavailable" in text_lower)
                    is_available = ("available" in text_lower and not is_taken) or ("put up for auction" in text_lower)

                    if is_sold:
                        status = "sold"
                        is_collectible = True
                        exists = True
                    elif is_auction:
                        status = "in_auction"
                        is_collectible = True
                        exists = True
                    elif is_available:
                        status = "available"
                        is_collectible = True
                        exists = True
                    elif is_taken:
                        status = "taken"
                        is_collectible = False
                        exists = True
                    else:
                        status = "not_found"
                        is_collectible = False
                        exists = False

                    return {
                        "exists_on_fragment": exists,
                        "is_collectible": is_collectible,
                        "status": status,
                        "price_ton": None,
                        "fragment_url": url,
                        "raw_details": f"Fragment HTTP 200 (Detected status: {status})"
                    }

                self.rate_limiter.record_error()
                return {
                    "exists_on_fragment": False,
                    "is_collectible": False,
                    "status": "error",
                    "price_ton": None,
                    "fragment_url": url,
                    "raw_details": f"Unexpected HTTP status: {resp.status_code}"
                }

        except httpx.TimeoutException:
            # Fragment timeout should not fail the search pipeline
            return {
                "exists_on_fragment": False,
                "is_collectible": False,
                "status": "timeout",
                "price_ton": None,
                "fragment_url": url,
                "raw_details": "Fragment request timed out"
            }
        except Exception as e:
            return {
                "exists_on_fragment": False,
                "is_collectible": False,
                "status": "unavailable",
                "price_ton": None,
                "fragment_url": url,
                "raw_details": f"Fragment check unavailable: {e!s}"
            }
