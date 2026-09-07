"""Multi-Timeframe Institutional Confluence Matrix scoring trading alignment across 1H, 15M, 5M, and Order Flow."""
from typing import Any, Dict, List, Optional

class ConfluenceMatrixEngine:
    """
    Evaluates confluence across 4 institutional pillars:
    1. Higher Timeframe (1H Structure & Trend): Weight 30 pts
    2. Intermediate Timeframe (15M Day Bias & Liquidity Sweep): Weight 30 pts
    3. Low Timeframe (5M Scalp Momentum, FVG & SuperTrend): Weight 25 pts
    4. Execution Proximity (Session VWAP Alignment & CVD Absorption): Weight 15 pts
    
    Produces a Confluence Score (0-100%) and Grade:
    - A+ Setup (>= 85% Confluence): Premium institutional setup
    - A Setup (70% - 84%): High probability
    - B Setup (55% - 69%): Moderate setup, smaller position
    - NO_TRADE (< 55%): Conflicting timeframes / chop
    """

    @staticmethod
    def evaluate_confluence(
        market_analysis: Dict[str, Any],
        liquidity_analysis: Dict[str, Any],
        cvd_analysis: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """Calculates multi-timeframe directional alignment score and setup grade."""
        tech_score = market_analysis.get("technical_score", 0.0)
        scalp_bias = market_analysis.get("scalp_bias", "")
        day_bias = market_analysis.get("day_trade_bias", "")
        overall_trend = market_analysis.get("trend", "NEUTRAL")
        vwap = market_analysis.get("vwap_5m", current_price)
        market_structure = market_analysis.get("market_structure", "RANGING")
        
        sweeps = liquidity_analysis.get("active_sweeps", [])
        cvd_bias = cvd_analysis.get("cvd_bias", "BALANCED")
        cvd_div = cvd_analysis.get("delta_divergence", "NONE")

        # Determine directional target
        bullish_pts = 0
        bearish_pts = 0
        aligned_factors = []
        conflicting_factors = []

        # Pillar 1: 1H Structure & Trend (30 pts)
        if "BULLISH" in overall_trend or "BULLISH_ORDERFLOW" in market_structure:
            bullish_pts += 30
            aligned_factors.append("1H Higher Timeframe Bullish Structure / BOS")
        elif "BEARISH" in overall_trend or "BEARISH_ORDERFLOW" in market_structure:
            bearish_pts += 30
            aligned_factors.append("1H Higher Timeframe Bearish Structure / BOS")

        # Pillar 2: 15M Day Bias & Sweep (30 pts)
        if "BULLISH" in day_bias:
            bullish_pts += 20
            aligned_factors.append("15M Day Trade Trend Alignment")
        elif "BEARISH" in day_bias:
            bearish_pts += 20
            aligned_factors.append("15M Day Trade Trend Alignment")

        for s in sweeps:
            if s.get("bias") == "BULLISH":
                bullish_pts += 10
                aligned_factors.append(f"15M SSL Liquidity Sweep ({s.get('level_swept', 'Low')})")
            elif s.get("bias") == "BEARISH":
                bearish_pts += 10
                aligned_factors.append(f"15M BSL Liquidity Sweep ({s.get('level_swept', 'High')})")

        # Pillar 3: 5M Scalp Momentum & SuperTrend (25 pts)
        if "BULLISH" in scalp_bias:
            bullish_pts += 25
            aligned_factors.append("5M Scalp SuperTrend / Momentum Bullish")
        elif "BEARISH" in scalp_bias:
            bearish_pts += 25
            aligned_factors.append("5M Scalp SuperTrend / Momentum Bearish")

        # Pillar 4: Session VWAP & CVD Absorption (15 pts)
        vwap_diff = current_price - vwap
        if vwap_diff > 0:
            bullish_pts += 8
            aligned_factors.append("Price Holding Above Session VWAP")
        else:
            bearish_pts += 8
            aligned_factors.append("Price Capped Below Session VWAP")

        if cvd_div == "BULLISH_CVD_DIVERGENCE" or "BULLISH" in cvd_bias:
            bullish_pts += 7
            aligned_factors.append("CVD Delta Aggressor Accumulation")
        elif cvd_div == "BEARISH_CVD_DIVERGENCE" or "BEARISH" in cvd_bias:
            bearish_pts += 7
            aligned_factors.append("CVD Delta Aggressor Distribution")

        # Normalize score
        if bullish_pts >= bearish_pts:
            confluence_bias = "BULLISH"
            confluence_score = min(100, bullish_pts)
            conflict_penalty = min(25, bearish_pts // 2)
            final_confluence = max(10, confluence_score - conflict_penalty)
        else:
            confluence_bias = "BEARISH"
            confluence_score = min(100, bearish_pts)
            conflict_penalty = min(25, bullish_pts // 2)
            final_confluence = max(10, confluence_score - conflict_penalty)

        # Grade assignment
        if final_confluence >= 85:
            grade = "A+"
            actionability = "PREMIUM_CONFLUENCE_SETUP"
        elif final_confluence >= 70:
            grade = "A"
            actionability = "HIGH_PROBABILITY_SETUP"
        elif final_confluence >= 55:
            grade = "B"
            actionability = "MODERATE_SETUP"
        else:
            grade = "NO_TRADE"
            actionability = "LOW_CONFLUENCE_CHOP"

        return {
            "confluence_bias": confluence_bias if grade != "NO_TRADE" else "NEUTRAL",
            "confluence_score": final_confluence,
            "setup_grade": grade,
            "actionability": actionability,
            "aligned_factors": aligned_factors,
            "bullish_points": bullish_pts,
            "bearish_points": bearish_pts,
            "is_actionable": grade in ["A+", "A"]
        }
