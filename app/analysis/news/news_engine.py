"""News Engine for sentiment aggregation, deduplication, and impact ranking."""
from typing import Any, Dict, List, Optional
import numpy as np
from app.core.logging import logger

class NewsEngine:
    """Processes news events to generate net sentiment score (-100 to +100) and top drivers."""

    def analyze(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not news_items:
            return {
                "news_score": 0.0,
                "sentiment_bias": "NEUTRAL",
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0,
                "critical_events": [],
                "top_headlines": [],
                "summary": "No recent high-impact news detected."
            }

        bullish_weights = 0.0
        bearish_weights = 0.0
        total_weight = 0.0

        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        critical_events = []
        top_headlines = []

        for item in news_items:
            relevance = item.get("relevance_score", 30.0)
            impact = item.get("impact_level", "LOW")
            gold_impact = item.get("gold_impact", "NEUTRAL")

            multiplier = 2.0 if impact == "CRITICAL" else 1.5 if impact == "HIGH" else 1.0
            weight = (relevance / 100.0) * multiplier
            total_weight += weight

            if gold_impact == "BULLISH":
                bullish_weights += weight
                bullish_count += 1
            elif gold_impact == "BEARISH":
                bearish_weights += weight
                bearish_count += 1
            else:
                neutral_count += 1

            if impact in ["CRITICAL", "HIGH"]:
                critical_events.append(item)

            if len(top_headlines) < 6:
                top_headlines.append({
                    "title": item["title"],
                    "source": item["source"],
                    "gold_impact": gold_impact,
                    "impact_level": impact,
                    "published_time": item.get("published_time")
                })

        # Calculate net score (-100 to +100)
        if total_weight > 0:
            net_ratio = (bullish_weights - bearish_weights) / total_weight
            news_score = round(net_ratio * 100.0, 1)
        else:
            news_score = 0.0

        sentiment_bias = "BULLISH" if news_score >= 20.0 else \
                         "BEARISH" if news_score <= -20.0 else "NEUTRAL"

        return {
            "news_score": news_score,
            "sentiment_bias": sentiment_bias,
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "neutral_count": neutral_count,
            "critical_events": critical_events[:3],
            "top_headlines": top_headlines,
            "total_articles_analyzed": len(news_items)
        }
