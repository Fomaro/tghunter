"""
Telegram Username Hunter PRO
Market Potential and Benchmark Analysis
"""
from typing import Any

from telegram_username_hunter.generators.dictionaries import (
    FRAGMENT_HISTORICAL_BENCHMARKS,
)


class MarketPotentialAnalyzer:
    """Provides market context and historical benchmarks for discovered usernames."""

    @classmethod
    def get_market_profile(cls, username: str, score: int) -> dict[str, Any]:
        clean = username.lower().replace("_bot", "").replace("bot", "")
        for sfx in ["_app", "_ai", "_game", "_agent", "_gay"]:
            if clean.endswith(sfx):
                clean = clean[:-len(sfx)]
                break

        benchmark_match = FRAGMENT_HISTORICAL_BENCHMARKS.get(clean)
        similar_benchmarks = []
        for name, data in FRAGMENT_HISTORICAL_BENCHMARKS.items():
            if name in clean or clean in name:
                similar_benchmarks.append({
                    "name": name,
                    "price_ton": data["price_ton"],
                    "category": data["category"]
                })

        # Potential classification
        if score >= 90:
            potential_tier = "LEGENDARY / TIER 1"
            description = "Exceptional brand appeal, maximum rarity or high-tier dictionary word."
        elif score >= 80:
            potential_tier = "HIGH POTENTIAL / TIER 2"
            description = "High liquidity potential, strong commercial keyword or clean 5-char combination."
        elif score >= 70:
            potential_tier = "ATTRACTIVE / TIER 3"
            description = "Solid commercial or brandable name, well suited for niche projects or bot branding."
        elif score >= 50:
            potential_tier = "MODERATE / TIER 4"
            description = "Average memorability, standard utility username."
        else:
            potential_tier = "LOW / TIER 5"
            description = "Longer or less pronounceable name, limited resale interest."

        return {
            "potential_tier": potential_tier,
            "description": description,
            "benchmark_match": benchmark_match,
            "similar_benchmarks": similar_benchmarks[:3],
            "price_disclaimer": "Valuation tier is an algorithmic estimate based on linguistic & structural metrics. No guaranteed market price."
        }
