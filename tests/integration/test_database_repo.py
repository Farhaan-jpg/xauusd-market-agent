"""Integration tests verifying SQLite persistence, deduplication, and cooldowns."""
from datetime import datetime, timezone
import pytest
from app.storage.database import init_db
from app.storage.repository import Repository

@pytest.mark.asyncio
async def test_database_initialization_and_snapshot_crud():
    await init_db()

    # Save Snapshot
    snap = await Repository.save_market_snapshot({
        "symbol": "XAUUSD",
        "price": 2535.40,
        "change_24h": 0.85,
        "high_24h": 2540.0,
        "low_24h": 2515.0,
        "atr": 18.5,
        "rsi": 62.0,
        "trend": "BULLISH"
    })
    assert snap.id is not None
    assert snap.price == 2535.40

    # Retrieve latest snapshot
    latest = await Repository.get_latest_market_snapshot()
    assert latest is not None
    assert latest.price == 2535.40

@pytest.mark.asyncio
async def test_news_deduplication_by_fingerprint():
    import uuid
    await init_db()
    unique_fp = f"test_fp_{uuid.uuid4().hex}"
    news = [
        {"fingerprint": unique_fp, "source": "Kitco", "title": "Gold Surges on Fed", "published_time": datetime.now(timezone.utc)},
        {"fingerprint": unique_fp, "source": "Kitco Duplicate", "title": "Gold Surges on Fed", "published_time": datetime.now(timezone.utc)}
    ]
    saved = await Repository.save_news_events(news)
    # Only first unique fingerprint should be saved
    assert len(saved) == 1

@pytest.mark.asyncio
async def test_alert_cooldown_check():
    import uuid
    await init_db()
    fp = f"TEST_ALERT_FP_{uuid.uuid4().hex}"

    # Initially not on cooldown
    is_cool = await Repository.is_alert_on_cooldown(fp, cooldown_minutes=30)
    assert is_cool is False

    # Save alert
    await Repository.save_alert({
        "alert_type": "TEST_ALERT",
        "title": "Test Title",
        "message": "Test Message",
        "fingerprint": fp,
        "sent_successfully": True
    })

    # Now on cooldown
    is_cool_after = await Repository.is_alert_on_cooldown(fp, cooldown_minutes=30)
    assert is_cool_after is True
