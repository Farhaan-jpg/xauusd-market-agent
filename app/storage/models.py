"""SQLAlchemy models for persisting market snapshots, liquidity zones, news, and analyses."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=get_utc_now, index=True)
    symbol = Column(String(32), default="XAUUSD", index=True)
    price = Column(Float, nullable=False)
    change_24h = Column(Float, default=0.0)
    high_24h = Column(Float, default=0.0)
    low_24h = Column(Float, default=0.0)
    atr = Column(Float, default=0.0)
    rsi = Column(Float, default=50.0)
    macd = Column(Float, default=0.0)
    macd_signal = Column(Float, default=0.0)
    ema_20 = Column(Float, default=0.0)
    ema_50 = Column(Float, default=0.0)
    ema_200 = Column(Float, default=0.0)
    trend = Column(String(32), default="NEUTRAL")
    volatility = Column(String(32), default="NORMAL")
    data_quality = Column(String(32), default="GOOD")
    raw_ohlc = Column(JSON, nullable=True)

class LiquidityZoneRecord(Base):
    __tablename__ = "liquidity_zones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, index=True)
    price = Column(Float, nullable=False)
    zone_range_low = Column(Float, nullable=False)
    zone_range_high = Column(Float, nullable=False)
    zone_type = Column(String(64), nullable=False)  # 'PDH', 'PDL', 'EQH', 'EQL', 'FVG', 'SESSION_HIGH', etc.
    timeframe = Column(String(16), default="1H")
    strength = Column(Float, default=50.0)  # 0 to 100
    distance_from_price = Column(Float, default=0.0)
    is_above = Column(Boolean, default=True)
    touch_count = Column(Integer, default=1)
    is_active = Column(Boolean, default=True, index=True)

class NewsEventRecord(Base):
    __tablename__ = "news_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fingerprint = Column(String(64), unique=True, index=True, nullable=False)
    source = Column(String(64), nullable=False)
    title = Column(String(512), nullable=False)
    published_time = Column(DateTime(timezone=True), default=get_utc_now, index=True)
    url = Column(String(1024), default="")
    category = Column(String(64), default="GENERAL")
    relevance_score = Column(Float, default=0.0)
    sentiment = Column(String(32), default="NEUTRAL")
    gold_impact = Column(String(32), default="NEUTRAL")  # BULLISH, BEARISH, NEUTRAL, UNCERTAIN
    impact_level = Column(String(32), default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    alerted = Column(Boolean, default=False)

class EconomicEventRecord(Base):
    __tablename__ = "economic_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fingerprint = Column(String(64), unique=True, index=True, nullable=False)
    event_name = Column(String(256), nullable=False)
    country = Column(String(32), default="US")
    currency = Column(String(16), default="USD")
    scheduled_time = Column(DateTime(timezone=True), index=True, nullable=False)
    importance = Column(String(16), default="HIGH")  # LOW, MEDIUM, HIGH
    forecast = Column(String(64), default="")
    previous = Column(String(64), default="")
    actual = Column(String(64), default="")
    surprise = Column(Float, nullable=True)
    status = Column(String(32), default="SCHEDULED")  # SCHEDULED, RELEASED
    gold_impact = Column(String(32), default="UNCERTAIN")
    alerted = Column(Boolean, default=False)

class AnalysisRunRecord(Base):
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=get_utc_now, index=True)
    gold_price = Column(Float, nullable=False)
    direction = Column(String(32), nullable=False)  # STRONGLY BULLISH, BULLISH, NEUTRAL, BEARISH, STRONGLY BEARISH, INSUFFICIENT DATA
    direction_score = Column(Float, nullable=False)  # -100 to +100
    confidence = Column(Float, nullable=False)  # 0 to 100
    macro_score = Column(Float, default=0.0)
    usd_score = Column(Float, default=0.0)
    yield_score = Column(Float, default=0.0)
    news_score = Column(Float, default=0.0)
    technical_score = Column(Float, default=0.0)
    liquidity_score = Column(Float, default=0.0)
    dominant_drivers = Column(JSON, default=list)
    supporting_factors = Column(JSON, default=list)
    contradicting_factors = Column(JSON, default=list)
    macro_summary = Column(Text, default="")
    news_summary = Column(Text, default="")
    liquidity_summary = Column(JSON, default=list)
    risk_factors = Column(Text, default="")
    data_quality = Column(String(32), default="GOOD")
    provider_used = Column(String(64), default="DETERMINISTIC_FALLBACK")

class AlertRecord(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=get_utc_now, index=True)
    alert_type = Column(String(64), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    fingerprint = Column(String(64), index=True)
    sent_successfully = Column(Boolean, default=True)

class ProviderHealthRecord(Base):
    __tablename__ = "provider_health"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_name = Column(String(64), unique=True, index=True, nullable=False)
    is_healthy = Column(Boolean, default=True)
    latency_ms = Column(Float, default=0.0)
    last_success = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(DateTime(timezone=True), nullable=True)
    last_error_message = Column(String(512), default="")
    consecutive_failures = Column(Integer, default=0)
