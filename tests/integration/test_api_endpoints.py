"""Integration tests for FastAPI endpoints."""
import httpx
import pytest
from datetime import datetime, timezone
from app.api.main import app
from app.storage.database import init_db
from app.alerts.engine import AlertEngine
from app.ai.base import AISynthesisOutput

@pytest.mark.asyncio
async def test_health_and_status_endpoints():
    await init_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        health_resp = await client.get("/health")
        assert health_resp.status_code == 200
        health_json = health_resp.json()
        assert "status" in health_json
        assert "version" in health_json

        status_resp = await client.get("/status")
        assert status_resp.status_code == 200
        status_json = status_resp.json()
        assert "timezone" in status_json
        assert status_json["timezone"] == "Asia/Kolkata"

@pytest.mark.asyncio
async def test_dashboard_and_api_endpoints():
    await init_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Dashboard HTML
        dash_resp = await client.get("/")
        assert dash_resp.status_code == 200
        assert "XAUUSD" in dash_resp.text

        # Market Data API
        m_resp = await client.get("/api/market-data")
        assert m_resp.status_code == 200

        # Liquidity API
        l_resp = await client.get("/api/liquidity")
        assert l_resp.status_code == 200

        # Candles API (Feature 1)
        candles_resp = await client.get("/api/candles?timeframe=H1")
        assert candles_resp.status_code == 200
        candles_json = candles_resp.json()
        assert "candles" in candles_json
        assert "liquidity_overlays" in candles_json
        assert len(candles_json["candles"]) > 0

        # Geopolitics CEI API (Feature 2)
        geo_resp = await client.get("/api/geopolitics")
        assert geo_resp.status_code == 200
        geo_json = geo_resp.json()
        assert "conflict_escalation_index" in geo_json
        assert "safe_haven_premium_usd" in geo_json
        assert "flashpoints" in geo_json

        # Institutional COT API (Feature 3)
        cot_resp = await client.get("/api/institutional-flow")
        assert cot_resp.status_code == 200
        cot_json = cot_resp.json()
        assert "managed_money" in cot_json
        assert "central_banks" in cot_json

        # Macro Scenario Simulator POST API (Feature 4)
        sim_resp = await client.post("/api/simulate-scenario", json={
            "current_price": 2900.0,
            "us10y_bps_shift": 15.0,
            "dxy_pct_shift": 1.0,
            "cpi_surprise_pct": 0.2,
            "geopolitical_shock": "MODERATE"
        })
        assert sim_resp.status_code == 200
        sim_json = sim_resp.json()
        assert "projected_price" in sim_json
        assert "net_delta_usd" in sim_json
        assert "projected_verdict" in sim_json

        # News API
        n_resp = await client.get("/api/news")
        assert n_resp.status_code == 200
        assert isinstance(n_resp.json(), list)

        # Economic Calendar API
        c_resp = await client.get("/api/economic-calendar")
        assert c_resp.status_code == 200
        assert isinstance(c_resp.json(), list)

        # Accuracy API
        a_resp = await client.get("/api/accuracy")
        assert a_resp.status_code == 200

        # Config GET API
        cfg_resp = await client.get("/api/config")
        assert cfg_resp.status_code == 200
        cfg_json = cfg_resp.json()
        assert "ai_priority" in cfg_json
        assert "timezone" in cfg_json

        # Config POST API
        post_cfg_resp = await client.post("/api/config", json={
            "AI_PRIORITY": "gemini_first",
            "ANALYSIS_INTERVAL_SECONDS": 180
        })
        assert post_cfg_resp.status_code == 200
        assert post_cfg_resp.json()["status"] == "SUCCESS"

@pytest.mark.asyncio
async def test_session_open_briefing_alert_dispatch():
    """Verify session briefing alert logic."""
    engine = AlertEngine()
    dummy_synthesis = AISynthesisOutput(
        direction="BULLISH BIAS",
        score=35.0,
        confidence=78.0,
        macro_summary="Real yields declining, gold supported.",
        news_summary="Geopolitical alerts remain active.",
        risk_factors="Hawkish FOMC surprise, DXY surge",
        dominant_drivers=["Real yield decline", "Central bank demand"],
        final_market_verdict="ACCUMULATION_FAVORED",
        executive_verdict_summary="Bullish continuation supported by yields and DXY easing."
    )
    # Test checking session briefing does not crash during execution
    await engine.check_and_dispatch_session_briefing(
        current_price=2905.50,
        current_direction={"direction": "BULLISH BIAS", "score": 35.0},
        liquidity_analysis={"liquidity_above": [{"price": 2915.0}], "liquidity_below": [{"price": 2895.0}]},
        geopolitical_data={"conflict_escalation_index": 45.0, "safe_haven_premium_usd": 22.50},
        upcoming_events=[],
        synthesis_output=dummy_synthesis,
        market_data={"high_24h": 2918.0, "low_24h": 2890.0},
        now_dt=datetime(2026, 9, 5, 7, 45, tzinfo=timezone.utc)
    )
