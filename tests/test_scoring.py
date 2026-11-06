"""
Tests for Scoring Engine & Auction Eligibility
"""
from telegram_username_hunter.analysis.scoring import UsernameScorer
from telegram_username_hunter.analysis.auction_eligibility import AuctionEligibilityAnalyzer
from telegram_username_hunter.analysis.market_analysis import MarketPotentialAnalyzer
from telegram_username_hunter.config.settings import (
    UsernameStatus,
    BotStatus,
    PremiumBotStatus,
    AuctionEligibility,
)


def test_scoring_bounds_and_structure():
    scorer = UsernameScorer()

    # Short dictionary / luxury name
    score_apex, bd_apex = scorer.calculate_score("apex", category="brand")
    assert 0 <= score_apex <= 100
    assert score_apex >= 70

    # Long random clumsy string
    score_clumsy, _bd_clumsy = scorer.calculate_score("qkzxjqwerty998", category="random")
    assert 0 <= score_clumsy <= 100
    assert score_clumsy < score_apex

    # Breakdown keys exist
    for key in ("length_score", "pronounce_score", "semantic_score", "commercial_score", "aesthetic_score"):
        assert key in bd_apex


def test_scoring_categories_weighting():
    scorer = UsernameScorer()
    # Financial keyword
    score_pay, _ = scorer.calculate_score("payvault", category="finance")
    score_rand, _ = scorer.calculate_score("plkvdfrt", category="other")
    assert score_pay > score_rand

    # AI category
    score_ai, _ = scorer.calculate_score("aimind", category="ai", is_premium_alias=True)
    assert score_ai > 0

    # Bot name scoring
    score_bot, _ = scorer.calculate_score("qevrobot", category="tech", is_bot=True)
    assert score_bot > 0


def test_auction_eligibility_analyzer():
    # 1. Confirmed collectible
    item_type, elig, _ = AuctionEligibilityAnalyzer.analyze_regular_username(
        "news", UsernameStatus.COLLECTIBLE.value, {"is_collectible": True}
    )
    assert item_type == "COLLECTIBLE_USERNAME"
    assert elig == AuctionEligibility.AUCTION_ELIGIBLE.value

    # 2. Available regular username
    item_type, elig, _ = AuctionEligibilityAnalyzer.analyze_regular_username(
        "qevro", UsernameStatus.AVAILABLE_TO_CLAIM.value, {"is_collectible": False}
    )
    assert item_type == "BASIC_USERNAME"
    assert elig == AuctionEligibility.AUCTION_NOT_SUPPORTED.value

    # 3. Taken regular username
    item_type, elig, _ = AuctionEligibilityAnalyzer.analyze_regular_username(
        "taken_name", UsernameStatus.TAKEN.value, {}
    )
    assert elig == AuctionEligibility.AUCTION_NOT_SUPPORTED.value

    # 4. Reserved or Invalid
    item_type, elig, _ = AuctionEligibilityAnalyzer.analyze_regular_username(
        "res", UsernameStatus.RESERVED.value, {}
    )
    assert elig == AuctionEligibility.AUCTION_NOT_SUPPORTED.value

    # 5. Unknown status
    item_type, elig, _ = AuctionEligibilityAnalyzer.analyze_regular_username(
        "unknown_name", UsernameStatus.UNKNOWN.value, {}
    )
    assert elig == AuctionEligibility.AUCTION_UNKNOWN.value

    # 6. Bot username collectible vs normal
    item_type, elig, _ = AuctionEligibilityAnalyzer.analyze_bot_username(
        "cryptobot", BotStatus.AVAILABLE_FOR_BOT.value, {"is_collectible": True}
    )
    assert elig == AuctionEligibility.AUCTION_ELIGIBLE.value

    item_type, elig, _ = AuctionEligibilityAnalyzer.analyze_bot_username(
        "cryptobot", BotStatus.AVAILABLE_FOR_BOT.value, {"is_collectible": False}
    )
    assert elig == AuctionEligibility.AUCTION_NOT_SUPPORTED.value

    # 7. Premium bot alias
    item_type, elig, _ = AuctionEligibilityAnalyzer.analyze_premium_alias(
        "qevro_app", PremiumBotStatus.ELIGIBLE_FOR_ASSIGNMENT.value, {}
    )
    assert item_type == "PREMIUM_BOT_ALIAS"
    assert elig == AuctionEligibility.AUCTION_NOT_SUPPORTED.value


def test_market_potential_analyzer():
    # Tier 1
    p1 = MarketPotentialAnalyzer.get_market_profile("crypto", 95)
    assert "TIER 1" in p1["potential_tier"]
    assert p1["benchmark_match"] is not None

    # Tier 2
    p2 = MarketPotentialAnalyzer.get_market_profile("payvault", 85)
    assert "TIER 2" in p2["potential_tier"]

    # Tier 3
    p3 = MarketPotentialAnalyzer.get_market_profile("goodbot", 72)
    assert "TIER 3" in p3["potential_tier"]

    # Tier 4
    p4 = MarketPotentialAnalyzer.get_market_profile("mediumname", 55)
    assert "TIER 4" in p4["potential_tier"]

    # Tier 5
    p5 = MarketPotentialAnalyzer.get_market_profile("clumsylongname999", 30)
    assert "TIER 5" in p5["potential_tier"]
