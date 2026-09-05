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
    """Multi-tiered synthesis engine with automatic fallback routing across Gemini, OpenRouter, and Deterministic Engine."""

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

        # Determine priority order
        if settings.AI_PRIORITY == "openrouter_first":
            tier_order = [
                ("OpenRouter", self.openrouter, settings.has_openrouter),
                ("Google_Gemini", self.gemini, settings.has_gemini)
            ]
        elif settings.AI_PRIORITY == "deterministic_only":
            tier_order = []
        else: # gemini_first (default)
            tier_order = [
                ("Google_Gemini", self.gemini, settings.has_gemini),
                ("OpenRouter", self.openrouter, settings.has_openrouter)
            ]

        for provider_name, provider_instance, is_configured in tier_order:
            if not is_configured:
                continue

            try:
                logger.info(f"Attempting AI synthesis via primary/secondary tier: {provider_name}...")
                output = await provider_instance.synthesize(payload)
                await Repository.update_provider_health(provider_name, is_healthy=True)
                return output, provider_name
            except Exception as e:
                logger.warning(f"AI Tier '{provider_name}' failed completely ({e}). Cascading to next fallback tier...")
                await Repository.update_provider_health(provider_name, is_healthy=False, error_message=str(e))

        # Safe Deterministic Fallback Mode (Runs when all remote AI providers fail or are unconfigured/rate-limited)
        logger.info("Engaging Safe Deterministic Fallback Engine for synthesis.")
        output = await self.fallback.synthesize(payload)
        await Repository.update_provider_health("Deterministic_Fallback", is_healthy=True)
        return output, "Deterministic_Fallback"
