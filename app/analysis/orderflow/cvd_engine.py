"""Order Flow Delta & Cumulative Volume Delta (CVD) absorption engine for intraday gold scalping."""
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

class OrderFlowDeltaEngine:
    """
    Computes proxy Cumulative Volume Delta (CVD) and aggressor buying/selling imbalances.
    Detects institutional absorption at structural highs/lows:
    - CVD Bullish Absorption: Price makes Lower Low while CVD makes Higher Low (Buyers absorbing sell pressure).
    - CVD Bearish Absorption: Price makes Higher High while CVD makes Lower High (Sellers absorbing buy pressure).
    """

    @staticmethod
    def calculate_cvd(df_5m: pd.DataFrame) -> Dict[str, Any]:
        """Calculates CVD series and detects orderflow absorption divergences."""
        if df_5m.empty or len(df_5m) < 5:
            return {
                "cvd_bias": "BALANCED",
                "delta_score": 0.0,
                "absorption_detected": False,
                "absorption_type": "NONE",
                "delta_divergence": "NONE",
                "recent_delta": 0.0,
                "description": "Insufficient bar volume history for CVD extraction."
            }

        df = df_5m.copy()
        
        # Approximate bar delta using candle body & wick aggressor ratio (Lee-Ready proxy)
        highs = df["high"].values
        lows = df["low"].values
        opens = df["open"].values
        closes = df["close"].values
        volumes = df["volume"].values if "volume" in df.columns else np.ones(len(df)) * 1000.0

        bar_deltas = []
        for i in range(len(df)):
            span = max(0.01, highs[i] - lows[i])
            body = closes[i] - opens[i]
            # Buy volume percentage approximated by candle close position within high-low range
            buy_pct = (closes[i] - lows[i]) / span
            sell_pct = 1.0 - buy_pct
            
            delta = volumes[i] * (buy_pct - sell_pct)
            bar_deltas.append(delta)

        bar_deltas = np.array(bar_deltas)
        cvd_series = np.cumsum(bar_deltas)
        
        recent_delta = float(bar_deltas[-1])
        net_delta_5bars = float(np.sum(bar_deltas[-5:]))
        
        # Check Absorption Divergences over last 10 bars
        window = min(15, len(df))
        price_slice = closes[-window:]
        cvd_slice = cvd_series[-window:]

        price_slope = price_slice[-1] - price_slice[0]
        cvd_slope = cvd_slice[-1] - cvd_slice[0]

        absorption_type = "NONE"
        delta_div = "NONE"
        delta_score = 0.0

        # Bullish Absorption Divergence: Price falling / making lower low, but CVD rising / absorbing
        if price_slope < -1.5 and cvd_slope > 0:
            absorption_type = "BULLISH_ABSORPTION"
            delta_div = "BULLISH_CVD_DIVERGENCE"
            delta_score = 35.0
            description = "Institutional buyers passively absorbing aggressive sell orders at support."
            bias = "BULLISH_ORDERFLOW"

        # Bearish Absorption Divergence: Price rising / making higher high, but CVD falling
        elif price_slope > 1.5 and cvd_slope < 0:
            absorption_type = "BEARISH_ABSORPTION"
            delta_div = "BEARISH_CVD_DIVERGENCE"
            delta_score = -35.0
            description = "Institutional sellers passively absorbing aggressive buy breakout orders at resistance."
            bias = "BEARISH_ORDERFLOW"

        elif net_delta_5bars > 0:
            delta_score = min(25.0, net_delta_5bars / 200.0)
            description = "Net aggressive buying pressure dominant across recent bars."
            bias = "BUY_PRESSURE"
        elif net_delta_5bars < 0:
            delta_score = max(-25.0, net_delta_5bars / 200.0)
            description = "Net aggressive selling pressure dominant across recent bars."
            bias = "SELL_PRESSURE"
        else:
            description = "Order flow delta evenly matched."
            bias = "BALANCED"

        return {
            "cvd_bias": bias,
            "delta_score": round(delta_score, 1),
            "absorption_detected": absorption_type != "NONE",
            "absorption_type": absorption_type,
            "delta_divergence": delta_div,
            "recent_delta": round(recent_delta, 1),
            "net_delta_5bars": round(net_delta_5bars, 1),
            "description": description
        }
