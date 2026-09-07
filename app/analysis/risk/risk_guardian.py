"""Daily Volatility & Over-Trading Risk Guardian monitoring ADR exhaustion and low-volatility chop."""
from typing import Any, Dict, Optional

class RiskGuardian:
    """
    Guards scalpers and day traders against unfavorable market conditions:
    1. ADR % Exhaustion: If daily range already exceeds 110% ADR, breakout chasing risk is very high.
    2. Chop / Low Volatility: If 5m ATR is too compressed, tight scalp stop hunting is rampant.
    3. Trade Readiness Status: GREEN (Ideal), YELLOW (Caution / Reduced Size), RED (High Risk / Cooldown).
    """

    @staticmethod
    def evaluate_risk(
        day_high: float,
        day_low: float,
        current_price: float,
        adr: float = 24.5,
        atr_5m: float = 2.5,
        is_news_lockout: bool = False
    ) -> Dict[str, Any]:
        """Calculates ADR exhaustion percentage and trading safety tier."""
        daily_range = max(0.1, day_high - day_low) if (day_high > 0 and day_low > 0) else 15.0
        adr = max(10.0, adr)
        
        adr_pct = round((daily_range / adr) * 100.0, 1)

        status = "GREEN"
        status_label = "OPTIMAL_TRADING_CONDITIONS"
        warnings = []

        if is_news_lockout:
            status = "RED"
            status_label = "PRE_NEWS_LOCKOUT_ACTIVE"
            warnings.append("Tier-1 economic event within 15 minutes. High slippage & spread expansion risk.")

        elif adr_pct >= 115.0:
            status = "YELLOW"
            status_label = "ADR_EXHAUSTED"
            warnings.append(f"Day range ({daily_range:.2f} pts) has consumed {adr_pct}% of ADR ({adr:.2f} pts). Reversal risk elevated; avoid chasing breakouts.")

        elif atr_5m < 1.0:
            status = "YELLOW"
            status_label = "LOW_VOLATILITY_CHOP"
            warnings.append(f"5M ATR is compressed (${atr_5m:.2f}). Market in low-liquidity consolidation.")

        return {
            "risk_status": status,
            "status_label": status_label,
            "daily_range": round(daily_range, 2),
            "adr": round(adr, 2),
            "adr_exhaustion_pct": adr_pct,
            "atr_5m": round(atr_5m, 2),
            "is_trade_recommended": status == "GREEN",
            "warnings": warnings,
            "guidance": "Trade normal position sizing." if status == "GREEN" else \
                        "Reduce position sizing by 50% or take quick profits at TP1." if status == "YELLOW" else \
                        "Step aside and wait for post-news stability."
        }
