"""Market Engine processing multi-timeframe technical indicators, trend, and volatility."""
from typing import Any, Dict, Optional
import pandas as pd
from app.analysis.technical.indicators import TechnicalIndicators
from app.core.logging import logger

class MarketEngine:
    """Executes multi-timeframe technical analysis on Gold market data."""

    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates indicators and analyzes trend/momentum/volatility across timeframes."""
        timeframes = market_data.get("timeframes", {})
        price = market_data.get("price", 0.0)

        # Primary analysis on 1h (or 15m/1d fallback)
        primary_tf = "1h" if "1h" in timeframes and not timeframes["1h"].empty else \
                     "15m" if "15m" in timeframes and not timeframes["15m"].empty else "1d"

        df = timeframes.get(primary_tf, pd.DataFrame())

        if df.empty or len(df) < 10:
            return self._default_analysis(price)

        # Calculate indicators on primary timeframe
        atr_series = TechnicalIndicators.calculate_atr(df, period=14)
        rsi_series = TechnicalIndicators.calculate_rsi(df, period=14)
        macd_line, macd_signal, macd_hist = TechnicalIndicators.calculate_macd(df)
        ema_20_series = TechnicalIndicators.calculate_ema(df, span=20)
        ema_50_series = TechnicalIndicators.calculate_ema(df, span=50)
        ema_200_series = TechnicalIndicators.calculate_ema(df, span=200)
        upper_bb, mid_bb, lower_bb = TechnicalIndicators.calculate_bollinger_bands(df, period=20)

        current_atr = float(atr_series.iloc[-1]) if not atr_series.empty else 0.0
        current_rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty else 50.0
        current_macd = float(macd_line.iloc[-1]) if not macd_line.empty else 0.0
        current_macd_sig = float(macd_signal.iloc[-1]) if not macd_signal.empty else 0.0
        current_macd_hist = float(macd_hist.iloc[-1]) if not macd_hist.empty else 0.0
        current_ema20 = float(ema_20_series.iloc[-1]) if not ema_20_series.empty else price
        current_ema50 = float(ema_50_series.iloc[-1]) if not ema_50_series.empty else price
        current_ema200 = float(ema_200_series.iloc[-1]) if not ema_200_series.empty else price

        # Trend Determination
        trend_score = 0
        if price > current_ema20: trend_score += 1
        if current_ema20 > current_ema50: trend_score += 1
        if price > current_ema50: trend_score += 1
        if price > current_ema200: trend_score += 2

        if price < current_ema20: trend_score -= 1
        if current_ema20 < current_ema50: trend_score -= 1
        if price < current_ema50: trend_score -= 1
        if price < current_ema200: trend_score -= 2

        if trend_score >= 3:
            trend = "STRONGLY_BULLISH"
        elif trend_score >= 1:
            trend = "BULLISH"
        elif trend_score <= -3:
            trend = "STRONGLY_BEARISH"
        elif trend_score <= -1:
            trend = "BEARISH"
        else:
            trend = "RANGING_NEUTRAL"

        # Volatility Regime
        # Normalized ATR as percentage of price
        atr_pct = (current_atr / price * 100.0) if price > 0 else 0.0
        if atr_pct > 0.8:
            volatility = "EXTREME_VOLATILITY"
        elif atr_pct > 0.45:
            volatility = "HIGH_VOLATILITY"
        elif atr_pct < 0.15:
            volatility = "LOW_VOLATILITY"
        else:
            volatility = "NORMAL_VOLATILITY"

        # Technical Score (-100 to +100)
        tech_score = 0.0
        # Trend contribution (+/- 40)
        tech_score += (trend_score / 5.0) * 40.0

        # RSI contribution (+/- 30)
        if current_rsi > 70:
            tech_score += 15.0  # Strong bullish momentum (or slightly overbought)
        elif current_rsi < 30:
            tech_score -= 15.0  # Strong bearish momentum
        else:
            tech_score += ((current_rsi - 50.0) / 20.0) * 30.0

        # MACD contribution (+/- 30)
        if current_macd > current_macd_sig:
            tech_score += 20.0
            if current_macd_hist > 0: tech_score += 10.0
        else:
            tech_score -= 20.0
            if current_macd_hist < 0: tech_score -= 10.0

        tech_score = max(-100.0, min(100.0, tech_score))

        return {
            "price": price,
            "timeframe": primary_tf,
            "atr": round(current_atr, 2),
            "atr_pct": round(atr_pct, 3),
            "rsi": round(current_rsi, 2),
            "macd": round(current_macd, 3),
            "macd_signal": round(current_macd_sig, 3),
            "macd_hist": round(current_macd_hist, 3),
            "ema_20": round(current_ema20, 2),
            "ema_50": round(current_ema50, 2),
            "ema_200": round(current_ema200, 2),
            "bb_upper": round(float(upper_bb.iloc[-1]), 2) if not upper_bb.empty else price,
            "bb_lower": round(float(lower_bb.iloc[-1]), 2) if not lower_bb.empty else price,
            "trend": trend,
            "volatility": volatility,
            "technical_score": round(tech_score, 1),
            "data_quality": "GOOD"
        }

    def _default_analysis(self, price: float) -> Dict[str, Any]:
        return {
            "price": price,
            "timeframe": "1h",
            "atr": 0.0,
            "atr_pct": 0.0,
            "rsi": 50.0,
            "macd": 0.0,
            "macd_signal": 0.0,
            "macd_hist": 0.0,
            "ema_20": price,
            "ema_50": price,
            "ema_200": price,
            "bb_upper": price,
            "bb_lower": price,
            "trend": "NEUTRAL",
            "volatility": "NORMAL_VOLATILITY",
            "technical_score": 0.0,
            "data_quality": "LIMITED"
        }
