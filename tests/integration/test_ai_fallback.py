"""Integration tests verifying AI fallback progression to Deterministic Synthesis."""
import pytest
from app.ai.base import AISynthesisOutput
from app.ai.fallback.deterministic_fallback import DeterministicFallbackProvider
from app.ai.synthesizer import AISynthesizer

@pytest.mark.asyncio
async def test_deterministic_fallback_output():
    fallback = DeterministicFallbackProvider()
    input_data = {
        "market": {"price": 2515.0, "data_quality": "GOOD"},
        "macro": {"dxy_change_pct": -0.25, "us10y_yield": 4.10, "us2y_yield": 4.00, "macro_condition": "SUPPORTIVE"},
        "news": {"news_score": 35.0, "top_headlines": [{"title": "Fed rate cut expectations boost Gold"}]},
        "liquidity": {
            "liquidity_above": [{"price": 2530.0, "zone_type": "PDH", "strength": 85.0}],
            "liquidity_below": [{"price": 2500.0, "zone_type": "PDL", "strength": 88.0}]
        },
        "direction": {
            "direction": "BULLISH",
            "direction_score": 48.0,
            "confidence": 75.0,
            "dominant_drivers": ["Weakening USD", "Supportive rate environment"],
            "supporting_factors": ["Macro aligns with direction"],
            "contradicting_factors": []
        }
    }

    result = await fallback.synthesize(input_data)
    assert isinstance(result, AISynthesisOutput)
    assert result.direction == "BULLISH"
    assert result.score == 48.0
    assert result.confidence == 75.0
    assert len(result.dominant_drivers) >= 1
    assert "2530.00" in result.liquidity_summary[0]
    assert "2500.00" in result.liquidity_summary[1]

@pytest.mark.asyncio
async def test_synthesizer_falls_back_when_no_keys():
    synthesizer = AISynthesizer()
    market_analysis = {"price": 2515.0, "data_quality": "GOOD"}
    liquidity_analysis = {"liquidity_above": [], "liquidity_below": []}
    macro_analysis = {"macro_score": 25.0}
    news_analysis = {"news_score": 10.0}
    direction_data = {"direction": "BULLISH", "direction_score": 30.0, "confidence": 65.0, "dominant_drivers": ["Macro"]}

    output, provider = await synthesizer.synthesize_market_intelligence(
        market_analysis,
        liquidity_analysis,
        macro_analysis,
        news_analysis,
        direction_data,
        []
    )

    assert isinstance(output, AISynthesisOutput)
    # When no API keys exist, provider should safely be Deterministic_Fallback
    assert provider == "Deterministic_Fallback"
