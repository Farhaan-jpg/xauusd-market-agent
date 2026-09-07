"""
Gold / US Dollar Index (DXY) Decoupling & Beta Matrix for XAUUSD.
Detects sovereign safe-haven accumulation regimes when Gold rises alongside the US Dollar.
"""

from typing import Dict, Any


class DollarDecouplingMatrix:
    """
    Measures 24-hour and rolling correlation between Gold and the US Dollar (DXY).
    """

    @staticmethod
    def calculate_decoupling(
        gold_price: float,
        gold_change_pct: float,
        dxy_price: float,
        dxy_change_pct: float,
        rolling_30d_corr: float = -0.72
    ) -> Dict[str, Any]:
        """
        Evaluates normal inverse correlation vs safe-haven positive decoupling.
        """
        # Normal relationship: DXY up -> Gold down, DXY down -> Gold up (negative correlation)
        both_positive = gold_change_pct > 0.1 and dxy_change_pct > 0.1
        both_negative = gold_change_pct < -0.1 and dxy_change_pct < -0.1

        if both_positive:
            regime = "SOVEREIGN_FLIGHT_TO_SAFETY_DECOUPLING"
            correlation_state = "POSITIVE_DECOUPLING (+)"
            intensity = "EXTREME_BULLISH_SAFE_HAVEN"
            narrative = f"Gold (+{gold_change_pct:.2f}%) is rallying simultaneously with DXY (+{dxy_change_pct:.2f}%). Signals urgent institutional safe-haven hedging overcoming currency drag."
        elif both_negative:
            regime = "LIQUIDITY_CONTRACTION_DECOUPLING"
            correlation_state = "NEGATIVE_DECOUPLING (-)"
            intensity = "BEARISH_LIQUIDITY_DRAIN"
            narrative = f"Gold ({gold_change_pct:.2f}%) and DXY ({dxy_change_pct:.2f}%) dropping simultaneously. Signals cash repatriation / systemic de-risking."
        elif dxy_change_pct < -0.1 and gold_change_pct > 0.1:
            regime = "CLASSICAL_DOLLAR_WEAKNESS_EXPANSION"
            correlation_state = "CLASSICAL_INVERSE_CORRELATION (-)"
            intensity = "HEALTHY_BULLISH_FLOW"
            narrative = f"Gold (+{gold_change_pct:.2f}%) capitalizing on broad Dollar weakness (DXY {dxy_change_pct:.2f}%)."
        elif dxy_change_pct > 0.1 and gold_change_pct < -0.1:
            regime = "CLASSICAL_DOLLAR_STRENGTH_COMPRESSION"
            correlation_state = "CLASSICAL_INVERSE_CORRELATION (-)"
            intensity = "BEARISH_CURRENCY_PRESSURE"
            narrative = f"Gold ({gold_change_pct:.2f}%) pressured by surging Greenback strength (DXY +{dxy_change_pct:.2f}%)."
        else:
            regime = "EQUILIBRIUM_NEUTRAL_CORRELATION"
            correlation_state = "NEUTRAL (0.0)"
            intensity = "NEUTRAL"
            narrative = "Gold and Dollar displaying balanced, low-volatility co-movement."

        # Compute synthetic beta: gold return / dxy return
        beta = round(gold_change_pct / dxy_change_pct, 2) if abs(dxy_change_pct) > 0.05 else 1.0

        return {
            "gold_price": gold_price,
            "gold_change_pct": gold_change_pct,
            "dxy_price": dxy_price,
            "dxy_change_pct": dxy_change_pct,
            "correlation_regime": regime,
            "correlation_state": correlation_state,
            "signal_intensity": intensity,
            "gold_dxy_beta": beta,
            "rolling_30d_correlation": rolling_30d_corr,
            "is_sovereign_decoupled": both_positive,
            "narrative": narrative
        }
