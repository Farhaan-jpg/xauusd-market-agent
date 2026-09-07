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
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """Calculates Volume Weighted Average Price (VWAP) or Typical Price proxy if volume is flat."""
        high = df["high"]
        low = df["low"]
        close = df["close"]
        typical_price = (high + low + close) / 3.0
        
        if "volume" in df.columns and (df["volume"] > 0).any():
            volume = df["volume"].replace(0, 1.0)
            pv = typical_price * volume
            vwap = pv.cumsum() / volume.cumsum()
            return vwap
        else:
            # Cumulative moving typical price when real tick volume is absent
            return typical_price.expanding().mean()

    @staticmethod
    def calculate_supertrend(
        df: pd.DataFrame,
        period: int = 10,
        multiplier: float = 3.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculates SuperTrend indicator (upper band, lower band, and trend direction: 1 bull, -1 bear)."""
        hl2 = (df["high"] + df["low"]) / 2.0
        atr = TechnicalIndicators.calculate_atr(df, period=period)
        
        upper_basic = hl2 + (multiplier * atr)
        lower_basic = hl2 - (multiplier * atr)
        
        n = len(df)
        if n == 0:
            return pd.Series(dtype=float), pd.Series(dtype=float), pd.Series(dtype=int)

        close = df["close"].to_numpy()
        u_b = upper_basic.to_numpy()
        l_b = lower_basic.to_numpy()
        u_f = upper_basic.to_numpy(copy=True)
        l_f = lower_basic.to_numpy(copy=True)
        dir_val = np.ones(n, dtype=int)
        
        for i in range(1, n):
            # Lower band
            if l_b[i] > l_f[i-1] or close[i-1] < l_f[i-1]:
                l_f[i] = l_b[i]
            else:
                l_f[i] = l_f[i-1]
                
            # Upper band
            if u_b[i] < u_f[i-1] or close[i-1] > u_f[i-1]:
                u_f[i] = u_b[i]
            else:
                u_f[i] = u_f[i-1]
                
            # Direction
            if dir_val[i-1] == 1:
                if close[i] < l_f[i]:
                    dir_val[i] = -1
                else:
                    dir_val[i] = 1
            else:
                if close[i] > u_f[i]:
                    dir_val[i] = 1
                else:
                    dir_val[i] = -1
                    
        return pd.Series(u_f, index=df.index), pd.Series(l_f, index=df.index), pd.Series(dir_val, index=df.index)

    @staticmethod
    def detect_market_structure(df: pd.DataFrame, window: int = 2) -> Dict[str, Any]:
        """Detects Higher Highs / Higher Lows (BULLISH) vs Lower Highs / Lower Lows (BEARISH) and Break of Structure (BOS)."""
        highs, lows = TechnicalIndicators.find_swing_highs_and_lows(df, window=window)
        if len(highs) < 2 or len(lows) < 2:
            return {
                "structure": "RANGING",
                "structure_score": 0.0,
                "bos": "NONE",
                "last_swing_high": float(highs[-1]["price"]) if highs else 0.0,
                "last_swing_low": float(lows[-1]["price"]) if lows else 0.0
            }
            
        h1, h2 = highs[-2]["price"], highs[-1]["price"]
        l1, l2 = lows[-2]["price"], lows[-1]["price"]
        curr_price = float(df["close"].iloc[-1])
        
        is_higher_highs = h2 > h1
        is_higher_lows = l2 > l1
        is_lower_highs = h2 < h1
        is_lower_lows = l2 < l1
        
        # Break of Structure (BOS)
        bos = "NONE"
        if curr_price > h2 and is_higher_highs:
            bos = "BULLISH_BOS"
        elif curr_price < l2 and is_lower_lows:
            bos = "BEARISH_BOS"
        elif curr_price < l1 and is_higher_highs:
            bos = "BEARISH_CHOCH" # Change of character
        elif curr_price > h1 and is_lower_lows:
            bos = "BULLISH_CHOCH"
            
        if is_lower_highs and is_lower_lows:
            structure = "BEARISH_STRUCTURE" # Classic Lower Highs & Lower Lows
            score = -35.0
        elif is_higher_highs and is_higher_lows:
            structure = "BULLISH_STRUCTURE" # Classic Higher Highs & Higher Lows
            score = 35.0
        elif is_lower_highs:
            structure = "BEARISH_LEAN" # Lower high pressure
            score = -20.0
        elif is_higher_lows:
            structure = "BULLISH_LEAN" # Higher low support
            score = 20.0
        else:
            structure = "RANGING_STRUCTURE"
            score = 0.0
            
        if "BEARISH" in bos:
            score -= 15.0
        elif "BULLISH" in bos:
            score += 15.0
            
        return {
            "structure": structure,
            "structure_score": max(-50.0, min(50.0, score)),
            "bos": bos,
            "last_swing_high": h2,
            "last_swing_low": l2,
            "prev_swing_high": h1,
            "prev_swing_low": l1
        }

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
