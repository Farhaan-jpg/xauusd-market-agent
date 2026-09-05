"""Mathematical and statistical calculations for technical indicators using pure Pandas & NumPy."""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

class TechnicalIndicators:
    """Computes ATR, RSI, MACD, EMAs, Bollinger Bands, and Swing Pivots."""

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        high = df["high"]
        low = df["low"]
        close = df["close"]
        prev_close = close.shift(1)

        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.ewm(span=period, adjust=False).mean()
        return atr

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50.0)

    @staticmethod
    def calculate_macd(
        df: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        close = df["close"]
        ema_fast = close.ewm(span=fast_period, adjust=False).mean()
        ema_slow = close.ewm(span=slow_period, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def calculate_ema(df: pd.DataFrame, span: int) -> pd.Series:
        return df["close"].ewm(span=span, adjust=False).mean()

    @staticmethod
    def calculate_sma(df: pd.DataFrame, window: int) -> pd.Series:
        return df["close"].rolling(window=window, min_periods=1).mean()

    @staticmethod
    def calculate_bollinger_bands(
        df: pd.DataFrame,
        period: int = 20,
        num_std: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        sma = df["close"].rolling(window=period, min_periods=1).mean()
        std = df["close"].rolling(window=period, min_periods=1).std().fillna(0)
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        return upper_band, sma, lower_band

    @staticmethod
    def find_swing_highs_and_lows(
        df: pd.DataFrame,
        window: int = 3
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Identifies pivot swing highs and lows with confirmation window."""
        highs = []
        lows = []
        n = len(df)

        if n < (window * 2 + 1):
            return highs, lows

        high_series = df["high"].values
        low_series = df["low"].values
        close_series = df["close"].values
        indices = df.index

        for i in range(window, n - window):
            curr_high = high_series[i]
            curr_low = low_series[i]

            # Swing High condition
            if all(curr_high > high_series[i - j] for j in range(1, window + 1)) and \
               all(curr_high >= high_series[i + j] for j in range(1, window + 1)):
                highs.append({
                    "index": i,
                    "timestamp": str(indices[i]),
                    "price": float(curr_high),
                    "type": "SWING_HIGH"
                })

            # Swing Low condition
            if all(curr_low < low_series[i - j] for j in range(1, window + 1)) and \
               all(curr_low <= low_series[i + j] for j in range(1, window + 1)):
                lows.append({
                    "index": i,
                    "timestamp": str(indices[i]),
                    "price": float(curr_low),
                    "type": "SWING_LOW"
                })

        return highs, lows
