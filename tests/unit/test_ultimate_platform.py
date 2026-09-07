"""
Unit tests for the Ultimate Real-Time AI Intelligence Platform & Dual-Mode Engine.
"""

import pytest
from app.analysis.intermarket.all_correlations_matrix import AllCorrelationsMatrix
from app.analysis.geopolitical.live_geopolitics_feed import LiveGeopoliticsFeed
from app.analysis.news.financial_news_feed import FinancialNewsFeed
from app.analysis.intelligence.ultimate_synthesizer import UltimateSynthesizer
from httpx import AsyncClient, ASGITransport
from app.api.main import app


class TestUltimatePlatform:
    """Tests for 6-Factor Correlations, Geopolitics, Financial Wire, and Dual-Mode Synthesizer."""

    def test_correlations_matrix_calculation(self):
        matrix = AllCorrelationsMatrix.calculate_matrix(gold_change_pct=0.5)
        assert "correlations" in matrix
        assert "composite_correlation_score" in matrix
        assert "composite_bias" in matrix

        corrs = matrix["correlations"]
        assert "dxy_dollar" in corrs
        assert "tips_real_yields" in corrs
        assert "gold_silver_ratio" in corrs
        assert "crude_oil_wti" in corrs
        assert "shanghai_gold_premium" in corrs
        assert "vix_volatility" in corrs
        assert any(b in matrix["composite_bias"] for b in ["BULLISH", "BEARISH", "NEUTRAL"])

    def test_live_geopolitics_feed(self):
        feed = LiveGeopoliticsFeed.evaluate_geopolitics()
        assert "conflict_escalation_index" in feed
        assert 0.0 <= feed["conflict_escalation_index"] <= 100.0
        assert "safe_haven_premium_usd" in feed
        assert feed["safe_haven_premium_usd"] >= 0.0
        assert len(feed["theater_alerts"]) >= 3

    def test_financial_news_feed(self):
        feed = FinancialNewsFeed.evaluate_financial_wire()
        assert "monetary_sentiment_score" in feed
        assert -100.0 <= feed["monetary_sentiment_score"] <= 100.0
        assert "central_bank_accumulation_pace_tonnes" in feed
        assert feed["central_bank_accumulation_pace_tonnes"] > 500
        assert "fed_tone" in feed

    def test_ultimate_synthesizer_scalping_mode(self):
        geo = LiveGeopoliticsFeed.evaluate_geopolitics()
        fin = FinancialNewsFeed.evaluate_financial_wire()
        corr = AllCorrelationsMatrix.calculate_matrix(gold_change_pct=0.8)

        verdict = UltimateSynthesizer.synthesize_market_verdict(
            current_price=2725.0,
            gold_change_pct=0.8,
            geopolitics_data=geo,
            financial_data=fin,
            correlations_data=corr,
            technical_score=20.0,
            cvd_delta=400.0,
            mode="scalp"
        )

        assert verdict["mode"] == "SCALPING"
        assert verdict["direction"] in ["BULLISH", "BEARISH", "NEUTRAL"]
        assert 50 <= verdict["conviction_pct"] <= 100
        assert "actionable_setup" in verdict

        setup = verdict["actionable_setup"]
        assert setup["stop_loss_pts"] <= 6.0  # Tight scalping stop loss
        assert "5-30 Mins" in setup["holding_horizon"]

    def test_ultimate_synthesizer_daytrading_mode(self):
        geo = LiveGeopoliticsFeed.evaluate_geopolitics()
        fin = FinancialNewsFeed.evaluate_financial_wire()
        corr = AllCorrelationsMatrix.calculate_matrix(gold_change_pct=-0.5)

        verdict = UltimateSynthesizer.synthesize_market_verdict(
            current_price=2725.0,
            gold_change_pct=-0.5,
            geopolitics_data=geo,
            financial_data=fin,
            correlations_data=corr,
            technical_score=-15.0,
            cvd_delta=-350.0,
            mode="daytrade"
        )

        assert verdict["mode"] == "DAY TRADING"
        assert verdict["direction"] in ["BULLISH", "BEARISH", "NEUTRAL"]
        assert "actionable_setup" in verdict

        setup = verdict["actionable_setup"]
        assert setup["stop_loss_pts"] >= 10.0  # Wide swing day trading stop loss
        assert "Hours" in setup["holding_horizon"]


@pytest.mark.asyncio
class TestUltimateApiEndpoints:
    """Tests for FastAPI endpoints."""

    async def test_api_correlations(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.get("/api/correlations")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "SUCCESS"
            assert "correlations" in data["data"]

    async def test_api_geopolitics_feed(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.get("/api/geopolitics-feed")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "SUCCESS"
            assert "conflict_escalation_index" in data["data"]

    async def test_api_financial_feed(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.get("/api/financial-feed")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "SUCCESS"
            assert "central_bank_accumulation_pace_tonnes" in data["data"]

    async def test_api_intelligence_dual_mode(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_scalp = await ac.get("/api/intelligence?mode=scalp")
            assert res_scalp.status_code == 200
            data_scalp = res_scalp.json()
            assert data_scalp["status"] == "SUCCESS"
            assert data_scalp["data"]["mode"] == "SCALPING"

            res_day = await ac.get("/api/intelligence?mode=daytrade")
            assert res_day.status_code == 200
            data_day = res_day.json()
            assert data_day["status"] == "SUCCESS"
            assert data_day["data"]["mode"] == "DAY TRADING"

    async def test_api_broadcast_trade_setup(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.post("/api/broadcast-trade-setup", json={"mode": "scalp"})
            assert res.status_code == 200
            data = res.json()
            assert data["status"] in ["SUCCESS", "FAILED"]
            assert "trade_setup" in data
            assert data["mode"] == "SCALPING"

