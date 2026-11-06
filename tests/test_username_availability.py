"""
Telegram Username Hunter PRO
Automated Test Suite: Username Availability & MTProto Verification
Verifies all 12 core requirements from the Telegram Username Availability Audit specification.
"""
from unittest.mock import AsyncMock, patch

import pytest

from telegram_username_hunter.checkers.fragment_checker import FragmentChecker
from telegram_username_hunter.checkers.mtproto_checker import (
    MockMTProtoClient,
    MTProtoClientInterface,
    MTProtoErrorCode,
    MTProtoRPCError,
    TargetEntityType,
)
from telegram_username_hunter.checkers.telegram_checker import TelegramChecker
from telegram_username_hunter.config.settings import AuctionEligibility, UsernameStatus
from telegram_username_hunter.services.rate_limiter import RateLimiter


@pytest.fixture
def mock_fragment_checker():
    """Returns a mock fragment checker returning non-fragment defaults."""
    fc = FragmentChecker(mock_mode=True)
    return fc


@pytest.fixture
def rate_limiter():
    return RateLimiter()


# =====================================================================
# 1. Truly free username -> AVAILABLE
# =====================================================================
@pytest.mark.asyncio
async def test_01_truly_free_username(rate_limiter, mock_fragment_checker):
    """
    1. A username confirmed by MTProto account.checkUsername as True
       and not resolved to any peer must yield AVAILABLE.
    """
    mock_client = MockMTProtoClient()
    mock_client.register_rule("freetestuser", check_result=True, resolve_error="USERNAME_NOT_OCCUPIED")

    checker = TelegramChecker(
        rate_limiter=rate_limiter,
        fragment_checker=mock_fragment_checker,
        mtproto_client=mock_client,
        mock_mode=False
    )
    status, details = await checker.check_username("freetestuser", entity_type=TargetEntityType.USER)

    assert status == UsernameStatus.AVAILABLE
    assert "account.checkUsername" in details["details"]


# =====================================================================
# 2. Occupied username -> OCCUPIED
# =====================================================================
@pytest.mark.asyncio
async def test_02_occupied_username(rate_limiter, mock_fragment_checker):
    """
    2. A username that resolves to an active peer via contacts.resolveUsername
       must yield OCCUPIED.
    """
    mock_client = MockMTProtoClient()
    mock_client.register_rule(
        "activeholder",
        resolve_peer={"type": "user", "id": 99999, "username": "activeholder"}
    )

    checker = TelegramChecker(
        rate_limiter=rate_limiter,
        fragment_checker=mock_fragment_checker,
        mtproto_client=mock_client,
        mock_mode=False
    )
    status, details = await checker.check_username("activeholder")

    assert status == UsernameStatus.OCCUPIED
    assert "Active Telegram peer resolved" in details["details"]


# =====================================================================
# 3. Username returning USERNAME_INVALID -> INVALID / RESTRICTED (never AVAILABLE)
# =====================================================================
@pytest.mark.asyncio
async def test_03_username_invalid_mtproto(rate_limiter, mock_fragment_checker):
    """
    3. Telegram MTProto returning USERNAME_INVALID must yield RESTRICTED or INVALID,
       and NEVER AVAILABLE.
    """
    mock_client = MockMTProtoClient()
    mock_client.register_rule("badhandle", check_error=MTProtoErrorCode.USERNAME_INVALID, resolve_error="USERNAME_NOT_OCCUPIED")

    checker = TelegramChecker(
        rate_limiter=rate_limiter,
        fragment_checker=mock_fragment_checker,
        mtproto_client=mock_client,
        mock_mode=False
    )
    status, details = await checker.check_username("badhandle")

    assert status in (UsernameStatus.RESTRICTED, UsernameStatus.INVALID)
    assert status != UsernameStatus.AVAILABLE


# =====================================================================
# 4. Username returning USERNAME_OCCUPIED -> OCCUPIED
# =====================================================================
@pytest.mark.asyncio
async def test_04_username_occupied_mtproto(rate_limiter, mock_fragment_checker):
    """
    4. Telegram MTProto returning USERNAME_OCCUPIED must yield OCCUPIED.
    """
    mock_client = MockMTProtoClient()
    mock_client.register_rule("occupiedhandle", check_error=MTProtoErrorCode.USERNAME_OCCUPIED, resolve_error="USERNAME_NOT_OCCUPIED")

    checker = TelegramChecker(
        rate_limiter=rate_limiter,
        fragment_checker=mock_fragment_checker,
        mtproto_client=mock_client,
        mock_mode=False
    )
    status, details = await checker.check_username("occupiedhandle")

    assert status == UsernameStatus.OCCUPIED


# =====================================================================
# 5. Username returning USERNAME_PURCHASE_AVAILABLE -> RESTRICTED + PURCHASE_AVAILABLE
# =====================================================================
@pytest.mark.asyncio
async def test_05_username_purchase_available(rate_limiter, mock_fragment_checker):
    """
    5. Telegram returning USERNAME_PURCHASE_AVAILABLE indicates the handle is
       obtainable only via Fragment auction, so availability is RESTRICTED and Fragment status is PURCHASE_AVAILABLE.
    """
    mock_client = MockMTProtoClient()
    mock_client.register_rule("premiumhandle", check_error=MTProtoErrorCode.USERNAME_PURCHASE_AVAILABLE, resolve_error="USERNAME_NOT_OCCUPIED")

    checker = TelegramChecker(
        rate_limiter=rate_limiter,
        fragment_checker=mock_fragment_checker,
        mtproto_client=mock_client,
        mock_mode=False
    )
    status, details = await checker.check_username("premiumhandle")

    assert status == UsernameStatus.RESTRICTED
    assert details["fragment_status"] == AuctionEligibility.PURCHASE_AVAILABLE.value


# =====================================================================
# 6. Unconfirmed resolve without account.checkUsername -> UNKNOWN
# =====================================================================
@pytest.mark.asyncio
async def test_06_unconfirmed_resolve_without_account_check(rate_limiter, mock_fragment_checker):
    """
    6. In web-only resolve mode (no MTProto session), when t.me returns 404 or empty profile,
       the absence of a public profile DOES NOT prove availability. It must return UNKNOWN.
    """
    checker = TelegramChecker(
        rate_limiter=rate_limiter,
        fragment_checker=mock_fragment_checker,
        mtproto_client=None,  # No MTProto client
        mock_mode=False
    )

    mock_resp = AsyncMock()
    mock_resp.status_code = 404

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        status, details = await checker.check_username("unconfirmedtest")

    assert status == UsernameStatus.UNKNOWN
    assert status != UsernameStatus.AVAILABLE


# =====================================================================
# 7. Reserved or restricted username -> RESTRICTED
# =====================================================================
@pytest.mark.asyncio
async def test_07_reserved_or_restricted_username(rate_limiter, mock_fragment_checker):
    """
    7. Protected dictionary handles and reserved handles (e.g. viper, admin, cloud)
       must be recognized as RESTRICTED.
    """
    checker = TelegramChecker(
        rate_limiter=rate_limiter,
        fragment_checker=mock_fragment_checker,
        mock_mode=True
    )
    for word in ("viper", "admin", "cloud", "amber", "orbit"):
        status, details = await checker.check_username(word)
        assert status == UsernameStatus.RESTRICTED
        assert status != UsernameStatus.AVAILABLE


# =====================================================================
# 8. Error connecting to server -> ERROR (never AVAILABLE)
# =====================================================================
@pytest.mark.asyncio
async def test_08_connection_error(rate_limiter, mock_fragment_checker):
    """
    8. Any network failure or transport error must yield ERROR, never AVAILABLE.
    """
    mock_client = MockMTProtoClient()
    mock_client.register_rule("connfail", network_error=True)

    checker = TelegramChecker(
        rate_limiter=rate_limiter,
        fragment_checker=mock_fragment_checker,
        mtproto_client=mock_client,
        mock_mode=False
    )
    status, details = await checker.check_username("connfail")

    assert status == UsernameStatus.ERROR
    assert status != UsernameStatus.AVAILABLE


# =====================================================================
# 9. HTTP 429 / FloodWait -> UNKNOWN with cooldown
# =====================================================================
@pytest.mark.asyncio
async def test_09_flood_wait_and_http_429(rate_limiter, mock_fragment_checker):
    """
    9. MTProto FLOOD_WAIT or HTTP 429 must return UNKNOWN, trigger rate limiter cooldown,
       and never falsely report AVAILABLE.
    """
    mock_client = MockMTProtoClient()
    mock_client.register_rule("floodtest", check_error=MTProtoErrorCode.FLOOD_WAIT, flood_wait=20)

    checker = TelegramChecker(
        rate_limiter=rate_limiter,
        fragment_checker=mock_fragment_checker,
        mtproto_client=mock_client,
        mock_mode=False
    )
    status, details = await checker.check_username("floodtest")

    assert status == UsernameStatus.UNKNOWN
    assert status != UsernameStatus.AVAILABLE
    assert rate_limiter.is_throttled is True
    assert rate_limiter.cooldown_remaining > 0


# =====================================================================
# 10. Entity difference: user vs channel vs bot
# =====================================================================
@pytest.mark.asyncio
async def test_10_target_entity_differences(rate_limiter, mock_fragment_checker):
    """
    10. Availability can vary depending on whether the target entity is
        a USER account, a CHANNEL/SUPERGROUP, or a BOT.
    """
    class EntitySensitiveMock(MTProtoClientInterface):
        async def check_username(self, username: str, entity_type: TargetEntityType = TargetEntityType.USER) -> bool:
            # Handle is free for a channel, but taken for a user account
            if entity_type == TargetEntityType.CHANNEL:
                return True
            raise MTProtoRPCError(MTProtoErrorCode.USERNAME_OCCUPIED, "Occupied for user accounts")

        async def resolve_username(self, username: str):
            raise MTProtoRPCError(MTProtoErrorCode.USERNAME_NOT_OCCUPIED, "Not resolved")

    client = EntitySensitiveMock()
    checker = TelegramChecker(
        rate_limiter=rate_limiter,
        fragment_checker=mock_fragment_checker,
        mtproto_client=client,
        mock_mode=False
    )

    status_user, _ = await checker.check_username("entitytest", entity_type=TargetEntityType.USER)
    assert status_user == UsernameStatus.OCCUPIED

    status_chan, _ = await checker.check_username("entitytest", entity_type=TargetEntityType.CHANNEL)
    assert status_chan == UsernameStatus.AVAILABLE


# =====================================================================
# 11. Zero false positives verification across test scenarios
# =====================================================================
@pytest.mark.asyncio
async def test_11_zero_false_positives(rate_limiter, mock_fragment_checker):
    """
    11. A battery of problematic, reserved, occupied, or collectible usernames
        must have 0% false positives (none should ever be marked AVAILABLE).
    """
    problematic_usernames = [
        "viper",
        "admin",
        "cloud",
        "shop",       # 4 chars -> restricted to fragment
        "game",       # 4 chars
        "taken123",   # starts with taken
        "invalid..x", # syntax invalid
        "conn_error",
    ]

    checker = TelegramChecker(
        rate_limiter=rate_limiter,
        fragment_checker=mock_fragment_checker,
        mock_mode=True
    )

    for name in problematic_usernames:
        status, _ = await checker.check_username(name)
        assert status != UsernameStatus.AVAILABLE, f"False positive detected for '{name}': received {status}"


# =====================================================================
# 12. Explicit regression test for 'viper'
# =====================================================================
@pytest.mark.asyncio
async def test_12_viper_regression_explicit(rate_limiter, mock_fragment_checker):
    """
    12. Explicit regression test for 'viper':
        - t.me/viper shows 404 or empty profile.
        - Telegram server returns USERNAME_INVALID when attempting to claim.
        - Must NEVER be marked AVAILABLE.
    """
    # 1. Verification in Mock / MTProto mode
    checker_mtproto = TelegramChecker(
        rate_limiter=rate_limiter,
        fragment_checker=mock_fragment_checker,
        mock_mode=True
    )
    status_mtproto, det_mtproto = await checker_mtproto.check_username("viper")
    assert status_mtproto == UsernameStatus.RESTRICTED
    assert status_mtproto != UsernameStatus.AVAILABLE

    # 2. Verification in Web Fallback mode (empty card / 404)
    checker_web = TelegramChecker(
        rate_limiter=rate_limiter,
        fragment_checker=mock_fragment_checker,
        mtproto_client=None,
        mock_mode=False
    )
    status_web, det_web = await checker_web.check_username("viper")
    # Even in web mode without MTProto, policy-restricted word list catches 'viper'
    assert status_web == UsernameStatus.RESTRICTED
    assert status_web != UsernameStatus.AVAILABLE
