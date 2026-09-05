"""Pytest fixtures providing synthetic OHLC, Macro, News, and Calendar datasets."""
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
import pytest

@pytest.fixture
def sample_ohlc_df() -> pd.DataFrame:
    """Generates 100 bars of realistic synthetic Gold 1H OHLCV data."""
    dates = pd.date_range(end=datetime.now(timezone.utc), periods=100, freq="1h")
    np.random.seed(42)

    base_price = 2500.0
    returns = np.random.normal(0.0002, 0.002, size=100)
    prices = base_price * np.exp(np.cumsum(returns))

    highs = prices * (1 + np.random.uniform(0.0005, 0.003, size=100))
    lows = prices * (1 - np.random.uniform(0.0005, 0.003, size=100))
    opens = prices * (1 + np.random.uniform(-0.001, 0.001, size=100))
    closes = prices
    volumes = np.random.randint(1000, 50000, size=100)

    # Ensure OHLC validity
    for i in range(100):
        highs[i] = max(highs[i], opens[i], closes[i])
        lows[i] = min(lows[i], opens[i], closes[i])

    df = pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes
    }, index=dates)

    return df

@pytest.fixture
def sample_market_data(sample_ohlc_df) -> dict:
    return {
        "symbol": "GC=F",
        "price": float(sample_ohlc_df["close"].iloc[-1]),
        "change_24h": 0.45,
        "high_24h": float(sample_ohlc_df["high"].iloc[-1]),
        "low_24h": float(sample_ohlc_df["low"].iloc[-1]),
        "timestamp": datetime.now(timezone.utc),
        "timeframes": {
            "1h": sample_ohlc_df,
            "15m": sample_ohlc_df.iloc[-20:],
            "1d": sample_ohlc_df.iloc[-10:]
        },
        "data_quality": "GOOD"
    }

@pytest.fixture
def sample_macro_data() -> dict:
    return {
        "dxy": {"symbol": "DX-Y.NYB", "price": 103.50, "change_pct": -0.35, "available": True},
        "us10y": {"symbol": "^TNX", "price": 4.15, "yield_pct": 4.15, "change_pct": -1.2, "available": True},
        "us2y": {"symbol": "^IRX", "price": 4.05, "yield_pct": 4.05, "change_pct": -0.8, "available": True},
        "tip": {"symbol": "TIP", "price": 108.20, "change_pct": 0.40, "available": True},
        "vix": {"symbol": "^VIX", "price": 16.5, "change_pct": 2.0, "available": True},
        "yield_spread_10y_2y": 0.10,
        "timestamp": datetime.now(timezone.utc),
        "status": "AVAILABLE"
    }

@pytest.fixture
def sample_news_items() -> list:
    return [
        {
            "fingerprint": "abc1",
            "source": "Kitco Metals",
            "title": "Gold rallies to fresh highs as Federal Reserve signals dovish rate cuts",
            "published_time": datetime.now(timezone.utc),
            "url": "https://example.com/news1",
            "category": "CENTRAL_BANK",
            "relevance_score": 85.0,
            "sentiment": "POSITIVE",
            "gold_impact": "BULLISH",
            "impact_level": "HIGH"
        },
        {
            "fingerprint": "abc2",
            "source": "FXStreet",
            "title": "US Dollar weakens across the board following soft inflation figures",
            "published_time": datetime.now(timezone.utc),
            "url": "https://example.com/news2",
            "category": "MACRO",
            "relevance_score": 75.0,
            "sentiment": "POSITIVE",
            "gold_impact": "BULLISH",
            "impact_level": "MEDIUM"
        }
    ]
