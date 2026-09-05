"""AI Synthesizer orchestrating Gemini, OpenRouter, and Deterministic Fallback."""
from typing import Any, Dict, Tuple
from app.ai.base import AISynthesisOutput
from app.ai.fallback.deterministic_fallback import DeterministicFallbackProvider
from app.ai.gemini.gemini_provider import GeminiProvider
from app.ai.openrouter.openrouter_provider import OpenRouterProvider
from app.config.settings import settings
from app.core.logging import logger
from app.storage.repository import Repository

class AISynthesizer:
    """Multi-tiered synthesis engine with automatic fallback routing."""

    def __init__(self):
        self.gemini = GeminiProvider()
        self.openrouter = OpenRouterProvider()
        self.fallback = DeterministicFallbackProvider()

    async def synthesize_market_intelligence(
        self,
        market_analysis: Dict[str, Any],
        liquidity_analysis: Dict[str, Any],
        macro_analysis: Dict[str, Any],
        news_analysis: Dict[str, Any],
        direction_data: Dict[str, Any],
        economic_events: list
    ) -> Tuple[AISynthesisOutput, str]:
        """Runs multi-tiered synthesis and returns (result, provider_name)."""
        payload = {
            "gold_price": market_analysis.get("price"),
            "market": market_analysis,
            "liquidity": {
                "liquidity_above": liquidity_analysis.get("liquidity_above", []),
                "liquidity_below": liquidity_analysis.get("liquidity_below", []),
                "active_sessions": liquidity_analysis.get("active_sessions", [])
            },
            "macro": macro_analysis,
            "news": {
                "news_score": news_analysis.get("news_score"),
                "top_headlines": news_analysis.get("top_headlines", [])
            },
            "direction": direction_data,
            "upcoming_events": [e for e in economic_events[:3]]
        }

        # 1. Check Gemini Primary
        if settings.has_gemini and settings.AI_PRIORITY in ["gemini_first", "auto"]:
            try:
                output = await self.gemini.synthesize(payload)
                await Repository.update_provider_health("Google_Gemini", is_healthy=True)
                return output, "Google_Gemini"
            except Exception as e:
                logger.warning(f"Primary AI Gemini failed: {e}. Falling back to OpenRouter...")
                await Repository.update_provider_health("Google_Gemini", is_healthy=False, error_message=str(e))

        # 2. Check OpenRouter Secondary
        if settings.has_openrouter:
            try:
                output = await self.openrouter.synthesize(payload)
                await Repository.update_provider_health("OpenRouter", is_healthy=True)
                return output, "OpenRouter"
            except Exception as e:
                logger.warning(f"Secondary AI OpenRouter failed: {e}. Falling back to Deterministic Mode...")
                await Repository.update_provider_health("OpenRouter", is_healthy=False, error_message=str(e))

        # 3. Safe Deterministic Fallback Mode
        logger.info("Using Deterministic Fallback Engine for synthesis.")
        output = await self.fallback.synthesize(payload)
        await Repository.update_provider_health("Deterministic_Fallback", is_healthy=True)
        return output, "Deterministic_Fallback"
