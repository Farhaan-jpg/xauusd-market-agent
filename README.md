# XAUUSD AI Market Intelligence & Real-Time Direction Platform

> **Institutional-grade, autonomous Real-Time Market Intelligence & Direction Platform for XAUUSD (Gold).**
> Features definitive market direction verdicts (`BULLISH`, `BEARISH`, `NEUTRAL`), real-time geopolitical conflict intelligence (Conflict Escalation Index & Safe-Haven $/oz Premium), financial news & central bank wire, 6-factor gold correlation matrix, dual-mode execution (⚡ Scalping vs 🎯 Day Trading), AI voice briefing, and interactive TradingView live charts.

---

## 🌟 Key Platform Modules

1. **Definitive Real-Time Market Direction & AI Brain**:
   - Multi-engine institutional synthesis generating unambiguous `BULLISH`, `BEARISH`, or `NEUTRAL` verdicts with conviction percentage (0–100%).
   - Deep contextual AI executive thesis explaining macroeconomic yield curves, dollar pressures, and sovereign accumulation.
   - 🔊 **Web Speech AI Audio Briefing**: Real-time voice readout of executive intelligence.

2. **Interactive Dual-Mode Master Switch (⚡ Scalping vs 🎯 Day Trading)**:
   - **⚡ Scalping (1M / 5M)**: Prioritizes 5M technical structure, orderflow CVD delta, and breaking news catalysts with tight 3–5 pt Stop Losses and 6–12 pt Take Profits.
   - **🎯 Day Trading (15M / 1H / 4H)**: Prioritizes higher timeframe structure, 6-factor correlations, and geopolitics with 10–14 pt Stop Losses and 22–38 pt Multi-Session Targets.
   - **TradingView Auto-Sync**: Chart widget dynamically adapts intervals (5M for Scalp vs 60M for Day Trade).

3. **Complete 6-Factor Gold Intermarket Correlation Matrix**:
   - **US Dollar Index (DXY)**: Greenback inverse pressure & sovereign safe-haven decoupling detection.
   - **10-Year TIPS Real Yields**: Inflation-adjusted bullion holding opportunity cost.
   - **Gold / Silver Ratio (GSR) & Silver Breakout**: Leading precious metals momentum signal.
   - **WTI Crude Oil**: Energy cost-push inflation pass-through gauge.
   - **Shanghai Gold Exchange (SGE) Physical Premium**: Eastern physical demand & arbitrage spreads.
   - **VIX Volatility Index**: Equity fear index & safe-haven portfolio hedging.

4. **Real-Time Geopolitics & Defense Flashpoints Feed**:
   - **Conflict Escalation Index (CEI 0–100)**: Quantitative threat scoring across global defense theaters.
   - **Safe-Haven Premium ($/oz)**: Calculates risk premium built into active spot prices.
   - **Theater Tracking**: Middle East, Red Sea choke points, Eastern Europe, and Taiwan Strait.

5. **Real-Time Financial News & Central Bank Accumulation Wire**:
   - Automated Dovish/Hawkish scoring on Federal Reserve statements and rate cut probabilities.
   - Live tracking of sovereign reserve accumulation pace for PBoC (China), RBI (India), and NBP (Poland).

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
