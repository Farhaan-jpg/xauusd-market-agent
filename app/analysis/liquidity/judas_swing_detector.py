"""
Judas Swing and Session Open Liquidity Sweep Detector for XAUUSD.
Detects false breakout sweeps of Asian High/Low during London or New York Open,
triggering high-probability Liquidity Purge Reversal trade signals.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class JudasSwingDetector:
    """
    Monitors session open liquidity purges (ICT Judas Swing).
    """

    @staticmethod
    def detect_judas_swing(
        current_price: float,
        asian_high: float,
        asian_low: float,
        active_killzone: str = "LONDON_OPEN",
        m5_candles: Optional[List[Dict[str, Any]]] = None,
        cvd_delta: float = 0.0
    ) -> Dict[str, Any]:
        """
        Analyzes whether a session open expansion swept Asian extremes and rejected.
        """
        if asian_high <= 0 or asian_low <= 0 or asian_high <= asian_low:
            return {
                "detected": False,
                "status": "INACTIVE_RANGE",
                "message": "Asian range baseline unavailable."
            }

        is_open_killzone = active_killzone in ["LONDON_OPEN", "NEW_YORK_OPEN", "NY_AM_EXPANSION"]
        
        # Check high sweep (Bearish Judas Swing)
        # Price pushed above Asian High then closed back below it
        swept_high = current_price >= asian_high or (m5_candles and any(c.get("high", 0) > asian_high for c in m5_candles[-3:]))
        swept_low = current_price <= asian_low or (m5_candles and any(c.get("low", 0) < asian_low for c in m5_candles[-3:]))

        if is_open_killzone and swept_high and current_price < asian_high:
            # Rejection confirmed below swept Asian High
            sweep_pts = round(max([c.get("high", asian_high) for c in (m5_candles[-3:] if m5_candles else [])] + [asian_high]) - asian_high, 2)
            return {
                "detected": True,
                "pattern": "BEARISH_JUDAS_SWING",
                "swept_level": "ASIAN_SESSION_HIGH",
                "swept_price": round(asian_high, 2),
                "rejection_price": round(current_price, 2),
                "sweep_magnitude_pts": sweep_pts,
                "conviction": "HIGH" if cvd_delta < 0 else "MODERATE",
                "action": "SELL_LIQUIDITY_PURGE",
                "target": round(asian_low, 2),
                "invalidation_sl": round(asian_high + max(3.5, sweep_pts + 1.5), 2),
                "description": f"London/NY Judas Swing: Price swept Asian High (${asian_high:.2f}) and sharply rejected back inside. Institutional buy stops absorbed."
            }

        if is_open_killzone and swept_low and current_price > asian_low:
            # Rejection confirmed above swept Asian Low
            sweep_pts = round(asian_low - min([c.get("low", asian_low) for c in (m5_candles[-3:] if m5_candles else [])] + [asian_low]), 2)
            return {
                "detected": True,
                "pattern": "BULLISH_JUDAS_SWING",
                "swept_level": "ASIAN_SESSION_LOW",
                "swept_price": round(asian_low, 2),
                "rejection_price": round(current_price, 2),
                "sweep_magnitude_pts": sweep_pts,
                "conviction": "HIGH" if cvd_delta > 0 else "MODERATE",
                "action": "BUY_LIQUIDITY_PURGE",
                "target": round(asian_high, 2),
                "invalidation_sl": round(asian_low - max(3.5, sweep_pts + 1.5), 2),
                "description": f"London/NY Judas Swing: Price swept Asian Low (${asian_low:.2f}) and sharply rejected back inside. Institutional sell stops absorbed."
            }

        return {
            "detected": False,
            "pattern": "NONE",
            "status": "MONITORING_SWEEPS",
            "active_killzone": active_killzone,
            "asian_high": asian_high,
            "asian_low": asian_low,
            "description": "No active session Judas Swing sweep detected."
        }
