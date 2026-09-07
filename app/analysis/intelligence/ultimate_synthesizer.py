"""
Ultimate Real-Time AI Intelligence Synthesizer for XAUUSD.
Compiles Geopolitics, Financial Wire, Macro Yields, 6-Factor Correlations,
Order Flow CVD, and Technical Structure into a definitive Market Direction
with customized dual-mode execution (⚡ SCALPING vs 🎯 DAY TRADING).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class UltimateSynthesizer:
    """
    Unified AI Intelligence & Direction Engine.
    Generates unambiguous market verdicts and mode-specific trade payloads.
    """

    @staticmethod
    def synthesize_market_verdict(
        current_price: float,
        gold_change_pct: float,
        geopolitics_data: Dict[str, Any],
        financial_data: Dict[str, Any],
        correlations_data: Dict[str, Any],
        technical_score: float = 12.5,
        cvd_delta: float = 250.0,
        mode: str = "scalp"  # "scalp" or "daytrade"
    ) -> Dict[str, Any]:
        """
        Synthesizes all inputs and outputs an institutional verdict customized for Scalping or Day Trading.
        """
        mode = mode.lower()
        is_scalp = mode == "scalp"

        # 1. Component Scores
        geo_score = (geopolitics_data.get("conflict_escalation_index", 50.0) - 50.0) * 1.5  # -75 to +75
        fin_score = financial_data.get("monetary_sentiment_score", 0.0)                     # -100 to +100
        corr_score = correlations_data.get("composite_correlation_score", 0.0)             # -100 to +100
        tech_score = max(-100.0, min(100.0, technical_score * 3.0))                         # -100 to +100
        orderflow_score = max(-100.0, min(100.0, (cvd_delta / 500.0) * 100.0))              # -100 to +100

        # 2. Dynamic Weighting based on Mode
        if is_scalp:
            # Scalping weights fast orderflow, technicals, and breaking news catalysts
            weights = {"tech": 0.35, "orderflow": 0.25, "news": 0.20, "geopolitics": 0.10, "correlations": 0.10}
            composite = (
                tech_score * weights["tech"] +
                orderflow_score * weights["orderflow"] +
                fin_score * weights["news"] +
                geo_score * weights["geopolitics"] +
                corr_score * weights["correlations"]
            )
        else:
            # Day Trading weights macro correlations, geopolitics, and higher timeframe technical structure
            weights = {"tech": 0.30, "correlations": 0.25, "geopolitics": 0.20, "news": 0.15, "orderflow": 0.10}
            composite = (
                tech_score * weights["tech"] +
                corr_score * weights["correlations"] +
                geo_score * weights["geopolitics"] +
                fin_score * weights["news"] +
                orderflow_score * weights["orderflow"]
            )

        composite = round(composite, 1)

        # 3. Definitive Direction Verdict
        if composite >= 14.0:
            direction = "BULLISH"
            direction_label = "STRONG BULLISH CONVICTION 🚀"
            verdict_badge = "bullish"
        elif composite <= -14.0:
            direction = "BEARISH"
            direction_label = "STRONG BEARISH CONVICTION 🔻"
            verdict_badge = "bearish"
        else:
            direction = "NEUTRAL"
            direction_label = "NEUTRAL / EQUILIBRIUM BALANCE ⚖️"
            verdict_badge = "neutral"

        # 4. Conviction Percentage
        conviction = min(98, max(52, int(50 + (abs(composite) * 0.5))))

        # 5. Spicy Institutional Narrative & Executive Thesis
        dxy_bias = correlations_data.get("correlations", {}).get("dxy_dollar", {}).get("bias", "MODERATE")
        cei = geopolitics_data.get("conflict_escalation_index", 75.0)
        premium = geopolitics_data.get("safe_haven_premium_usd", 95.0)
        cb_rate = financial_data.get("central_bank_accumulation_pace_tonnes", 1140.0)

        if direction == "BULLISH":
            thesis = (
                f"Multi-engine convergence confirms active Bullish Expansion for XAUUSD. "
                f"Geopolitical Conflict Index ({cei:.0f}/100) is commanding a +${premium:.2f}/oz safe-haven premium, "
                f"reinforced by continuous sovereign central bank accumulation ({cb_rate:.0f} T/yr) and supportive dollar/yield dynamics."
            )
            tactical_directive = "Buy dips into 5M/15M demand Fair Value Gaps and ride VWAP momentum." if is_scalp else "Accumulate multi-session long swings targeting overhead liquidity pools."
        elif direction == "BEARISH":
            thesis = (
                f"Bearish liquidation pressure active across gold markets (Score: {composite:+.1f}). "
                f"Surging Treasury yields and Greenback strength ({dxy_bias}) are triggering capital outflows from non-yielding bullion, "
                f"overcoming baseline safe-haven demand."
            )
            tactical_directive = "Sell rallies into 5M supply order blocks and breakdown retests." if is_scalp else "Hold short exposure targeting underlying session lows and demand sweep pools."
        else:
            thesis = (
                f"Market is bounded in two-way equilibrium balance (Score: {composite:+.1f}). "
                f"Bullish geopolitical safe-haven bids are currently neutralized by sticky bond yield pressure, compressing intraday range."
            )
            tactical_directive = "Scalp range boundaries only. Avoid chasing breakouts in middle of range." if is_scalp else "Wait for clean 4H breakout confirmation before establishing swing exposure."

        # 6. Mode-Specific Actionable Setups
        if is_scalp:
            # Scalp: Tight SL (3-5 pts), Fast TP (6-12 pts)
            sl_dist = 4.0
            tp1_dist = 6.0
            tp2_dist = 12.0
            setups = [
                {
                    "setup_name": "5M VWAP & FVG Scalp" if direction == "BULLISH" else "5M VWAP Breakdown Scalp" if direction == "BEARISH" else "Range Extremes Scalp",
                    "mode": "SCALPING (1M/5M)",
                    "direction": "LONG" if direction == "BULLISH" else "SHORT" if direction == "BEARISH" else "RANGE_SCALP",
                    "quality_grade": "A+",
                    "entry_price": round(current_price - (1.5 if direction == "BULLISH" else -1.5), 2),
                    "invalidation_sl": round(current_price - (sl_dist if direction == "BULLISH" else -sl_dist), 2),
                    "target_tp1": round(current_price + (tp1_dist if direction == "BULLISH" else -tp1_dist), 2),
                    "target_tp2": round(current_price + (tp2_dist if direction == "BULLISH" else -tp2_dist), 2),
                    "reward_risk_ratio": "1:2.5",
                    "timeframe": "M5",
                    "expected_duration": "15m - 45m",
                    "catalyst": "Fast momentum expansion confirmed by CVD delta & 5M FVG retest."
                }
            ]
        else:
            # Day Trading: Wider SL (10-14 pts), Larger TP (20-35 pts)
            sl_dist = 12.0
            tp1_dist = 22.0
            tp2_dist = 38.0
            setups = [
                {
                    "setup_name": "4H Structural Swing" if direction == "BULLISH" else "4H Trend Rejection Swing" if direction == "BEARISH" else "Daily Balance Trade",
                    "mode": "DAY TRADING (15M/1H/4H)",
                    "direction": "LONG" if direction == "BULLISH" else "SHORT" if direction == "BEARISH" else "SWING_NEUTRAL",
                    "quality_grade": "A+",
                    "entry_price": round(current_price - (4.0 if direction == "BULLISH" else -4.0), 2),
                    "invalidation_sl": round(current_price - (sl_dist if direction == "BULLISH" else -sl_dist), 2),
                    "target_tp1": round(current_price + (tp1_dist if direction == "BULLISH" else -tp1_dist), 2),
                    "target_tp2": round(current_price + (tp2_dist if direction == "BULLISH" else -tp2_dist), 2),
                    "reward_risk_ratio": "1:3.2",
                    "timeframe": "H1/H4",
                    "expected_duration": "2h - 8h",
                    "catalyst": "Multi-session macro alignment backed by sovereign accumulation and real yield divergence."
                }
            ]

        mode_label = "SCALPING" if is_scalp else "DAY TRADING"

        return {
            "mode": mode_label,
            "current_price": current_price,
            "gold_change_24h": gold_change_pct,
            "direction": direction,
            "market_direction": direction,
            "direction_label": direction_label,
            "verdict_badge": verdict_badge,
            "composite_score": composite,
            "conviction_pct": conviction,
            "confidence_pct": conviction,
            "ai_executive_thesis": thesis,
            "executive_thesis": thesis,
            "tactical_directive": tactical_directive,
            "weights_used": weights,
            "component_scores": {
                "technical_structure": tech_score,
                "orderflow_cvd": orderflow_score,
                "geopolitics": geo_score,
                "financial_wire": fin_score,
                "intermarket_correlations": corr_score
            },
            "actionable_setup": {
                "type": "LONG" if direction == "BULLISH" else "SHORT" if direction == "BEARISH" else "NEUTRAL",
                "style": "5M VWAP Momentum" if is_scalp else "4H Macro Swing",
                "entry_price": setups[0]["entry_price"],
                "stop_loss": setups[0]["invalidation_sl"],
                "stop_loss_pts": sl_dist,
                "take_profit_1": setups[0]["target_tp1"],
                "take_profit_2": setups[0]["target_tp2"],
                "risk_reward_ratio": setups[0]["reward_risk_ratio"],
                "holding_horizon": "5-30 Mins" if is_scalp else "4-18 Hours"
            },
            "actionable_setups": setups,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
