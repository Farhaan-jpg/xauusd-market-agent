"""Failure simulation tests verifying self-healing and deterministic fallback resilience."""
from unittest.mock import AsyncMock, patch
import pytest
from app.ai.base import AISynthesisOutput
from app.ai.gemini.gemini_provider import GeminiProvider
from app.ai.openrouter.openrouter_provider import OpenRouterProvider
from app.ai.synthesizer import AISynthesizer
from app.config.settings import settings
from app.data.market.market_provider import MarketDataProvider
from app.data.validation import DataValidationError
from app.scheduler.orchestrator import IntelligenceOrchestrator
from app.storage.database import init_db
from app.telegram.bot import TelegramBot

@pytest.mark.asyncio
async def test_simulate_gemini_and_openrouter_outages_recover_to_deterministic():
    """Simulates Gemini HTTP 500 followed by OpenRouter Rate Limit 429."""
    synthesizer = AISynthesizer()

    with patch.object(settings, "GEMINI_API_KEY", "mock_gemini_key"):
        with patch.object(settings, "OPENROUTER_API_KEY", "mock_openrouter_key"):
            with patch.object(GeminiProvider, "synthesize", side_effect=Exception("Simulated Gemini Quota Exceeded (429)")):
                with patch.object(OpenRouterProvider, "synthesize", side_effect=Exception("Simulated OpenRouter Model Unavailable (503)")):
                    output, provider = await synthesizer.synthesize_market_intelligence(
                        market_analysis={"price": 2520.0, "data_quality": "GOOD"},
                        liquidity_analysis={"liquidity_above": [], "liquidity_below": []},
                        macro_analysis={"macro_score": 10.0},
                        news_analysis={"news_score": 0.0},
                        direction_data={"direction": "NEUTRAL", "direction_score": 0.0, "confidence": 50.0, "dominant_drivers": ["Neutral Macro"]},
                        economic_events=[]
                    )

                    # System must seamlessly recover using Deterministic Fallback
                    assert isinstance(output, AISynthesisOutput)
                    assert provider == "Deterministic_Fallback"
                    assert output.direction == "NEUTRAL"

@pytest.mark.asyncio
async def test_simulate_telegram_network_error_graceful_handling():
    """Simulates Telegram API network disconnect."""
    bot = TelegramBot()
    bot.enabled = True
    bot.token = "fake_token"
    bot.chat_id = "fake_chat"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=Exception("Connection reset by peer")):
        # Must return False and log without raising an unhandled exception
        success = await bot.send_message("<b>Test Alert</b>")
        assert success is False

@pytest.mark.asyncio
async def test_simulate_malformed_ai_json_triggers_fallback():
    """Simulates an AI returning invalid JSON syntax."""
    synthesizer = AISynthesizer()
    with patch.object(settings, "GEMINI_API_KEY", "mock_gemini_key"):
        with patch.object(GeminiProvider, "synthesize", side_effect=ValueError("Invalid JSON returned")):
            output, provider = await synthesizer.synthesize_market_intelligence(
                market_analysis={"price": 2520.0, "data_quality": "GOOD"},
                liquidity_analysis={},
                macro_analysis={},
                news_analysis={},
                direction_data={"direction": "NEUTRAL", "direction_score": 0.0, "confidence": 50.0},
                economic_events=[]
            )
            assert isinstance(output, AISynthesisOutput)
            assert provider == "Deterministic_Fallback"

@pytest.mark.asyncio
async def test_full_orchestrator_cycle_with_simulated_market_api_failure():
    """Simulates complete failure of external market data provider."""
    await init_db()
    orchestrator = IntelligenceOrchestrator()

    with patch.object(MarketDataProvider, "fetch", side_effect=Exception("Yahoo Finance Connection Timeout")):
        result = await orchestrator.run_cycle(force_report=False)
        assert "direction" in result
        assert "synthesis" in result
        # Must gracefully report INSUFFICIENT DATA rather than crashing
        assert result["direction"] in ["INSUFFICIENT DATA", "NEUTRAL"]
