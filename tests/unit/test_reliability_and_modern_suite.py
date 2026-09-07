"""
Unit tests for Ultimate Reliability, Anti-Confusion & Modern Intelligence Suite.
"""

import pytest
from datetime import datetime, timezone, timedelta

from app.analysis.trend.htf_anchor import HTFTrendLockEngine
from app.analysis.liquidity.judas_swing_detector import JudasSwingDetector
from app.analysis.orderflow.fvg_engine import FairValueGapEngine
from app.analysis.trade_setups.trade_management import TradeManagementEngine
from app.analysis.risk.news_blackout import NewsBlackoutGuard
from app.analysis.macro.fedwatch_engine import FedWatchEngine
from app.analysis.intermarket.decoupling_matrix import DollarDecouplingMatrix
from app.analysis.performance.trade_journal import TradeJournalEngine


class TestReliabilityAndModernSuite:

    def test_htf_trend_lock_prevents_false_flip(self):
        """Verify that 5M pullbacks during a 1D/4H bull trend are tagged as healthy pullbacks, not bear reversals."""
        result = HTFTrendLockEngine.evaluate_trend_hierarchy(
            daily_trend="BULLISH",
            h4_trend="BULLISH",
            h1_trend="BULLISH",
            m15_trend="NEUTRAL",
            m5_trend="BEARISH",
            technical_score=15.0,
            current_price=2700.0
        )
        assert result["htf_bias"] == "BULLISH"
        assert result["is_counter_trend"] is True
        assert "HEALTHY_BULLISH_PULLBACK" in result["clarity_label"]
        assert result["sync_score_pct"] >= 70.0

    def test_htf_trend_lock_bearish_anchor(self):
        """Verify that 5M bounces during a 1D/4H bear trend are tagged as counter-trend relief rallies (sell-the-rip)."""
        result = HTFTrendLockEngine.evaluate_trend_hierarchy(
            daily_trend="BEARISH",
            h4_trend="BEARISH",
            h1_trend="BEARISH",
            m15_trend="BULLISH",
            m5_trend="BULLISH",
            technical_score=-20.0,
            current_price=2650.0
        )
        assert result["htf_bias"] == "BEARISH"
        assert result["is_counter_trend"] is True
        assert "COUNTER_TREND_RELIEF_RALLY" in result["clarity_label"]

    def test_ambiguity_crusher_in_tight_chop(self):
        """Verify that narrow ranging neutral action is explicitly labeled as CHOP_ZONE."""
        result = HTFTrendLockEngine.evaluate_trend_hierarchy(
            daily_trend="NEUTRAL",
            h4_trend="NEUTRAL",
            h1_trend="NEUTRAL",
            m15_trend="NEUTRAL",
            m5_trend="NEUTRAL",
            technical_score=0.5,
            current_price=2700.0
        )
        assert result["ambiguity_status"] == "CHOP_ZONE_DETECTED"
        assert "MARKET IN BALANCE" in result["actionable_directive"]

    def test_judas_swing_detector(self):
        """Verify London open sweep of Asian High triggers a Bearish Judas Swing."""
        m5_candles = [
            {"high": 2710.0, "low": 2702.0, "close": 2708.0},
            {"high": 2716.5, "low": 2706.0, "close": 2712.0},  # Swept Asian High 2714
            {"high": 2713.0, "low": 2704.0, "close": 2705.0}   # Rejected back inside
        ]
        result = JudasSwingDetector.detect_judas_swing(
            current_price=2705.0,
            asian_high=2714.0,
            asian_low=2695.0,
            active_killzone="LONDON_OPEN",
            m5_candles=m5_candles,
            cvd_delta=-450.0
        )
        assert result["detected"] is True
        assert result["pattern"] == "BEARISH_JUDAS_SWING"
        assert result["swept_price"] == 2714.0
        assert result["action"] == "SELL_LIQUIDITY_PURGE"

    def test_fvg_engine_detection(self):
        """Verify unmitigated 3-candle Fair Value Gap detection."""
        candles = [
            {"open": 2700.0, "high": 2702.0, "low": 2698.0, "close": 2701.0},
            {"open": 2701.0, "high": 2712.0, "low": 2701.0, "close": 2711.0},  # Aggressive impulse
            {"open": 2711.0, "high": 2716.0, "low": 2706.0, "close": 2715.0},  # C3 Low 2706 > C1 High 2702 -> Bullish FVG
            {"open": 2715.0, "high": 2718.0, "low": 2713.0, "close": 2717.0}
        ]
        result = FairValueGapEngine.detect_fvg_and_orderblocks(candles=candles, current_price=2717.0, timeframe="5M")
        assert len(result["active_fvgs"]) > 0
        bull_fvg = [f for f in result["active_fvgs"] if f["type"] == "BULLISH_FVG"][0]
        assert bull_fvg["gap_low"] == 2702.0
        assert bull_fvg["gap_high"] == 2706.0

    def test_trade_management_roadmap(self):
        """Verify 4-step scale-out execution roadmap calculations."""
        roadmap = TradeManagementEngine.generate_trade_roadmap(
            direction="LONG",
            entry_price=2700.0,
            invalidation_sl=2692.0,
            target_tp1=2712.0,
            target_tp2=2724.0
        )
        assert roadmap["risk_pts"] == 8.0
        assert roadmap["tp1_gain_pts"] == 12.0
        assert roadmap["tp2_gain_pts"] == 24.0
        assert len(roadmap["execution_steps"]) == 4
        assert "50% Profit at TP1" in roadmap["execution_steps"][1]["action"]

    def test_news_blackout_guard(self):
        """Verify defensive blackout triggers 10 mins before high-impact CPI release."""
        now = datetime.now(timezone.utc)
        cpi_time = now + timedelta(minutes=10)
        events = [
            {"event_name": "US Core CPI MoM", "importance": "CRITICAL", "scheduled_time": cpi_time.isoformat()}
        ]
        result = NewsBlackoutGuard.evaluate_news_lockout(calendar_events=events, current_time_utc=now)
        assert result["is_locked_out"] is True
        assert result["status"] == "DEFENSIVE_LOCKOUT"
        assert "CPI" in result["lockout_reason"]

    def test_fedwatch_engine(self):
        """Verify CME FedWatch rate probabilities calculation."""
        result = FedWatchEngine.calculate_rate_probabilities(us2y_yield=4.05, fed_funds_rate=4.88)
        assert result["total_cut_probability_pct"] >= 70.0
        assert "BULLISH" in result["gold_macro_impact"]

    def test_dollar_decoupling_matrix(self):
        """Verify positive decoupling detection when Gold and Dollar rally together."""
        result = DollarDecouplingMatrix.calculate_decoupling(
            gold_price=2710.0,
            gold_change_pct=0.85,
            dxy_price=104.50,
            dxy_change_pct=0.45
        )
        assert result["is_sovereign_decoupled"] is True
        assert result["correlation_regime"] == "SOVEREIGN_FLIGHT_TO_SAFETY_DECOUPLING"

    def test_trade_journal_engine(self):
        """Verify win rate and expectancy calculations in trade journal."""
        result = TradeJournalEngine.get_journal_metrics()
        assert result["total_logged_setups"] >= 5
        assert result["win_rate_pct"] > 60.0
        assert result["expectancy_per_trade_r"] > 0.0
