"""
Telegram Username Hunter PRO
Bot Username Generator
"""
import random

from telegram_username_hunter.config.settings import UsernameCategory
from telegram_username_hunter.generators.dictionaries import (
    BRAND_PREFIXES,
    CRYPTO_WORDS,
    DICTIONARY_WORDS,
    FINANCIAL_WORDS,
    GAMING_WORDS,
    PHONETIC_VOWELS,
    PREMIUM_CONSONANTS,
    SHORT_SYLLABLES,
    TECH_WORDS,
)
from telegram_username_hunter.generators.username_generator import (
    is_valid_telegram_username,
)


def is_valid_bot_username(username: str) -> bool:
    """Validate that the username complies with BotFather rules: ends with 'bot' or '_bot'."""
    lower = username.lower()
    if not lower.endswith(("bot", "_bot")):
        return False
    # Check length and general rules
    return is_valid_telegram_username(lower)


class BotUsernameGenerator:
    """Generates valid bot usernames ending in 'bot' or '_bot' across domains."""

    def __init__(self, seed: int | None = None):
        if seed is not None:
            random.seed(seed)

    def _append_bot(self, base: str, allow_underscore: bool = False) -> str:
        """Append 'bot' or '_bot' to a base name."""
        if allow_underscore and random.random() < 0.25 and not base.endswith("_"):
            res = f"{base}_bot"
        else:
            res = f"{base}bot"
        return res

    def generate_short_bot(self) -> str:
        """e.g. qevrobot, vexlybot, orvixbot, qivrobot, xevonbot."""
        # 3 or 4 letter phonetic base + bot
        pattern = random.choice(["CVC", "CVCV", "CVCC", "VCV"])
        chars = []
        for p in pattern:
            if p == "C":
                chars.append(random.choice(PREMIUM_CONSONANTS))
            else:
                chars.append(random.choice(PHONETIC_VOWELS))
        base = "".join(chars)
        # Maybe add a short suffix before bot (e.g. qevro -> qevrobot, vexly -> vexlybot)
        if len(base) == 3 and random.random() < 0.6:
            base += random.choice(["ro", "ly", "ix", "on", "ex", "is"])
        return self._append_bot(base)

    def generate_brand_bot(self) -> str:
        prefix = random.choice(BRAND_PREFIXES)
        suffix = random.choice(["", "x", "io", "ia", "a", "o"])
        return self._append_bot(prefix + suffix)

    def generate_dictionary_bot(self) -> str:
        word = random.choice(DICTIONARY_WORDS)
        # Prefer shorter words so word+bot is concise
        if len(word) > 7:
            word = word[:6]
        return self._append_bot(word)

    def generate_finance_bot(self) -> str:
        word = random.choice(FINANCIAL_WORDS)
        if len(word) > 8:
            word = word[:7]
        return self._append_bot(word)

    def generate_crypto_bot(self) -> str:
        word = random.choice(CRYPTO_WORDS)
        if len(word) > 8:
            word = word[:7]
        return self._append_bot(word)

    def generate_tech_bot(self) -> str:
        word = random.choice(TECH_WORDS)
        if len(word) > 8:
            word = word[:7]
        return self._append_bot(word)

    def generate_gaming_bot(self) -> str:
        word = random.choice(GAMING_WORDS)
        if len(word) > 8:
            word = word[:7]
        return self._append_bot(word)

    def generate_rare_bot(self) -> str:
        syl = random.choice(SHORT_SYLLABLES)
        end = random.choice(["on", "ix", "ex", "or", "er", "is", "a", "o", "y"])
        return self._append_bot(syl + end)

    def generate_by_category(self, category: UsernameCategory) -> str:
        if category == UsernameCategory.FINANCE:
            return self.generate_finance_bot()
        elif category == UsernameCategory.CRYPTO:
            return self.generate_crypto_bot()
        elif category == UsernameCategory.TECH:
            return self.generate_tech_bot()
        elif category == UsernameCategory.GAMING:
            return self.generate_gaming_bot()
        elif category == UsernameCategory.BRAND:
            return self.generate_brand_bot()
        elif category == UsernameCategory.DICTIONARY:
            return self.generate_dictionary_bot()
        elif category == UsernameCategory.RARE_COMBINATION:
            return self.generate_rare_bot()
        else:
            return self.generate_short_bot()

    def generate_batch(
        self,
        count: int = 100,
        categories: list[UsernameCategory] | None = None,
        min_length: int = 5,
        max_length: int = 32
    ) -> list[tuple[str, str]]:
        if not categories:
            categories = [
                UsernameCategory.BRAND,
                UsernameCategory.DICTIONARY,
                UsernameCategory.FINANCE,
                UsernameCategory.CRYPTO,
                UsernameCategory.TECH,
                UsernameCategory.GAMING,
                UsernameCategory.RARE_COMBINATION,
            ]

        results: list[tuple[str, str]] = []
        seen: set[str] = set()
        attempts = 0
        max_attempts = count * 20

        while len(results) < count and attempts < max_attempts:
            attempts += 1
            cat = random.choice(categories)
            raw = self.generate_by_category(cat).lower()

            if min_length <= len(raw) <= max_length and is_valid_bot_username(raw):
                if raw not in seen:
                    seen.add(raw)
                    results.append((raw, cat.value))

        return results
