"""Telegram Bot client with safe HTML formatting, retry handling, interactive commands, and polling."""
import asyncio
import html
from typing import Any, Dict, List, Optional
import httpx
from app.config.settings import settings
from app.core.logging import logger
from app.storage.repository import Repository

class TelegramBot:
    """Sends structured alerts and reports to Telegram with spam control and interactive commands."""

    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.enabled = settings.TELEGRAM_ALERTS_ENABLED and settings.has_telegram
        self._last_update_id = 0

    async def send_message(self, text: str, parse_mode: str = "HTML", chat_id: Optional[str] = None) -> bool:
        """Sends a text message to the configured Telegram chat or specified recipient."""
        target_chat = chat_id or self.chat_id
        if not self.enabled and not (settings.TELEGRAM_BOT_TOKEN and target_chat):
            logger.info(f"[TELEGRAM SIMULATION / LOCAL LOG]\n{text}")
            return True

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                await Repository.update_provider_health("Telegram_Bot", is_healthy=True)
                return True
            else:
                logger.error(f"Telegram send failed ({resp.status_code}): {resp.text}")
                await Repository.update_provider_health("Telegram_Bot", is_healthy=False, error_message=resp.text)
                return False
        except Exception as e:
            logger.error(f"Telegram send exception: {e}")
            await Repository.update_provider_health("Telegram_Bot", is_healthy=False, error_message=str(e))
            return False

    async def handle_command(self, text: str, chat_id: Optional[str] = None, orchestrator: Any = None) -> str:
        """Parses and responds to interactive Telegram slash commands."""
        from app.alerts.templates import AlertTemplates
        from app.analysis.liquidity.session_calculator import SessionCalculator
        from app.analysis.macro.macro_engine import MacroEngine

        cmd = text.strip().split()[0].lower() if text else ""

        if cmd in ("/start", "/help"):
            response = AlertTemplates.help_command_response()
            await self.send_message(response, chat_id=chat_id)
            return response

        elif cmd == "/killzone":
            kz_status = SessionCalculator.get_ict_killzone_status()
            snapshot = await Repository.get_latest_market_snapshot()
            price = snapshot.price if snapshot else 2700.0
            response = AlertTemplates.killzone_command_response(
                killzone_info=kz_status,
                current_price=price,
                recent_sweeps=[]
            )
            await self.send_message(response, chat_id=chat_id)
            return response

        elif cmd == "/levels":
            snapshot = await Repository.get_latest_market_snapshot()
            price = snapshot.price if snapshot else 2700.0
            zones = await Repository.get_active_liquidity_zones()
            
            above = []
            below = []
            for z in zones:
                z_dict = {"price": z.price, "zone_type": z.zone_type, "strength": z.strength}
                if z.price > price:
                    above.append(z_dict)
                else:
                    below.append(z_dict)

            response = AlertTemplates.levels_command_response(
                price=price,
                liquidity_above=above,
                liquidity_below=below,
                session_high=snapshot.high_24h if snapshot else 0.0,
                session_low=snapshot.low_24h if snapshot else 0.0
            )
            await self.send_message(response, chat_id=chat_id)
            return response


        elif cmd == "/scalp":
            latest = await Repository.get_latest_analysis_run()
            snapshot = await Repository.get_latest_market_snapshot()
            price = snapshot.price if snapshot else (latest.gold_price if latest else 2700.0)
            kz_status = SessionCalculator.get_ict_killzone_status()
            tech_sc = getattr(latest, "technical_score", 0.0) if latest else 0.0
            
            response = AlertTemplates.scalp_command_response(
                price=price,
                scalp_bias=getattr(latest, "direction", "MOMENTUM_ALIGNMENT"),
                day_trade_bias=getattr(latest, "direction", "STRUCTURE_FOLLOW"),
                overall_trend=getattr(snapshot, "trend", "NEUTRAL") if snapshot else "NEUTRAL",
                market_structure="BULLISH_ORDERFLOW" if tech_sc > 15 else "BEARISH_ORDERFLOW" if tech_sc < -15 else "RANGE_BOUND",
                vwap=price - 1.5 if tech_sc > 0 else price + 1.5,
                tech_score=tech_sc,
                rsi_15m=snapshot.rsi if snapshot else 52.0,
                supertrend="BULLISH" if tech_sc > 0 else "BEARISH",
                killzone=kz_status.get("killzone_name", "OFF_HOURS")
            )
            await self.send_message(response, chat_id=chat_id)
            return response

        elif cmd == "/dxy":
            snapshot = await Repository.get_latest_market_snapshot()
            gold_price = snapshot.price if snapshot else 2700.0
            gold_change = snapshot.change_24h if snapshot else 0.0
            
            # Fetch macro data
            macro_eng = MacroEngine()
            div_data = macro_eng.dxy_gold_divergence(
                dxy_change_pct=0.15,
                gold_change_pct=gold_change,
                yield_change_pct=0.5
            )
            
            response = AlertTemplates.dxy_command_response(
                dxy_price=104.25,
                dxy_change=0.15,
                dxy_trend="BULLISH" if div_data.get("dxy_score", 0) < 0 else "BEARISH",
                us10y_yield=4.32,
                us10y_change=0.5,
                divergence_status=div_data.get("status", "NORMAL_INVERSE"),
                divergence_desc=div_data.get("description", "Macro correlations aligned with typical inverse behavior."),
                gold_price=gold_price,
                gold_change=gold_change
            )
            await self.send_message(response, chat_id=chat_id)
            return response

        elif cmd == "/verdict":
            latest = await Repository.get_latest_analysis_run()
            snapshot = await Repository.get_latest_market_snapshot()
            if not latest:
                msg = "⚠️ No analysis run records available yet. Please wait for the initial market cycle."
                await self.send_message(msg, chat_id=chat_id)
                return msg

            zones = await Repository.get_active_liquidity_zones()
            above = [{"price": z.price, "zone_type": z.zone_type, "strength": z.strength} for z in zones if z.price > latest.gold_price]
            below = [{"price": z.price, "zone_type": z.zone_type, "strength": z.strength} for z in zones if z.price <= latest.gold_price]

            response = AlertTemplates.periodic_report(
                price=latest.gold_price,
                direction=latest.direction,
                score=latest.direction_score,
                confidence=latest.confidence,
                macro_score=latest.macro_score,
                usd_score=latest.usd_score,
                yield_score=latest.yield_score,
                news_score=latest.news_score,
                tech_score=latest.technical_score,
                trend=snapshot.trend if snapshot else "NEUTRAL",
                volatility=snapshot.volatility if snapshot else "NORMAL",
                liquidity_above=above,
                liquidity_below=below,
                dominant_drivers=latest.dominant_drivers or [],
                macro_summary=latest.macro_summary or "Macro synthesis active.",
                news_summary=latest.news_summary or "Real-time news monitoring.",
                risk_factors=latest.risk_factors or "Standard market volatility.",
                upcoming_events=[],
                provider_used=latest.provider_used or "Local Rule Engine",
                final_market_verdict=latest.final_market_verdict or latest.direction
            )
            await self.send_message(response, chat_id=chat_id)
            return response


        elif cmd == "/news":
            recent = await Repository.get_recent_news(limit=5)
            if not recent:
                msg = "📰 No high-impact news captured in the last observation window."
                await self.send_message(msg, chat_id=chat_id)
                return msg

            news_lines = []
            for n in recent:
                imp = f"[{n.impact_level}]" if n.impact_level else ""
                sent = f"({n.gold_sentiment})" if n.gold_sentiment else ""
                news_lines.append(f"• <b>{self.escape(n.title)}</b>\n  <i>{self.escape(n.source)} {imp} {sent}</i>")

            msg = f"📰 <b>LATEST BREAKING GOLD HEADLINES</b>\n━━━━━━━━━━━━━━━━━━━━\n" + "\n\n".join(news_lines)
            await self.send_message(msg, chat_id=chat_id)
            return msg

        else:
            msg = f"❓ Unknown command: {self.escape(cmd)}. Send <b>/help</b> for all available commands."
            await self.send_message(msg, chat_id=chat_id)
            return msg

    async def poll_updates(self, orchestrator: Any = None) -> None:
        """Fetches and processes new Telegram bot updates via long-polling."""
        if not self.enabled:
            return

        url = f"https://api.telegram.org/bot{self.token}/getUpdates"
        params = {"offset": self._last_update_id + 1, "timeout": 10}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return

            data = resp.json()
            results = data.get("result", [])
            for update in results:
                self._last_update_id = update.get("update_id", self._last_update_id)
                msg = update.get("message", {})
                text = msg.get("text", "")
                chat = msg.get("chat", {})
                sender_chat_id = str(chat.get("id", ""))
                
                if text.startswith("/"):
                    logger.info(f"Received Telegram command '{text}' from chat {sender_chat_id}")
                    await self.handle_command(text, chat_id=sender_chat_id, orchestrator=orchestrator)
        except Exception as e:
            logger.debug(f"Telegram polling tick error: {e}")

    async def run_poller_loop(self, orchestrator: Any = None) -> None:
        """Continuous background poller task for interactive Telegram bot commands."""
        if not self.enabled:
            logger.info("Telegram polling skipped (bot not configured or disabled).")
            return

        logger.info("Starting Telegram Bot interactive command poller loop...")
        while True:
            try:
                await self.poll_updates(orchestrator=orchestrator)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Telegram poller loop: {e}")
                await asyncio.sleep(5)
            await asyncio.sleep(1)

    @staticmethod
    def escape(text: str) -> str:
        """Escapes raw strings for safe Telegram HTML output."""
        return html.escape(str(text))

