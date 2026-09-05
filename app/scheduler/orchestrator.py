"""Market Intelligence Orchestrator executing analysis cycles and continuous scheduling."""
import asyncio
from datetime import datetime, timezone
import time
from typing import Any, Dict, Optional
from app.ai.synthesizer import AISynthesizer
from app.alerts.engine import AlertEngine
from app.analysis.liquidity.liquidity_engine import LiquidityEngine
from app.analysis.macro.macro_engine import MacroEngine
from app.analysis.news.news_engine import NewsEngine
from app.analysis.sentiment.market_direction_engine import MarketDirectionEngine
from app.analysis.technical.market_engine import MarketEngine
from app.config.settings import settings
from app.core.logging import logger
from app.data.economic.economic_provider import EconomicCalendarProvider
from app.data.macro.macro_provider import MacroDataProvider
from app.data.market.market_provider import MarketDataProvider
from app.data.news.news_provider import NewsProvider
from app.storage.database import init_db
from app.storage.repository import Repository

class IntelligenceOrchestrator:
    """Orchestrates end-to-end data ingestion, calculations, AI synthesis, persistence, and alerts."""

    def __init__(self):
        self.market_provider = MarketDataProvider()
        self.macro_provider = MacroDataProvider()
        self.news_provider = NewsProvider()
        self.economic_provider = EconomicCalendarProvider()

        self.market_engine = MarketEngine()
        self.liquidity_engine = LiquidityEngine()
        self.macro_engine = MacroEngine()
        self.news_engine = NewsEngine()
        self.direction_engine = MarketDirectionEngine()

        self.synthesizer = AISynthesizer()
        self.alert_engine = AlertEngine()
        self.is_running = False

    async def initialize(self) -> None:
        """Initializes database schema and prepares state."""
        await init_db()
        logger.info("IntelligenceOrchestrator initialized.")

    async def run_cycle(self, force_report: bool = False) -> Dict[str, Any]:
        """Runs a complete end-to-end analysis cycle."""
        cycle_start = time.time()
        logger.info("Starting Market Intelligence cycle...")

        # 1. Fetch data concurrently
        market_res, macro_res, news_res, econ_res = await asyncio.gather(
            self.market_provider.fetch(),
            self.macro_provider.fetch(),
            self.news_provider.fetch(),
            self.economic_provider.fetch(),
            return_exceptions=True
        )

        market_data = market_res if not isinstance(market_res, Exception) else {"price": 0.0, "timeframes": {}, "data_quality": "ERROR"}
        macro_data = macro_res if not isinstance(macro_res, Exception) else {}
        news_data = news_res if not isinstance(news_res, Exception) else []
        econ_data = econ_res if not isinstance(econ_res, Exception) else []

        # 2. Persist raw news & economic events
        if news_data:
            await Repository.save_news_events(news_data)
        if econ_data:
            await Repository.save_economic_events(econ_data)

        # 3. Execute Deterministic Analysis Engines
        market_analysis = self.market_engine.analyze(market_data)
        liquidity_analysis = self.liquidity_engine.analyze(market_data)
        macro_analysis = self.macro_engine.analyze(macro_data)
        news_analysis = self.news_engine.analyze(news_data)

        direction_data = self.direction_engine.calculate_direction(
            market_analysis=market_analysis,
            liquidity_analysis=liquidity_analysis,
            macro_analysis=macro_analysis,
            news_analysis=news_analysis,
            economic_events=econ_data
        )

        # Merge trend and volatility info into direction_data for report display
        direction_data["trend"] = market_analysis.get("trend", "NEUTRAL")
        direction_data["volatility"] = market_analysis.get("volatility", "NORMAL")

        # 4. Save Market Snapshot & Liquidity Zones to Database
        current_price = market_analysis.get("price", 0.0)
        if current_price > 0:
            await Repository.save_market_snapshot({
                "symbol": "XAUUSD",
                "price": current_price,
                "change_24h": market_data.get("change_24h", 0.0),
                "high_24h": market_data.get("high_24h", 0.0),
                "low_24h": market_data.get("low_24h", 0.0),
                "atr": market_analysis.get("atr", 0.0),
                "rsi": market_analysis.get("rsi", 50.0),
                "macd": market_analysis.get("macd", 0.0),
                "macd_signal": market_analysis.get("macd_signal", 0.0),
                "ema_20": market_analysis.get("ema_20", 0.0),
                "ema_50": market_analysis.get("ema_50", 0.0),
                "ema_200": market_analysis.get("ema_200", 0.0),
                "trend": market_analysis.get("trend", "NEUTRAL"),
                "volatility": market_analysis.get("volatility", "NORMAL"),
                "data_quality": market_analysis.get("data_quality", "GOOD")
            })

            if liquidity_analysis.get("all_zones"):
                db_zones = []
                for z in liquidity_analysis["all_zones"]:
                    db_zones.append({
                        "price": z["price"],
                        "zone_range_low": z["zone_range_low"],
                        "zone_range_high": z["zone_range_high"],
                        "zone_type": z["zone_type"],
                        "timeframe": z["timeframe"],
                        "strength": z["strength"],
                        "distance_from_price": z["distance_from_price"],
                        "is_above": z["is_above"],
                        "touch_count": z.get("touch_count", 1),
                        "is_active": True
                    })
                await Repository.save_liquidity_zones(db_zones)

        # 5. Execute AI Synthesis (Gemini -> OpenRouter -> Safe Deterministic Fallback)
        synthesis_output, provider_used = await self.synthesizer.synthesize_market_intelligence(
            market_analysis=market_analysis,
            liquidity_analysis=liquidity_analysis,
            macro_analysis=macro_analysis,
            news_analysis=news_analysis,
            direction_data=direction_data,
            economic_events=econ_data
        )

        # 6. Fetch previous analysis for change detection
        previous_analysis = await Repository.get_latest_analysis_run()

        # 7. Persist Analysis Run to Database
        saved_run = await Repository.save_analysis_run({
            "gold_price": current_price,
            "direction": synthesis_output.direction,
            "direction_score": synthesis_output.score,
            "confidence": synthesis_output.confidence,
            "macro_score": direction_data.get("macro_score", 0.0),
            "usd_score": direction_data.get("usd_score", 0.0),
            "yield_score": direction_data.get("yield_score", 0.0),
            "news_score": direction_data.get("news_score", 0.0),
            "technical_score": direction_data.get("technical_score", 0.0),
            "liquidity_score": direction_data.get("liquidity_score", 0.0),
            "dominant_drivers": synthesis_output.dominant_drivers,
            "supporting_factors": synthesis_output.supporting_factors,
            "contradicting_factors": synthesis_output.contradicting_factors,
            "macro_summary": synthesis_output.macro_summary,
            "news_summary": synthesis_output.news_summary,
            "liquidity_summary": synthesis_output.liquidity_summary,
            "risk_factors": synthesis_output.risk_factors,
            "data_quality": synthesis_output.data_quality,
            "provider_used": provider_used
        })

        # 8. Evaluate and Trigger Alerts
        upcoming_events = await Repository.get_upcoming_economic_events(hours_ahead=24)
        await self.alert_engine.evaluate_and_dispatch_alerts(
            current_price=current_price,
            current_direction=direction_data,
            previous_analysis=previous_analysis,
            liquidity_analysis=liquidity_analysis,
            news_items=news_data,
            synthesis_output=synthesis_output,
            provider_used=provider_used,
            upcoming_events=upcoming_events,
            force_report=force_report
        )

        elapsed = round((time.time() - cycle_start), 2)
        logger.info(f"Analysis cycle completed in {elapsed}s. Direction: {synthesis_output.direction} ({synthesis_output.score:+.1f}), Confidence: {synthesis_output.confidence:.0f}% via {provider_used}")

        return {
            "gold_price": current_price,
            "direction": synthesis_output.direction,
            "score": synthesis_output.score,
            "confidence": synthesis_output.confidence,
            "provider_used": provider_used,
            "market_analysis": market_analysis,
            "liquidity_analysis": liquidity_analysis,
            "macro_analysis": macro_analysis,
            "news_analysis": news_analysis,
            "synthesis": synthesis_output.model_dump(),
            "cycle_duration_seconds": elapsed,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def start_continuous_loop(self) -> None:
        """Runs the intelligence cycle in an infinite scheduled loop."""
        self.is_running = True
        await self.initialize()

        logger.info(f"Starting continuous intelligence scheduler (Interval: {settings.ANALYSIS_INTERVAL_SECONDS}s)")
        # First cycle triggers initial report
        try:
            await self.run_cycle(force_report=True)
        except Exception as e:
            logger.error(f"Error in initial intelligence cycle: {e}")

        while self.is_running:
            try:
                await asyncio.sleep(settings.ANALYSIS_INTERVAL_SECONDS)
                await self.run_cycle(force_report=False)
            except asyncio.CancelledError:
                logger.info("Intelligence loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in continuous intelligence loop: {e}")
                await asyncio.sleep(15)  # Pause before retry on failure

    def stop(self) -> None:
        self.is_running = False
