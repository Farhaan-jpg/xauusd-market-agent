"""Deterministic Fallback AI Provider requiring zero external API keys."""
from typing import Any, Dict, List
from app.ai.base import AISynthesisOutput, BaseAIProvider
from app.core.logging import logger

class DeterministicFallbackProvider(BaseAIProvider):
    """Generates structured market intelligence reports using deterministic rule-based algorithms."""

    def __init__(self):
        super().__init__(name="Deterministic_Fallback")

    async def synthesize(self, structured_input: Dict[str, Any]) -> AISynthesisOutput:
        market = structured_input.get("market", {})
        macro = structured_input.get("macro", {})
        news = structured_input.get("news", {})
        liquidity = structured_input.get("liquidity", {})
        direction_data = structured_input.get("direction", {})

        direction = direction_data.get("direction", "NEUTRAL")
        score = direction_data.get("direction_score", 0.0)
        confidence = direction_data.get("confidence", 50.0)
        dominant_drivers = direction_data.get("dominant_drivers", [])
        supporting = direction_data.get("supporting_factors", [])
        contradicting = direction_data.get("contradicting_factors", [])

        # Format Liquidity Summary
        liq_summary = []
        above = liquidity.get("liquidity_above", [])
        below = liquidity.get("liquidity_below", [])
        if above:
            top_a = above[0]
            liq_summary.append(f"Primary overhead resistance: ${top_a['price']:.2f} ({top_a['zone_type']}, strength {top_a['strength']:.0f}/100)")
        if below:
            top_b = below[0]
            liq_summary.append(f"Primary underlying support: ${top_b['price']:.2f} ({top_b['zone_type']}, strength {top_b['strength']:.0f}/100)")
        if not liq_summary:
            liq_summary.append("No dense liquidity clusters detected within immediate 1% range.")

        # Format Macro Summary
        dxy_chg = macro.get("dxy_change_pct", 0.0)
        y10 = macro.get("us10y_yield", 0.0)
        y2 = macro.get("us2y_yield", 0.0)
        vix = macro.get("vix", 15.0)

        usd_state = "softening" if dxy_chg < -0.1 else "strengthening" if dxy_chg > 0.1 else "range-bound"
        macro_summary = (
            f"The US Dollar is {usd_state} ({dxy_chg:+.2f}%), with US 10Y yields at {y10:.2f}% and 2Y yields at {y2:.2f}%. "
            f"VIX is trading at {vix:.1f}. Macro conditions are classified as {macro.get('macro_condition', 'NEUTRAL').replace('_', ' ')}."
        )

        # Format News Summary
        headlines = news.get("top_headlines", [])
        if headlines:
            top_titles = [h["title"] for h in headlines[:2]]
            news_summary = f"Recent news focus includes: {' | '.join(top_titles)}. Net news sentiment score is {news.get('news_score', 0.0):+.1f}."
        else:
            news_summary = "No major market-moving news headlines detected in the current monitoring window."

        # Determine simplified clean final verdict (BULLISH, BEARISH, NEUTRAL)
        if "BULLISH" in direction:
            final_verdict = "BULLISH"
            verdict_desc = f"Overall market evidence indicates a BULLISH posture (Score: {score:+.1f}, Confidence: {confidence:.0f}%). Supportive factors across macro/yields and technical momentum favor upward expansion."
        elif "BEARISH" in direction:
            final_verdict = "BEARISH"
            verdict_desc = f"Overall market evidence indicates a BEARISH posture (Score: {score:+.1f}, Confidence: {confidence:.0f}%). Prevailing headwinds across USD strength, yields, and resistance structure constrain upward price potential."
        else:
            final_verdict = "NEUTRAL"
            verdict_desc = f"Overall market evidence indicates a NEUTRAL / CONSOLIDATION posture (Score: {score:+.1f}, Confidence: {confidence:.0f}%). Drivers are balanced with competing forces across macroeconomic signals and technical ranges."

        # Risk factors
        risk_factors = (
            f"Key watchpoints include upcoming economic data releases, shifts in Treasury yields, "
            f"and sudden geopolitical developments. Evidence conflict is {direction_data.get('conflict_level', 'LOW')}."
        )

        return AISynthesisOutput(
            direction=direction,
            score=score,
            confidence=confidence,
            final_market_verdict=final_verdict,
            executive_verdict_summary=verdict_desc,
            dominant_drivers=dominant_drivers,
            supporting_factors=supporting,
            contradicting_factors=contradicting,
            liquidity_summary=liq_summary,
            macro_summary=macro_summary,
            news_summary=news_summary,
            risk_factors=risk_factors,
            data_quality=market.get("data_quality", "GOOD")
        )
