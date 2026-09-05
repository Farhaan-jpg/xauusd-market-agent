"""Unit tests for NewsEngine scoring and impact categorization."""
import pytest
from app.analysis.news.news_engine import NewsEngine

def test_news_engine_sentiment_aggregation(sample_news_items):
    engine = NewsEngine()
    result = engine.analyze(sample_news_items)

    assert "news_score" in result
    assert "sentiment_bias" in result
    assert result["bullish_count"] == 2
    assert result["bearish_count"] == 0
    assert result["news_score"] > 0
    assert result["sentiment_bias"] == "BULLISH"

def test_empty_news_handling():
    engine = NewsEngine()
    result = engine.analyze([])
    assert result["news_score"] == 0.0
    assert result["sentiment_bias"] == "NEUTRAL"
