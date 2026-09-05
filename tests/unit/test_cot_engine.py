"""Unit tests for CFTC COT & Central Bank Reserve Flow Engine."""
import pytest
from app.analysis.institutional.cot_engine import InstitutionalCOTEngine

def test_cot_engine_telemetry():
    engine = InstitutionalCOTEngine()
    result = engine.analyze(gold_price=2900.0)
    
    assert "managed_money" in result
    assert result["managed_money"]["net_contracts"] > 0
    assert "long_short_ratio" in result["managed_money"]
    assert result["managed_money"]["long_short_ratio"] > 1.0
    assert "central_banks" in result
    assert result["central_banks"]["quarterly_pace_tonnes"] > 200
    assert "institutional_bias" in result
    assert "summary_statement" in result
