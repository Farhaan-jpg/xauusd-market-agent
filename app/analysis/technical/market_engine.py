"""Market Engine processing multi-timeframe technical indicators, scalping momentum (5m), intraday structure (15m), and session trend (1h)."""
from typing import Any, Dict, Optional
import pandas as pd
from app.analysis.technical.indicators import TechnicalIndicators
from app.core.logging import logger

class MarketEngine:
    """Executes multi-timeframe technical analysis optimized for XAUUSD Scalping and Day Trading."""

    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates 5m Scalp Momentum, 15m Intraday Structure, 1h Trend, VWAP, and Multi-Timeframe Technical Score."""
        timeframes = market_data.get("timeframes", {})
        price = market_data.get("price", 0.0)

        df_5m = timeframes.get("5m", pd.DataFrame())
        df_15m = timeframes.get("15m", pd.DataFrame())
        df_1h = timeframes.get("1h", pd.DataFrame())
        df_1d = timeframes.get("1d", pd.DataFrame())

        # Fallbacks if some timeframes are empty
        primary_df = df_1h if not df_1h.empty and len(df_1h) >= 10 else \
                     df_15m if not df_15m.empty and len(df_15m) >= 10 else \
                     df_5m if not df_5m.empty and len(df_5m) >= 10 else df_1d

        if primary_df.empty or price <= 0:
            return self._default_analysis(price)

        # ----------------------------------------------------
        # 1. 1H / Primary Framework (Session Trend & Volatility)
        # ----------------------------------------------------
        atr_series = TechnicalIndicators.calculate_atr(primary_df, period=14)
        rsi_series = TechnicalIndicators.calculate_rsi(primary_df, period=14)
        macd_line, macd_signal, macd_hist = TechnicalIndicators.calculate_macd(primary_df)
        ema_20_series = TechnicalIndicators.calculate_ema(primary_df, span=20)
        ema_50_series = TechnicalIndicators.calculate_ema(primary_df, span=50)
        ema_200_series = TechnicalIndicators.calculate_ema(primary_df, span=200)
        upper_bb, mid_bb, lower_bb = TechnicalIndicators.calculate_bollinger_bands(primary_df, period=20)

        current_atr = float(atr_series.iloc[-1]) if not atr_series.empty else 0.0
        current_rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty else 50.0
        current_macd = float(macd_line.iloc[-1]) if not macd_line.empty else 0.0
        current_macd_sig = float(macd_signal.iloc[-1]) if not macd_signal.empty else 0.0
        current_macd_hist = float(macd_hist.iloc[-1]) if not macd_hist.empty else 0.0
        current_ema20 = float(ema_20_series.iloc[-1]) if not ema_20_series.empty else price
        current_ema50 = float(ema_50_series.iloc[-1]) if not ema_50_series.empty else price
        current_ema200 = float(ema_20_series.iloc[-1]) if not ema_200_series.empty else price

        # 1H Trend Score (-100 to +100)
        h1_score = 0.0
        if price > current_ema20: h1_score += 20.0
        else: h1_score -= 20.0
        if current_ema20 > current_ema50: h1_score += 20.0
        else: h1_score -= 20.0
        if price > current_ema50: h1_score += 20.0
        else: h1_score -= 20.0
        if price > current_ema200: h1_score += 20.0
        else: h1_score -= 20.0
        if current_macd > current_macd_sig: h1_score += 10.0
        else: h1_score -= 10.0
        if current_macd_hist > 0: h1_score += 10.0
        else: h1_score -= 10.0
        h1_score = max(-100.0, min(100.0, h1_score))

        # ----------------------------------------------------
        # 2. 15M Intraday Market Structure & Day Trading Bias
        # ----------------------------------------------------
        m15_df = df_15m if not df_15m.empty and len(df_15m) >= 10 else primary_df
        m15_structure = TechnicalIndicators.detect_market_structure(m15_df, window=2)
        m15_ema20 = TechnicalIndicators.calculate_ema(m15_df, span=20).iloc[-1] if not m15_df.empty else price
        m15_ema50 = TechnicalIndicators.calculate_ema(m15_df, span=50).iloc[-1] if not m15_df.empty else price
        m15_rsi = TechnicalIndicators.calculate_rsi(m15_df, period=14).iloc[-1] if not m15_df.empty else 50.0
        m15_vwap = TechnicalIndicators.calculate_vwap(m15_df).iloc[-1] if not m15_df.empty else price

        day_trade_score = float(m15_structure.get("structure_score", 0.0))
        # EMA alignment on 15m
        if price > m15_ema20: day_trade_score += 15.0
        else: day_trade_score -= 15.0
        if m15_ema20 > m15_ema50: day_trade_score += 15.0
        else: day_trade_score -= 15.0
        # VWAP positioning on 15m
        if price > m15_vwap: day_trade_score += 20.0
        else: day_trade_score -= 20.0
        day_trade_score = max(-100.0, min(100.0, day_trade_score))

        if day_trade_score >= 35.0:
            day_trade_bias = "DAY_TRADE_BULLISH"
        elif day_trade_score <= -35.0:
            day_trade_bias = "DAY_TRADE_BEARISH"
        elif day_trade_score >= 15.0:
            day_trade_bias = "DAY_TRADE_BULLISH_LEAN"
        elif day_trade_score <= -15.0:
            day_trade_bias = "DAY_TRADE_BEARISH_LEAN"
        else:
            day_trade_bias = "DAY_TRADE_RANGING"

        # ----------------------------------------------------
        # 3. 5M Scalping Momentum & Fast Execution Trigger
        # ----------------------------------------------------
        m5_df = df_5m if not df_5m.empty and len(df_5m) >= 10 else m15_df
        m5_ema9 = TechnicalIndicators.calculate_ema(m5_df, span=9).iloc[-1] if not m5_df.empty else price
        m5_ema21 = TechnicalIndicators.calculate_ema(m5_df, span=21).iloc[-1] if not m5_df.empty else price
        m5_rsi = TechnicalIndicators.calculate_rsi(m5_df, period=9).iloc[-1] if not m5_df.empty else 50.0
        m5_vwap = TechnicalIndicators.calculate_vwap(m5_df).iloc[-1] if not m5_df.empty else price
        _, _, m5_supertrend_dir = TechnicalIndicators.calculate_supertrend(m5_df, period=7, multiplier=2.5) if not m5_df.empty and len(m5_df) >= 8 else (None, None, pd.Series([1]))
        current_m5_st = int(m5_supertrend_dir.iloc[-1]) if not m5_supertrend_dir.empty else 1

        scalp_score = 0.0
        # Fast EMA 9 / 21 cross
        if price > m5_ema9 > m5_ema21: scalp_score += 30.0
        elif price < m5_ema9 < m5_ema21: scalp_score -= 30.0
        elif price > m5_ema9: scalp_score += 15.0
        elif price < m5_ema9: scalp_score -= 15.0

        # Fast VWAP position
        if price > m5_vwap: scalp_score += 25.0
        else: scalp_score -= 25.0

        # SuperTrend on 5m
        if current_m5_st == 1: scalp_score += 25.0
        else: scalp_score -= 25.0

        # Fast RSI Momentum
        if m5_rsi > 60.0: scalp_score += 20.0
        elif m5_rsi < 40.0: scalp_score -= 20.0
        else: scalp_score += ((m5_rsi - 50.0) / 10.0) * 10.0

        scalp_score = max(-100.0, min(100.0, scalp_score))

        if scalp_score >= 50.0:
            scalp_bias = "SCALP_STRONG_BULLISH (Fast Momentum Expansion Above VWAP)"
        elif scalp_score >= 20.0:
            scalp_bias = "SCALP_BULLISH_PULLBACK (Buying Dips Near 9/21 EMA)"
        elif scalp_score <= -50.0:
            scalp_bias = "SCALP_STRONG_BEARISH (Fast Momentum Breakdown Below VWAP)"
        elif scalp_score <= -20.0:
            scalp_bias = "SCALP_BEARISH_PULLBACK (Selling Rallies Into 9/21 EMA)"
        else:
            scalp_bias = "SCALP_RANGING_CONSOLIDATION (Mean Reversion Mode)"

        # ----------------------------------------------------
        # 4. Multi-Timeframe Synthesis (Technical Score: -100 to +100)
        # ----------------------------------------------------
        # 5m Scalp Momentum (35%), 15m Day Trade Structure (40%), 1h Session Trend (25%)
        tech_score = (scalp_score * 0.35) + (day_trade_score * 0.40) + (h1_score * 0.25)
        
        # Confluence Multiplier: If all 3 timeframes are aligned in direction, boost conviction
        if scalp_score > 20 and day_trade_score > 20 and h1_score > 0:
            tech_score = min(100.0, tech_score * 1.25)
        elif scalp_score < -20 and day_trade_score < -20 and h1_score < 0:
            tech_score = max(-100.0, tech_score * 1.25)

        tech_score = max(-100.0, min(100.0, tech_score))

        # Overall Trend Label
        if tech_score >= 40.0:
            trend = "STRONGLY_BULLISH"
        elif tech_score >= 12.0:
            trend = "BULLISH"
        elif tech_score <= -40.0:
            trend = "STRONGLY_BEARISH"
        elif tech_score <= -12.0:
            trend = "BEARISH"
        else:
            trend = "RANGING_NEUTRAL"

        # Volatility Regime
        atr_pct = (current_atr / price * 100.0) if price > 0 else 0.0
        if atr_pct > 0.8:
            volatility = "EXTREME_VOLATILITY"
        elif atr_pct > 0.45:
            volatility = "HIGH_VOLATILITY"
        elif atr_pct < 0.15:
            volatility = "LOW_VOLATILITY"
        else:
            volatility = "NORMAL_VOLATILITY"

        return {
            "price": price,
            "timeframe": "MULTI_TIMEFRAME (5m/15m/1h)",
            "atr": round(current_atr, 2),
            "atr_pct": round(atr_pct, 3),
            "rsi": round(current_rsi, 2),
            "m5_rsi": round(float(m5_rsi), 1),
            "m15_rsi": round(float(m15_rsi), 1),
            "vwap_15m": round(float(m15_vwap), 2),
            "vwap_5m": round(float(m5_vwap), 2),
            "macd": round(current_macd, 3),
            "macd_signal": round(current_macd_sig, 3),
            "macd_hist": round(current_macd_hist, 3),
            "ema_20": round(current_ema20, 2),
            "ema_50": round(current_ema50, 2),
            "ema_200": round(current_ema200, 2),
            "m5_ema9": round(float(m5_ema9), 2),
            "m5_ema21": round(float(m5_ema21), 2),
            "bb_upper": round(float(upper_bb.iloc[-1]), 2) if not upper_bb.empty else price,
            "bb_lower": round(float(lower_bb.iloc[-1]), 2) if not lower_bb.empty else price,
            "trend": trend,
            "volatility": volatility,
            "technical_score": round(tech_score, 1),
            "scalp_score": round(scalp_score, 1),
            "scalp_bias": scalp_bias,
            "day_trade_score": round(day_trade_score, 1),
            "day_trade_bias": day_trade_bias,
            "market_structure": m15_structure.get("structure", "RANGING"),
            "bos": m15_structure.get("bos", "NONE"),
            "data_quality": "GOOD"
        }

    def _default_analysis(self, price: float) -> Dict[str, Any]:
        return {
            "price": price,
            "timeframe": "1h",
            "atr": 0.0,
            "atr_pct": 0.0,
            "rsi": 50.0,
            "m5_rsi": 50.0,
            "m15_rsi": 50.0,
            "vwap_15m": price,
            "vwap_5m": price,
            "macd": 0.0,
            "macd_signal": 0.0,
            "macd_hist": 0.0,
            "ema_20": price,
            "ema_50": price,
            "ema_200": price,
            "m5_ema9": price,
            "m5_ema21": price,
            "bb_upper": price,
            "bb_lower": price,
            "trend": "NEUTRAL",
            "volatility": "NORMAL_VOLATILITY",
            "technical_score": 0.0,
            "scalp_score": 0.0,
            "scalp_bias": "SCALP_RANGING_CONSOLIDATION",
            "day_trade_score": 0.0,
            "day_trade_bias": "DAY_TRADE_RANGING",
            "market_structure": "RANGING",
            "bos": "NONE",
            "data_quality": "LIMITED"
        }

