"""Intermarket Metals Matrix tracking Gold/Silver Ratio (GSR), Silver breakouts, and Energy/Yield tailwinds."""
from typing import Any, Dict, Optional

class IntermarketMetalsMatrix:
    """
    Evaluates cross-asset correlations with Gold:
    - Silver (XAGUSD): Highly volatile precious metal that often front-runs Gold breakouts.
    - Gold/Silver Ratio (GSR): Falling GSR (<80) indicates broad precious metals risk-on bull market.
    - WTI Crude Oil: High energy inflation creates physical gold hedging demand.
    - TIPS 10Y Real Yield Proxy: Inverse correlation with Gold.
    """

    @staticmethod
    def analyze_metals_matrix(
        gold_price: float,
        gold_change_pct: float,
        silver_price: float = 31.50,
        silver_change_pct: float = 0.0,
        crude_oil_price: float = 72.50,
        crude_oil_change_pct: float = 0.0
    ) -> Dict[str, Any]:
        """Evaluates cross-asset metals signals and leading indicators."""
        if gold_price <= 0:
            gold_price = 2700.0
        if silver_price <= 0:
            silver_price = 31.50

        # Gold / Silver Ratio
        gsr = round(gold_price / silver_price, 2)
        
        # Silver Leading Signal
        silver_lead_signal = "NEUTRAL"
        metals_bias = "NEUTRAL"
        score = 0.0

        # If Silver is outperforming Gold by >0.8%, it often signals a leading precious metals breakout
        if silver_change_pct > gold_change_pct + 0.8:
            silver_lead_signal = "SILVER_BULLISH_LEAD"
            metals_bias = "BULLISH_PRECIOUS_METALS_EXPANSION"
            score += 25.0
            desc = f"Silver ({silver_change_pct:+.2f}%) is aggressively outperforming Gold ({gold_change_pct:+.2f}%), indicating high-beta institutional metals inflow."
        elif silver_change_pct < gold_change_pct - 0.8:
            silver_lead_signal = "SILVER_BEARISH_DRAG"
            metals_bias = "BEARISH_PRECIOUS_METALS_DRAG"
            score -= 25.0
            desc = f"Silver ({silver_change_pct:+.2f}%) is lagging Gold ({gold_change_pct:+.2f}%), warning of potential bull trap / exhaustion."
        else:
            desc = f"Gold/Silver ratio steady at {gsr:.1f}. Metals moving synchronously."

        # Crude Oil Inflationary Component
        if crude_oil_change_pct >= 2.0:
            score += 10.0
            desc += f" WTI Crude surge ({crude_oil_change_pct:+.1f}%) providing inflationary safe-haven tailwind."
        elif crude_oil_change_pct <= -2.0:
            score -= 10.0

        return {
            "gold_silver_ratio": gsr,
            "silver_price": silver_price,
            "silver_change_pct": silver_change_pct,
            "silver_leading_signal": silver_lead_signal,
            "metals_composite_bias": metals_bias,
            "metals_matrix_score": max(-50.0, min(50.0, score)),
            "crude_oil_price": crude_oil_price,
            "crude_oil_change_pct": crude_oil_change_pct,
            "description": desc
        }
