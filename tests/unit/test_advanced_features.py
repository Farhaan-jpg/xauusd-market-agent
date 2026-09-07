"""Unit tests for advanced scalping, ICT Killzones, sweeps, divergence, and Telegram commands."""
import pytest
from datetime import datetime, timezone, timedelta
from app.analysis.liquidity.session_calculator import SessionCalculator
from app.analysis.liquidity.liquidity_engine import LiquidityEngine
from app.analysis.macro.macro_engine import MacroEngine
from app.telegram.bot import TelegramBot
from app.alerts.templates import AlertTemplates

def test_ict_killzone_status():
    """Verify ICT Killzone status identification."""
    status = SessionCalculator.get_ict_killzone_status()
    assert "active_killzone" in status
    assert "is_active" in status
    assert "next_killzone" in status
    assert "starts_in_minutes" in status

def test_liquidity_sweep_detection():
    """Verify BSL and SSL sweeps detection."""
    engine = LiquidityEngine()
    
    # Test Bullish Sweep of Lows (Judas swing down and immediate recovery)
    bullish_candles = [
        {"time": 1000, "open": 2705.0, "high": 2710.0, "low": 2698.0, "close": 2704.0},
        {"time": 1060, "open": 2704.0, "high": 2706.0, "low": 2692.0, "close": 2702.0},  # Swept 2698 low, closed 2702
    ]
    sweeps = engine._detect_liquidity_sweeps(bullish_candles, current_price=2702.0)
    assert len(sweeps) >= 1
    assert sweeps[0]["type"] == "SSL_SWEEP_REVERSAL"
    assert sweeps[0]["bias"] == "BULLISH"

    # Test Bearish Sweep of Highs (Judas swing up and immediate rejection)
    bearish_candles = [
        {"time": 1000, "open": 2700.0, "high": 2710.0, "low": 2698.0, "close": 2704.0},
        {"time": 1060, "open": 2704.0, "high": 2718.0, "low": 2702.0, "close": 2705.0},  # Swept 2710 high, closed 2705
    ]
    sweeps_bear = engine._detect_liquidity_sweeps(bearish_candles, current_price=2705.0)
    assert len(sweeps_bear) >= 1
    assert sweeps_bear[0]["type"] == "BSL_SWEEP_REVERSAL"
    assert sweeps_bear[0]["bias"] == "BEARISH"

def test_dxy_gold_divergence_engine():
    """Verify Intermarket Divergence analysis."""
    engine = MacroEngine()
    
    # Bullish Divergence: DXY surging (+0.8%) but Gold also rising (+0.5%) -> Strong underlying gold demand
    div_bull = engine.dxy_gold_divergence(dxy_change_pct=0.8, gold_change_pct=0.5, yield_change_pct=0.2)
    assert div_bull["status"] == "BULLISH_DIVERGENCE"
    assert div_bull["gold_bias"] == "BULLISH"
    assert div_bull["divergence_score"] > 0

    # Bearish Divergence: DXY falling (-0.8%) but Gold also falling (-0.5%) -> Unusual gold weakness
    div_bear = engine.dxy_gold_divergence(dxy_change_pct=-0.8, gold_change_pct=-0.5, yield_change_pct=-0.2)
    assert div_bear["status"] == "BEARISH_DIVERGENCE"
    assert div_bear["gold_bias"] == "BEARISH"
    assert div_bear["divergence_score"] < 0

    # Normal Inverse: DXY up, Gold down
    div_norm = engine.dxy_gold_divergence(dxy_change_pct=0.5, gold_change_pct=-0.6, yield_change_pct=0.3)
    assert div_norm["status"] == "NORMAL_INVERSE"

def test_pre_news_lockout():
    """Verify pre-news volatility lockout detection."""
    engine = MacroEngine()
    now = datetime.now(timezone.utc)
    
    # High impact event in 10 minutes -> Should trigger lockout
    upcoming = [{
        "event_name": "US Non-Farm Payrolls (NFP)",
        "importance": "HIGH",
        "scheduled_time": (now + timedelta(minutes=10)).isoformat()
    }]
    
    lockout_info = engine.is_news_lockout(upcoming, window_minutes=30)
    assert lockout_info["is_lockout"] is True
    assert "Non-Farm Payrolls" in lockout_info["event_name"]
    assert lockout_info["minutes_to_event"] <= 15

    # Event in 2 hours -> Should NOT trigger lockout
    future_events = [{
        "event_name": "US PPI",
        "importance": "HIGH",
        "scheduled_time": (now + timedelta(hours=2)).isoformat()
    }]
    lockout_future = engine.is_news_lockout(future_events, window_minutes=30)
    assert lockout_future["is_lockout"] is False

@pytest.mark.asyncio
async def test_telegram_interactive_commands():
    """Verify TelegramBot commands response formatting."""
    bot = TelegramBot()
    
    # Test /help
    help_resp = await bot.handle_command("/help")
    assert "/scalp" in help_resp
    assert "/levels" in help_resp
    assert "/killzone" in help_resp
    assert "/dxy" in help_resp

    # Test /killzone
    kz_resp = await bot.handle_command("/killzone")
    assert "ICT SESSION & KILLZONE TELEMETRY" in kz_resp
    assert "Asian Range" in kz_resp

    # Test /scalp
    scalp_resp = await bot.handle_command("/scalp")
    assert "REAL-TIME XAUUSD SCALP RADAR" in scalp_resp
    assert "VWAP" in scalp_resp

    # Test /dxy
    dxy_resp = await bot.handle_command("/dxy")
    assert "INTERMARKET DIVERGENCE" in dxy_resp

    # Test /levels
    levels_resp = await bot.handle_command("/levels")
    assert "KEY LIQUIDITY & ORDERFLOW LEVELS" in levels_resp

def test_alert_templates_formatting():
    """Verify all new template methods execute and produce valid strings."""
    t_scalp = AlertTemplates.scalp_command_response(
        price=2710.50,
        scalp_bias="STRONG_BULLISH_MOMENTUM",
        day_trade_bias="BULLISH_CONTINUATION",
        overall_trend="BULLISH_TREND",
        market_structure="BULLISH_ORDERFLOW",
        vwap=2708.20,
        tech_score=45.0,
        rsi_15m=58.5,
        supertrend="BULLISH",
        killzone="NY_AM_OPEN",
        sweep_warning="SSL Purged at $2698.00"
    )
    assert "STRONG_BULLISH_MOMENTUM" in t_scalp
    assert "$2708.20" in t_scalp

    t_webhook = AlertTemplates.tradingview_webhook_alert(
        ticker="XAUUSD",
        action="BUY",
        price=2712.00,
        timeframe="5m",
        strategy_name="EMA Cross Scalper",
        message="5m EMA 9 crossed above EMA 21"
    )
    assert "TRADINGVIEW WEBHOOK" in t_webhook
    assert "$2712.00" in t_webhook
