"""
Dynamic Trade Management & Scale-Out Roadmap Engine for XAUUSD.
Builds systematic 4-step execution roadmaps (Entry, Partial Scale at TP1, Breakeven SL, Runner Trail).
"""

from typing import Dict, Any, List


class TradeManagementEngine:
    """
    Generates unambiguous step-by-step trade execution rules for any trade setup.
    """

    @staticmethod
    def generate_trade_roadmap(
        direction: str,
        entry_price: float,
        invalidation_sl: float,
        target_tp1: float,
        target_tp2: float,
        spread_buffer: float = 0.5
    ) -> Dict[str, Any]:
        """
        Creates a clear 4-step execution roadmap.
        """
        is_long = direction.upper() == "LONG"
        risk_pts = abs(entry_price - invalidation_sl)
        tp1_pts = abs(target_tp1 - entry_price)
        tp2_pts = abs(target_tp2 - entry_price)

        be_price = round(entry_price + (spread_buffer if is_long else -spread_buffer), 2)

        steps = [
            {
                "step_num": 1,
                "stage": "EXECUTION_ENTRY",
                "action": f"Enter {direction} position at ${entry_price:.2f}",
                "rule": f"Place initial Stop Loss at ${invalidation_sl:.2f} ({risk_pts:.1f} pts risk, 1.0R). Max account risk: 1-2%."
            },
            {
                "step_num": 2,
                "stage": "PARTIAL_PROFIT_SCALE",
                "action": f"Take 50% Profit at TP1 (${target_tp1:.2f})",
                "rule": f"Secures +{tp1_pts:.1f} pts profit (+1.5R). Bank partial profit immediately upon tag."
            },
            {
                "step_num": 3,
                "stage": "RISK_ELIMINATION",
                "action": f"Move Stop Loss to Breakeven (${be_price:.2f})",
                "rule": "Locks in zero-risk trade. Remaining position cannot result in a loss."
            },
            {
                "step_num": 4,
                "stage": "RUNNER_TRAIL",
                "action": f"Trail remaining 50% runner to TP2 (${target_tp2:.2f})",
                "rule": f"Trail stop behind 5M swing pivots targeting +{tp2_pts:.1f} pts (+3.0R+ expansion)."
            }
        ]

        return {
            "direction": direction,
            "entry_price": entry_price,
            "invalidation_sl": invalidation_sl,
            "target_tp1": target_tp1,
            "target_tp2": target_tp2,
            "breakeven_trigger_price": target_tp1,
            "breakeven_sl_price": be_price,
            "risk_pts": round(risk_pts, 2),
            "tp1_gain_pts": round(tp1_pts, 2),
            "tp2_gain_pts": round(tp2_pts, 2),
            "execution_steps": steps,
            "summary": f"4-Step Rule: Enter ${entry_price:.2f} -> Take 50% at ${target_tp1:.2f} -> Move SL to BE (${be_price:.2f}) -> Trail to ${target_tp2:.2f}."
        }
