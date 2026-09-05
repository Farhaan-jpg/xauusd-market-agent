"""News Provider aggregating multiple financial RSS feeds for Gold, Macro, and Central Bank news."""
import asyncio
from datetime import datetime, timezone
import hashlib
import re
import time
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
import feedparser
import httpx
from app.core.logging import logger
from app.data.base import BaseDataProvider

# Financial & Gold RSS Feeds
RSS_FEEDS = [
    {"source": "FXStreet Gold", "url": "https://www.fxstreet.com/rss/news/commodities/gold", "weight": 1.2},
    {"source": "Kitco Metals", "url": "https://www.kitco.com/rss/news.html", "weight": 1.3},
    {"source": "CNBC Economy", "url": "https://search.cnbc.com/rs/search/combinedserver/search.xml?partnerId=wrss01&id=20910258", "weight": 1.1},
    {"source": "MarketWatch Top", "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories", "weight": 1.0},
    {"source": "Federal Reserve", "url": "https://www.federalreserve.gov/feeds/press_all.xml", "weight": 1.5},
    {"source": "Investing.com Commodities", "url": "https://www.investing.com/rss/commodities_News.rss", "weight": 1.1},
]

KEYWORDS_GOLD_BULLISH = [
    "rate cut", "dovish", "inflation surges", "war", "geopolitical tension", "safe haven",
    "dollar drops", "yields slide", "gold surges", "gold rallies", "central bank buying",
    "gold demand rises", "escalation", "banking crisis", "stagflation", "weak nfp", "weak jobs"
]

KEYWORDS_GOLD_BEARISH = [
    "rate hike", "hawkish", "higher for longer", "dollar strengthens", "yields surge",
    "strong economy", "strong nfp", "hot cpi", "gold drops", "gold tumbles", "de-escalation",
    "fed pause on cuts", "us growth resilient", "selloff"
]

KEYWORDS_HIGH_IMPACT = [
    "fomc", "fed", "powell", "cpi", "pce", "nfp", "nonfarm payrolls", "interest rate",
    "inflation", "gdp", "treasury", "middle east", "russia", "china", "tariffs", "sanctions"
]

class NewsProvider(BaseDataProvider):
    """Aggregates and processes real-time news for Gold, Macro, and Geopolitics."""

    def __init__(self):
        super().__init__(name="News_RSS_Provider")

    async def fetch(self) -> List[Dict[str, Any]]:
        start_time = time.time()
        try:
            loop = asyncio.get_running_loop()
            news_items = await loop.run_in_executor(None, self._fetch_all_feeds_sync)
            latency_ms = (time.time() - start_time) * 1000
            await self.record_health(is_healthy=True, latency_ms=latency_ms)
            return news_items
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"NewsProvider error: {e}")
            await self.record_health(is_healthy=False, latency_ms=latency_ms, error_message=str(e))
            return []

    def _fetch_all_feeds_sync(self) -> List[Dict[str, Any]]:
        all_news = []
        for feed_config in RSS_FEEDS:
            try:
                parsed = feedparser.parse(
                    feed_config["url"],
                    request_headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )
                for entry in parsed.entries[:10]:
                    item = self._process_entry(entry, feed_config["source"], feed_config["weight"])
                    if item and item["relevance_score"] >= 20.0:
                        all_news.append(item)
            except Exception as e:
                logger.debug(f"Failed parsing feed {feed_config['source']}: {e}")
                continue

        # Sort by relevance and recency
        all_news.sort(key=lambda x: (x["impact_level"] == "CRITICAL", x["relevance_score"]), reverse=True)
        return all_news

    def _process_entry(self, entry: Any, source: str, weight: float) -> Optional[Dict[str, Any]]:
        title = entry.get("title", "").strip()
        if not title:
            return None

        summary_raw = entry.get("summary", "") or entry.get("description", "")
        summary = BeautifulSoup(summary_raw, "html.parser").get_text().strip() if summary_raw else ""
        full_text = f"{title} {summary}".lower()

        # Generate fingerprint using MD5 hash of normalized title
        clean_title = re.sub(r'[^a-zA-Z0-9]', '', title.lower())
        fingerprint = hashlib.md5(clean_title.encode('utf-8')).hexdigest()

        # Published time parsing
        published_dt = datetime.now(timezone.utc)
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            except Exception:
                published_dt = datetime.now(timezone.utc)

        # Relevance scoring (0 to 100)
        relevance_score = 0.0
        if any(w in full_text for w in ["gold", "xau", "precious metal", "bullion"]):
            relevance_score += 45.0
        if any(w in full_text for w in ["fed", "federal reserve", "powell", "fomc", "interest rate", "cpi", "pce", "nfp"]):
            relevance_score += 35.0
        if any(w in full_text for w in ["dollar", "dxy", "treasury", "yield", "inflation"]):
            relevance_score += 20.0
        if any(w in full_text for w in ["war", "conflict", "sanctions", "geopolitical", "iran", "taiwan", "russia"]):
            relevance_score += 25.0

        relevance_score = min(100.0, relevance_score * weight)

        # Sentiment & Gold Impact
        bull_hits = sum(1 for kw in KEYWORDS_GOLD_BULLISH if kw in full_text)
        bear_hits = sum(1 for kw in KEYWORDS_GOLD_BEARISH if kw in full_text)

        if bull_hits > bear_hits:
            gold_impact = "BULLISH"
            sentiment = "POSITIVE"
        elif bear_hits > bull_hits:
            gold_impact = "BEARISH"
            sentiment = "NEGATIVE"
        else:
            gold_impact = "NEUTRAL"
            sentiment = "NEUTRAL"

        # Impact Level
        is_high_impact = any(kw in full_text for kw in KEYWORDS_HIGH_IMPACT)
        if relevance_score >= 80.0 and is_high_impact:
            impact_level = "CRITICAL"
        elif relevance_score >= 60.0 or is_high_impact:
            impact_level = "HIGH"
        elif relevance_score >= 35.0:
            impact_level = "MEDIUM"
        else:
            impact_level = "LOW"

        category = "CENTRAL_BANK" if "fed" in full_text or "rate" in full_text else \
                   "GEOPOLITICAL" if "war" in full_text or "sanction" in full_text else \
                   "COMMODITY" if "gold" in full_text or "metal" in full_text else "MACRO"

        return {
            "fingerprint": fingerprint,
            "source": source,
            "title": title,
            "published_time": published_dt,
            "url": entry.get("link", ""),
            "category": category,
            "relevance_score": round(relevance_score, 1),
            "sentiment": sentiment,
            "gold_impact": gold_impact,
            "impact_level": impact_level,
            "alerted": False
        }
