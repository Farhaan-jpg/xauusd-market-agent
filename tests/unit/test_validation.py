"""Unit tests for DataValidator ensuring rejection of invalid/corrupted data."""
from datetime import datetime, timedelta, timezone
import pandas as pd
import pytest
from app.data.validation import DataValidationError, DataValidator

def test_valid_price_validation():
    p = DataValidator.validate_price(2540.50, symbol="GC=F")
    assert p == 2540.50

def test_negative_or_zero_price_rejected():
    with pytest.raises(DataValidationError):
        DataValidator.validate_price(-10.0, symbol="GC=F")
    with pytest.raises(DataValidationError):
        DataValidator.validate_price(0.0, symbol="GC=F")
    with pytest.raises(DataValidationError):
        DataValidator.validate_price("invalid_string", symbol="GC=F")

def test_unrealistic_gold_price_rejected():
    with pytest.raises(DataValidationError):
        DataValidator.validate_price(50000.0, symbol="XAUUSD")
    with pytest.raises(DataValidationError):
        DataValidator.validate_price(100.0, symbol="XAUUSD")

def test_corrupted_ohlc_filtering():
    # Construct dataframe with an invalid bar (High < Low)
    bad_df = pd.DataFrame({
        "open": [2500, 2505, 2510, 2515, 2520],
        "high": [2502, 2490, 2512, 2518, 2522], # Row 1 high < open (2490 < 2505)
        "low":  [2495, 2500, 2508, 2512, 2518],
        "close": [2501, 2504, 2511, 2517, 2521]
    })
    # Should discard row 1 and accept remaining valid bars
    cleaned = DataValidator.validate_ohlc_df(bad_df, timeframe="1h")
    assert len(cleaned) == 4

def test_timestamp_freshness():
    now = datetime.now(timezone.utc)
    fresh_ts = now - timedelta(minutes=10)
    stale_ts = now - timedelta(days=5)

    assert DataValidator.is_timestamp_fresh(fresh_ts, max_age_seconds=3600) is True
    assert DataValidator.is_timestamp_fresh(stale_ts, max_age_seconds=3600) is False
