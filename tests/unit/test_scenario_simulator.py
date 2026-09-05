"""Unit tests for Macro 'What-If' Scenario Simulator Engine."""
import pytest
from app.analysis.macro.scenario_simulator import MacroScenarioSimulator

def test_scenario_simulator_baseline_neutral():
    simulator = MacroScenarioSimulator()
    res = simulator.simulate(
        current_price=2900.0,
        us10y_bps_shift=0.0,
        dxy_pct_shift=0.0,
        cpi_surprise_pct=0.0,
        geopolitical_shock="NONE"
    )
    assert res["projected_price"] == 2900.0
    assert res["net_delta_usd"] == 0.0
    assert res["net_delta_pct"] == 0.0
    assert res["projected_verdict"] == "NEUTRAL"

def test_scenario_simulator_hawkish_shock():
    simulator = MacroScenarioSimulator()
    res = simulator.simulate(
        current_price=2900.0,
        us10y_bps_shift=30.0,    # +30 bps yields -> bearish gold
        dxy_pct_shift=2.0,       # +2% USD -> bearish gold
        cpi_surprise_pct=-0.4,   # cooling CPI -> lower inflation hedge
        geopolitical_shock="DE_ESCALATION"
    )
    assert res["projected_price"] < 2900.0
    assert res["net_delta_usd"] < 0.0
    assert "BEARISH" in res["projected_verdict"]
    assert res["net_delta_pct"] < -1.0

def test_scenario_simulator_geopolitical_shock():
    simulator = MacroScenarioSimulator()
    res = simulator.simulate(
        current_price=2900.0,
        us10y_bps_shift=-15.0,   # falling yields -> bullish gold
        dxy_pct_shift=-1.5,      # weakening USD -> bullish gold
        cpi_surprise_pct=0.3,    # hot CPI -> bullish hedge
        geopolitical_shock="SEVERE" # surge safe-haven
    )
    assert res["projected_price"] > 2900.0
    assert res["net_delta_usd"] > 0.0
    assert "BULLISH" in res["projected_verdict"]
    assert res["net_delta_pct"] > 1.5
