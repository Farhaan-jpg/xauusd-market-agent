"""Macro Engine analyzing DXY, Treasury Yields, Real Yield proxy, Intermarket Divergences, and Pre-News Lockouts."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.core.logging import logger

HIGH_IMPACT_LOCKOUT_KEYWORDS = [
    "cpi", "consumer price index", "nfp", "nonfarm payrolls", "fomc", "interest rate decision",
    "fed interest rate", "fed chair powell", "gdp", "core pce", "employment report", "ism manufacturing"
]

class MacroEngine:
    """Evaluates macroeconomic indicators, DXY/Yield relative divergences, and red-folder event lockouts."""

    def analyze(
        self,
        macro_data: Dict[str, Any],
        gold_change_pct: float = 0.0,
        upcoming_events: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        dxy = macro_data.get("dxy", {})
        us10y = macro_data.get("us10y", {})
        us2y = macro_data.get("us2y", {})
        tip = macro_data.get("tip", {})
        vix = macro_data.get("vix", {})

        dxy_chg = dxy.get("change_pct", 0.0)
        us10y_chg = us10y.get("change_pct", 0.0)
        us2y_chg = us2y.get("change_pct", 0.0)
        tip_chg = tip.get("change_pct", 0.0)
        vix_price = vix.get("price", 15.0)

        # 1. USD Score (Impact on Gold: Falling USD = Bullish for Gold)
        usd_score = max(-100.0, min(100.0, -dxy_chg * 100.0))

        # 2. Yield Score (Impact on Gold: Falling yields = Bullish for Gold)
        avg_yield_chg = (us10y_chg + us2y_chg) / 2.0
        yield_score = max(-100.0, min(100.0, -avg_yield_chg * 50.0))

        # 3. Real Yield / TIPS Score
        real_yield_score = max(-100.0, min(100.0, tip_chg * 100.0))

        # 4. Risk / Geopolitical Score
        risk_score = 0.0
        if vix_price > 25.0:
            risk_score = 60.0
        elif vix_price > 20.0:
            risk_score = 30.0
        elif vix_price < 13.0:
            risk_score = -20.0

        # Aggregate Macro Score (-100 to +100)
        macro_score = (0.35 * usd_score) + (0.35 * yield_score) + (0.20 * real_yield_score) + (0.10 * risk_score)
        macro_score = max(-100.0, min(100.0, round(macro_score, 1)))

        # 5. DXY & Gold Intermarket Relative Divergence
        div_info = self.dxy_gold_divergence(
            dxy_change_pct=dxy_chg,
            gold_change_pct=gold_change_pct,
            yield_change_pct=us10y_chg
        )
        divergence_type = div_info["status"]
        divergence_desc = div_info["description"]
        macro_score = max(-100.0, min(100.0, macro_score + div_info["divergence_score"]))

        # 6. Pre-News Lockout & Red-Folder Volatility Window Check (within 15 mins before or 10 mins after)
        lockout_info = self.is_news_lockout(upcoming_events or [], window_minutes=15)
        is_news_lockout = lockout_info["is_lockout"]
        lockout_event_name = lockout_info["event_name"]
        lockout_time_delta_mins = lockout_info["minutes_to_event"]

        macro_condition = "STRONGLY_SUPPORTIVE" if macro_score >= 50.0 else \
                          "SUPPORTIVE" if macro_score >= 15.0 else \
                          "STRONGLY_HEADWIND" if macro_score <= -50.0 else \
                          "HEADWIND" if macro_score <= -15.0 else "NEUTRAL"

        return {
            "macro_score": macro_score,
            "usd_score": round(usd_score, 1),
            "yield_score": round(yield_score, 1),
            "real_yield_score": round(real_yield_score, 1),
            "risk_score": round(risk_score, 1),
            "macro_condition": macro_condition,
            "dxy_change_pct": dxy_chg,
            "us10y_yield": us10y.get("yield_pct", 0.0),
            "us2y_yield": us2y.get("yield_pct", 0.0),
            "yield_spread_10y_2y": macro_data.get("yield_spread_10y_2y", 0.0),
            "vix": vix_price,
            "divergence_type": divergence_type,
            "divergence_description": divergence_desc,
            "is_news_lockout": is_news_lockout,
            "lockout_event_name": lockout_event_name,
            "lockout_time_delta_mins": lockout_time_delta_mins
        }

    def dxy_gold_divergence(
        self,
        dxy_change_pct: float,
        gold_change_pct: float,
        yield_change_pct: float = 0.0
    ) -> Dict[str, Any]:
        """Analyzes intermarket divergence between DXY, Treasury yields, and Gold."""
        # Bullish Divergence: DXY up (or flat) while Gold is surging up
        if dxy_change_pct >= 0.15 and gold_change_pct >= 0.15:
            return {
                "status": "BULLISH_DIVERGENCE",
                "gold_bias": "BULLISH",
                "divergence_score": 25.0,
                "dxy_score": -dxy_change_pct * 100.0,
                "description": "Gold rallying despite strengthening US Dollar (Strong Institutional Safe-Haven Accumulation)"
            }
        # Bearish Divergence: DXY falling while Gold is also dropping
        elif dxy_change_pct <= -0.15 and gold_change_pct <= -0.15:
            return {
                "status": "BEARISH_DIVERGENCE",
                "gold_bias": "BEARISH",
                "divergence_score": -25.0,
                "dxy_score": -dxy_change_pct * 100.0,
                "description": "Gold selling off despite weakening US Dollar (Aggressive Institutional Distribution / Yield Headwind)"
            }
        else:
            return {
                "status": "NORMAL_INVERSE",
                "gold_bias": "NEUTRAL",
                "divergence_score": 0.0,
                "dxy_score": -dxy_change_pct * 100.0,
                "description": "Standard inverse correlation between USD and Gold spot auction"
            }

    def is_news_lockout(
        self,
        upcoming_events: List[Dict[str, Any]],
        window_minutes: int = 30
    ) -> Dict[str, Any]:
        """Determines whether high-impact tier-1 red-folder events are within the risk lockout window."""
        now_utc = datetime.now(timezone.utc)
        for ev in upcoming_events:
            ev_name = ev.get("event_name", "").lower()
            is_tier1 = any(kw in ev_name for kw in HIGH_IMPACT_LOCKOUT_KEYWORDS) or ev.get("importance") == "HIGH"
            if not is_tier1:
                continue

            sched_time = ev.get("scheduled_time")
            if sched_time:
                if isinstance(sched_time, str):
                    try:
                        sched_time = datetime.fromisoformat(sched_time.replace("Z", "+00:00"))
                    except Exception:
                        continue
                if sched_time.tzinfo is None:
                    sched_time = sched_time.replace(tzinfo=timezone.utc)

                delta_mins = (sched_time - now_utc).total_seconds() / 60.0
                # Within window_minutes before event or up to 10 minutes after release
                if -10.0 <= delta_mins <= float(window_minutes):
                    return {
                        "is_lockout": True,
                        "event_name": ev.get("event_name", "High Impact Release"),
                        "minutes_to_event": round(delta_mins, 1),
                        "importance": ev.get("importance", "HIGH")
                    }

        return {
            "is_lockout": False,
            "event_name": "",
            "minutes_to_event": 999,
            "importance": "LOW"
        }


