"""
HTF Trend Lock and Ambiguity Crusher Engine.
Prevents counter-trend lower-timeframe noise from flipping macro directional bias.
Anchors 1D and 4H structural bias and classifies localized pullbacks/bounces.
"""

from typing import Dict, Any, List


class HTFTrendLockEngine:
    """
    Evaluates 5-tier timeframe hierarchy (1D, 4H, 1H, 15M, 5M).
    Anchors the dominant trend and eliminates false trend flip confusion.
    """

    @staticmethod
    def evaluate_trend_hierarchy(
        daily_trend: str = "BULLISH",
        h4_trend: str = "BULLISH",
        h1_trend: str = "BULLISH",
        m15_trend: str = "NEUTRAL",
        m5_trend: str = "BEARISH",
        technical_score: float = 15.0,
        current_price: float = 2700.0,
        atr_daily: float = 28.0
    ) -> Dict[str, Any]:
        """
        Calculates multi-timeframe synchronization and anchors macro trend.
        """
        tf_weights = {
            "1D": {"trend": daily_trend, "weight": 0.35},
            "4H": {"trend": h4_trend, "weight": 0.30},
            "1H": {"trend": h1_trend, "weight": 0.20},
            "15M": {"trend": m15_trend, "weight": 0.10},
            "5M": {"trend": m5_trend, "weight": 0.05}
        }

        bull_points = 0.0
        bear_points = 0.0

        for tf, data in tf_weights.items():
            t = data["trend"].upper()
            w = data["weight"]
            if "BULL" in t:
                bull_points += w
            elif "BEAR" in t:
                bear_points += w
            else:
                bull_points += w * 0.5
                bear_points += w * 0.5

        sync_score = round(max(bull_points, bear_points) * 100, 1)
        sync_direction = "BULLISH" if bull_points > bear_points else "BEARISH" if bear_points > bull_points else "NEUTRAL"

        # HTF Anchor is determined strictly by 1D and 4H
        if "BULL" in daily_trend.upper() and "BULL" in h4_trend.upper():
            htf_anchor = "STRONG_BULLISH_DOMINANCE"
            htf_bias = "BULLISH"
        elif "BEAR" in daily_trend.upper() and "BEAR" in h4_trend.upper():
            htf_anchor = "STRONG_BEARISH_DOMINANCE"
            htf_bias = "BEARISH"
        elif "BULL" in h4_trend.upper():
            htf_anchor = "MODERATE_BULLISH_BIAS"
            htf_bias = "BULLISH"
        elif "BEAR" in h4_trend.upper():
            htf_anchor = "MODERATE_BEARISH_BIAS"
            htf_bias = "BEARISH"
        else:
            htf_anchor = "CONSOLIDATION_BALANCE"
            htf_bias = "NEUTRAL"

        # Anti-Confusion Classification: Check if lower timeframes conflict with HTF
        is_counter_trend = False
        clarity_label = "FULL_TREND_SYNCHRONIZATION"
        tactical_posture = "TREND_CONTINUATION_ENTRY"

        if htf_bias == "BULLISH":
            if "BEAR" in m15_trend.upper() or "BEAR" in m5_trend.upper():
                is_counter_trend = True
                clarity_label = "HEALTHY_BULLISH_PULLBACK (Buy-the-Dip in Demand)"
                tactical_posture = "WAIT_FOR_5M_BOS_TO_JOIN_MACRO_LONG"
            else:
                clarity_label = "STRONG_BULLISH_EXPANSION"
                tactical_posture = "MOMENTUM_LONG_BREAKOUTS_AND_VWAP_TESTS"
        elif htf_bias == "BEARISH":
            if "BULL" in m15_trend.upper() or "BULL" in m5_trend.upper():
                is_counter_trend = True
                clarity_label = "COUNTER_TREND_RELIEF_RALLY (Sell-the-Rip in Supply)"
                tactical_posture = "WAIT_FOR_5M_REJECTION_TO_JOIN_MACRO_SHORT"
            else:
                clarity_label = "STRONG_BEARISH_EXPANSION"
                tactical_posture = "MOMENTUM_SHORT_BREAKDOWNS_AND_SUPPLY_SWEEPS"
        else:
            clarity_label = "RANGE_BOUND_CHOP_EQUILIBRIUM"
            tactical_posture = "SCALP_RANGE_EXTREMES_ONLY"

        # Ambiguity Crusher Filter
        polarization_pct = abs(bull_points - bear_points) * 100.0
        if polarization_pct < 20.0 and abs(technical_score) < 8.0:
            ambiguity_status = "CHOP_ZONE_DETECTED"
            actionable_directive = "MARKET IN BALANCE: Do NOT chase breakouts. Scalp support/resistance boundaries."
        else:
            ambiguity_status = "CLEAR_DIRECTIONAL_REGIME"
            actionable_directive = f"Follow {htf_bias} order-flow. {tactical_posture}."

        scorecard = [
            {"timeframe": "1D", "trend": daily_trend, "weight_pct": 35, "status": "ALIGNED" if ("BULL" in daily_trend and htf_bias == "BULLISH") or ("BEAR" in daily_trend and htf_bias == "BEARISH") else "CONFLICT"},
            {"timeframe": "4H", "trend": h4_trend, "weight_pct": 30, "status": "ALIGNED" if ("BULL" in h4_trend and htf_bias == "BULLISH") or ("BEAR" in h4_trend and htf_bias == "BEARISH") else "CONFLICT"},
            {"timeframe": "1H", "trend": h1_trend, "weight_pct": 20, "status": "ALIGNED" if ("BULL" in h1_trend and htf_bias == "BULLISH") or ("BEAR" in h1_trend and htf_bias == "BEARISH") else "PULLBACK"},
            {"timeframe": "15M", "trend": m15_trend, "weight_pct": 10, "status": "ALIGNED" if ("BULL" in m15_trend and htf_bias == "BULLISH") or ("BEAR" in m15_trend and htf_bias == "BEARISH") else "LOCAL_PULLBACK"},
            {"timeframe": "5M", "trend": m5_trend, "weight_pct": 5, "status": "ALIGNED" if ("BULL" in m5_trend and htf_bias == "BULLISH") or ("BEAR" in m5_trend and htf_bias == "BEARISH") else "SCALP_NOISE"}
        ]

        return {
            "htf_anchor": htf_anchor,
            "htf_bias": htf_bias,
            "sync_score_pct": sync_score,
            "sync_direction": sync_direction,
            "is_counter_trend": is_counter_trend,
            "clarity_label": clarity_label,
            "tactical_posture": tactical_posture,
            "ambiguity_status": ambiguity_status,
            "actionable_directive": actionable_directive,
            "polarization_pct": round(polarization_pct, 1),
            "scorecard": scorecard
        }
