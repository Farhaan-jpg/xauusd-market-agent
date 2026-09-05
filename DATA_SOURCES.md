# Data Source Strategy & Feeds

This agent leverages resilient, free, public, and open financial data sources without requiring paid API tiers.

---

## Data Providers Overview

| Category | Provider Source | Primary Symbols / Feeds | Fallback / Redundancy |
| :--- | :--- | :--- | :--- |
| **Market Data** | Yahoo Finance (`yfinance`) | `GC=F` (Gold Futures) | `XAUUSD=X` (Spot), `GLD` (ETF) |
| **Macro Indicators** | Yahoo Finance / Open feeds | `DX-Y.NYB` (DXY), `^TNX` (US10Y), `^IRX` (US2Y), `TIP` (Real Yields), `^VIX` | `UUP`, `IEF`, `SHY` |
| **News Intelligence** | Financial RSS Feeds | FXStreet, Kitco Metals, CNBC Economy, MarketWatch, Federal Reserve, Investing.com | Multi-feed aggregation & scoring |
| **Economic Calendar** | Open Calendar JSON / RSS | US High-Impact (FOMC, CPI, NFP, PCE, GDP, PPI) | Scheduled baseline event templates |

---

## Financial News RSS Sources

The news engine continuously scans and parses the following feeds:
1. **Kitco Metals**: `https://www.kitco.com/rss/news.html`
2. **FXStreet Gold**: `https://www.fxstreet.com/rss/news/commodities/gold`
3. **CNBC Economy**: `https://search.cnbc.com/rs/search/combinedserver/search.xml?partnerId=wrss01&id=20910258`
4. **Federal Reserve Press Releases**: `https://www.federalreserve.gov/feeds/press_all.xml`
5. **MarketWatch Top Stories**: `https://feeds.content.dowjones.io/public/rss/mw_topstories`
6. **Investing.com Commodities**: `https://www.investing.com/rss/commodities_News.rss`

---

## Relevance & Sentiment Heuristics

Articles are filtered across 30+ keywords covering:
- **Central Bank & Rates**: Fed, Powell, FOMC, rate cut, rate hike, hawkish, dovish, balance sheet.
- **Inflation & Jobs**: CPI, PCE, NFP, payrolls, unemployment, wage growth.
- **Geopolitics & Tail Risks**: Sanctions, tariffs, conflict, safe haven demand, central bank gold buying.
- **Deduplication**: MD5 title fingerprinting and timestamp clustering prevent duplicate alerts.
