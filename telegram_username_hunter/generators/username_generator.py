"""
Telegram Username Hunter PRO
Regular Username Generator
"""
import random
import re

from telegram_username_hunter.config.settings import UsernameCategory
from telegram_username_hunter.generators.dictionaries import (
    BRAND_PREFIXES,
    BRAND_SUFFIXES,
    CRYPTO_WORDS,
    DICTIONARY_WORDS,
    FINANCIAL_WORDS,
    GAMING_WORDS,
    PHONETIC_CONSONANTS,
    PHONETIC_VOWELS,
    PREMIUM_CONSONANTS,
    SHORT_SYLLABLES,
    TECH_WORDS,
)

# Telegram username regex: 5-32 chars, a-z0-9_, cannot start or end with _, no consecutive __, must have at least one letter
USERNAME_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{3,30}[a-zA-Z0-9]$")


def is_valid_telegram_username(username: str) -> bool:
    """Validate username according to official Telegram rules."""
    if not (5 <= len(username) <= 32):
        return False
    if not USERNAME_REGEX.match(username):
        return False
    if "__" in username:
        return False
    if username.isdigit():
        return False
    return True


class UsernameGenerator:
    """High-performance generator for valuable, pronounceable Telegram usernames."""

    def __init__(self, seed: int | None = None):
        if seed is not None:
            random.seed(seed)

    def generate_pronounceable(self, length: int) -> str:
        """Generate a pronounceable sequence using alternating consonants and vowels."""
        patterns: list[str] = []
        if length == 5:
            patterns = ["CVCVC", "VCCVC", "CVCCV", "VVCVC", "CVCVV"]
        elif length == 6:
            patterns = ["CVCVCV", "CVCCVC", "VCCVCV", "CVCVCC"]
        elif length == 7:
            patterns = ["CVCVCVC", "CVCCVCV", "CVCVCCV"]
        elif length == 8:
            patterns = ["CVCVCVCV", "CVCCVCVC", "CVCVCVCC"]
        else:
            # For 9-12
            res: list[str] = []
            while len(res) < length:
                res.append(random.choice(PREMIUM_CONSONANTS))
                if len(res) < length:
                    res.append(random.choice(PHONETIC_VOWELS))
            return "".join(res[:length])

        pattern: str = random.choice(patterns)
        chars: list[str] = []
        for char_type in pattern:
            if char_type == "C":
                chars.append(random.choice(PREMIUM_CONSONANTS))
            else:
                chars.append(random.choice(PHONETIC_VOWELS))
        return "".join(chars)

    def generate_fixed_length(self, length: int) -> str:
        """Generate name of exact length."""
        # Mix pronounceable and syllable combinations
        if random.random() < 0.65:
            return self.generate_pronounceable(length)
        else:
            syl1 = random.choice(SHORT_SYLLABLES)
            syl2 = random.choice(SHORT_SYLLABLES)
            combined = syl1 + syl2
            if len(combined) == length:
                return combined
            elif len(combined) < length:
                diff = length - len(combined)
                return combined + "".join(random.choices(PHONETIC_CONSONANTS, k=diff))
            else:
                return combined[:length]

    def generate_dictionary_name(self) -> str:
        word = random.choice(DICTIONARY_WORDS).lower()
        if random.random() < 0.15:
            # e.g., 'the' prefix or clean suffix
            variant = random.choice(["the" + word, word + "x", word + "s", word + "hq"])
            if is_valid_telegram_username(variant):
                return variant
        return word

    def generate_financial_name(self) -> str:
        w1 = random.choice(FINANCIAL_WORDS)
        if random.random() < 0.35 and len(w1) >= 5:
            return w1
        # Compound
        w2 = random.choice(["pay", "vault", "fund", "cap", "coin", "link", "hub", "flow", "x", "pro", "desk"])
        res = w1 + w2
        if len(res) > 32:
            res = res[:32]
        return res

    def generate_crypto_name(self) -> str:
        w1 = random.choice(CRYPTO_WORDS)
        if random.random() < 0.35 and len(w1) >= 5:
            return w1
        w2 = random.choice(["ton", "eth", "sol", "dex", "node", "swap", "dao", "pay", "core", "net", "lab", "x"])
        res = w1 + w2
        if len(res) > 32:
            res = res[:32]
        return res

    def generate_tech_name(self) -> str:
        w1 = random.choice(TECH_WORDS)
        if random.random() < 0.35 and len(w1) >= 5:
            return w1
        w2 = random.choice(["dev", "cloud", "code", "net", "sys", "hub", "lab", "grid", "core", "stack", "sync", "io"])
        res = w1 + w2
        return res[:32]

    def generate_gaming_name(self) -> str:
        w1 = random.choice(GAMING_WORDS)
        if random.random() < 0.35 and len(w1) >= 5:
            return w1
        w2 = random.choice(["play", "quest", "loot", "clan", "zone", "arena", "duel", "craft", "hero", "guild", "x"])
        res = w1 + w2
        return res[:32]

    def generate_brand_name(self) -> str:
        p = random.choice(BRAND_PREFIXES)
        s = random.choice(BRAND_SUFFIXES)
        res = p + s
        if len(res) < 5:
            res += random.choice(["x", "o", "a", "s"])
        return res[:32]

    def generate_rare_combination(self) -> str:
        # High value CVCV, VCV, or double syllable patterns with rare premium letters
        syl1 = random.choice(SHORT_SYLLABLES)
        syl2 = random.choice(SHORT_SYLLABLES)
        # Randomly mutate one letter with premium consonants
        variant = syl1 + syl2
        if len(variant) > 6:
            variant = variant[:5]
        return variant

    def generate_by_category(self, category: UsernameCategory) -> str:
        if category == UsernameCategory.FIVE_CHAR:
            return self.generate_fixed_length(5)
        elif category == UsernameCategory.SIX_CHAR:
            return self.generate_fixed_length(6)
        elif category == UsernameCategory.SEVEN_CHAR:
            return self.generate_fixed_length(7)
        elif category == UsernameCategory.EIGHT_CHAR:
            return self.generate_fixed_length(8)
        elif category == UsernameCategory.NINE_TWELVE_CHAR:
            return self.generate_fixed_length(random.randint(9, 12))
        elif category == UsernameCategory.DICTIONARY:
            return self.generate_dictionary_name()
        elif category == UsernameCategory.FINANCE:
            return self.generate_financial_name()
        elif category == UsernameCategory.CRYPTO:
            return self.generate_crypto_name()
        elif category == UsernameCategory.TECH:
            return self.generate_tech_name()
        elif category == UsernameCategory.GAMING:
            return self.generate_gaming_name()
        elif category == UsernameCategory.BRAND:
            return self.generate_brand_name()
        elif category == UsernameCategory.RARE_COMBINATION:
            return self.generate_rare_combination()
        else:
            return self.generate_fixed_length(5)

    def generate_batch(
        self,
        count: int = 100,
        categories: list[UsernameCategory] | None = None,
        min_length: int = 5,
        max_length: int = 32
    ) -> list[tuple[str, str]]:
        """
        Generate a batch of unique, valid usernames across specified categories.
        Returns a list of (username, category_name) tuples.
        """
        if not categories:
            categories = [
                UsernameCategory.FIVE_CHAR,
                UsernameCategory.SIX_CHAR,
                UsernameCategory.SEVEN_CHAR,
                UsernameCategory.DICTIONARY,
                UsernameCategory.FINANCE,
                UsernameCategory.CRYPTO,
                UsernameCategory.TECH,
                UsernameCategory.GAMING,
                UsernameCategory.BRAND,
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

            if min_length <= len(raw) <= max_length and is_valid_telegram_username(raw):
                if raw not in seen:
                    seen.add(raw)
                    results.append((raw, cat.value))

        return results
