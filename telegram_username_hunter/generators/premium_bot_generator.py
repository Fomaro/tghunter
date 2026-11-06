"""
Telegram Username Hunter PRO
Premium Bot Names Generator (Bot Aliases)
"""
import random

from telegram_username_hunter.config.settings import UsernameCategory
from telegram_username_hunter.generators.dictionaries import (
    AI_WORDS,
    APP_WORDS,
    BRAND_PREFIXES,
    CRYPTO_WORDS,
    FINANCIAL_WORDS,
    GAMING_WORDS,
    SHORT_SYLLABLES,
)
from telegram_username_hunter.generators.username_generator import (
    is_valid_telegram_username,
)

SUPPORTED_PREMIUM_SUFFIXES = ["_app", "_ai", "_game", "_agent", "_gay"]


def is_valid_premium_bot_alias(username: str) -> bool:
    """Validate that the alias has one of the supported suffixes and meets Telegram rules."""
    lower = username.lower()
    has_valid_suffix = any(lower.endswith(sfx) for sfx in SUPPORTED_PREMIUM_SUFFIXES)
    if not has_valid_suffix:
        return False
    return is_valid_telegram_username(lower)


class PremiumBotGenerator:
    """Generator for Telegram Premium Bot Aliases ending in _app, _ai, _game, _agent, _gay."""

    def __init__(self, seed: int | None = None):
        if seed is not None:
            random.seed(seed)

    def _generate_base(self, category: UsernameCategory) -> str:
        """Generate base word according to category."""
        if category == UsernameCategory.AI:
            if random.random() < 0.4:
                return random.choice(AI_WORDS)
            syl = random.choice(SHORT_SYLLABLES)
            return syl + random.choice(["mind", "net", "syn", "tron", "ix", "on"])
        elif category == UsernameCategory.APPS:
            if random.random() < 0.4:
                return random.choice(APP_WORDS)
            return random.choice(BRAND_PREFIXES) + random.choice(["ly", "io", "ix", "flow"])
        elif category == UsernameCategory.GAMING:
            if random.random() < 0.5:
                w = random.choice(GAMING_WORDS)
                return w[:7]
            return random.choice(SHORT_SYLLABLES) + random.choice(["quest", "craft", "zone", "frag"])
        elif category == UsernameCategory.AGENTS:
            syl = random.choice(SHORT_SYLLABLES)
            return syl + random.choice(["core", "node", "link", "syn", "flow", "orv"])
        elif category == UsernameCategory.FINANCE:
            w = random.choice(FINANCIAL_WORDS)
            return w[:7]
        elif category == UsernameCategory.CRYPTO:
            w = random.choice(CRYPTO_WORDS)
            return w[:7]
        elif category == UsernameCategory.BRAND:
            return random.choice(BRAND_PREFIXES) + random.choice(["a", "o", "x", "is", "ly"])
        elif category == UsernameCategory.RARE_COMBINATION:
            # e.g., qevro, vexly, orvix, zenvy
            syl = random.choice(SHORT_SYLLABLES)
            end = random.choice(["ro", "ly", "ix", "vy", "on", "ex", "is"])
            return syl + end
        else:
            return random.choice(SHORT_SYLLABLES) + random.choice(["ro", "ix", "on"])

    def generate_alias(
        self,
        category: UsernameCategory,
        preferred_suffix: str | None = None
    ) -> tuple[str, str]:
        """Generate single (alias_name, suffix)."""
        suffix = preferred_suffix if (preferred_suffix in SUPPORTED_PREMIUM_SUFFIXES) else None
        if not suffix:
            # Map category default if appropriate
            if category == UsernameCategory.AI:
                suffix = "_ai"
            elif category == UsernameCategory.APPS:
                suffix = "_app"
            elif category == UsernameCategory.GAMING:
                suffix = "_game"
            elif category == UsernameCategory.AGENTS:
                suffix = "_agent"
            else:
                suffix = random.choice(SUPPORTED_PREMIUM_SUFFIXES)

        base = self._generate_base(category)
        # Avoid ending base with underscore before adding _suffix
        base = base.rstrip("_")
        name = f"{base}{suffix}"
        return name, suffix

    def generate_batch(
        self,
        count: int = 100,
        categories: list[UsernameCategory] | None = None,
        suffixes: list[str] | None = None,
        min_length: int = 5,
        max_length: int = 32
    ) -> list[tuple[str, str, str]]:
        """
        Generate a batch of unique premium aliases.
        Returns list of (username, suffix, category).
        """
        if not categories:
            categories = [
                UsernameCategory.AI,
                UsernameCategory.APPS,
                UsernameCategory.GAMING,
                UsernameCategory.AGENTS,
                UsernameCategory.FINANCE,
                UsernameCategory.CRYPTO,
                UsernameCategory.BRAND,
                UsernameCategory.RARE_COMBINATION,
            ]

        chosen_suffixes = suffixes or SUPPORTED_PREMIUM_SUFFIXES

        results: list[tuple[str, str, str]] = []
        seen: set[str] = set()
        attempts = 0
        max_attempts = count * 20

        while len(results) < count and attempts < max_attempts:
            attempts += 1
            cat = random.choice(categories)
            sfx = random.choice(chosen_suffixes)
            name, used_sfx = self.generate_alias(cat, preferred_suffix=sfx)
            name = name.lower()

            if min_length <= len(name) <= max_length and is_valid_premium_bot_alias(name):
                if name not in seen:
                    seen.add(name)
                    results.append((name, used_sfx, cat.value))

        return results
