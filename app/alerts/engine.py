"""Alert Engine managing event fingerprinting, cooldowns, and Telegram dispatching."""
import hashlib
from typing import Any, Dict, List, Optional
from app.alerts.templates import AlertTemplates
from app.config.settings import settings
from app.core.logging import logger
from app.storage.repository import Repository
from app.telegram.bot import TelegramBot

class AlertEngine:
    """Dispatches Telegram alerts while preventing duplicate spam or jitter alerts."""

    def __init__(self):
        self.bot = TelegramBot()

    async def evaluate_and_dispatch_alerts(
        self,
        current_price: float,
        current_direction: Dict[str, Any],
        previous_analysis: Optional[Any],
        liquidity_analysis: Dict[str, Any],
        news_items: List[Dict[str, Any]],
        synthesis_output: Any,
        provider_used: str,
        upcoming_events: List[Dict[str, Any]],
        force_report: bool = False
    ) -> None:
        """Evaluates conditions for Direction Change, High-Impact News, Liquidity Proximity, and Periodic Reports."""

        # 1. Direction Shift Alert
        if previous_analysis:
            prev_dir = previous_analysis.direction
            prev_score = previous_analysis.direction_score
            curr_dir = current_direction["direction"]
            curr_score = current_direction["direction_score"]

            score_diff = abs(curr_score - prev_score)
            dir_changed = (prev_dir != curr_dir and score_diff >= settings.DIRECTION_CHANGE_THRESHOLD_SCORE)

            if dir_changed:
                fp = hashlib.md5(f"DIR_CHANGE_{prev_dir}_{curr_dir}_{int(curr_score)}".encode()).hexdigest()
                if not await Repository.is_alert_on_cooldown(fp, cooldown_minutes=60):
                    msg = AlertTemplates.direction_change_alert(
                        prev_direction=prev_dir,
                        prev_score=prev_score,
                        new_direction=curr_dir,
                        new_score=curr_score,
                        price=current_price,
                        dominant_drivers=current_direction.get("dominant_drivers", [])
                    )
                    sent = await self.bot.send_message(msg)
                    await Repository.save_alert({
                        "alert_type": "DIRECTION_CHANGE",
                        "title": f"Direction Change: {prev_dir} -> {curr_dir}",
                        "message": msg,
                        "fingerprint": fp,
                        "sent_successfully": sent
                    })

        # 2. High-Impact News Alert
        for item in news_items:
            if item.get("impact_level") in ["CRITICAL", "HIGH"] and not item.get("alerted"):
                fp = f"NEWS_{item['fingerprint']}"
                if not await Repository.is_alert_on_cooldown(fp, cooldown_minutes=180):
                    msg = AlertTemplates.high_impact_news_alert(
                        title=item["title"],
                        source=item["source"],
                        gold_impact=item.get("gold_impact", "NEUTRAL"),
                        impact_level=item.get("impact_level", "HIGH"),
                        summary=synthesis_output.news_summary
                    )
                    sent = await self.bot.send_message(msg)
                    await Repository.save_alert({
                        "alert_type": "HIGH_IMPACT_NEWS",
                        "title": item["title"],
                        "message": msg,
                        "fingerprint": fp,
                        "sent_successfully": sent
                    })

        # 3. Major Liquidity Proximity Alert (Within $2.00 or 0.1% of high strength zone)
        all_zones = liquidity_analysis.get("all_zones", [])
        for z in all_zones:
            if z.get("strength", 0) >= 80 and z.get("distance_from_price", 999) <= 2.0:
                fp = f"LIQ_PROX_{int(z['price'])}_{z['zone_type']}"
                if not await Repository.is_alert_on_cooldown(fp, cooldown_minutes=60):
                    msg = AlertTemplates.liquidity_proximity_alert(
                        zone_price=z["price"],
                        zone_type=z["zone_type"],
                        strength=z["strength"],
                        current_price=current_price,
                        distance=z["distance_from_price"]
                    )
                    sent = await self.bot.send_message(msg)
                    await Repository.save_alert({
                        "alert_type": "LIQUIDITY_PROXIMITY",
                        "title": f"Liquidity Proximity: ${z['price']:.2f}",
                        "message": msg,
                        "fingerprint": fp,
                        "sent_successfully": sent
                    })

        # 4. Periodic Market Intelligence Report (if forced or on schedule)
        if force_report:
            msg = AlertTemplates.periodic_report(
                price=current_price,
                direction=synthesis_output.direction,
                score=synthesis_output.score,
                confidence=synthesis_output.confidence,
                macro_score=current_direction.get("macro_score", 0.0),
                usd_score=current_direction.get("usd_score", 0.0),
                yield_score=current_direction.get("yield_score", 0.0),
                news_score=current_direction.get("news_score", 0.0),
                tech_score=current_direction.get("technical_score", 0.0),
                trend=current_direction.get("trend", "NEUTRAL"),
                volatility=current_direction.get("volatility", "NORMAL"),
                liquidity_above=liquidity_analysis.get("liquidity_above", []),
                liquidity_below=liquidity_analysis.get("liquidity_below", []),
                dominant_drivers=synthesis_output.dominant_drivers,
                macro_summary=synthesis_output.macro_summary,
                news_summary=synthesis_output.news_summary,
                risk_factors=synthesis_output.risk_factors,
                upcoming_events=upcoming_events,
                provider_used=provider_used,
                final_market_verdict=synthesis_output.final_market_verdict,
                executive_verdict_summary=synthesis_output.executive_verdict_summary
            )
            sent = await self.bot.send_message(msg)
            await Repository.save_alert({
                "alert_type": "PERIODIC_REPORT",
                "title": f"Market Intelligence Report - {synthesis_output.direction} ({synthesis_output.final_market_verdict})",
                "message": msg,
                "fingerprint": f"REPORT_{int(current_price)}_{synthesis_output.direction}",
                "sent_successfully": sent
            })
