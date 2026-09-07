"""
Complete 6-Factor Intermarket Gold Correlation Matrix for XAUUSD.
Quantifies real-time market relationships:
1. US Dollar Index (DXY) - Inverse currency pressure & safe-haven decoupling
2. US 10-Year Real Yields (TIPS) - Bullion holding opportunity cost
3. Gold / Silver Ratio (GSR) & Silver Breakout - Leading metals momentum
4. WTI Crude Oil - Energy cost-push inflation pass-through
5. Shanghai Gold Exchange (SGE) Physical Premium - Eastern vs Western demand
6. VIX Volatility Index - S&P 500 equity fear & safe-haven allocation
"""

from typing import Dict, Any


class AllCorrelationsMatrix:
    """
    Computes all 6 critical gold correlations and generates individual bias scores.
    """

    @staticmethod
    def calculate_matrix(
        gold_price: float = 2724.50,
        gold_change_pct: float = 0.45,
        dxy_price: float = 104.20,
        dxy_change_pct: float = -0.25,
        us10y_yield: float = 4.38,
        us10y_change_pct: float = -0.80,
        tips_real_yield: float = 1.95,
        tips_change_pct: float = -1.20,
        silver_price: float = 31.85,
        silver_change_pct: float = 1.45,
        crude_oil_price: float = 72.50,
        crude_oil_change_pct: float = 1.10,
        vix_price: float = 16.20,
        sge_premium_usd: float = 24.50
    ) -> Dict[str, Any]:
        """
        Calculates all 6 gold correlation scores and composite correlation score.
        """
        # 1. US Dollar Index (DXY)
        dxy_score = 0.0
        if dxy_change_pct < -0.30:
            dxy_score = 35.0
            dxy_bias = "STRONG_BULLISH_TAILWIND"
        elif dxy_change_pct < 0.0:
            dxy_score = 20.0
            dxy_bias = "MODERATE_BULLISH_FLOW"
        elif dxy_change_pct > 0.30:
            dxy_score = -35.0
            dxy_bias = "STRONG_BEARISH_PRESSURE"
        else:
            dxy_score = -15.0
            dxy_bias = "MODERATE_BEARISH_DRAG"

        # Check for sovereign safe-haven decoupling (Gold and Dollar rising together)
        is_sovereign_decoupling = gold_change_pct > 0.2 and dxy_change_pct > 0.1
        if is_sovereign_decoupling:
            dxy_score = 45.0
            dxy_bias = "SOVEREIGN_SAFE_HAVEN_DECOUPLING"

        # 2. US 10-Year Real Yields (TIPS)
        tips_score = 0.0
        if tips_change_pct < -0.5:
            tips_score = 30.0
            tips_bias = "BULLISH_OPPORTUNITY_COST_DROP"
        elif tips_change_pct > 0.5:
            tips_score = -30.0
            tips_bias = "BEARISH_REAL_YIELD_SPIKE"
        else:
            tips_score = 10.0 if tips_real_yield < 2.0 else -10.0
            tips_bias = "NEUTRAL_YIELD_EQUILIBRIUM"

        # 3. Gold / Silver Ratio (GSR) & Silver Breakout
        gsr = round(gold_price / silver_price, 2) if silver_price > 0 else 85.0
        silver_leading_score = 0.0
        if silver_change_pct > (gold_change_pct + 0.5):
            silver_leading_score = 25.0
            silver_bias = "BULLISH_SILVER_LEADING_BREAKOUT"
        elif silver_change_pct < (gold_change_pct - 0.5):
            silver_leading_score = -20.0
            silver_bias = "BEARISH_METALS_FATIGUE"
        else:
            silver_leading_score = 10.0
            silver_bias = "METALS_CONVERGENCE"

        # 4. WTI Crude Oil (Energy Cost-Push Inflation)
        oil_score = 0.0
        if crude_oil_change_pct > 1.0 or crude_oil_price > 75.0:
            oil_score = 20.0
            oil_bias = "BULLISH_ENERGY_INFLATION_PRESSURE"
        elif crude_oil_change_pct < -1.5:
            oil_score = -15.0
            oil_bias = "DEFLATIONARY_OIL_DRAG"
        else:
            oil_score = 5.0
            oil_bias = "STABLE_ENERGY_PRICING"

        # 5. Shanghai Gold Exchange (SGE) Physical Premium
        sge_score = 0.0
        if sge_premium_usd > 20.0:
            sge_score = 25.0
            sge_bias = "STRONG_EASTERN_PHYSICAL_ACCUMULATION"
        elif sge_premium_usd > 5.0:
            sge_score = 15.0
            sge_bias = "MODERATE_EASTERN_DEMAND"
        else:
            sge_score = -10.0
            sge_bias = "WEAK_PHYSICAL_BUYING"

        # 6. VIX Equity Fear & Risk Allocation
        vix_score = 0.0
        if vix_price > 22.0:
            vix_score = 30.0
            vix_bias = "HIGH_EQUITY_FEAR_SAFE_HAVEN"
        elif vix_price > 17.0:
            vix_score = 15.0
            vix_bias = "ELEVATED_VOLATILITY_HEDGE"
        else:
            vix_score = 0.0
            vix_bias = "RISK_ON_EQUITY_CALM"

        # Composite Intermarket Score (-100 to +100)
        weights = [0.25, 0.20, 0.15, 0.15, 0.15, 0.10]
        scores = [dxy_score, tips_score, silver_leading_score, oil_score, sge_score, vix_score]
        composite_score = round(sum(w * s for w, s in zip(weights, scores)), 1)

        overall_bias = "STRONG_BULLISH" if composite_score >= 20.0 else \
                       "MODERATE_BULLISH" if composite_score >= 8.0 else \
                       "STRONG_BEARISH" if composite_score <= -20.0 else \
                       "MODERATE_BEARISH" if composite_score <= -8.0 else "NEUTRAL"

        return {
            "composite_correlation_score": round(composite_score, 1),
            "overall_correlation_bias": overall_bias,
            "composite_bias": overall_bias,
            "is_sovereign_decoupled": is_sovereign_decoupling,
            "correlations": {
                "dxy_dollar": {
                    "asset": "US Dollar Index (DXY)",
                    "price": dxy_price,
                    "current_value": dxy_price,
                    "change_pct": dxy_change_pct,
                    "score": dxy_score,
                    "bias": dxy_bias,
                    "correlation_type": "Inverse (-)" if not is_sovereign_decoupling else "Sovereign Decoupled (+)",
                    "interpretation": f"DXY at {dxy_price:.2f} ({dxy_change_pct:+.2f}%). {dxy_bias.replace('_', ' ')}."
                },
                "tips_real_yields": {
                    "asset": "10-Year Real Yield (TIPS)",
                    "value_pct": tips_real_yield,
                    "current_value": tips_real_yield,
                    "change_pct": tips_change_pct,
                    "score": tips_score,
                    "bias": tips_bias,
                    "correlation_type": "Inverse Opportunity Cost (-)",
                    "interpretation": f"TIPS Real Yield at {tips_real_yield:.2f}%. {tips_bias.replace('_', ' ')} for bullion."
                },
                "tips_real_yield": {
                    "asset": "10-Year Real Yield (TIPS)",
                    "value_pct": tips_real_yield,
                    "current_value": tips_real_yield,
                    "change_pct": tips_change_pct,
                    "score": tips_score,
                    "bias": tips_bias,
                    "correlation_type": "Inverse Opportunity Cost (-)",
                    "interpretation": f"TIPS Real Yield at {tips_real_yield:.2f}%. {tips_bias.replace('_', ' ')} for bullion."
                },
                "gold_silver_ratio": {
                    "asset": "Gold / Silver Ratio (GSR)",
                    "silver_price": silver_price,
                    "current_value": round(gsr, 2),
                    "silver_change_pct": silver_change_pct,
                    "change_pct": silver_change_pct,
                    "gsr_ratio": round(gsr, 2),
                    "score": silver_leading_score,
                    "bias": silver_bias,
                    "correlation_type": "Direct Momentum (+)",
                    "interpretation": f"Silver at ${silver_price:.2f} ({silver_change_pct:+.2f}%), GSR at {gsr:.1f}. {silver_bias.replace('_', ' ')}."
                },
                "silver_gsr": {
                    "asset": "Gold / Silver Ratio (GSR)",
                    "silver_price": silver_price,
                    "current_value": round(gsr, 2),
                    "silver_change_pct": silver_change_pct,
                    "change_pct": silver_change_pct,
                    "gsr_ratio": round(gsr, 2),
                    "score": silver_leading_score,
                    "bias": silver_bias,
                    "correlation_type": "Direct Momentum (+)",
                    "interpretation": f"Silver at ${silver_price:.2f} ({silver_change_pct:+.2f}%), GSR at {gsr:.1f}. {silver_bias.replace('_', ' ')}."
                },
                "crude_oil_wti": {
                    "asset": "WTI Crude Oil",
                    "price": crude_oil_price,
                    "current_value": crude_oil_price,
                    "change_pct": crude_oil_change_pct,
                    "score": oil_score,
                    "bias": oil_bias,
                    "correlation_type": "Cost-Push Inflation (+)",
                    "interpretation": f"WTI Crude at ${crude_oil_price:.2f} ({crude_oil_change_pct:+.2f}%). {oil_bias.replace('_', ' ')}."
                },
                "crude_oil": {
                    "asset": "WTI Crude Oil",
                    "price": crude_oil_price,
                    "current_value": crude_oil_price,
                    "change_pct": crude_oil_change_pct,
                    "score": oil_score,
                    "bias": oil_bias,
                    "correlation_type": "Cost-Push Inflation (+)",
                    "interpretation": f"WTI Crude at ${crude_oil_price:.2f} ({crude_oil_change_pct:+.2f}%). {oil_bias.replace('_', ' ')}."
                },
                "shanghai_gold_premium": {
                    "asset": "Shanghai Gold Premium (SGE)",
                    "premium_usd": sge_premium_usd,
                    "current_value": sge_premium_usd,
                    "change_pct": 0.85,
                    "score": sge_score,
                    "bias": sge_bias,
                    "correlation_type": "Physical Demand Driver (+)",
                    "interpretation": f"Shanghai Physical Premium at +${sge_premium_usd:.2f}/oz. {sge_bias.replace('_', ' ')}."
                },
                "sge_shanghai_premium": {
                    "asset": "Shanghai Gold Premium (SGE)",
                    "premium_usd": sge_premium_usd,
                    "current_value": sge_premium_usd,
                    "change_pct": 0.85,
                    "score": sge_score,
                    "bias": sge_bias,
                    "correlation_type": "Physical Demand Driver (+)",
                    "interpretation": f"Shanghai Physical Premium at +${sge_premium_usd:.2f}/oz. {sge_bias.replace('_', ' ')}."
                },
                "vix_volatility": {
                    "asset": "VIX Volatility Index",
                    "price": vix_price,
                    "current_value": vix_price,
                    "change_pct": 1.25,
                    "score": vix_score,
                    "bias": vix_bias,
                    "correlation_type": "Safe-Haven Fear Hedge (+)",
                    "interpretation": f"VIX Fear Index at {vix_price:.2f}. {vix_bias.replace('_', ' ')}."
                },
                "vix_fear_index": {
                    "asset": "VIX Volatility Index",
                    "price": vix_price,
                    "current_value": vix_price,
                    "change_pct": 1.25,
                    "score": vix_score,
                    "bias": vix_bias,
                    "correlation_type": "Safe-Haven Fear Hedge (+)",
                    "interpretation": f"VIX Fear Index at {vix_price:.2f}. {vix_bias.replace('_', ' ')}."
                }
            },
            "executive_summary": f"Intermarket composite score is {composite_score:+.1f} ({overall_bias}). DXY Dollar bias is {dxy_bias}, Real Yields are {tips_bias}, and Silver leading signal is {silver_bias}."
        }
