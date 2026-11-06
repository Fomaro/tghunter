"""
Tests for Checkers (Mock mode, FloodWait handling, Category isolation, Live HTTP branches)
"""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from telegram_username_hunter.checkers.bot_checker import BotChecker
from telegram_username_hunter.checkers.fragment_checker import FragmentChecker
from telegram_username_hunter.checkers.premium_bot_checker import PremiumBotChecker
from telegram_username_hunter.checkers.telegram_checker import TelegramChecker
from telegram_username_hunter.config.settings import (
    BotStatus,
    PremiumBotStatus,
    UsernameStatus,
)
from telegram_username_hunter.services.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_telegram_checker_mock_modes():
    checker = TelegramChecker(mock_mode=True)

    # Valid free name
    status, _details = await checker.check_username("qevro")
    assert status == UsernameStatus.AVAILABLE_TO_CLAIM

    # Taken simulation
    status, _details = await checker.check_username("taken_user")
    assert status == UsernameStatus.TAKEN

    # Invalid name
    status, _details = await checker.check_username("ab")
    assert status == UsernameStatus.INVALID

    # Error simulation
    status, _details = await checker.check_username("error_user")
    assert status == UsernameStatus.ERROR

    # Unknown simulation
    status, _details = await checker.check_username("unknown_user")
    assert status == UsernameStatus.UNKNOWN


@pytest.mark.asyncio
async def test_bot_checker_mock_modes():
    checker = BotChecker(mock_mode=True)

    status, _details = await checker.check_bot_username("qevrobot")
    assert status == BotStatus.AVAILABLE_FOR_BOT

    status, _details = await checker.check_bot_username("takenbot")
    assert status == BotStatus.TAKEN

    # Invalid syntax for bot (does not end in bot)
    status, _details = await checker.check_bot_username("regularname")
    assert status == BotStatus.INVALID


@pytest.mark.asyncio
async def test_premium_bot_checker_mock_modes():
    checker = PremiumBotChecker(mock_mode=True)

    status, _details = await checker.check_alias("qevro_app")
    assert status == PremiumBotStatus.ELIGIBLE_FOR_ASSIGNMENT

    status, _details = await checker.check_alias("taken_app")
    assert status == PremiumBotStatus.ALREADY_ASSIGNED

    status, _details = await checker.check_alias("invalidalias")
    assert status == PremiumBotStatus.INVALID


@pytest.mark.asyncio
async def test_rate_limiter_flood_wait():
    limiter = RateLimiter(base_delay=0.01, jitter=0.0)
    limiter.record_error(is_rate_limit=True, retry_after=0.1)

    t0 = asyncio.get_event_loop().time()
    await limiter.acquire()
    elapsed = asyncio.get_event_loop().time() - t0

    assert elapsed >= 0.1


@pytest.mark.asyncio
async def test_fragment_checker_live_branches():
    fc = FragmentChecker(mock_mode=False)

    # 404 branch
    mock_resp_404 = AsyncMock()
    mock_resp_404.status_code = 404
    with patch("httpx.AsyncClient.get", return_value=mock_resp_404):
        res = await fc.check_fragment("notfounduser")
        assert res["status"] == "not_found"

    # 429 FloodWait branch
    mock_resp_429 = AsyncMock()
    mock_resp_429.status_code = 429
    mock_resp_429.headers = {"Retry-After": "5"}
    with patch("httpx.AsyncClient.get", return_value=mock_resp_429):
        res = await fc.check_fragment("floodeduser")
        assert res["status"] == "rate_limited"

    # 200 Sold branch
    mock_resp_200 = AsyncMock()
    mock_resp_200.status_code = 200
    mock_resp_200.text = "This username was sold for 5000 TON"
    with patch("httpx.AsyncClient.get", return_value=mock_resp_200):
        res = await fc.check_fragment("solduser")
        assert res["status"] == "sold"
        assert res["is_collectible"] is True


@pytest.mark.asyncio
async def test_telegram_checker_live_branches():
    tc = TelegramChecker(mock_mode=False)
    tc.fragment_checker.check_fragment = AsyncMock(return_value={"is_collectible": False, "status": "not_found"})

    # 200 Taken with Send Message
    mock_resp_taken = AsyncMock()
    mock_resp_taken.status_code = 200
    mock_resp_taken.text = '<html><div class="tgme_page_action"><a class="tgme_action_button_new">Send Message</a></div></html>'
    with patch("httpx.AsyncClient.get", return_value=mock_resp_taken):
        status, details = await tc.check_username("activeuser")
        assert status == UsernameStatus.TAKEN

    # 200 Unclaimed
    mock_resp_free = AsyncMock()
    mock_resp_free.status_code = 200
    mock_resp_free.text = '<html><div class="tgme_page_description">If you have Telegram, you can contact @freeuser right away.</div></html>'
    with patch("httpx.AsyncClient.get", return_value=mock_resp_free):
        status, details = await tc.check_username("freeuser")
        assert status == UsernameStatus.AVAILABLE_TO_CLAIM

    # 404 Free
    mock_resp_404 = AsyncMock()
    mock_resp_404.status_code = 404
    with patch("httpx.AsyncClient.get", return_value=mock_resp_404):
        status, details = await tc.check_username("notfoundname")
        assert status == UsernameStatus.AVAILABLE_TO_CLAIM


@pytest.mark.asyncio
async def test_bot_checker_live_branches():
    bc = BotChecker(mock_mode=False)
    bc.fragment_checker.check_fragment = AsyncMock(return_value={"exists_on_fragment": False})

    # 200 Taken bot
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.text = '<html><div class="tgme_page_title">Bot Title</div><div class="tgme_page_extra">bot</div></html>'
    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        status, details = await bc.check_bot_username("livebot")
        assert status == BotStatus.TAKEN

    # 404 Available bot
    mock_resp_404 = AsyncMock()
    mock_resp_404.status_code = 404
    with patch("httpx.AsyncClient.get", return_value=mock_resp_404):
        status, details = await bc.check_bot_username("freebotnamebot")
        assert status == BotStatus.AVAILABLE_FOR_BOT


@pytest.mark.asyncio
async def test_premium_bot_checker_live_branches():
    pbc = PremiumBotChecker(mock_mode=False)
    pbc.fragment_checker.check_fragment = AsyncMock(return_value={"exists_on_fragment": False})

    # 200 Taken alias
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.text = '<html><div class="tgme_page_title">App Title</div><div class="tgme_page_extra">channel</div></html>'
    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        status, details = await pbc.check_alias("my_app")
        assert status == PremiumBotStatus.ALREADY_ASSIGNED

    # 404 Eligible alias
    mock_resp_404 = AsyncMock()
    mock_resp_404.status_code = 404
    with patch("httpx.AsyncClient.get", return_value=mock_resp_404):
        status, details = await pbc.check_alias("freebrand_ai")
        assert status == PremiumBotStatus.ELIGIBLE_FOR_ASSIGNMENT
