"""Integration tests for FastAPI endpoints."""
import httpx
import pytest
from app.api.main import app
from app.storage.database import init_db

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
