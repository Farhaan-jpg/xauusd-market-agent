"""Session Calculator determining active forex/gold market sessions and session boundaries."""
from datetime import datetime, time as dt_time, timezone
from typing import Any, Dict, List, Optional
import pandas as pd

class SessionCalculator:
    """Calculates Asian, London, and New York session highs, lows, and status."""

    # Session UTC boundaries
    # Asian: 00:00 - 08:00 UTC
    # London: 07:00 - 15:30 UTC
    # New York: 12:00 - 20:00 UTC
    # London / NY Overlap: 12:00 - 15:30 UTC

    @staticmethod
    def get_active_sessions(utc_dt: datetime) -> List[str]:
        current_time = utc_dt.time()
        active = []

        if dt_time(0, 0) <= current_time < dt_time(8, 0):
            active.append("ASIAN")
        if dt_time(7, 0) <= current_time < dt_time(15, 30):
            active.append("LONDON")
        if dt_time(12, 0) <= current_time < dt_time(20, 0):
            active.append("NEW_YORK")
        if dt_time(12, 0) <= current_time < dt_time(15, 30):
            active.append("LONDON_NY_OVERLAP")

        if not active:
            active.append("OFF_HOURS")
        return active

    @staticmethod
    def extract_session_ranges(df_15m_or_1h: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Extracts recent high, low, and range for each major market session."""
        if df_15m_or_1h.empty:
            return {}

        sessions_data = {
            "ASIAN": {"high": 0.0, "low": 0.0, "range": 0.0, "active": False},
            "LONDON": {"high": 0.0, "low": 0.0, "range": 0.0, "active": False},
            "NEW_YORK": {"high": 0.0, "low": 0.0, "range": 0.0, "active": False}
        }

        now_utc = datetime.now(timezone.utc)
        active_list = SessionCalculator.get_active_sessions(now_utc)
        for s in ["ASIAN", "LONDON", "NEW_YORK"]:
            if s in active_list:
                sessions_data[s]["active"] = True

        try:
            # Group bars by session
            df = df_15m_or_1h.copy()
            if not isinstance(df.index, pd.DatetimeIndex):
                return sessions_data

            # Make index UTC aware
            if df.index.tz is None:
                df.index = df.index.tz_localize(timezone.utc)
            else:
                df.index = df.index.tz_convert(timezone.utc)

            # Filter for the last 24-48 hours
            recent_df = df[df.index >= (now_utc - pd.Timedelta(days=2))]

            for session_name, (start_h, end_h) in [
                ("ASIAN", (0, 8)),
                ("LONDON", (7, 16)),
                ("NEW_YORK", (12, 20))
            ]:
                session_bars = recent_df[(recent_df.index.hour >= start_h) & (recent_df.index.hour < end_h)]
                if not session_bars.empty:
                    s_high = float(session_bars["high"].max())
                    s_low = float(session_bars["low"].min())
                    sessions_data[session_name]["high"] = round(s_high, 2)
                    sessions_data[session_name]["low"] = round(s_low, 2)
                    sessions_data[session_name]["range"] = round(s_high - s_low, 2)
        except Exception:
            pass

        return sessions_data
