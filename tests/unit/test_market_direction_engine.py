"""Unit tests for MarketDirectionEngine and evidence contradiction penalty."""
import pytest
from app.analysis.sentiment.market_direction_engine import MarketDirectionEngine

def test_bullish_direction_synthesis():
    engine = MarketDirectionEngine()
    market_analysis = {"price": 2520.0, "technical_score": 45.0, "trend": "BULLISH", "volatility": "NORMAL", "data_quality": "GOOD"}
    liquidity_analysis = {"liquidity_above": [], "liquidity_below": [{"strength": 85.0}]}
    macro_analysis = {"macro_score": 50.0, "usd_score": 60.0, "yield_score": 40.0}
    news_analysis = {"news_score": 40.0}

    result = engine.calculate_direction(
        market_analysis=market_analysis,
        liquidity_analysis=liquidity_analysis,
        macro_analysis=macro_analysis,
        news_analysis=news_analysis,
        economic_events=[]
    )

    assert result["direction"] in ["BULLISH", "STRONGLY BULLISH"]
    assert result["direction_score"] > 20.0
    assert result["confidence"] > 50.0
    assert result["conflict_level"] == "LOW"

def test_contradiction_penalty_reduces_confidence():
    engine = MarketDirectionEngine()
    # Strongly bullish macro (+70) but strongly bearish technicals (-80)
    market_analysis = {"price": 2520.0, "technical_score": -80.0, "trend": "STRONGLY_BEARISH", "volatility": "HIGH", "data_quality": "GOOD"}
    liquidity_analysis = {"liquidity_above": [], "liquidity_below": []}
    macro_analysis = {"macro_score": 70.0, "usd_score": 65.0, "yield_score": 75.0}
    news_analysis = {"news_score": 0.0}

    result = engine.calculate_direction(
        market_analysis=market_analysis,
        liquidity_analysis=liquidity_analysis,
        macro_analysis=macro_analysis,
        news_analysis=news_analysis,
        economic_events=[]
    )

    # Contradictions should be flagged and confidence reduced
    assert len(result["contradicting_factors"]) >= 1
    assert result["confidence"] < 70.0

def test_insufficient_data_handling():
    engine = MarketDirectionEngine()
    market_analysis = {"price": 0.0, "data_quality": "INSUFFICIENT"}
    result = engine.calculate_direction(market_analysis, {}, {}, {}, [])
    assert result["direction"] == "INSUFFICIENT DATA"
