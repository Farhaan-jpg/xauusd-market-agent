"""FastAPI application providing REST endpoints and serving the Web Dashboard."""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import os
from typing import Any, Dict, List
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.analysis.backtest.evaluator import BacktestEvaluator
from app.config.settings import settings
from app.core.logging import logger
from app.scheduler.orchestrator import IntelligenceOrchestrator
from app.storage.database import init_db
from app.storage.repository import Repository

orchestrator = IntelligenceOrchestrator()
orchestrator_task: asyncio.Task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    global orchestrator_task
    logger.info("Initializing XAUUSD Market Intelligence Agent...")
    await init_db()
    # Trigger initial cycle
    try:
        await orchestrator.run_cycle(force_report=False)
    except Exception as e:
        logger.error(f"Initial run cycle error: {e}")

    # Launch background scheduler task
    orchestrator_task = asyncio.create_task(orchestrator.start_continuous_loop())
    yield
    logger.info("Shutting down XAUUSD Market Intelligence Agent...")
    orchestrator.stop()
    if orchestrator_task:
        orchestrator_task.cancel()

app = FastAPI(
    title="XAUUSD AI Market Intelligence & Liquidity Agent",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Templates and Static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

from fastapi.responses import HTMLResponse, JSONResponse, Response

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Renders the main dark-mode web dashboard."""
    if request.method == "HEAD":
        return Response(status_code=200, media_type="text/html")
    return templates.TemplateResponse(request=request, name="index.html", context={"app_name": settings.APP_NAME})

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Favicon endpoint preventing 404 logs."""
    svg_data = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">⚜️</text></svg>'
    return Response(content=svg_data, media_type="image/svg+xml")

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check(request: Request) -> Any:
    """Health check endpoint evaluating database and provider status."""
    if request.method == "HEAD":
        return Response(status_code=200)

    health_records = await Repository.get_all_provider_health()
    all_healthy = all(r.is_healthy for r in health_records) if health_records else True

    providers_status = {
        r.provider_name: {
            "healthy": r.is_healthy,
            "latency_ms": r.latency_ms,
            "last_success": r.last_success.isoformat() if r.last_success else None,
            "consecutive_failures": r.consecutive_failures
        } for r in health_records
    }

    return {
        "status": "HEALTHY" if all_healthy else "DEGRADED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.APP_VERSION,
        "ai_active_provider": settings.AI_PRIORITY,
        "has_gemini_key": settings.has_gemini,
        "has_openrouter_key": settings.has_openrouter,
        "telegram_configured": settings.has_telegram,
        "providers": providers_status
    }

@app.get("/status")
async def system_status() -> Dict[str, Any]:
    """Detailed status report of the agent."""
    latest_run = await Repository.get_latest_analysis_run()
    latest_snapshot = await Repository.get_latest_market_snapshot()
    health_records = await Repository.get_all_provider_health()

    return {
        "agent_name": settings.APP_NAME,
        "timezone": settings.TIMEZONE,
        "analysis_interval_seconds": settings.ANALYSIS_INTERVAL_SECONDS,
        "latest_direction": latest_run.direction if latest_run else "INITIALIZING",
        "latest_score": latest_run.direction_score if latest_run else 0.0,
        "latest_confidence": latest_run.confidence if latest_run else 0.0,
        "latest_gold_price": latest_snapshot.price if latest_snapshot else 0.0,
        "last_updated": latest_run.timestamp.isoformat() if latest_run else None,
        "provider_used": latest_run.provider_used if latest_run else "NONE",
        "health": {r.provider_name: r.is_healthy for r in health_records}
    }

@app.get("/api/latest-report")
async def get_latest_report() -> Dict[str, Any]:
    """Returns the latest market intelligence report and AI synthesis."""
    run = await Repository.get_latest_analysis_run()
    if not run:
        return {"status": "NO_DATA", "message": "First analysis cycle in progress."}

    return {
        "timestamp": run.timestamp.isoformat(),
        "gold_price": run.gold_price,
        "direction": run.direction,
        "direction_score": run.direction_score,
        "confidence": run.confidence,
        "scores": {
            "macro_score": run.macro_score,
            "usd_score": run.usd_score,
            "yield_score": run.yield_score,
            "news_score": run.news_score,
            "technical_score": run.technical_score,
            "liquidity_score": run.liquidity_score
        },
        "dominant_drivers": run.dominant_drivers or [],
        "supporting_factors": run.supporting_factors or [],
        "contradicting_factors": run.contradicting_factors or [],
        "macro_summary": run.macro_summary,
        "news_summary": run.news_summary,
        "liquidity_summary": run.liquidity_summary or [],
        "final_market_verdict": run.final_market_verdict or "NEUTRAL",
        "executive_verdict_summary": run.executive_verdict_summary or "",
        "risk_factors": run.risk_factors,
        "data_quality": run.data_quality,
        "provider_used": run.provider_used
    }

@app.get("/api/market-data")
async def get_market_data() -> Dict[str, Any]:
    """Returns current market snapshot and technical indicators."""
    snapshot = await Repository.get_latest_market_snapshot()
    if not snapshot:
        return {"status": "NO_DATA"}

    return {
        "timestamp": snapshot.timestamp.isoformat(),
        "symbol": snapshot.symbol,
        "price": snapshot.price,
        "change_24h": snapshot.change_24h,
        "high_24h": snapshot.high_24h,
        "low_24h": snapshot.low_24h,
        "indicators": {
            "atr": snapshot.atr,
            "rsi": snapshot.rsi,
            "macd": snapshot.macd,
            "macd_signal": snapshot.macd_signal,
            "ema_20": snapshot.ema_20,
            "ema_50": snapshot.ema_50,
            "ema_200": snapshot.ema_200,
            "trend": snapshot.trend,
            "volatility": snapshot.volatility
        }
    }

@app.get("/api/liquidity")
async def get_liquidity_zones() -> Dict[str, Any]:
    """Returns active liquidity zones above and below price."""
    zones = await Repository.get_active_liquidity_zones()
    snapshot = await Repository.get_latest_market_snapshot()
    price = snapshot.price if snapshot else 0.0

    above = [z for z in zones if z.is_above]
    below = [z for z in zones if not z.is_above]

    return {
        "current_price": price,
        "total_zones": len(zones),
        "liquidity_above": [
            {
                "price": z.price,
                "range_low": z.zone_range_low,
                "range_high": z.zone_range_high,
                "type": z.zone_type,
                "timeframe": z.timeframe,
                "strength": z.strength,
                "distance": z.distance_from_price
            } for z in above
        ],
        "liquidity_below": [
            {
                "price": z.price,
                "range_low": z.zone_range_low,
                "range_high": z.zone_range_high,
                "type": z.zone_type,
                "timeframe": z.timeframe,
                "strength": z.strength,
                "distance": z.distance_from_price
            } for z in below
        ]
    }

@app.get("/api/news")
async def get_recent_news() -> List[Dict[str, Any]]:
    """Returns recent news events."""
    news = await Repository.get_recent_news(limit=15)
    return [
        {
            "title": n.title,
            "source": n.source,
            "published_time": n.published_time.isoformat(),
            "url": n.url,
            "category": n.category,
            "relevance_score": n.relevance_score,
            "sentiment": n.sentiment,
            "gold_impact": n.gold_impact,
            "impact_level": n.impact_level
        } for n in news
    ]

@app.get("/api/economic-calendar")
async def get_economic_calendar() -> List[Dict[str, Any]]:
    """Returns upcoming economic calendar events."""
    events = await Repository.get_upcoming_economic_events(hours_ahead=48)
    return [
        {
            "event_name": e.event_name,
            "country": e.country,
            "scheduled_time": e.scheduled_time.isoformat(),
            "importance": e.importance,
            "forecast": e.forecast,
            "previous": e.previous,
            "actual": e.actual,
            "surprise": e.surprise,
            "status": e.status,
            "gold_impact": e.gold_impact
        } for e in events
    ]

@app.get("/api/history")
async def get_history() -> List[Dict[str, Any]]:
    """Returns past analysis runs."""
    runs = await Repository.get_analysis_history(limit=25)
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "gold_price": r.gold_price,
            "direction": r.direction,
            "score": r.direction_score,
            "confidence": r.confidence,
            "provider_used": r.provider_used
        } for r in runs
    ]

@app.get("/api/config")
async def get_config() -> Dict[str, Any]:
    """Returns current runtime configuration with secrets masked."""
    def mask_secret(s: Optional[str]) -> str:
        if not s or len(s) < 6:
            return ""
        return f"{s[:4]}...{s[-3:]}"

    return {
        "timezone": settings.TIMEZONE,
        "analysis_interval_seconds": settings.ANALYSIS_INTERVAL_SECONDS,
        "ai_priority": settings.AI_PRIORITY,
        "gemini_configured": settings.has_gemini,
        "gemini_key_masked": mask_secret(settings.GEMINI_API_KEY),
        "gemini_model": settings.GEMINI_MODEL,
        "openrouter_configured": settings.has_openrouter,
        "openrouter_key_masked": mask_secret(settings.OPENROUTER_API_KEY),
        "openrouter_model": settings.OPENROUTER_MODEL,
        "telegram_configured": settings.has_telegram,
        "telegram_token_masked": mask_secret(settings.TELEGRAM_BOT_TOKEN),
        "telegram_chat_id": settings.TELEGRAM_CHAT_ID or "",
        "telegram_alerts_enabled": settings.TELEGRAM_ALERTS_ENABLED,
        "pause_on_weekends": settings.PAUSE_ON_WEEKENDS,
        "liquidity_tolerance_pips": settings.LIQUIDITY_TOLERANCE_PIPS,
        "direction_change_threshold": settings.DIRECTION_CHANGE_THRESHOLD_SCORE
    }

@app.post("/api/config")
async def update_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Updates runtime configuration in memory."""
    # Filter out empty or masked secret strings
    clean_updates = {}
    for k, v in payload.items():
        if k in ["GEMINI_API_KEY", "OPENROUTER_API_KEY", "TELEGRAM_BOT_TOKEN"]:
            if v and not v.endswith("...") and "..." not in v:
                clean_updates[k] = v
        elif k in ["TELEGRAM_CHAT_ID", "AI_PRIORITY", "TIMEZONE", "GEMINI_MODEL", "OPENROUTER_MODEL"]:
            if v is not None:
                clean_updates[k] = str(v).strip()
        elif k in ["ANALYSIS_INTERVAL_SECONDS", "DIRECTION_CHANGE_THRESHOLD_SCORE"]:
            if v is not None:
                try: clean_updates[k] = int(v)
                except Exception: pass
        elif k == "LIQUIDITY_TOLERANCE_PIPS":
            if v is not None:
                try: clean_updates[k] = float(v)
                except Exception: pass
        elif k in ["TELEGRAM_ALERTS_ENABLED", "PAUSE_ON_WEEKENDS"]:
            clean_updates[k] = bool(v)

    settings.update_runtime_config(clean_updates)
    
    # Re-initialize providers with updated keys & models
    orchestrator.synthesizer.gemini.api_key = settings.GEMINI_API_KEY
    orchestrator.synthesizer.gemini.model = settings.GEMINI_MODEL
    orchestrator.synthesizer.openrouter.api_key = settings.OPENROUTER_API_KEY
    orchestrator.synthesizer.openrouter.models = [m.strip() for m in settings.OPENROUTER_MODEL.split(",") if m.strip()]
    orchestrator.alert_engine.bot.token = settings.TELEGRAM_BOT_TOKEN
    orchestrator.alert_engine.bot.chat_id = settings.TELEGRAM_CHAT_ID
    orchestrator.alert_engine.bot.enabled = settings.TELEGRAM_ALERTS_ENABLED and settings.has_telegram

    logger.info(f"Configuration updated dynamically: {list(clean_updates.keys())}")
    return {"status": "SUCCESS", "message": "Configuration updated successfully."}

@app.post("/api/test-telegram")
async def test_telegram_alert() -> Dict[str, Any]:
    """Sends an immediate verification test alert to Telegram."""
    from app.telegram.bot import TelegramBot
    bot = TelegramBot()
    if not settings.has_telegram:
        return {"status": "ERROR", "message": "Telegram Bot Token and Chat ID must be configured first."}

    test_msg = f"""<b>🔔 XAUUSD AGENT - CONNECTION TEST</b>
📅 <i>{datetime.now(timezone.utc).strftime('%d %b %Y, %I:%M %p UTC')}</i>
━━━━━━━━━━━━━━━━━━━━
✅ Telegram Alert Bot is active and connected.
📊 Real-time notifications and direction shift alerts are enabled.
━━━━━━━━━━━━━━━━━━━━
<i>Market intelligence system online.</i>"""

    success = await bot.send_message(test_msg)
    if success:
        return {"status": "SUCCESS", "message": "Test alert sent to Telegram successfully!"}
    else:
        return {"status": "ERROR", "message": "Failed to send Telegram message. Check Bot Token & Chat ID."}

@app.get("/api/accuracy")
async def get_accuracy() -> Dict[str, Any]:
    """Returns backtesting / historical predictive accuracy statistics."""
    return await BacktestEvaluator.evaluate_accuracy()

@app.post("/api/trigger-analysis")
async def trigger_analysis(background_tasks: BackgroundTasks) -> Dict[str, str]:
    """Manually triggers an immediate analysis cycle."""
    background_tasks.add_task(orchestrator.run_cycle, True)
    return {"status": "SUCCESS", "message": "Analysis cycle triggered in background."}
