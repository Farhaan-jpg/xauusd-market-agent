"""Unit tests for Scalping & Day Trading enhancements, VWAP, Market Structure, and News Recency Decay."""
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
import pytest
from app.analysis.news.news_engine import NewsEngine
from app.analysis.sentiment.market_direction_engine import MarketDirectionEngine
from app.analysis.technical.indicators import TechnicalIndicators
from app.analysis.technical.market_engine import MarketEngine

def test_vwap_and_supertrend_calculation(sample_ohlc_df):
    vwap = TechnicalIndicators.calculate_vwap(sample_ohlc_df)
    assert not vwap.empty
    assert len(vwap) == len(sample_ohlc_df)
    assert (vwap > 0).all()

    upper, lower, direction = TechnicalIndicators.calculate_supertrend(sample_ohlc_df, period=7, multiplier=2.5)
    assert len(upper) == len(sample_ohlc_df)
    assert len(lower) == len(sample_ohlc_df)
    assert len(direction) == len(sample_ohlc_df)
    assert set(direction.unique()).issubset({-1, 1})

def test_market_structure_lower_highs_lower_lows():
    dates = pd.date_range("2026-09-07 10:00", periods=20, freq="15min", tz="UTC")
    prices = [2950, 2940, 2945, 2930, 2935, 2920, 2925, 2910, 2915, 2900,
              2905, 2890, 2895, 2880, 2885, 2870, 2875, 2860, 2865, 2850]
    records = []
    for d, p in zip(dates, prices):
        records.append({
            "timestamp": d,
            "open": p + 1.0,
            "high": p + 3.0,
            "low": p - 3.0,
            "close": p,
            "volume": 1000.0
        })
    df = pd.DataFrame(records).set_index("timestamp")
    structure = TechnicalIndicators.detect_market_structure(df, window=1)
    
    assert "BEARISH" in structure["structure"]
    assert structure["structure_score"] < 0.0

def test_market_engine_scalp_and_day_trade_bias():
    engine = MarketEngine()
    dates = pd.date_range("2026-09-07 10:00", periods=30, freq="5min", tz="UTC")
    records = []
    for i, d in enumerate(dates):
        p = 2900.0 - (i * 1.5)
        records.append({
            "timestamp": d,
            "open": p + 1.0,
            "high": p + 2.0,
            "low": p - 2.0,
            "close": p,
            "volume": 500.0
        })
    df_5m = pd.DataFrame(records).set_index("timestamp")
    df_15m = df_5m.resample("15min").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    df_1h = df_5m.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()

    market_data = {
        "price": float(df_5m["close"].iloc[-1]),
        "timeframes": {
            "5m": df_5m,
            "15m": df_15m,
            "1h": df_1h
        }
    }

    analysis = engine.analyze(market_data)
    assert analysis["technical_score"] < -30.0
    assert "BEARISH" in analysis["trend"]
    assert "BEARISH" in analysis["scalp_bias"]
    assert "BEARISH" in analysis["day_trade_bias"]

def test_news_recency_decay():
    engine = NewsEngine()
    now = datetime.now(timezone.utc)
    
    fresh_item = {
        "fingerprint": "fresh1",
        "source": "ForexLive",
        "title": "US CPI Surges to Hot 3.8%, Fed to Hike Rates Aggressively",
        "published_time": now - timedelta(minutes=5),
        "relevance_score": 90.0,
        "impact_level": "CRITICAL",
        "gold_impact": "BEARISH"
    }
    
    stale_item = {
        "fingerprint": "stale1",
        "source": "Random News",
        "title": "Safe haven buying continues in early week",
        "published_time": now - timedelta(days=2),
        "relevance_score": 80.0,
        "impact_level": "HIGH",
        "gold_impact": "BULLISH"
    }
    
    result = engine.analyze([fresh_item, stale_item])
    assert result["news_score"] < -20.0
    assert result["sentiment_bias"] == "BEARISH"

def test_market_direction_engine_responsiveness_for_scalping():
    engine = MarketDirectionEngine()
    market_analysis = {
        "price": 2850.0,
        "technical_score": -65.0,
        "scalp_score": -70.0,
        "day_trade_score": -60.0,
        "scalp_bias": "SCALP_STRONG_BEARISH",
        "day_trade_bias": "DAY_TRADE_BEARISH",
        "market_structure": "BEARISH_STRUCTURE",
        "trend": "STRONGLY_BEARISH",
        "volatility": "HIGH_VOLATILITY",
        "data_quality": "GOOD"
    }
    liquidity_analysis = {
        "order_flow_bias": "BEARISH_ORDER_FLOW",
        "liquidity_above": [{"strength": 80.0, "price": 2860.0}],
        "liquidity_below": []
    }
    macro_analysis = {"macro_score": 0.0, "usd_score": 0.0, "yield_score": 0.0}
    news_analysis = {"news_score": -20.0}

    direction = engine.calculate_direction(
        market_analysis=market_analysis,
        liquidity_analysis=liquidity_analysis,
        macro_analysis=macro_analysis,
        news_analysis=news_analysis,
        economic_events=[]
    )

    assert direction["direction"] in ["BEARISH", "STRONGLY BEARISH"]
    assert direction["direction_score"] <= -20.0
    assert direction["scalp_bias"] == "SCALP_STRONG_BEARISH"
