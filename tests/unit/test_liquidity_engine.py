"""Unit tests for LiquidityEngine detecting zones and calculating strength."""
import pytest
from app.analysis.liquidity.liquidity_engine import LiquidityEngine

def test_liquidity_engine_zone_detection(sample_market_data):
    engine = LiquidityEngine()
    result = engine.analyze(sample_market_data)

    assert "current_price" in result
    assert "liquidity_above" in result
    assert "liquidity_below" in result
    assert "aggregate_liquidity_score" in result
    assert isinstance(result["all_zones"], list)

    # Check strength score bounds (0 to 100)
    for z in result["all_zones"]:
        assert 0.0 <= z["strength"] <= 100.0
        assert z["zone_range_low"] <= z["price"] <= z["zone_range_high"]
        assert z["classification"] in ["LOW", "MODERATE", "HIGH", "VERY_HIGH"]

def test_liquidity_separation_above_and_below(sample_market_data):
    engine = LiquidityEngine()
    result = engine.analyze(sample_market_data)
    price = result["current_price"]

    for z in result["liquidity_above"]:
        assert z["price"] >= price

    for z in result["liquidity_below"]:
        assert z["price"] <= price
