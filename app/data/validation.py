"""Strict validation for external financial data, prices, OHLC, timestamps, and schemas."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from app.core.logging import logger

class DataValidationError(Exception):
    """Raised when incoming data fails validation checks."""
    pass

class DataValidator:
    """Validates financial data integrity, timestamps, and OHLC structures."""

    @staticmethod
    def validate_price(price: Any, symbol: str = "XAUUSD") -> float:
        """Validates that a price is a positive, non-zero, realistic numeric float."""
        try:
            val = float(price)
        except (ValueError, TypeError):
            raise DataValidationError(f"Invalid price value '{price}' for symbol {symbol}.")

        if val <= 0:
            raise DataValidationError(f"Non-positive price {val} encountered for symbol {symbol}.")

        # Sanity check for gold price range (e.g., $1000 - $10,000)
        if "GC" in symbol or "XAU" in symbol:
            if val < 500.0 or val > 20000.0:
                raise DataValidationError(f"Unrealistic gold price value {val} for {symbol}.")

        return val

    @staticmethod
    def validate_ohlc_df(df: pd.DataFrame, timeframe: str = "1h") -> pd.DataFrame:
        """
        Validates OHLC DataFrame integrity:
        - High >= max(Open, Close, Low)
        - Low <= min(Open, Close, High)
        - No NaN or Inf
        - Sorted timestamps
        """
        if df.empty:
            raise DataValidationError(f"Empty OHLC DataFrame provided for timeframe {timeframe}.")

        required_cols = ["open", "high", "low", "close"]
        # Normalize column names to lowercase
        df.columns = [str(c).lower() for c in df.columns]

        for col in required_cols:
            if col not in df.columns:
                raise DataValidationError(f"Missing required OHLC column '{col}' in timeframe {timeframe}.")

        # Drop rows with nulls in OHLC
        clean_df = df.dropna(subset=required_cols).copy()

        if clean_df.empty:
            raise DataValidationError(f"All rows contained NaN values in OHLC for timeframe {timeframe}.")

        # Ensure numeric
        for col in required_cols:
            clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce")

        clean_df = clean_df.dropna(subset=required_cols)

        # Check OHLC logical constraints
        invalid_high = clean_df["high"] < clean_df[["open", "close", "low"]].max(axis=1)
        invalid_low = clean_df["low"] > clean_df[["open", "close", "high"]].min(axis=1)
        invalid_pos = (clean_df[required_cols] <= 0).any(axis=1)

        invalid_mask = invalid_high | invalid_low | invalid_pos
        if invalid_mask.any():
            invalid_count = int(invalid_mask.sum())
            logger.warning(f"Discarding {invalid_count} corrupt/invalid OHLC bars in timeframe {timeframe}.")
            clean_df = clean_df[~invalid_mask]

        if len(clean_df) < 3:
            raise DataValidationError(f"Insufficient valid bars ({len(clean_df)}) for timeframe {timeframe}.")

        return clean_df

    @staticmethod
    def is_timestamp_fresh(ts: datetime, max_age_seconds: int = 86400) -> bool:
        """Checks if a timestamp is within the acceptable freshness window."""
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age = (now - ts).total_seconds()
        return age <= max_age_seconds
