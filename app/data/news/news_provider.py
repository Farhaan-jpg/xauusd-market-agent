"""News Provider aggregating multiple financial, breaking forex, and international geopolitical feeds for Gold in real time."""
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

# Comprehensive Real-Time Financial, Breaking Forex, Commodity & Geopolitical Conflict Feeds
RSS_FEEDS = [
    # Breaking Forex & Gold Specialists (Real-time scalping/day-trading catalysts)
    {"source": "ForexLive Realtime", "url": "https://www.forexlive.com/feed/news", "weight": 1.5},
    {"source": "FXStreet Breaking", "url": "https://www.fxstreet.com/rss/news", "weight": 1.4},
    {"source": "FXStreet Gold", "url": "https://www.fxstreet.com/rss/news/commodities/gold", "weight": 1.4},
    {"source": "Investing.com Breaking", "url": "https://www.investing.com/rss/news_285.rss", "weight": 1.3},
    {"source": "Investing.com Commodities", "url": "https://www.investing.com/rss/commodities_News.rss", "weight": 1.2},
    {"source": "Kitco Metals", "url": "https://www.kitco.com/rss/news.html", "weight": 1.3},
    
    # Macro & Central Bank Authorities
    {"source": "Federal Reserve", "url": "https://www.federalreserve.gov/feeds/press_all.xml", "weight": 1.5},
    {"source": "MarketWatch Realtime", "url": "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines", "weight": 1.2},
    {"source": "CNBC Economy", "url": "https://search.cnbc.com/rs/search/combinedserver/search.xml?partnerId=wrss01&id=20910258", "weight": 1.2},
    
    # Global Geopolitics, War & Conflict Channels (Safe-Haven Catalysts)
    {"source": "Al Jazeera World", "url": "https://www.aljazeera.com/xml/rss/all.xml", "weight": 1.4},
    {"source": "BBC World News", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "weight": 1.3},
    {"source": "CNBC World & Geopolitics", "url": "https://search.cnbc.com/rs/search/combinedserver/search.xml?partnerId=wrss01&id=100003114", "weight": 1.2},
]

KEYWORDS_GEOPOLITICAL_CONFLICT = [
    "war", "military strike", "missile strike", "airstrike", "invasion", "escalation",
    "middle east", "iran", "israel", "gaza", "lebanon", "red sea", "houthi",
    "russia", "ukraine", "taiwan", "south china sea", "strait of hormuz",
    "nuclear", "sanctions", "embargo", "geopolitical tension", "safe haven",
    "oil disruption", "sovereign risk", "coup", "defense alert", "armed conflict",
    "drone attack", "hostilities", "retaliation", "blockade", "conscription"
]

KEYWORDS_GOLD_BULLISH = [
    "rate cut", "dovish", "inflation surges", "war", "geopolitical tension", "safe haven",
    "dollar drops", "yields slide", "gold surges", "gold rallies", "central bank buying",
    "gold demand rises", "escalation", "banking crisis", "stagflation", "weak nfp", "weak jobs",
    "missile strike", "military action", "middle east crisis", "sanctions imposed", "safe-haven bid"
]

KEYWORDS_GOLD_BEARISH = [
    "rate hike", "hawkish", "higher for longer", "dollar strengthens", "yields surge",
    "strong economy", "strong nfp", "hot cpi", "gold drops", "gold tumbles", "de-escalation",
    "fed pause on cuts", "us growth resilient", "selloff", "ceasefire agreed", "peace treaty",
    "tensions ease", "diplomatic breakthrough"
]

KEYWORDS_HIGH_IMPACT = [
    "fomc", "fed", "powell", "cpi", "pce", "nfp", "nonfarm payrolls", "interest rate",
    "inflation", "gdp", "treasury", "war", "middle east", "russia", "china", "tariffs",
    "sanctions", "military strike", "nuclear", "iran", "israel", "ukraine", "taiwan"
]

class NewsProvider(BaseDataProvider):
    """Aggregates and processes real-time news for Gold, Macro, Geopolitics, and War/Conflict Catalysts concurrently."""

    def __init__(self):
        super().__init__(name="News_RSS_Provider")

    async def fetch(self) -> List[Dict[str, Any]]:
        start_time = time.time()
        try:
            news_items = await self._fetch_all_feeds_async()
            latency_ms = (time.time() - start_time) * 1000
            await self.record_health(is_healthy=True, latency_ms=latency_ms)
            return news_items
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"NewsProvider error: {e}")
            await self.record_health(is_healthy=False, latency_ms=latency_ms, error_message=str(e))
            return []

    async def _fetch_all_feeds_async(self) -> List[Dict[str, Any]]:
        """Fetches all RSS feeds concurrently using httpx async client for sub-second latency."""
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        async with httpx.AsyncClient(timeout=4.5, headers=headers, follow_redirects=True) as client:
            tasks = [self._fetch_single_feed(client, feed_cfg) for feed_cfg in RSS_FEEDS]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        all_news = []
        for res in results:
            if isinstance(res, list):
                all_news.extend(res)

        # Deduplicate based on title fingerprint
        unique_news = {}
        for n in all_news:
            fp = n["fingerprint"]
            if fp not in unique_news or n["relevance_score"] > unique_news[fp]["relevance_score"]:
                unique_news[fp] = n

        deduped = list(unique_news.values())

        # Sort primarily by published_time (newest first), prioritizing critical breaking news
        deduped.sort(
            key=lambda x: (
                x.get("impact_level") == "CRITICAL",
                x.get("published_time") or datetime.min.replace(tzinfo=timezone.utc),
                x.get("relevance_score", 0)
            ),
            reverse=True
        )
        return deduped

    async def _fetch_single_feed(self, client: httpx.AsyncClient, feed_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        items = []
        try:
            resp = await client.get(feed_config["url"])
            if resp.status_code == 200:
                parsed = feedparser.parse(resp.content)
                for entry in parsed.entries[:15]:
                    item = self._process_entry(entry, feed_config["source"], feed_config["weight"])
                    if item and item["relevance_score"] >= 20.0:
                        items.append(item)
        except Exception as e:
            logger.debug(f"Failed parsing feed {feed_config['source']}: {e}")
        return items

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
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            try:
                published_dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            except Exception:
                published_dt = datetime.now(timezone.utc)

        # Relevance scoring (0 to 100)
        relevance_score = 0.0
        is_geopolitical = any(w in full_text for w in KEYWORDS_GEOPOLITICAL_CONFLICT)
        is_gold_direct = any(w in full_text for w in ["gold", "xau", "precious metal", "bullion"])
        is_macro_direct = any(w in full_text for w in ["fed", "federal reserve", "powell", "fomc", "interest rate", "cpi", "pce", "nfp"])
        is_yield_currency = any(w in full_text for w in ["dollar", "dxy", "treasury", "yield", "inflation"])

        if is_gold_direct:
            relevance_score += 45.0
        if is_geopolitical:
            relevance_score += 40.0
        if is_macro_direct:
            relevance_score += 35.0
        if is_yield_currency:
            relevance_score += 20.0

        relevance_score = min(100.0, relevance_score * weight)

        # Sentiment & Gold Impact
        bull_hits = sum(1 for kw in KEYWORDS_GOLD_BULLISH if kw in full_text)
        bear_hits = sum(1 for kw in KEYWORDS_GOLD_BEARISH if kw in full_text)

        # Geopolitical conflict escalation creates instant safe-haven bullion demand
        if is_geopolitical and not any(kw in full_text for kw in ["ceasefire", "peace", "tensions ease", "de-escalation"]):
            bull_hits += 2

        if bull_hits > bear_hits:
            gold_impact = "BULLISH"
            sentiment = "POSITIVE"
        elif bear_hits > bull_hits:
            gold_impact = "BEARISH"
            sentiment = "NEGATIVE"
        else:
            gold_impact = "NEUTRAL"
            sentiment = "NEUTRAL"

        # Impact Level determination
        is_high_impact = any(kw in full_text for kw in KEYWORDS_HIGH_IMPACT)
        if (relevance_score >= 75.0 and is_high_impact) or (is_geopolitical and ("missile" in full_text or "war" in full_text or "strike" in full_text)):
            impact_level = "CRITICAL"
        elif relevance_score >= 55.0 or is_high_impact or is_geopolitical:
            impact_level = "HIGH"
        elif relevance_score >= 35.0:
            impact_level = "MEDIUM"
        else:
            impact_level = "LOW"

        category = "WAR_CONFLICT" if any(w in full_text for w in ["war", "missile", "strike", "airstrike", "invasion", "military"]) else \
                   "GEOPOLITICAL" if is_geopolitical else \
                   "CENTRAL_BANK" if "fed" in full_text or "rate" in full_text else \
                   "COMMODITY" if is_gold_direct else "MACRO"

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
            "impact_level": impact_level
        }

