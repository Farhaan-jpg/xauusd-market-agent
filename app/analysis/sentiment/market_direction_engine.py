"""Market Direction Engine synthesizing multi-factor evidence, conflict penalties, and confidence."""
from typing import Any, Dict, List, Optional
import numpy as np
from app.config.settings import settings
from app.core.logging import logger

class MarketDirectionEngine:
    """Deterministically synthesizes Macro, USD, Yields, News, Technicals, and Liquidity into Market Direction."""

    def calculate_direction(
        self,
        market_analysis: Dict[str, Any],
        liquidity_analysis: Dict[str, Any],
        macro_analysis: Dict[str, Any],
        news_analysis: Dict[str, Any],
        economic_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        # Check data quality
        if market_analysis.get("data_quality") == "INSUFFICIENT" or market_analysis.get("price", 0.0) <= 0:
            return {
                "direction": "INSUFFICIENT DATA",
                "direction_score": 0.0,
                "confidence": 0.0,
                "dominant_drivers": ["Insufficient market data available."],
                "supporting_factors": [],
                "contradicting_factors": [],
                "conflict_level": "HIGH",
                "data_quality": "INSUFFICIENT"
            }

        macro_score = macro_analysis.get("macro_score", 0.0)
        usd_score = macro_analysis.get("usd_score", 0.0)
        yield_score = macro_analysis.get("yield_score", 0.0)
        news_score = news_analysis.get("news_score", 0.0)
        tech_score = market_analysis.get("technical_score", 0.0)
        scalp_score = market_analysis.get("scalp_score", 0.0)
        day_trade_score = market_analysis.get("day_trade_score", 0.0)

        # Liquidity & Order Flow Bias (-100 to +100)
        liq_above = liquidity_analysis.get("liquidity_above", [])
        liq_below = liquidity_analysis.get("liquidity_below", [])
        order_flow_bias = liquidity_analysis.get("order_flow_bias", "")
        liq_score = 0.0
        
        if order_flow_bias == "BEARISH_ORDER_FLOW":
            liq_score -= 20.0
        elif order_flow_bias == "BULLISH_ORDER_FLOW":
            liq_score += 20.0
            
        if liq_below and (not liq_above or liq_below[0]["strength"] > liq_above[0]["strength"]):
            liq_score += 15.0  # Strong support cluster below
        elif liq_above and (not liq_below or liq_above[0]["strength"] > liq_below[0]["strength"]):
            liq_score -= 15.0  # Strong overhead resistance cluster above

        liq_score = max(-100.0, min(100.0, liq_score))

        # Rebalanced Weighted Synthesis Optimized for Day Trading & Scalping:
        # Technical Price Action (50%), Real-Time News (20%), Intraday Liquidity/Order-Flow (15%), Macro Backdrop (15%)
        raw_score = (
            (tech_score * 0.50) +
            (news_score * 0.20) +
            (liq_score * 0.15) +
            (macro_score * 0.05) +
            (usd_score * 0.05) +
            (yield_score * 0.05)
        )

        raw_score = max(-100.0, min(100.0, raw_score))

        # Check for contradictions between key pillars
        contradictions = []
        supporting = []
        dominant_drivers = []

        factors = [
            ("Technical Structure & Momentum", tech_score),
            ("Real-Time News Catalyst", news_score),
            ("Intraday Liquidity & Order Flow", liq_score),
            ("US Dollar Dynamics", usd_score),
            ("Treasury Yields", yield_score),
            ("Macro Backdrop", macro_score)
        ]

        for name, score in factors:
            if abs(score) >= 15.0:
                if (raw_score > 0 and score > 0) or (raw_score < 0 and score < 0):
                    supporting.append(f"{name} aligns with direction ({score:+.1f})")
                elif (raw_score > 0 and score < -15.0) or (raw_score < 0 and score > 15.0):
                    contradictions.append(f"{name} opposes direction ({score:+.1f})")

        # Proportional conflict penalty (4.0 per opposing pillar, capped at 12.0)
        conflict_penalty = min(12.0, len(contradictions) * 4.0)
        # Base confidence scales with directional conviction (60% to 95%)
        base_confidence = min(95.0, 60.0 + (abs(raw_score) * 0.38))
        final_confidence = max(45.0, base_confidence - conflict_penalty)

        # Responsive Day Trading / Scalping Directional Label
        if raw_score >= 45.0:
            direction = "STRONGLY BULLISH"
        elif raw_score >= 10.0:
            direction = "BULLISH"
        elif raw_score <= -45.0:
            direction = "STRONGLY BEARISH"
        elif raw_score <= -10.0:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

        # Dominant drivers selection
        sorted_by_abs = sorted(factors, key=lambda x: abs(x[1]), reverse=True)
        for name, score in sorted_by_abs[:3]:
            if abs(score) >= 10.0:
                bias_str = "supportive for gold" if score > 0 else "headwind / sell pressure for gold"
                dominant_drivers.append(f"{name} ({score:+.1f}): {bias_str}")

        if not dominant_drivers:
            dominant_drivers.append("Balanced conditions across intraday technicals and macroeconomic indicators.")

        return {
            "direction": direction,
            "direction_score": round(raw_score, 1),
            "confidence": round(final_confidence, 1),
            "technical_score": round(tech_score, 1),
            "scalp_score": round(scalp_score, 1),
            "day_trade_score": round(day_trade_score, 1),
            "scalp_bias": market_analysis.get("scalp_bias", "SCALP_RANGING_CONSOLIDATION"),
            "day_trade_bias": market_analysis.get("day_trade_bias", "DAY_TRADE_RANGING"),
            "market_structure": market_analysis.get("market_structure", "RANGING"),
            "news_score": round(news_score, 1),
            "liquidity_score": round(liq_score, 1),
            "macro_score": round(macro_score, 1),
            "usd_score": round(usd_score, 1),
            "yield_score": round(yield_score, 1),
            "dominant_drivers": dominant_drivers,
            "supporting_factors": supporting,
            "contradicting_factors": contradictions,
            "conflict_level": "HIGH" if len(contradictions) >= 2 else "MODERATE" if len(contradictions) == 1 else "LOW",
            "data_quality": "GOOD"
        }
