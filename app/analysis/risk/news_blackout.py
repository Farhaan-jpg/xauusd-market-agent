"""
Economic News Blackout & Spread Expansion Safeguard for XAUUSD.
Protects scalpers by enforcing defensive lockouts 15 minutes before and after Tier-1 economic releases.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone


class NewsBlackoutGuard:
    """
    Checks upcoming and recent high-impact events (CPI, NFP, FOMC, PPI, PCE).
    """

    TIER_1_KEYWORDS = [
        "CPI", "NON-FARM", "NFP", "FOMC", "RATE DECISION",
        "FEDERAL FUNDS", "PCE", "POWELL", "INFLATION", "EMPLOYMENT"
    ]

    @staticmethod
    def evaluate_news_lockout(
        calendar_events: List[Dict[str, Any]],
        current_time_utc: datetime = None,
        blackout_window_mins: int = 15
    ) -> Dict[str, Any]:
        """
        Determines if trading is restricted due to proximity to high-impact catalysts.
        """
        if current_time_utc is None:
            current_time_utc = datetime.now(timezone.utc)

        is_locked_out = False
        lockout_reason = "CLEAR_TRADING_CONDITIONS"
        minutes_to_next = 999
        next_event_name = "None"

        for event in calendar_events:
            title = (event.get("event_name") or event.get("title") or "").upper()
            importance = (event.get("importance") or event.get("impact") or "MEDIUM").upper()

            is_tier_1 = importance in ["CRITICAL", "HIGH"] or any(k in title for k in NewsBlackoutGuard.TIER_1_KEYWORDS)
            if not is_tier_1:
                continue

            scheduled = event.get("scheduled_time") or event.get("time")
            if not scheduled:
                continue

            try:
                if isinstance(scheduled, str):
                    ev_time = datetime.fromisoformat(scheduled.replace("Z", "+00:00"))
                else:
                    ev_time = scheduled
                
                diff_secs = (ev_time - current_time_utc).total_seconds()
                diff_mins = int(diff_secs / 60)

                # Active blackout if within -15 mins to +15 mins of event
                if -blackout_window_mins <= diff_mins <= blackout_window_mins:
                    is_locked_out = True
                    lockout_reason = f"TIER-1 CATALYST LOCKOUT: {title} ({'IN ' + str(diff_mins) + 'm' if diff_mins >= 0 else str(abs(diff_mins)) + 'm AGO'}). SPREAD RISK HIGH."
                    minutes_to_next = diff_mins
                    next_event_name = title
                    break
                elif diff_mins > 0 and diff_mins < minutes_to_next:
                    minutes_to_next = diff_mins
                    next_event_name = title
            except Exception:
                continue

        return {
            "is_locked_out": is_locked_out,
            "status": "DEFENSIVE_LOCKOUT" if is_locked_out else "OPTIMAL_LIQUIDITY",
            "lockout_reason": lockout_reason,
            "minutes_to_next_catalyst": minutes_to_next if minutes_to_next != 999 else None,
            "next_catalyst_title": next_event_name,
            "action_directive": "HALT SCALPING: Wide spreads & slippage expected. Await post-event dust settle." if is_locked_out else "CLEAR TO TRADE: Normal execution spreads."
        }
