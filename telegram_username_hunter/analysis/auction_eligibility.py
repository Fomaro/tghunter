"""
Telegram Username Hunter PRO
Fragment Auction Eligibility Analyzer
"""
from typing import Any

from telegram_username_hunter.config.settings import (
    AuctionEligibility,
    BotStatus,
    UsernameStatus,
)


class AuctionEligibilityAnalyzer:
    """Evaluates Fragment auction eligibility and requirements for usernames."""

    FRAGMENT_BASE_URL = "https://fragment.com/username"

    @classmethod
    def get_fragment_url(cls, username: str) -> str:
        clean = username.lstrip("@").lower()
        return f"{cls.FRAGMENT_BASE_URL}/{clean}"

    @classmethod
    def analyze_regular_username(
        cls,
        username: str,
        status: str,
        fragment_details: dict[str, Any]
    ) -> tuple[str, str, str]:
        """
        Analyze regular username.
        Returns (item_type, auction_eligibility, explanation).
        """
        frag_status = fragment_details.get("status", "")
        is_collectible = fragment_details.get("is_collectible", False)

        # 1. Available for purchase / bidding on Fragment
        if frag_status in ("available", "in_auction", "sale") or fragment_details.get("price_ton") is not None or fragment_details.get("purchase_available"):
            return (
                "FRAGMENT_COLLECTIBLE",
                AuctionEligibility.PURCHASE_AVAILABLE.value,
                "Listed on Fragment: available for purchase, auction bidding, or direct acquisition."
            )

        # 2. Collectible NFT on Fragment (supports auction / secondary market)
        if is_collectible or frag_status == "sold":
            return (
                "COLLECTIBLE_USERNAME",
                AuctionEligibility.AUCTION_SUPPORTED.value,
                "Confirmed Collectible on Fragment. Supports trading and auctions on secondary marketplace."
            )

        # 3. Not supported on Fragment auction
        if frag_status in ("not_found", "unavailable") or status in (
            UsernameStatus.AVAILABLE.value,
            UsernameStatus.OCCUPIED.value,
            UsernameStatus.RESTRICTED.value,
            UsernameStatus.INVALID.value,
        ):
            return (
                "BASIC_USERNAME",
                AuctionEligibility.AUCTION_NOT_SUPPORTED.value,
                "Standard Telegram handle. Fragment auction not supported unless converted by owner."
            )

        return (
            "BASIC_USERNAME",
            AuctionEligibility.AUCTION_UNKNOWN.value,
            "Verification pending or Fragment status could not be determined."
        )

    @classmethod
    def analyze_bot_username(
        cls,
        username: str,
        status: str,
        fragment_details: dict[str, Any]
    ) -> tuple[str, str, str]:
        """
        Analyze bot username for auction capability.
        """
        frag_status = fragment_details.get("status", "")
        if frag_status in ("available", "in_auction", "sale") or fragment_details.get("price_ton") is not None:
            return (
                "FRAGMENT_COLLECTIBLE",
                AuctionEligibility.PURCHASE_AVAILABLE.value,
                "Bot username is listed on Fragment for purchase or auction."
            )

        if fragment_details.get("is_collectible") or frag_status == "sold":
            return (
                "COLLECTIBLE_USERNAME",
                AuctionEligibility.AUCTION_SUPPORTED.value,
                "Bot username is registered as Fragment TON collectible NFT."
            )

        if status == BotStatus.AVAILABLE.value:
            return (
                "BOT_USERNAME",
                AuctionEligibility.AUCTION_NOT_SUPPORTED.value,
                "Available for BotFather registration. Fragment auction not supported."
            )

        return (
            "BOT_USERNAME",
            AuctionEligibility.AUCTION_NOT_SUPPORTED.value,
            "Bot usernames are not auction-eligible by default."
        )

    @classmethod
    def analyze_premium_alias(
        cls,
        username: str,
        status: str,
        fragment_details: dict[str, Any]
    ) -> tuple[str, str, str]:
        """
        Analyze premium bot alias.
        Important rule: Never confuse right to assign alias with right to auction on Fragment.
        """
        return (
            "PREMIUM_BOT_ALIAS",
            AuctionEligibility.AUCTION_NOT_SUPPORTED.value,
            "Telegram Premium Bot Alias. Only assignable to existing bots in Telegram. Fragment auction not officially supported."
        )
