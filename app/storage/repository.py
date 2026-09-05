"""Data access repository for database transactions."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.storage.database import get_db_session
from app.storage.models import (
    AlertRecord,
    AnalysisRunRecord,
    EconomicEventRecord,
    LiquidityZoneRecord,
    MarketSnapshot,
    NewsEventRecord,
    ProviderHealthRecord
)

class Repository:
    """Repository class encapsulating database operations."""

    @staticmethod
    async def save_market_snapshot(data: Dict[str, Any]) -> MarketSnapshot:
        async with get_db_session() as session:
            snapshot = MarketSnapshot(**data)
            session.add(snapshot)
            await session.flush()
            return snapshot

    @staticmethod
    async def get_latest_market_snapshot() -> Optional[MarketSnapshot]:
        async with get_db_session() as session:
            result = await session.execute(
                select(MarketSnapshot).order_by(desc(MarketSnapshot.timestamp)).limit(1)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def save_liquidity_zones(zones: List[Dict[str, Any]]) -> None:
        async with get_db_session() as session:
            # Deactivate older zones before inserting new ones
            await session.execute(
                update(LiquidityZoneRecord).values(is_active=False)
            )
            for z in zones:
                rec = LiquidityZoneRecord(**z)
                session.add(rec)

    @staticmethod
    async def get_active_liquidity_zones() -> List[LiquidityZoneRecord]:
        async with get_db_session() as session:
            result = await session.execute(
                select(LiquidityZoneRecord)
                .where(LiquidityZoneRecord.is_active == True)
                .order_by(desc(LiquidityZoneRecord.strength))
            )
            return list(result.scalars().all())

    @staticmethod
    async def save_news_events(news_list: List[Dict[str, Any]]) -> List[NewsEventRecord]:
        saved_events = []
        seen_fps = set()
        async with get_db_session() as session:
            for item in news_list:
                fp = item.get("fingerprint")
                if not fp or fp in seen_fps:
                    continue
                seen_fps.add(fp)
                # Check duplicate in DB
                existing = await session.execute(
                    select(NewsEventRecord).where(NewsEventRecord.fingerprint == fp)
                )
                if existing.scalar_one_or_none() is None:
                    event = NewsEventRecord(**item)
                    session.add(event)
                    saved_events.append(event)
        return saved_events

    @staticmethod
    async def get_recent_news(limit: int = 20) -> List[NewsEventRecord]:
        async with get_db_session() as session:
            result = await session.execute(
                select(NewsEventRecord).order_by(desc(NewsEventRecord.published_time)).limit(limit)
            )
            return list(result.scalars().all())

    @staticmethod
    async def save_economic_events(events: List[Dict[str, Any]]) -> List[EconomicEventRecord]:
        saved = []
        seen_fps = set()
        async with get_db_session() as session:
            for item in events:
                fp = item.get("fingerprint")
                if not fp or fp in seen_fps:
                    continue
                seen_fps.add(fp)
                existing = await session.execute(
                    select(EconomicEventRecord).where(EconomicEventRecord.fingerprint == fp)
                )
                rec = existing.scalar_one_or_none()
                if rec is None:
                    event = EconomicEventRecord(**item)
                    session.add(event)
                    saved.append(event)
                else:
                    # Update status and actual if changed
                    if item.get("actual") and rec.actual != item.get("actual"):
                        rec.actual = item.get("actual")
                        rec.status = "RELEASED"
                        rec.surprise = item.get("surprise")
        return saved

    @staticmethod
    async def get_upcoming_economic_events(hours_ahead: int = 48) -> List[EconomicEventRecord]:
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=hours_ahead)
        async with get_db_session() as session:
            result = await session.execute(
                select(EconomicEventRecord)
                .where(EconomicEventRecord.scheduled_time >= now - timedelta(hours=6))
                .where(EconomicEventRecord.scheduled_time <= cutoff)
                .order_by(EconomicEventRecord.scheduled_time)
            )
            return list(result.scalars().all())

    @staticmethod
    async def save_analysis_run(data: Dict[str, Any]) -> AnalysisRunRecord:
        async with get_db_session() as session:
            rec = AnalysisRunRecord(**data)
            session.add(rec)
            await session.flush()
            return rec

    @staticmethod
    async def get_latest_analysis_run() -> Optional[AnalysisRunRecord]:
        async with get_db_session() as session:
            result = await session.execute(
                select(AnalysisRunRecord).order_by(desc(AnalysisRunRecord.timestamp)).limit(1)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_previous_analysis_run() -> Optional[AnalysisRunRecord]:
        async with get_db_session() as session:
            result = await session.execute(
                select(AnalysisRunRecord).order_by(desc(AnalysisRunRecord.timestamp)).offset(1).limit(1)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_analysis_history(limit: int = 50) -> List[AnalysisRunRecord]:
        async with get_db_session() as session:
            result = await session.execute(
                select(AnalysisRunRecord).order_by(desc(AnalysisRunRecord.timestamp)).limit(limit)
            )
            return list(result.scalars().all())

    @staticmethod
    async def save_alert(data: Dict[str, Any]) -> AlertRecord:
        async with get_db_session() as session:
            rec = AlertRecord(**data)
            session.add(rec)
            await session.flush()
            return rec

    @staticmethod
    async def is_alert_on_cooldown(fingerprint: str, cooldown_minutes: int = 30) -> bool:
        if not fingerprint:
            return False
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=cooldown_minutes)
        async with get_db_session() as session:
            result = await session.execute(
                select(AlertRecord)
                .where(AlertRecord.fingerprint == fingerprint)
                .where(AlertRecord.timestamp >= cutoff)
            )
            return result.scalar_one_or_none() is not None

    @staticmethod
    async def update_provider_health(
        provider_name: str,
        is_healthy: bool,
        latency_ms: float = 0.0,
        error_message: str = ""
    ) -> None:
        now = datetime.now(timezone.utc)
        async with get_db_session() as session:
            result = await session.execute(
                select(ProviderHealthRecord).where(ProviderHealthRecord.provider_name == provider_name)
            )
            rec = result.scalar_one_or_none()
            if rec is None:
                rec = ProviderHealthRecord(
                    provider_name=provider_name,
                    is_healthy=is_healthy,
                    latency_ms=latency_ms,
                    last_success=now if is_healthy else None,
                    last_error=now if not is_healthy else None,
                    last_error_message=error_message,
                    consecutive_failures=0 if is_healthy else 1
                )
                session.add(rec)
            else:
                rec.is_healthy = is_healthy
                rec.latency_ms = latency_ms
                if is_healthy:
                    rec.last_success = now
                    rec.consecutive_failures = 0
                else:
                    rec.last_error = now
                    rec.last_error_message = error_message
                    rec.consecutive_failures += 1

    @staticmethod
    async def get_all_provider_health() -> List[ProviderHealthRecord]:
        async with get_db_session() as session:
            result = await session.execute(
                select(ProviderHealthRecord).order_by(ProviderHealthRecord.provider_name)
            )
            return list(result.scalars().all())
