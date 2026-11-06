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
        # If Fragment confirmed it is already a collectible
        if status == UsernameStatus.COLLECTIBLE.value or fragment_details.get("is_collectible"):
            return (
                "COLLECTIBLE_USERNAME",
                AuctionEligibility.AUCTION_ELIGIBLE.value,
                "Confirmed Collectible on Fragment. Can be traded on the Fragment secondary market."
            )

        # If it is available to claim
        if status == UsernameStatus.AVAILABLE_TO_CLAIM.value:
            return (
                "BASIC_USERNAME",
                AuctionEligibility.AUCTION_NOT_SUPPORTED.value,
                "Standard Telegram username. Must first be claimed via Telegram, then converted to Collectible via Fragment TON auction fee."
            )

        if status == UsernameStatus.TAKEN.value:
            return (
                "BASIC_USERNAME",
                AuctionEligibility.AUCTION_NOT_SUPPORTED.value,
                "Already occupied by an account. Cannot be auctioned unless owned and converted by the holder."
            )

        if status == UsernameStatus.RESERVED.value or status == UsernameStatus.INVALID.value:
            return (
                "BASIC_USERNAME",
                AuctionEligibility.AUCTION_NOT_SUPPORTED.value,
                "Reserved by Telegram or invalid syntax."
            )

        return (
            "BASIC_USERNAME",
            AuctionEligibility.AUCTION_UNKNOWN.value,
            "Verification pending or incomplete."
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
        if fragment_details.get("is_collectible"):
            return (
                "COLLECTIBLE_USERNAME",
                AuctionEligibility.AUCTION_ELIGIBLE.value,
                "Bot username is registered as Fragment TON collectible NFT."
            )

        if status == BotStatus.AVAILABLE_FOR_BOT.value:
            return (
                "BOT_USERNAME",
                AuctionEligibility.AUCTION_NOT_SUPPORTED.value,
                "Free for BotFather registration. Cannot be auctioned on Fragment directly without TON collectible conversion."
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
