"""Macro Engine analyzing DXY, Treasury Yields, Real Yield proxy, and Fed policy expectations."""
from typing import Any, Dict, Optional
from app.core.logging import logger

class MacroEngine:
    """Evaluates macroeconomic indicators and calculates macro & USD/Yield scores."""

    def analyze(self, macro_data: Dict[str, Any]) -> Dict[str, Any]:
        dxy = macro_data.get("dxy", {})
        us10y = macro_data.get("us10y", {})
        us2y = macro_data.get("us2y", {})
        tip = macro_data.get("tip", {})
        vix = macro_data.get("vix", {})

        dxy_chg = dxy.get("change_pct", 0.0)
        us10y_chg = us10y.get("change_pct", 0.0)
        us2y_chg = us2y.get("change_pct", 0.0)
        tip_chg = tip.get("change_pct", 0.0)
        vix_price = vix.get("price", 15.0)

        # 1. USD Score (Impact on Gold: Falling USD = Bullish for Gold)
        # Invert DXY change: -0.5% DXY gives +50 to gold bullishness
        usd_score = max(-100.0, min(100.0, -dxy_chg * 100.0))

        # 2. Yield Score (Impact on Gold: Falling yields = Bullish for Gold)
        avg_yield_chg = (us10y_chg + us2y_chg) / 2.0
        yield_score = max(-100.0, min(100.0, -avg_yield_chg * 50.0))

        # 3. Real Yield / TIPS Score (Rising TIPS ETF = Falling real yields = Bullish for Gold)
        real_yield_score = max(-100.0, min(100.0, tip_chg * 100.0))

        # 4. Risk / Geopolitical Score (VIX > 20 indicates flight to safety)
        risk_score = 0.0
        if vix_price > 25.0:
            risk_score = 60.0
        elif vix_price > 20.0:
            risk_score = 30.0
        elif vix_price < 13.0:
            risk_score = -20.0  # Complacent market, less safe-haven demand

        # Aggregate Macro Score (-100 to +100)
        # 35% USD, 35% Yields, 20% Real Yields, 10% Risk
        macro_score = (0.35 * usd_score) + (0.35 * yield_score) + (0.20 * real_yield_score) + (0.10 * risk_score)
        macro_score = max(-100.0, min(100.0, round(macro_score, 1)))

        macro_condition = "STRONGLY_SUPPORTIVE" if macro_score >= 50.0 else \
                          "SUPPORTIVE" if macro_score >= 15.0 else \
                          "STRONGLY_HEADWIND" if macro_score <= -50.0 else \
                          "HEADWIND" if macro_score <= -15.0 else "NEUTRAL"

        return {
            "macro_score": macro_score,
            "usd_score": round(usd_score, 1),
            "yield_score": round(yield_score, 1),
            "real_yield_score": round(real_yield_score, 1),
            "risk_score": round(risk_score, 1),
            "macro_condition": macro_condition,
            "dxy_change_pct": dxy_chg,
            "us10y_yield": us10y.get("yield_pct", 0.0),
            "us2y_yield": us2y.get("yield_pct", 0.0),
            "yield_spread_10y_2y": macro_data.get("yield_spread_10y_2y", 0.0),
            "vix": vix_price
        }
