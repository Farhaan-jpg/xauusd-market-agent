"""Actionable Trade Setup Generator producing risk-defined scalp and day-trade execution cards."""
from typing import Any, Dict, List, Optional

class TradeSetupGenerator:
    """
    Generates actionable institutional scalp & day-trade setup cards with:
    - Setup Type (Judas Sweep Reversal, VWAP Pullback, Breakout Continuation)
    - Entry Zone (Price Range)
    - Invalidation / Stop Loss
    - Take Profit 1 (1:1.5 Risk-to-Reward)
    - Take Profit 2 (1:3+ Risk-to-Reward)
    - Risk/Reward Ratio & Confluence Grade
    """

    @staticmethod
    def generate_setups(
        current_price: float,
        direction: str,
        confluence_data: Dict[str, Any],
        liquidity_data: Dict[str, Any],
        market_analysis: Dict[str, Any],
        atr: float = 8.5
    ) -> List[Dict[str, Any]]:
        """Generates actionable structured trade cards."""
        if current_price <= 0:
            return []

        setups = []
        grade = confluence_data.get("setup_grade", "B")
        bias = confluence_data.get("confluence_bias", direction)
        vwap = market_analysis.get("vwap_5m", current_price)
        sweeps = liquidity_data.get("active_sweeps", [])
        
        atr = max(3.0, atr)
        sl_buffer = round(atr * 0.45, 2)  # Tight institutional scalp stop buffer
        
        # 1. Bullish Setup Generation
        if "BULLISH" in bias.upper() and grade in ["A+", "A", "B"]:
            # Nearest resistance targets
            liq_above = liquidity_data.get("liquidity_above", [])
            tp1_price = liq_above[0]["price"] if liq_above else round(current_price + (sl_buffer * 1.5), 2)
            tp2_price = liq_above[1]["price"] if len(liq_above) > 1 else round(current_price + (sl_buffer * 3.0), 2)
            
            entry_low = round(min(current_price, vwap) - 0.5, 2)
            entry_high = round(current_price + 0.8, 2)
            stop_loss = round(entry_low - sl_buffer, 2)

            risk = max(0.5, current_price - stop_loss)
            reward_tp1 = max(0.5, tp1_price - current_price)
            rr_ratio = round(reward_tp1 / risk, 2)

            setup_name = "Bullish Judas Sweep Reversal" if sweeps and sweeps[0].get("bias") == "BULLISH" else \
                         "Bullish VWAP Pullback Long" if current_price >= vwap else "Bullish Momentum Continuation"

            setups.append({
                "setup_id": "XAU-LONG-01",
                "setup_name": setup_name,
                "action": "BUY_LONG",
                "grade": grade,
                "confluence_score": confluence_data.get("confluence_score", 75),
                "entry_zone": f"${entry_low:.2f} - ${entry_high:.2f}",
                "entry_mid": round((entry_low + entry_high) / 2.0, 2),
                "invalidation_sl": stop_loss,
                "sl_pips": round(risk * 10, 1),
                "take_profit_1": tp1_price,
                "tp1_pips": round(reward_tp1 * 10, 1),
                "take_profit_2": tp2_price,
                "risk_reward_ratio": f"1:{rr_ratio:.1f}",
                "status": "ACTIVE_TRIGGER",
                "catalyst": confluence_data.get("aligned_factors", ["Multi-timeframe structure confluence"])[0]
            })

        # 2. Bearish Setup Generation
        elif "BEARISH" in bias.upper() and grade in ["A+", "A", "B"]:
            liq_below = liquidity_data.get("liquidity_below", [])
            tp1_price = liq_below[0]["price"] if liq_below else round(current_price - (sl_buffer * 1.5), 2)
            tp2_price = liq_below[1]["price"] if len(liq_below) > 1 else round(current_price - (sl_buffer * 3.0), 2)
            
            entry_high = round(max(current_price, vwap) + 0.5, 2)
            entry_low = round(current_price - 0.8, 2)
            stop_loss = round(entry_high + sl_buffer, 2)

            risk = max(0.5, stop_loss - current_price)
            reward_tp1 = max(0.5, current_price - tp1_price)
            rr_ratio = round(reward_tp1 / risk, 2)

            setup_name = "Bearish Judas Sweep Reversal" if sweeps and sweeps[0].get("bias") == "BEARISH" else \
                         "Bearish VWAP Rejection Short" if current_price <= vwap else "Bearish Breakdown Continuation"

            setups.append({
                "setup_id": "XAU-SHORT-01",
                "setup_name": setup_name,
                "action": "SELL_SHORT",
                "grade": grade,
                "confluence_score": confluence_data.get("confluence_score", 75),
                "entry_zone": f"${entry_low:.2f} - ${entry_high:.2f}",
                "entry_mid": round((entry_low + entry_high) / 2.0, 2),
                "invalidation_sl": stop_loss,
                "sl_pips": round(risk * 10, 1),
                "take_profit_1": tp1_price,
                "tp1_pips": round(reward_tp1 * 10, 1),
                "take_profit_2": tp2_price,
                "risk_reward_ratio": f"1:{rr_ratio:.1f}",
                "status": "ACTIVE_TRIGGER",
                "catalyst": confluence_data.get("aligned_factors", ["Multi-timeframe structure confluence"])[0]
            })

        return setups
