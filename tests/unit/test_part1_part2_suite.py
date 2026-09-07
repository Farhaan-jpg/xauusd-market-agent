"""Unit tests for Part 1 (Core Logic Enhancements) and Part 2 (Actionable Scalper Tools)."""
import pytest
import pandas as pd
from app.analysis.regime.regime_classifier import MarketRegimeClassifier
from app.analysis.orderflow.cvd_engine import OrderFlowDeltaEngine
from app.analysis.confluence.confluence_engine import ConfluenceMatrixEngine
from app.analysis.intermarket.metals_matrix import IntermarketMetalsMatrix
from app.analysis.news.nlp_classifier import FinancialNLPClassifier
from app.analysis.trade_setups.setup_generator import TradeSetupGenerator
from app.analysis.risk.risk_guardian import RiskGuardian
from app.tools.pinescript_generator import PineScriptGenerator
from app.telegram.bot import TelegramBot

def test_regime_classifier():
    """Verify market regime classification and dynamic weight adjustment."""
    # News Shock
    reg_news = MarketRegimeClassifier.classify_regime(
        trend="BULLISH", volatility="HIGH_VOLATILITY", market_structure="RANGING",
        killzone="NY_AM", is_news_lockout=True
    )
    assert reg_news["regime"] == "VOLATILITY_NEWS_SHOCK"
    assert reg_news["weights"]["news"] >= 0.35

    # Trending Expansion
    reg_trend = MarketRegimeClassifier.classify_regime(
        trend="BULLISH_TREND", volatility="NORMAL", market_structure="BULLISH_ORDERFLOW",
        killzone="LONDON_OPEN", is_news_lockout=False
    )
    assert reg_trend["regime"] == "TRENDING_EXPANSION"
    assert reg_trend["weights"]["technical"] >= 0.60

def test_orderflow_cvd_engine():
    """Verify Cumulative Volume Delta and absorption detection."""
    # Synthetic candles with falling price but rising close aggressor delta (Bullish Absorption)
    bars = [
        {"open": 2705.0, "high": 2706.0, "low": 2700.0, "close": 2701.0, "volume": 1000.0},
        {"open": 2701.0, "high": 2702.0, "low": 2695.0, "close": 2696.0, "volume": 1000.0},
        {"open": 2696.0, "high": 2698.0, "low": 2690.0, "close": 2697.5, "volume": 2500.0}, # Strong buy absorption
    ]
    df = pd.DataFrame(bars)
    res = OrderFlowDeltaEngine.calculate_cvd(df)
    assert "cvd_bias" in res
    assert "delta_score" in res

def test_confluence_matrix_engine():
    """Verify multi-timeframe confluence scoring."""
    market_analysis = {
        "technical_score": 45.0,
        "scalp_bias": "STRONG_BULLISH_MOMENTUM",
        "day_trade_bias": "BULLISH_CONTINUATION",
        "trend": "BULLISH_TREND",
        "vwap_5m": 2700.0,
        "market_structure": "BULLISH_ORDERFLOW"
    }
    liq_analysis = {
        "active_sweeps": [{"bias": "BULLISH", "level_swept": "Asian Low"}]
    }
    cvd_analysis = {"cvd_bias": "BULLISH", "delta_divergence": "BULLISH_CVD_DIVERGENCE"}
    
    res = ConfluenceMatrixEngine.evaluate_confluence(market_analysis, liq_analysis, cvd_analysis, current_price=2705.0)
    assert res["confluence_bias"] == "BULLISH"
    assert res["setup_grade"] in ["A+", "A"]
    assert res["confluence_score"] >= 70

def test_intermarket_metals_matrix():
    """Verify Gold/Silver ratio and Silver leading signal calculation."""
    res = IntermarketMetalsMatrix.analyze_metals_matrix(
        gold_price=2700.0,
        gold_change_pct=0.2,
        silver_price=32.0,
        silver_change_pct=1.5 # Outperforming Gold by 1.3% -> Leading signal
    )
    assert res["silver_leading_signal"] == "SILVER_BULLISH_LEAD"
    assert res["metals_matrix_score"] > 0
    assert res["gold_silver_ratio"] == 84.38

def test_financial_nlp_classifier():
    """Verify keyword and theme classification for central banks and Fed."""
    news = [
        {"title": "Fed signals rate cuts on the table as inflation cools down rapidly"},
        {"title": "PBOC and Global Central Banks increase physical gold bullion reserves in August"}
    ]
    res = FinancialNLPClassifier.classify_headlines(news)
    assert res["fed_sentiment_score"] > 0
    assert res["central_bank_buying_score"] > 0
    assert res["nlp_composite_gold_impact"] == "BULLISH"

def test_trade_setup_generator():
    """Verify generation of risk-defined trade setups with SL, TP1, TP2, R:R."""
    confluence_data = {"setup_grade": "A+", "confluence_bias": "BULLISH", "confluence_score": 90, "aligned_factors": ["1H BOS + 5M FVG"]}
    liq_data = {
        "liquidity_above": [{"price": 2715.0}],
        "liquidity_below": [{"price": 2690.0}],
        "active_sweeps": [{"bias": "BULLISH"}]
    }
    market_data = {"vwap_5m": 2702.0}
    
    setups = TradeSetupGenerator.generate_setups(
        current_price=2704.0,
        direction="BULLISH",
        confluence_data=confluence_data,
        liquidity_data=liq_data,
        market_analysis=market_data,
        atr=8.0
    )
    assert len(setups) >= 1
    s = setups[0]
    assert s["action"] == "BUY_LONG"
    assert s["invalidation_sl"] < 2704.0
    assert s["take_profit_1"] > 2704.0
    assert "1:" in s["risk_reward_ratio"]

def test_risk_guardian():
    """Verify ADR exhaustion tracking and chop risk evaluation."""
    # Normal Day
    res_normal = RiskGuardian.evaluate_risk(day_high=2710.0, day_low=2695.0, current_price=2705.0, adr=25.0)
    assert res_normal["risk_status"] == "GREEN"

    # ADR Exhausted Day (Range = 35 pts on 25 ADR = 140%)
    res_exhausted = RiskGuardian.evaluate_risk(day_high=2735.0, day_low=2700.0, current_price=2730.0, adr=25.0)
    assert res_exhausted["risk_status"] == "YELLOW"
    assert res_exhausted["status_label"] == "ADR_EXHAUSTED"

def test_pinescript_generator():
    """Verify TradingView Pine Script v5 generation."""
    script = PineScriptGenerator.generate_script(
        current_price=2705.0,
        direction="BULLISH",
        score=45.0,
        liquidity_above=[{"price": 2715.0, "zone_type": "RESISTANCE"}],
        liquidity_below=[{"price": 2695.0, "zone_type": "SUPPORT"}],
        asian_high=2710.0,
        asian_low=2698.0
    )
    assert "//@version=5" in script
    assert "indicator(" in script
    assert "2715.00" in script
    assert "2695.00" in script

@pytest.mark.asyncio
async def test_new_telegram_commands():
    """Verify all new Telegram command handlers produce valid responses."""
    bot = TelegramBot()
    
    # /setups
    setups_resp = await bot.handle_command("/setups")
    assert "TRADE SETUPS" in setups_resp
    
    # /confluence
    conf_resp = await bot.handle_command("/confluence")
    assert "CONFLUENCE MATRIX" in conf_resp

    # /regime
    reg_resp = await bot.handle_command("/regime")
    assert "MARKET REGIME" in reg_resp

    # /pinescript
    pine_resp = await bot.handle_command("/pinescript")
    assert "PINE SCRIPT" in pine_resp
