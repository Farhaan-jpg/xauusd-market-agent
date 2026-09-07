"""
CME FedWatch Implied Interest Rate Expectation Engine for XAUUSD.
Quantifies market-implied probabilities of Federal Reserve rate cuts/hikes
and determines macroeconomic monetary tailwinds for Gold.
"""

from typing import Dict, Any


class FedWatchEngine:
    """
    Computes Federal Reserve interest rate path expectation probabilities.
    """

    @staticmethod
    def calculate_rate_probabilities(
        us2y_yield: float = 4.15,
        us10y_yield: float = 4.38,
        fed_funds_rate: float = 4.88,
        macro_sentiment_score: float = 12.0
    ) -> Dict[str, Any]:
        """
        Calculates implied rate cut probabilities for next FOMC meeting.
        """
        # Yield inversion spread vs Fed Funds Rate
        spread = fed_funds_rate - us2y_yield
        
        # Base probabilities derived from 2Y treasury delta to target rate
        if spread > 0.60:
            prob_cut_50bps = min(45.0, round(spread * 30.0, 1))
            prob_cut_25bps = round(max(40.0, 95.0 - prob_cut_50bps), 1)
            prob_pause = round(max(2.0, 100.0 - prob_cut_25bps - prob_cut_50bps), 1)
            prob_hike = 0.0
            bias = "AGGRESSIVE_DOVISH_EASING"
            gold_impact = "STRONG_BULLISH_TAILWIND"
        elif spread > 0.20:
            prob_cut_50bps = 10.0
            prob_cut_25bps = 75.0
            prob_pause = 15.0
            prob_hike = 0.0
            bias = "MODERATE_DOVISH_EASING"
            gold_impact = "BULLISH_TAILWIND"
        elif spread > -0.20:
            prob_cut_50bps = 0.0
            prob_cut_25bps = 35.0
            prob_pause = 60.0
            prob_hike = 5.0
            bias = "NEUTRAL_PAUSE_REGIME"
            gold_impact = "NEUTRAL_CONSOLIDATION"
        else:
            prob_cut_50bps = 0.0
            prob_cut_25bps = 5.0
            prob_pause = 55.0
            prob_hike = 40.0
            bias = "HAWKISH_TIGHTENING_PRESSURE"
            gold_impact = "BEARISH_HEADWIND"

        total_cut_prob = prob_cut_25bps + prob_cut_50bps

        return {
            "fed_funds_effective_rate": fed_funds_rate,
            "us2y_treasury_yield": us2y_yield,
            "us10y_treasury_yield": us10y_yield,
            "yield_discount_spread_bps": round(spread * 100, 1),
            "prob_cut_25bps": prob_cut_25bps,
            "prob_cut_50bps": prob_cut_50bps,
            "prob_pause": prob_pause,
            "prob_hike": prob_hike,
            "total_cut_probability_pct": total_cut_prob,
            "monetary_policy_regime": bias,
            "gold_macro_impact": gold_impact,
            "narrative": f"Markets pricing {total_cut_prob:.0f}% probability of Fed rate cuts. Monetary policy stance creates {gold_impact.replace('_', ' ').lower()} for bullion."
        }
