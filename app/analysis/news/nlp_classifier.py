"""Financial NLP Classifier for Central Bank accumulation, Fed speaker tone, and geopolitical urgency."""
from typing import Any, Dict, List, Optional

FED_HAWKISH_KEYWORDS = ["hike", "higher for longer", "inflation sticky", "restrictive", "not ready to cut", "tame inflation", "tight labor"]
FED_DOVISH_KEYWORDS = ["rate cut", "easing", "inflation cooling", "labor market softening", "recession risk", "lower rates", "pivot"]
CENTRAL_BANK_BUYING_KEYWORDS = ["central bank", "pboc", "rbi", "gold reserves", "bullion purchases", "de-dollarization", "reserve accumulation"]
GEOPOLITICAL_KEYWORDS = ["war", "missile", "airstrike", "conflict", "sanctions", "retaliation", "escalation", "tensions", "military"]

class FinancialNLPClassifier:
    """Classifies financial news headlines into structured institutional signals."""

    @staticmethod
    def classify_headlines(news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluates Fed sentiment, Central Bank buying score, and geopolitical risk urgency."""
        fed_score = 0.0
        cb_buying_score = 0.0
        geopolitical_score = 0.0
        
        detected_themes = []

        for item in news_items:
            title = (item.get("title", "") if isinstance(item, dict) else getattr(item, "title", "")).lower()
            
            # 1. Fed Tone Analysis (Dovish = Bullish for Gold, Hawkish = Bearish for Gold)
            if any(k in title for k in FED_DOVISH_KEYWORDS):
                fed_score += 25.0
                detected_themes.append(f"Dovish Fed Signal: {title[:60]}")
            elif any(k in title for k in FED_HAWKISH_KEYWORDS):
                fed_score -= 25.0
                detected_themes.append(f"Hawkish Fed Signal: {title[:60]}")

            # 2. Central Bank Gold Buying
            if any(k in title for k in CENTRAL_BANK_BUYING_KEYWORDS):
                cb_buying_score += 30.0
                detected_themes.append(f"Central Bank Reserve Accumulation: {title[:60]}")

            # 3. Geopolitical Risk
            if any(k in title for k in GEOPOLITICAL_KEYWORDS):
                geopolitical_score += 20.0
                detected_themes.append(f"Geopolitical Safe-Haven Catalyst: {title[:60]}")

        fed_score = max(-100.0, min(100.0, fed_score))
        cb_buying_score = min(100.0, cb_buying_score)
        geopolitical_score = min(100.0, geopolitical_score)

        return {
            "fed_sentiment_score": round(fed_score, 1),
            "central_bank_buying_score": round(cb_buying_score, 1),
            "geopolitical_risk_score": round(geopolitical_score, 1),
            "detected_themes": detected_themes[:5],
            "nlp_composite_gold_impact": "BULLISH" if (fed_score + cb_buying_score + geopolitical_score) > 15.0 else \
                                         "BEARISH" if fed_score < -20.0 else "NEUTRAL"
        }
