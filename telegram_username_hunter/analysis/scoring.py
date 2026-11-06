"""
Telegram Username Hunter PRO
Scoring Engine (0 - 100)
"""
import re
from typing import Any

from telegram_username_hunter.generators.dictionaries import (
    AI_WORDS,
    BRAND_PREFIXES,
    CRYPTO_WORDS,
    DICTIONARY_WORDS,
    FINANCIAL_WORDS,
    FRAGMENT_HISTORICAL_BENCHMARKS,
    GAMING_WORDS,
    TECH_WORDS,
)

VOWELS = set("aeiou")
CONSONANTS = set("bcdfghjklmnpqrstvwxyz")
CLUMSY_CONSONANT_PAIRS = {"qj", "qk", "qx", "qz", "jq", "jx", "jz", "zk", "zx", "zq", "vk", "vq"}
FOUR_CONSONANTS_RE = re.compile(r"[bcdfghjklmnpqrstvwxyz]{4,}")
THREE_CONSONANTS_RE = re.compile(r"[bcdfghjklmnpqrstvwxyz]{3,}")


class UsernameScorer:
    """Calculates potential and attractiveness score (0-100) for usernames and bot names."""

    def calculate_score(
        self,
        username: str,
        category: str = "",
        is_bot: bool = False,
        is_premium_alias: bool = False
    ) -> tuple[int, dict[str, Any]]:
        """
        Calculate score from 0 to 100 with detailed factor breakdown.
        """
        name = username.lower()
        clean_name = name
        # Strip suffix for base analysis if it's a bot or alias
        if is_premium_alias:
            for sfx in ["_app", "_ai", "_game", "_agent", "_gay"]:
                if clean_name.endswith(sfx):
                    clean_name = clean_name[:-len(sfx)]
                    break
        elif is_bot:
            if clean_name.endswith("_bot"):
                clean_name = clean_name[:-4]
            elif clean_name.endswith("bot"):
                clean_name = clean_name[:-3]

        breakdown: dict[str, Any] = {}

        # 1. Length factor (0 - 30 points)
        length = len(clean_name)
        if length <= 4:
            length_pts = 30
        elif length == 5:
            length_pts = 28
        elif length == 6:
            length_pts = 24
        elif length == 7:
            length_pts = 19
        elif length == 8:
            length_pts = 14
        elif length <= 10:
            length_pts = 9
        else:
            length_pts = 4
        breakdown["length_score"] = length_pts

        # 2. Pronounceability factor (0 - 20 points)
        pronounce_pts = 20
        # Deduct for clumsy clusters
        for pair in CLUMSY_CONSONANT_PAIRS:
            if pair in clean_name:
                pronounce_pts -= 5

        # Check vowel ratio
        vowel_count = sum(1 for c in clean_name if c in VOWELS)
        consonant_count = sum(1 for c in clean_name if c in CONSONANTS)
        total_letters = vowel_count + consonant_count

        if total_letters > 0:
            vowel_ratio = vowel_count / total_letters
            if 0.3 <= vowel_ratio <= 0.6:
                pronounce_pts += 0  # Optimal
            elif vowel_ratio == 0 or vowel_ratio == 1.0:
                pronounce_pts -= 10
            else:
                pronounce_pts -= 4

        # Deduct for 3+ consecutive consonants
        if FOUR_CONSONANTS_RE.search(clean_name):
            pronounce_pts -= 8
        elif THREE_CONSONANTS_RE.search(clean_name):
            pronounce_pts -= 4

        pronounce_pts = max(0, min(20, pronounce_pts))
        breakdown["pronounce_score"] = pronounce_pts

        # 3. Dictionary & Semantic Meaning (0 - 20 points)
        semantic_pts = 0
        if clean_name in DICTIONARY_WORDS:
            semantic_pts = 20
        elif any(clean_name.startswith(w) or clean_name.endswith(w) for w in DICTIONARY_WORDS if len(w) >= 4):
            semantic_pts = 14
        elif any(p in clean_name for p in BRAND_PREFIXES):
            semantic_pts = 10
        else:
            semantic_pts = 3
        breakdown["semantic_score"] = semantic_pts

        # 4. Commercial & Niche Attractiveness (0 - 20 points)
        commercial_pts = 0
        cat_lower = category.lower()

        is_finance = any(w in clean_name for w in FINANCIAL_WORDS) or "finance" in cat_lower
        is_crypto = any(w in clean_name for w in CRYPTO_WORDS) or "crypto" in cat_lower
        is_tech = any(w in clean_name for w in TECH_WORDS) or "tech" in cat_lower
        is_ai = any(w in clean_name for w in AI_WORDS) or "ai" in cat_lower
        is_gaming = any(w in clean_name for w in GAMING_WORDS) or "gaming" in cat_lower

        if is_finance:
            commercial_pts = 20
        elif is_crypto:
            commercial_pts = 19
        elif is_ai:
            commercial_pts = 18
        elif is_tech:
            commercial_pts = 16
        elif is_gaming:
            commercial_pts = 15
        elif "brand" in cat_lower:
            commercial_pts = 14
        else:
            commercial_pts = 8

        breakdown["commercial_score"] = commercial_pts

        # 5. Aesthetic & Structure Bonus / Penalties (0 - 10 points)
        aesthetic_pts = 10
        # Digits penalty for luxury brands
        digit_count = sum(1 for c in clean_name if c.isdigit())
        if digit_count > 0:
            aesthetic_pts -= min(6, digit_count * 2)

        # Underscore penalty in base name
        if "_" in clean_name:
            aesthetic_pts -= 4

        # Historical benchmark similarity bonus
        if clean_name in FRAGMENT_HISTORICAL_BENCHMARKS:
            aesthetic_pts += 5
        elif any(bench in clean_name for bench in FRAGMENT_HISTORICAL_BENCHMARKS if len(bench) >= 4):
            aesthetic_pts += 3

        aesthetic_pts = max(0, min(10, aesthetic_pts))
        breakdown["aesthetic_score"] = aesthetic_pts

        # Total Raw Score
        raw_score = length_pts + pronounce_pts + semantic_pts + commercial_pts + aesthetic_pts

        # Category Weighting Modifier
        if "finance" in cat_lower or is_finance or "ai" in cat_lower or is_ai:
            raw_score = int(raw_score * 1.05)
        elif "rare" in cat_lower and length <= 5:
            raw_score = int(raw_score * 1.08)

        final_score = max(0, min(100, raw_score))
        breakdown["final_score"] = final_score
        return final_score, breakdown
