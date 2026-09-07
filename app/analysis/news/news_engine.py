"""News Engine for real-time sentiment aggregation, recency decay weighting, and impact ranking."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np
from app.core.logging import logger

class NewsEngine:
    """Processes real-time news events with exponential recency decay for scalping & day trading sentiment."""

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

        now_utc = datetime.now(timezone.utc)
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
            pub_time = item.get("published_time")

            # Calculate recency multiplier
            if pub_time and isinstance(pub_time, datetime):
                if pub_time.tzinfo is None:
                    pub_time = pub_time.replace(tzinfo=timezone.utc)
                age_hours = max(0.0, (now_utc - pub_time).total_seconds() / 3600.0)
            else:
                age_hours = 2.0

            if age_hours <= 0.25:    # Under 15 minutes (Breaking news flash)
                recency_mult = 2.5
            elif age_hours <= 1.0:   # Under 1 hour
                recency_mult = 2.0
            elif age_hours <= 4.0:   # Under 4 hours
                recency_mult = 1.3
            elif age_hours <= 12.0:  # Under 12 hours
                recency_mult = 0.8
            elif age_hours <= 24.0:  # Under 24 hours
                recency_mult = 0.4
            else:                    # Over 24 hours (Stale news)
                recency_mult = 0.1

            impact_mult = 2.2 if impact == "CRITICAL" else 1.6 if impact == "HIGH" else 1.0
            weight = (relevance / 100.0) * impact_mult * recency_mult
            total_weight += weight

            if gold_impact == "BULLISH":
                bullish_weights += weight
                bullish_count += 1
            elif gold_impact == "BEARISH":
                bearish_weights += weight
                bearish_count += 1
            else:
                neutral_count += 1

            if impact in ["CRITICAL", "HIGH"] and age_hours <= 12.0:
                critical_events.append(item)

            if len(top_headlines) < 6:
                top_headlines.append({
                    "title": item["title"],
                    "source": item["source"],
                    "gold_impact": gold_impact,
                    "impact_level": impact,
                    "published_time": item.get("published_time"),
                    "age_minutes": int(age_hours * 60)
                })

        # Calculate recency-weighted net score (-100 to +100)
        if total_weight > 0:
            net_ratio = (bullish_weights - bearish_weights) / total_weight
            news_score = round(net_ratio * 100.0, 1)
        else:
            news_score = 0.0

        sentiment_bias = "BULLISH" if news_score >= 15.0 else \
                         "BEARISH" if news_score <= -15.0 else "NEUTRAL"

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

