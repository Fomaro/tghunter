"""
Telegram Username Hunter PRO
Telegram MTProto API Protocol Definitions & Client Interface
Based on official Telegram MTProto Documentation:
- https://core.telegram.org/method/account.checkUsername
- https://core.telegram.org/method/contacts.resolveUsername
- https://core.telegram.org/method/channels.checkUsername
"""
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TargetEntityType(str, Enum):
    """Target entity type for username claiming."""
    USER = "USER"
    CHANNEL = "CHANNEL"
    BOT = "BOT"


class MTProtoErrorCode(str, Enum):
    """Official Telegram MTProto RPC Error Codes."""
    USERNAME_INVALID = "USERNAME_INVALID"
    USERNAME_OCCUPIED = "USERNAME_OCCUPIED"
    USERNAME_PURCHASE_AVAILABLE = "USERNAME_PURCHASE_AVAILABLE"
    USERNAME_NOT_OCCUPIED = "USERNAME_NOT_OCCUPIED"
    USERNAME_NOT_MODIFIED = "USERNAME_NOT_MODIFIED"
    FLOOD_WAIT = "FLOOD_WAIT"
    CHANNELS_ADMIN_PUBLIC_TOO_MUCH = "CHANNELS_ADMIN_PUBLIC_TOO_MUCH"


class MTProtoRPCError(Exception):
    """Telegram MTProto RPC exception."""

    def __init__(self, code: str, message: str = "", flood_wait_seconds: int = 0):
        super().__init__(f"MTProto RPC Error [{code}]: {message}")
        self.code = code
        self.message = message
        self.flood_wait_seconds = flood_wait_seconds


# Well-known restricted, protected dictionary words, and system handles in Telegram
# In MTProto account.checkUsername, Telegram returns USERNAME_INVALID for these handles.
TELEGRAM_RESTRICTED_WORDS = {
    # System handles and infrastructure
    "admin", "administrator", "root", "support", "help", "service", "security",
    "telegram", "durov", "channel", "group", "contact", "settings", "privacy",
    "terms", "wallet", "status", "update", "updates", "news", "official", "system",
    "verify", "verification", "moderator", "staff", "founder", "ceo", "fragment",
    "ton", "blockchain", "premium", "stickers", "themes", "proxy", "desktop",
    "web", "android", "ios", "login", "auth", "oauth", "token", "connect",
    "account", "profile", "notification", "notifications", "alerts", "securitybot",
    "spam", "spambot", "botfather", "cloud",
    # 5-letter restricted/protected dictionary words that return USERNAME_INVALID
    "viper", "amber", "angel", "arrow", "atlas", "blaze", "bloom", "brave", "breeze",
    "cider", "cliff", "comet", "coral", "crown", "delta", "eagle", "ember",
    "fable", "flame", "flash", "frost", "giant", "glory", "grace", "grove",
    "haven", "hazel", "honor", "ivory", "laser", "lemon", "logic", "lunar",
    "magic", "manor", "maple", "merit", "noble", "oasis", "ocean", "orbit",
    "pearl", "pilot", "polar", "prism", "pulse", "quest", "radar", "raven",
    "rider", "river", "robin", "royal", "sable", "scout", "shadow", "shard",
    "shore", "solar", "spark", "spear", "spice", "stone", "storm", "swift",
    "talon", "tiger", "titan", "tower", "trace", "trail", "vapor", "vigor",
    "vista", "vivid", "vocal", "vortex", "wheat", "whisper", "willow", "winter",
    "zenith", "zephyr",
}


class MTProtoClientInterface(ABC):
    """Abstract interface for Telegram MTProto client."""

    @abstractmethod
    async def check_username(
        self,
        username: str,
        entity_type: TargetEntityType = TargetEntityType.USER
    ) -> bool:
        """
        Execute MTProto account.checkUsername or channels.checkUsername.
        Returns True if username is free to claim.
        Raises MTProtoRPCError if Telegram returns an RPC error.
        """
        pass

    @abstractmethod
    async def resolve_username(self, username: str) -> dict[str, Any]:
        """
        Execute MTProto contacts.resolveUsername.
        Returns peer dict if username resolves to an active peer.
        Raises MTProtoRPCError(code="USERNAME_NOT_OCCUPIED") if no peer holds the username.
        """
        pass


class MockMTProtoClient(MTProtoClientInterface):
    """
    Deterministic Mock MTProto client for automated tests and offline simulation.
    Faithfully reproduces MTProto behaviors and RPC responses.
    """

    def __init__(self):
        self._rules: dict[str, dict[str, Any]] = {}
        # Preconfigure canonical test cases
        self.register_rule("freeuser", check_result=True, resolve_error="USERNAME_NOT_OCCUPIED")
        self.register_rule("occupieduser", check_error="USERNAME_OCCUPIED", resolve_peer={"type": "user", "id": 1001})
        self.register_rule("viper", check_error="USERNAME_INVALID", resolve_error="USERNAME_NOT_OCCUPIED")
        self.register_rule("admin", check_error="USERNAME_INVALID", resolve_peer={"type": "channel", "id": 777})
        self.register_rule("shop", check_error="USERNAME_PURCHASE_AVAILABLE", resolve_error="USERNAME_NOT_OCCUPIED")
        self.register_rule("game", check_error="USERNAME_PURCHASE_AVAILABLE", resolve_error="USERNAME_NOT_OCCUPIED")
        self.register_rule("crypto", check_error="USERNAME_PURCHASE_AVAILABLE", resolve_peer={"type": "channel", "id": 888})
        self.register_rule("flooduser", check_error="FLOOD_WAIT", flood_wait=15)
        self.register_rule("conn_error", network_error=True)

    def register_rule(
        self,
        username: str,
        check_result: bool | None = None,
        check_error: str | None = None,
        resolve_peer: dict[str, Any] | None = None,
        resolve_error: str | None = None,
        flood_wait: int = 0,
        network_error: bool = False,
    ) -> None:
        clean = username.lstrip("@").lower()
        self._rules[clean] = {
            "check_result": check_result,
            "check_error": check_error,
            "resolve_peer": resolve_peer,
            "resolve_error": resolve_error,
            "flood_wait": flood_wait,
            "network_error": network_error,
        }

    async def check_username(
        self,
        username: str,
        entity_type: TargetEntityType = TargetEntityType.USER
    ) -> bool:
        clean = username.lstrip("@").lower()
        rule = self._rules.get(clean)

        if rule:
            if rule.get("network_error"):
                raise ConnectionError("Mock MTProto connection timeout")
            if rule.get("check_error") == "FLOOD_WAIT":
                raise MTProtoRPCError("FLOOD_WAIT", "Rate limit exceeded", flood_wait_seconds=rule.get("flood_wait", 30))
            if rule.get("check_error"):
                raise MTProtoRPCError(rule["check_error"], f"RPC error: {rule['check_error']}")
            if rule.get("check_result") is not None:
                return bool(rule["check_result"])

        # Default fallback rules for unconfigured usernames
        if clean.startswith("error") or clean.startswith("fail"):
            raise ConnectionError("Mock MTProto connection timeout")
        if clean.startswith("unknown"):
            raise MTProtoRPCError("FLOOD_WAIT", "Simulated unknown", flood_wait_seconds=30)
        if len(clean) < 5 and entity_type == TargetEntityType.USER:
            raise MTProtoRPCError("USERNAME_PURCHASE_AVAILABLE", "4-char usernames require Fragment")
        if clean in TELEGRAM_RESTRICTED_WORDS:
            raise MTProtoRPCError("USERNAME_INVALID", "Username is reserved/restricted by Telegram")
        if clean.startswith("taken"):
            raise MTProtoRPCError("USERNAME_OCCUPIED", "Username is occupied")
        if clean.startswith("invalid"):
            raise MTProtoRPCError("USERNAME_INVALID", "Invalid username syntax")
        if clean.startswith("flood"):
            raise MTProtoRPCError("FLOOD_WAIT", "Rate limit", flood_wait_seconds=30)

        # In mock mode, names starting with 'free' or unlisted are free
        return True

    async def resolve_username(self, username: str) -> dict[str, Any]:
        clean = username.lstrip("@").lower()
        rule = self._rules.get(clean)

        if rule:
            if rule.get("network_error"):
                raise ConnectionError("Mock MTProto connection timeout")
            if rule.get("resolve_peer"):
                return rule["resolve_peer"]
            if rule.get("resolve_error"):
                raise MTProtoRPCError(rule["resolve_error"], f"RPC error: {rule['resolve_error']}")

        if clean.startswith("error") or clean.startswith("fail"):
            raise ConnectionError("Mock MTProto connection timeout")
        if clean.startswith("unknown"):
            raise MTProtoRPCError("FLOOD_WAIT", "Simulated unknown", flood_wait_seconds=30)
        if clean in ("admin", "telegram", "durov", "crypto") or clean.startswith("taken"):
            return {"type": "channel", "id": 12345, "username": clean}

        raise MTProtoRPCError("USERNAME_NOT_OCCUPIED", "Username is not occupied by any active peer")
