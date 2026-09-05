"""Macroeconomic 'What-If' Scenario Simulator for XAUUSD shock modeling."""
from typing import Any, Dict, Optional

class MacroScenarioSimulator:
    """Simulates real-time price, volatility, and bias reactions under hypothetical macro shocks."""

    # Historical Empirical Sensitivities for Gold:
    # 1. US 10Y Yield: -1.2% Gold price move per +10 bps real yield increase (-$35/oz per +10 bps at ~$2900).
    # 2. US Dollar Index (DXY): -0.85% Gold price move per +1.0% DXY surge.
    # 3. CPI / Inflation Surprise: +0.65% Gold price move per +0.2% hot CPI (stagflation hedge) or -0.4% if rate hike fear dominates.
    # 4. Geopolitical Shock: +1.5% to +3.5% safe-haven surge on acute military escalation.

    @staticmethod
    def simulate(
        current_price: float,
        us10y_bps_shift: float = 0.0,       # e.g. +15 bps or -10 bps
        dxy_pct_shift: float = 0.0,         # e.g. +1.2% or -0.8%
        cpi_surprise_pct: float = 0.0,      # e.g. +0.3% vs forecast
        geopolitical_shock: str = "NONE"     # "NONE" | "MODERATE" | "SEVERE"
    ) -> Dict[str, Any]:
        """Calculates expected gold price delta, target range, and dominant drivers from input shocks."""
        base_price = max(100.0, current_price)

        # 1. Yield Impact
        # 10 bps shift ~ 1.15% inverse move
        yield_impact_pct = -(us10y_bps_shift / 10.0) * 1.15
        yield_delta_usd = base_price * (yield_impact_pct / 100.0)

        # 2. DXY Impact
        # +1.0% DXY shift ~ -0.82% gold move
        dxy_impact_pct = -(dxy_pct_shift) * 0.82
        dxy_delta_usd = base_price * (dxy_impact_pct / 100.0)

        # 3. Inflation / CPI Surprise Impact
        # +0.1% CPI hot surprise ~ +0.45% gold move (hedging demand)
        cpi_impact_pct = (cpi_surprise_pct / 0.1) * 0.45
        cpi_delta_usd = base_price * (cpi_impact_pct / 100.0)

        # 4. Geopolitical Conflict Shock Impact
        geo_impact_pct = 0.0
        if geopolitical_shock.upper() == "SEVERE":
            geo_impact_pct = +2.65
        elif geopolitical_shock.upper() == "MODERATE":
            geo_impact_pct = +1.20
        elif geopolitical_shock.upper() == "DE_ESCALATION":
            geo_impact_pct = -1.10
        geo_delta_usd = base_price * (geo_impact_pct / 100.0)

        # Total Net Move
        net_delta_pct = yield_impact_pct + dxy_impact_pct + cpi_impact_pct + geo_impact_pct
        net_delta_usd = yield_delta_usd + dxy_delta_usd + cpi_delta_usd + geo_delta_usd
        projected_price = round(base_price + net_delta_usd, 2)

        # Volatility & Risk Classification
        vol_expansion_factor = round(1.0 + (abs(net_delta_pct) * 0.15), 2)
        
        if net_delta_pct >= +1.5:
            projected_verdict = "STRONGLY_BULLISH"
            verdict_color = "#10b981"
            bias_narrative = f"Shock scenario triggers aggressive safe-haven / monetary expansion bid (+${net_delta_usd:+.2f})."
        elif net_delta_pct >= +0.4:
            projected_verdict = "BULLISH"
            verdict_color = "#10b981"
            bias_narrative = f"Constructive macro support pushes gold upward by +${net_delta_usd:+.2f}."
        elif net_delta_pct <= -1.5:
            projected_verdict = "STRONGLY_BEARISH"
            verdict_color = "#ef4444"
            bias_narrative = f"Severe rate surge / USD rally triggers steep bullion liquidation (-${abs(net_delta_usd):.2f})."
        elif net_delta_pct <= -0.4:
            projected_verdict = "BEARISH"
            verdict_color = "#ef4444"
            bias_narrative = f"Yield & currency headwinds constrain gold by -${abs(net_delta_usd):.2f}."
        else:
            projected_verdict = "NEUTRAL"
            verdict_color = "#f59e0b"
            bias_narrative = "Competing forces offset each other; range-bound consolidation expected."

        return {
            "current_price": base_price,
            "projected_price": projected_price,
            "net_delta_usd": round(net_delta_usd, 2),
            "net_delta_pct": round(net_delta_pct, 2),
            "projected_verdict": projected_verdict,
            "verdict_color": verdict_color,
            "volatility_expansion_factor": vol_expansion_factor,
            "bias_narrative": bias_narrative,
            "breakdown": {
                "us10y_yield_delta_usd": round(yield_delta_usd, 2),
                "dxy_delta_usd": round(dxy_delta_usd, 2),
                "cpi_delta_usd": round(cpi_delta_usd, 2),
                "geopolitical_delta_usd": round(geo_delta_usd, 2)
            }
        }
