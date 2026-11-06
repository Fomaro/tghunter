"""
Tests for Username, Bot, and Premium Bot Generators
"""
from telegram_username_hunter.config.settings import UsernameCategory
from telegram_username_hunter.generators.bot_generator import (
    BotUsernameGenerator,
    is_valid_bot_username,
)
from telegram_username_hunter.generators.premium_bot_generator import (
    SUPPORTED_PREMIUM_SUFFIXES,
    PremiumBotGenerator,
    is_valid_premium_bot_alias,
)
from telegram_username_hunter.generators.username_generator import (
    UsernameGenerator,
    is_valid_telegram_username,
)


def test_regular_username_rules():
    assert is_valid_telegram_username("alexander") is True
    assert is_valid_telegram_username("qevro") is True
    assert is_valid_telegram_username("ton_trade") is True
    # Too short
    assert is_valid_telegram_username("abc") is False
    # Starting/ending with underscore
    assert is_valid_telegram_username("_testname") is False
    assert is_valid_telegram_username("testname_") is False
    # Double underscore
    assert is_valid_telegram_username("test__name") is False
    # All digits
    assert is_valid_telegram_username("123456") is False


def test_regular_generator_batch():
    gen = UsernameGenerator(seed=42)
    batch = gen.generate_batch(count=200, min_length=5, max_length=15)

    assert len(batch) == 200
    names = [name for name, _cat in batch]

    # No duplicates
    assert len(names) == len(set(names))

    # All valid
    for name, _cat in batch:
        assert is_valid_telegram_username(name)
        assert 5 <= len(name) <= 15


def test_regular_generator_all_categories():
    gen = UsernameGenerator(seed=123)
    for cat in UsernameCategory:
        name = gen.generate_by_category(cat)
        assert len(name) >= 4


def test_bot_username_rules():
    assert is_valid_bot_username("qevrobot") is True
    assert is_valid_bot_username("vexly_bot") is True
    assert is_valid_bot_username("regular_user") is False
    assert is_valid_bot_username("bot") is False  # Length < 5


def test_bot_generator_batch():
    gen = BotUsernameGenerator(seed=42)
    batch = gen.generate_batch(count=150)

    assert len(batch) == 150
    names = [name for name, _cat in batch]
    assert len(names) == len(set(names))

    for name, _cat in batch:
        assert is_valid_bot_username(name)
        assert name.endswith(("bot", "_bot"))
        assert 5 <= len(name) <= 32


def test_bot_generator_all_categories():
    gen = BotUsernameGenerator(seed=123)
    for cat in (
        UsernameCategory.FINANCE,
        UsernameCategory.CRYPTO,
        UsernameCategory.TECH,
        UsernameCategory.GAMING,
        UsernameCategory.BRAND,
        UsernameCategory.DICTIONARY,
        UsernameCategory.RARE_COMBINATION,
    ):
        name = gen.generate_by_category(cat)
        assert is_valid_bot_username(name)


def test_premium_bot_alias_rules():
    assert is_valid_premium_bot_alias("qevro_app") is True
    assert is_valid_premium_bot_alias("qevro_ai") is True
    assert is_valid_premium_bot_alias("vexly_game") is True
    assert is_valid_premium_bot_alias("orvix_agent") is True
    assert is_valid_premium_bot_alias("zenvy_gay") is True
    assert is_valid_premium_bot_alias("regularname") is False
    assert is_valid_premium_bot_alias("qevrobot") is False


def test_premium_bot_generator_batch():
    gen = PremiumBotGenerator(seed=42)
    batch = gen.generate_batch(count=150)

    assert len(batch) == 150
    names = [name for name, sfx, _cat in batch]
    assert len(names) == len(set(names))

    for name, sfx, _cat in batch:
        assert is_valid_premium_bot_alias(name)
        assert sfx in SUPPORTED_PREMIUM_SUFFIXES
        assert name.endswith(sfx)


def test_premium_bot_generator_all_categories():
    gen = PremiumBotGenerator(seed=123)
    for cat in (
        UsernameCategory.AI,
        UsernameCategory.APPS,
        UsernameCategory.GAMING,
        UsernameCategory.AGENTS,
        UsernameCategory.FINANCE,
        UsernameCategory.CRYPTO,
        UsernameCategory.BRAND,
        UsernameCategory.RARE_COMBINATION,
    ):
        name, sfx = gen.generate_alias(cat)
        assert is_valid_premium_bot_alias(name)
        assert sfx in SUPPORTED_PREMIUM_SUFFIXES
