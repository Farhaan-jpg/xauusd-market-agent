"""Unit tests for weekend pause detection and executive final market verdict synthesis."""
from datetime import datetime, timezone
import pytest
from app.ai.fallback.deterministic_fallback import DeterministicFallbackProvider
from app.alerts.templates import AlertTemplates
from app.scheduler.orchestrator import is_weekend_market_closed

def test_weekend_market_closed_detection():
    # Friday 21:00 UTC -> Open
    fri_open = datetime(2026, 9, 4, 21, 0, 0, tzinfo=timezone.utc)
    assert is_weekend_market_closed(fri_open) is False

    # Friday 22:30 UTC -> Closed
    fri_closed = datetime(2026, 9, 4, 22, 30, 0, tzinfo=timezone.utc)
    assert is_weekend_market_closed(fri_closed) is True

    # Saturday 14:00 UTC -> Closed
    sat_closed = datetime(2026, 9, 5, 14, 0, 0, tzinfo=timezone.utc)
    assert is_weekend_market_closed(sat_closed) is True

    # Sunday 20:00 UTC -> Closed
    sun_closed = datetime(2026, 9, 6, 20, 0, 0, tzinfo=timezone.utc)
    assert is_weekend_market_closed(sun_closed) is True

    # Sunday 22:30 UTC -> Open
    sun_open = datetime(2026, 9, 6, 22, 30, 0, tzinfo=timezone.utc)
    assert is_weekend_market_closed(sun_open) is False

    # Tuesday 10:00 UTC -> Open
    tue_open = datetime(2026, 9, 8, 10, 0, 0, tzinfo=timezone.utc)
    assert is_weekend_market_closed(tue_open) is False

@pytest.mark.asyncio
async def test_deterministic_final_verdict_synthesis():
    provider = DeterministicFallbackProvider()
    structured_input = {
        "market": {"price": 2515.50, "technical_score": 40.0, "trend": "BULLISH", "volatility": "NORMAL", "data_quality": "GOOD"},
        "liquidity": {"liquidity_above": [], "liquidity_below": []},
        "macro": {"macro_score": 50.0},
        "news": {"news_score": 30.0},
        "direction": {
            "direction": "BULLISH",
            "direction_score": 38.0,
            "confidence": 75.0,
            "dominant_drivers": ["Macro tailwinds", "Technical breakout"],
            "supporting_factors": ["USD softening"],
            "contradicting_factors": []
        },
        "economic_events": []
    }

    output = await provider.synthesize(structured_input)

    assert output.final_market_verdict == "BULLISH"
    assert "BULL" in output.executive_verdict_summary.upper()
    assert len(output.executive_verdict_summary) > 20

def test_periodic_report_template_with_verdict():
    msg = AlertTemplates.periodic_report(
        price=2515.50,
        direction="BULLISH",
        score=38.0,
        confidence=75.0,
        macro_score=50.0,
        usd_score=40.0,
        yield_score=30.0,
        news_score=20.0,
        tech_score=40.0,
        trend="BULLISH",
        volatility="NORMAL",
        liquidity_above=[],
        liquidity_below=[],
        dominant_drivers=["Macro tailwinds"],
        macro_summary="Macro environment is favorable.",
        news_summary="News is positive.",
        risk_factors="Watch yields.",
        upcoming_events=[],
        provider_used="Safe Deterministic Engine",
        final_market_verdict="BULLISH",
        executive_verdict_summary="Overall market is in a confirmed BULL market phase."
    )

    assert "FINAL MARKET VERDICT" in msg
    assert "BULL MARKET" in msg
    assert "EXECUTIVE ANALYSIS" in msg
