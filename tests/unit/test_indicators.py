"""Unit tests for TechnicalIndicators and statistical calculations."""
import pandas as pd
import pytest
from app.analysis.technical.indicators import TechnicalIndicators

def test_atr_calculation(sample_ohlc_df):
    atr = TechnicalIndicators.calculate_atr(sample_ohlc_df, period=14)
    assert not atr.empty
    assert len(atr) == len(sample_ohlc_df)
    assert (atr > 0).all()

def test_rsi_calculation(sample_ohlc_df):
    rsi = TechnicalIndicators.calculate_rsi(sample_ohlc_df, period=14)
    assert not rsi.empty
    assert len(rsi) == len(sample_ohlc_df)
    # RSI must be strictly bounded between 0 and 100
    assert (rsi >= 0).all() and (rsi <= 100).all()

def test_macd_calculation(sample_ohlc_df):
    macd, signal, hist = TechnicalIndicators.calculate_macd(sample_ohlc_df)
    assert len(macd) == len(sample_ohlc_df)
    assert len(signal) == len(sample_ohlc_df)
    assert len(hist) == len(sample_ohlc_df)
    # Histogram must equal macd - signal
    pd.testing.assert_series_equal(hist, macd - signal)

def test_ema_and_bollinger_bands(sample_ohlc_df):
    ema20 = TechnicalIndicators.calculate_ema(sample_ohlc_df, span=20)
    upper, mid, lower = TechnicalIndicators.calculate_bollinger_bands(sample_ohlc_df, period=20)

    assert len(ema20) == len(sample_ohlc_df)
    assert (upper >= mid).all()
    assert (mid >= lower).all()

def test_swing_pivot_detection(sample_ohlc_df):
    highs, lows = TechnicalIndicators.find_swing_highs_and_lows(sample_ohlc_df, window=2)
    assert isinstance(highs, list)
    assert isinstance(lows, list)
    if highs:
        assert "price" in highs[0]
        assert highs[0]["type"] == "SWING_HIGH"
