"""Session Calculator determining active forex/gold market sessions, ICT Killzones, and session boundaries."""
from datetime import datetime, time as dt_time, timezone
from typing import Any, Dict, List, Optional
import pandas as pd

class SessionCalculator:
    """Calculates Asian, London, and New York session highs, lows, ICT Killzones, and status."""

    # ICT Killzone UTC boundaries
    # Asian Range: 00:00 - 06:00 UTC (Liquidity Accumulation)
    # London Open Killzone: 07:00 - 10:00 UTC (Judas Swing / London Expansion)
    # NY AM Killzone: 12:00 - 15:00 UTC (Key US Equities & Data Releases Scalp Window)
    # London Close Killzone: 15:00 - 17:00 UTC (Reversals & Profit Taking)

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
    def get_ict_killzone_status(utc_dt: Optional[datetime] = None) -> Dict[str, Any]:
        """Evaluates active ICT Killzone, phase description, and time to next high-probability scalp window."""
        if utc_dt is None:
            utc_dt = datetime.now(timezone.utc)
        elif utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)

        t = utc_dt.time()
        
        active_kz = "OFF_KILLZONE"
        kz_name = "Off-Hours / Range Intermission"
        kz_phase = "Consolidation / Range Preparation"
        is_active = False

        if dt_time(0, 0) <= t < dt_time(6, 0):
            active_kz = "ASIAN_RANGE"
            kz_name = "Asian Range"
            kz_phase = "Initial Liquidity Pool Formation (Establish Asian High & Low)"
            is_active = True
        elif dt_time(7, 0) <= t < dt_time(10, 0):
            active_kz = "LONDON_OPEN_KILLZONE"
            kz_name = "London Open Killzone (07:00 - 10:00 UTC)"
            kz_phase = "Judas Swing / Session High-Low Expansion"
            is_active = True
        elif dt_time(12, 0) <= t < dt_time(15, 0):
            active_kz = "NY_AM_KILLZONE"
            kz_name = "New York AM Killzone (12:00 - 15:00 UTC)"
            kz_phase = "Prime Volatility Scalp Window (US Open & Economic Catalysts)"
            is_active = True
        elif dt_time(15, 0) <= t < dt_time(17, 0):
            active_kz = "LONDON_CLOSE_KILLZONE"
            kz_name = "London Close Killzone (15:00 - 17:00 UTC)"
            kz_phase = "Daily Trend Continuation or Profit-Taking Reversal"
            is_active = True

        # Calculate next killzone & countdown
        current_minutes = t.hour * 60 + t.minute
        kz_starts = [
            ("Asian Range", 0),
            ("London Open Killzone", 7 * 60),
            ("New York AM Killzone", 12 * 60),
            ("London Close Killzone", 15 * 60),
            ("Asian Range (Tomorrow)", 24 * 60)
        ]
        
        next_kz = "Asian Range"
        starts_in = 60
        for name, start_m in kz_starts:
            if start_m > current_minutes:
                next_kz = name
                starts_in = start_m - current_minutes
                break

        return {
            "active_killzone": active_kz,
            "killzone": active_kz,
            "killzone_name": kz_name,
            "name": kz_name,
            "phase": kz_phase,
            "is_active": is_active,
            "is_active_killzone": is_active,
            "next_killzone": next_kz,
            "starts_in_minutes": starts_in,
            "utc_time": utc_dt.strftime("%H:%M UTC")
        }


    @staticmethod
    def extract_session_ranges(df_15m_or_1h: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Extracts recent high, low, and range for each major market session and Asian Range baseline."""
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
            df = df_15m_or_1h.copy()
            if not isinstance(df.index, pd.DatetimeIndex):
                return sessions_data

            if df.index.tz is None:
                df.index = df.index.tz_localize(timezone.utc)
            else:
                df.index = df.index.tz_convert(timezone.utc)

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

