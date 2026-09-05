"""Unit tests for Geopolitical Conflict Escalation Index (CEI) Engine."""
import pytest
from app.analysis.geopolitical.conflict_engine import GeopoliticalConflictEngine

def test_conflict_engine_escalation_scoring():
    engine = GeopoliticalConflictEngine()
    
    # Test with geopolitical news articles
    news_items = [
        {"title": "Missile strikes reported across Middle East oil facilities", "description": "Tensions surge as military action escalates", "category": "WAR_CONFLICT"},
        {"title": "Sovereign sanctions tightened amid Eastern Europe conflict escalation", "description": "Diplomatic standoff intensifies", "category": "GEOPOLITICAL"},
        {"title": "US CPI data released slightly above expectations", "description": "Inflation metrics published", "category": "MACRO"}
    ]
    
    result = engine.analyze(news_items=news_items, gold_price=2900.0)
    
    assert "conflict_escalation_index" in result
    assert 0.0 <= result["conflict_escalation_index"] <= 100.0
    assert result["conflict_escalation_index"] > 20.0  # News contains conflict keywords
    assert "safe_haven_premium_usd" in result
    assert result["safe_haven_premium_usd"] > 0.0
    assert "flashpoints" in result
    assert len(result["flashpoints"]) >= 3
    assert "status_level" in result

def test_conflict_engine_empty_news():
    engine = GeopoliticalConflictEngine()
    result = engine.analyze(news_items=[], gold_price=2900.0)
    
    assert "conflict_escalation_index" in result
    assert result["conflict_escalation_index"] >= 10.0  # Baseline active flashpoints
    assert result["safe_haven_premium_usd"] >= 0.0
