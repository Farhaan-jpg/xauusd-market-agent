"""Market Regime Classifier dynamically adjusting factor synthesis weights based on active market state."""
from typing import Any, Dict, Optional

class MarketRegimeClassifier:
    """
    Classifies the current XAUUSD market regime into one of 4 states:
    1. TRENDING_EXPANSION: Strong directional momentum, breakout above/below key structure.
    2. MEAN_REVERSION_RANGE: Low directional drift, price oscillating between resting liquidity bounds.
    3. VOLATILITY_NEWS_SHOCK: Pre/post economic data release, violent 2-way expansion.
    4. ASIAN_CONSOLIDATION: Off-hours / low liquidity Asian session range formation.
    """

    @staticmethod
    def classify_regime(
        trend: str,
        volatility: str,
        market_structure: str,
        killzone: str,
        is_news_lockout: bool,
        atr_ratio: float = 1.0
    ) -> Dict[str, Any]:
        """Determines active market regime and outputs dynamically rebalanced synthesis weights."""
        regime = "MEAN_REVERSION_RANGE"
        description = "Sideways balanced auction. Mean reversion & liquidity boundaries prioritized."
        
        # 1. News Shock Priority
        if is_news_lockout or volatility in ["EXTREME", "HIGH_VOLATILITY"]:
            regime = "VOLATILITY_NEWS_SHOCK"
            description = "High-impact macro/geopolitical catalyst in progress. Strict volatility protection active."
            weights = {
                "technical": 0.30,
                "news": 0.40,
                "liquidity": 0.10,
                "macro": 0.20
            }

        # 2. Asian Consolidation
        elif "ASIAN" in killzone.upper():
            regime = "ASIAN_CONSOLIDATION"
            description = "Asian session range accumulation. Prioritizing session boundary sweeps & VWAP mean-reversion."
            weights = {
                "technical": 0.40,
                "news": 0.15,
                "liquidity": 0.35,
                "macro": 0.10
            }

        # 3. Trending Expansion
        elif "TREND" in trend.upper() or "BULLISH_ORDERFLOW" in market_structure or "BEARISH_ORDERFLOW" in market_structure:
            regime = "TRENDING_EXPANSION"
            description = "High-conviction directional momentum. Structure continuation & breakout alignment prioritized."
            weights = {
                "technical": 0.65,
                "news": 0.15,
                "liquidity": 0.10,
                "macro": 0.10
            }

        # 4. Standard Mean Reversion Range
        else:
            regime = "MEAN_REVERSION_RANGE"
            weights = {
                "technical": 0.45,
                "news": 0.20,
                "liquidity": 0.20,
                "macro": 0.15
            }

        return {
            "regime": regime,
            "description": description,
            "weights": weights,
            "is_trending": regime == "TRENDING_EXPANSION",
            "is_ranging": regime in ["MEAN_REVERSION_RANGE", "ASIAN_CONSOLIDATION"],
            "is_news_shock": regime == "VOLATILITY_NEWS_SHOCK"
        }
