# Troubleshooting & Operational Guide

---

## 1. Common Diagnostics & Solutions

### A. Market Data Returns `INSUFFICIENT DATA`
- **Cause**: Weekend market closure or Yahoo Finance rate limiting.
- **Solution**: The agent automatically attempts fallback tickers (`GC=F` $\rightarrow$ `XAUUSD=X` $\rightarrow$ `GLD`). During weekend hours, it safely utilizes the latest available Friday closing bars.

### B. Gemini API Error (429 Rate Limit / Quota Exceeded)
- **Cause**: Free tier request limit exceeded on Google AI Studio.
- **Solution**: The agent automatically catches the error, marks Gemini degraded, and switches to OpenRouter or Safe Deterministic Mode. No crash occurs.

### C. Telegram Alerts Not Appearing
- **Verification Checklist**:
  1. Did you start a conversation with your bot by clicking **Start** or sending `/start`? (Bots cannot initiate conversations with users who haven't started them).
  2. Is `TELEGRAM_ALERTS_ENABLED=true` in your `.env`?
  3. Are your `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` set correctly?
  4. Note that if no significant score change or high-impact event occurred, alert cooldown suppresses spam notifications. Run `python scripts/run_cycle.py` to trigger a forced test report.

### D. SQLite Database Lock Errors
- **Cause**: Concurrent write attempts from multiple uncoordinated processes.
- **Solution**: The repository uses `aiosqlite` with transactional context management and SQLite write serialization. Ensure only one main server process runs against the database file.

---

## 2. Health Monitoring

Check endpoint:
```bash
curl http://localhost:8000/health
```

Expected output:
```json
{
  "status": "HEALTHY",
  "version": "1.0.0",
  "ai_active_provider": "gemini_first",
  "providers": {
    "YahooFinance_Market": { "healthy": true, "latency_ms": 520.1 },
    "Macro_Provider": { "healthy": true, "latency_ms": 310.4 },
    "News_RSS_Provider": { "healthy": true, "latency_ms": 412.0 }
  }
}
```
