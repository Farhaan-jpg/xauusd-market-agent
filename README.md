# XAUUSD AI Market Intelligence & Liquidity Agent

> **Enterprise-grade, autonomous Market Intelligence & Liquidity Analysis Agent for XAUUSD (Gold).**
> Built with deterministic quantitative calculation engines, multi-tier AI synthesis (Gemini $\rightarrow$ OpenRouter $\rightarrow$ Deterministic Fallback), session-aware structural liquidity detection, real-time news aggregation, Telegram alerting, and an interactive dark-mode dashboard.

---

## 🏛 Core Philosophy & Compliance Policy

- **Market Intelligence Only**: This system strictly analyzes market conditions and determines directional bias (`BULLISH`, `BEARISH`, `NEUTRAL`, `INSUFFICIENT DATA`), strength (-100 to +100), confidence (0 to 100%), and structural liquidity zones.
- **Zero Trading Instructions**: The system **never** outputs trade entries, buy/sell signals, stop-loss orders, take-profit levels, or personalized financial advice.
- **No Hallucinations**: All mathematical, statistical, indicator, and liquidity computations are executed deterministically in pure Python/NumPy/Pandas. AI models are used strictly for contextual synthesis and narrative explanation of validated data.
- **100% Free-Tier & Zero-Key Operation**: Operates fully out-of-the-box using free and open public market/macro data feeds and rule-based deterministic synthesis without requiring paid API keys.

---

## 🌟 Key Features

1. **Deterministic Technical Engine**: Multi-timeframe OHLC analysis (5m, 15m, 30m, 1H, 4H, 1D), ATR volatility regimes, RSI momentum, MACD histogram, EMA ribbons (20, 50, 200), Bollinger Bands, and swing pivot points.
2. **Session-Aware Liquidity Engine**:
   - Previous Day High/Low (PDH / PDL) & Previous Week High/Low (PWH / PWL)
   - Asian (00:00-08:00 UTC), London (07:00-15:30 UTC), and New York (12:00-20:00 UTC) session ranges
   - Equal Highs (EQH) & Equal Lows (EQL) cluster detection within configurable pip tolerances
   - 3-bar Fair Value Gaps (FVG / Bullish & Bearish Imbalances)
   - Deterministic 0–100 Liquidity Strength scoring & distance proximity radar.
3. **Macro & Yield Evidence Matrix**:
   - US Dollar Index (DXY) momentum
   - US 10-Year & 2-Year Treasury Yields & 10Y-2Y yield curve spread
   - TIPS Real Yield proxy & VIX market risk sentiment.
4. **News & Economic Calendar Aggregator**:
   - High-impact financial RSS feed aggregation (Reuters, Kitco Gold, FXStreet, CNBC, MarketWatch, Federal Reserve)
   - Keyword relevance scoring, sentiment analysis, event fingerprinting, and deduplication
   - High-impact USD economic calendar tracking (FOMC, CPI, NFP, PCE, GDP, PPI).
5. **Multi-Tier AI Fallback Engine**:
   - **Primary**: Google Gemini API (`gemini-2.5-flash`)
   - **Secondary**: OpenRouter API (`claude-3.5-sonnet`, `llama-3.3-70b-instruct`, `gemini-2.0-flash-exp`)
   - **Tertiary / Default**: Safe Deterministic Fallback Engine requiring zero API keys.
6. **Telegram Bot Alert Engine**:
   - Institutional HTML/Markdown alert templates for Periodic Reports, Direction Shift Alerts, High-Impact News Alerts, and Major Liquidity Proximity Triggers.
   - Spam cooldown and fingerprint deduplication.
7. **Web Dashboard & REST API**:
   - Real-time dark-mode dashboard displaying live gold price, direction meter, score progress gauges, liquidity radar, calendar table, and news feed in `Asia/Kolkata` (IST) timezone.
   - `/health` and `/status` monitoring endpoints.
8. **Deployment & CI/CD**:
   - Docker containerization & Docker Compose
   - Render Blueprint (`render.yaml`)
   - GitHub Actions workflows for scheduled headless runs, health monitoring, and test suites.

---

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/your-username/xauusd-ai-agent.git
cd xauusd-ai-agent

# Create virtual environment
python -m venv venv
# Activate virtual environment (Windows: venv\Scripts\activate, Unix: source venv/bin/activate)

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration (.env)

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` (all external keys are optional; the agent will run in safe deterministic mode if left blank):

```env
TIMEZONE=Asia/Kolkata
ANALYSIS_INTERVAL_SECONDS=180
PORT=8000

# Optional AI Keys
GEMINI_API_KEY=
OPENROUTER_API_KEY=

# Optional Telegram Keys
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
TELEGRAM_ALERTS_ENABLED=false
```

### 3. Run the Agent & Web Dashboard

```bash
python scripts/run_agent.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

### 4. Execute a One-Shot Intelligence Cycle (CLI)

```bash
python scripts/run_cycle.py
```

### 5. Run Test Suite

```bash
pytest tests/ -v
```

---

## 📁 Repository Structure

```
├── app/
│   ├── ai/                      # Multi-tier AI synthesis (Gemini, OpenRouter, Deterministic)
│   ├── alerts/                  # Alert engine, spam cooldowns, templates
│   ├── analysis/                # Technical, Liquidity, Macro, News & Direction engines
│   ├── api/                     # FastAPI backend & REST endpoints
│   ├── config/                  # Pydantic settings & configuration
│   ├── core/                    # Structured logging with secret masking
│   ├── data/                    # Market, Macro, News & Calendar providers
│   ├── scheduler/               # Orchestrator & continuous background daemon
│   ├── static/                  # CSS, JS client assets
│   ├── storage/                 # SQLite schema, async engine, repository CRUD
│   ├── telegram/                # Telegram bot client
│   └── templates/               # Jinja2 HTML dashboard template
├── scripts/                     # Helper CLI scripts (run_agent, run_cycle, evaluate_backtest)
├── tests/                       # Unit, integration, and failure simulation tests
├── .github/workflows/           # Scheduled analysis, CI test suite, and health workflows
├── Dockerfile                   # Production Docker image
├── docker-compose.yml           # Compose configuration
├── render.yaml                  # Render Blueprint definition
└── requirements.txt             # Project dependencies
```

---

## ⚖️ License & Disclaimer

This project is for informational and educational purposes only. Market intelligence outputs should never be construed as financial, investment, or trading advice.
