"""
Telegram Username Hunter PRO
Data Models
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from telegram_username_hunter.config.settings import (
    AuctionEligibility,
    BotStatus,
    PremiumBotStatus,
    UsernameStatus,
)


@dataclass
class UsernameRecord:
    id: int | None = None
    username: str = ""
    category: str = ""
    status: str = UsernameStatus.UNKNOWN.value
    score: int = 0
    auction_eligibility: str = AuctionEligibility.AUCTION_UNKNOWN.value
    fragment_url: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    last_checked_at: str | None = None
    check_source: str = ""
    notes: str = ""

    @property
    def length(self) -> int:
        return len(self.username)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "category": self.category,
            "status": self.status,
            "score": self.score,
            "auction_eligibility": self.auction_eligibility,
            "fragment_url": self.fragment_url,
            "generated_at": self.generated_at,
            "last_checked_at": self.last_checked_at,
            "check_source": self.check_source,
            "notes": self.notes,
            "length": self.length,
        }


@dataclass
class BotRecord:
    id: int | None = None
    username: str = ""
    category: str = ""
    status: str = BotStatus.UNKNOWN.value
    score: int = 0
    auction_eligibility: str = AuctionEligibility.AUCTION_NOT_SUPPORTED.value
    fragment_url: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    last_checked_at: str | None = None
    check_source: str = ""
    notes: str = ""

    @property
    def length(self) -> int:
        return len(self.username)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "category": self.category,
            "status": self.status,
            "score": self.score,
            "auction_eligibility": self.auction_eligibility,
            "fragment_url": self.fragment_url,
            "generated_at": self.generated_at,
            "last_checked_at": self.last_checked_at,
            "check_source": self.check_source,
            "notes": self.notes,
            "length": self.length,
        }


@dataclass
class PremiumAliasRecord:
    id: int | None = None
    username: str = ""
    suffix: str = ""
    category: str = ""
    status: str = PremiumBotStatus.UNKNOWN.value
    score: int = 0
    auction_eligibility: str = AuctionEligibility.AUCTION_NOT_SUPPORTED.value
    fragment_url: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    last_checked_at: str | None = None
    check_source: str = ""
    notes: str = ""

    @property
    def length(self) -> int:
        return len(self.username)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "suffix": self.suffix,
            "category": self.category,
            "status": self.status,
            "score": self.score,
            "auction_eligibility": self.auction_eligibility,
            "fragment_url": self.fragment_url,
            "generated_at": self.generated_at,
            "last_checked_at": self.last_checked_at,
            "check_source": self.check_source,
            "notes": self.notes,
            "length": self.length,
        }


@dataclass
class DashboardStats:
    total_generated: int = 0
    total_checked: int = 0
    available_usernames: int = 0
    available_bot_names: int = 0
    premium_bot_aliases: int = 0
    promising_usernames: int = 0
    promising_bot_names: int = 0
    check_errors: int = 0
    last_activity: str = "No activity yet"
