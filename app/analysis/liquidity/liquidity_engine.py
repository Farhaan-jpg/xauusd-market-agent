"""Liquidity Engine detecting PDH/PDL, PWH/PWL, Session Highs/Lows, EQH/EQL, FVGs, and scoring zone strength."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from app.analysis.liquidity.session_calculator import SessionCalculator
from app.analysis.technical.indicators import TechnicalIndicators
from app.config.settings import settings
from app.core.logging import logger

class LiquidityEngine:
    """Calculates deterministic market liquidity zones and strength scoring (0-100)."""

    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        price = market_data.get("price", 0.0)
        timeframes = market_data.get("timeframes", {})
        df_1d = timeframes.get("1d", pd.DataFrame())
        df_1h = timeframes.get("1h", pd.DataFrame())
        df_15m = timeframes.get("15m", pd.DataFrame())

        zones: List[Dict[str, Any]] = []

        # 1. Previous Day High / Low (PDH / PDL)
        if not df_1d.empty and len(df_1d) >= 2:
            pdh = float(df_1d["high"].iloc[-2])
            pdl = float(df_1d["low"].iloc[-2])
            zones.append(self._create_zone(
                price_level=pdh,
                zone_type="PREVIOUS_DAY_HIGH",
                timeframe="1D",
                current_price=price,
                touch_count=2,
                base_strength=85.0
            ))
            zones.append(self._create_zone(
                price_level=pdl,
                zone_type="PREVIOUS_DAY_LOW",
                timeframe="1D",
                current_price=price,
                touch_count=2,
                base_strength=85.0
            ))

        # 2. Previous Week High / Low (PWH / PWL)
        if not df_1d.empty and len(df_1d) >= 5:
            pwh = float(df_1d["high"].iloc[-5:].max())
            pwl = float(df_1d["low"].iloc[-5:].min())
            zones.append(self._create_zone(
                price_level=pwh,
                zone_type="PREVIOUS_WEEK_HIGH",
                timeframe="1W",
                current_price=price,
                touch_count=2,
                base_strength=90.0
            ))
            zones.append(self._create_zone(
                price_level=pwl,
                zone_type="PREVIOUS_WEEK_LOW",
                timeframe="1W",
                current_price=price,
                touch_count=2,
                base_strength=90.0
            ))

        # 3. Session Highs / Lows
        session_data = SessionCalculator.extract_session_ranges(df_1h if not df_1h.empty else df_15m)
        for s_name, s_info in session_data.items():
            if s_info.get("high", 0.0) > 0:
                zones.append(self._create_zone(
                    price_level=s_info["high"],
                    zone_type=f"{s_name}_SESSION_HIGH",
                    timeframe="1H",
                    current_price=price,
                    touch_count=1,
                    base_strength=70.0
                ))
            if s_info.get("low", 0.0) > 0:
                zones.append(self._create_zone(
                    price_level=s_info["low"],
                    zone_type=f"{s_name}_SESSION_LOW",
                    timeframe="1H",
                    current_price=price,
                    touch_count=1,
                    base_strength=70.0
                ))

        # 4. Equal Highs (EQH) and Equal Lows (EQL)
        active_df = df_1h if not df_1h.empty else df_15m
        if not active_df.empty and len(active_df) >= 15:
            eq_zones = self._detect_equal_highs_lows(active_df, price, tolerance_dollars=settings.LIQUIDITY_TOLERANCE_PIPS)
            zones.extend(eq_zones)

        # 5. Fair Value Gaps (FVG / Imbalances)
        if not active_df.empty and len(active_df) >= 10:
            fvg_zones = self._detect_fair_value_gaps(active_df, price)
            zones.extend(fvg_zones)

        # 6. Deduplicate and cluster adjacent zones
        clustered_zones = self._cluster_zones(zones, price)

        # Separate above and below
        liquidity_above = [z for z in clustered_zones if z["is_above"]]
        liquidity_below = [z for z in clustered_zones if not z["is_above"]]

        # Sort: Above sorted ascending by price (closest first), Below sorted descending by price (closest first)
        liquidity_above.sort(key=lambda z: z["price"])
        liquidity_below.sort(key=lambda z: z["price"], reverse=True)

        # Compute aggregate liquidity score
        avg_strength = np.mean([z["strength"] for z in clustered_zones]) if clustered_zones else 50.0

        return {
            "current_price": price,
            "liquidity_above": liquidity_above[:5],
            "liquidity_below": liquidity_below[:5],
            "all_zones": clustered_zones,
            "active_sessions": SessionCalculator.get_active_sessions(datetime.now(timezone.utc)),
            "session_ranges": session_data,
            "aggregate_liquidity_score": round(float(avg_strength), 1),
            "total_zones_detected": len(clustered_zones)
        }

    def _create_zone(
        self,
        price_level: float,
        zone_type: str,
        timeframe: str,
        current_price: float,
        touch_count: int = 1,
        base_strength: float = 60.0
    ) -> Dict[str, Any]:
        """Calculates deterministic liquidity strength (0-100) and range boundaries."""
        dist = abs(price_level - current_price)
        dist_pct = (dist / current_price * 100.0) if current_price > 0 else 0.0

        # Strength adjustments
        strength = base_strength
        # Proximity bonus (closer = higher urgency/attention)
        if dist_pct < 0.3:
            strength += 15.0
        elif dist_pct < 0.8:
            strength += 8.0
        elif dist_pct > 3.0:
            strength -= 15.0

        # Touch count bonus
        if touch_count >= 3:
            strength += 15.0
        elif touch_count == 2:
            strength += 8.0

        strength = max(10.0, min(99.0, strength))

        # Range buffer (approx $1.50 range for gold)
        range_buffer = 1.0 if timeframe in ["15m", "5m"] else 1.8
        zone_low = round(price_level - range_buffer, 2)
        zone_high = round(price_level + range_buffer, 2)

        # Classification
        if strength >= 80:
            classification = "VERY_HIGH"
        elif strength >= 60:
            classification = "HIGH"
        elif strength >= 40:
            classification = "MODERATE"
        else:
            classification = "LOW"

        return {
            "price": round(price_level, 2),
            "zone_range_low": zone_low,
            "zone_range_high": zone_high,
            "zone_range_display": f"{zone_low:.2f} - {zone_high:.2f}",
            "zone_type": zone_type,
            "timeframe": timeframe,
            "strength": round(strength, 1),
            "classification": classification,
            "distance_from_price": round(dist, 2),
            "distance_pct": round(dist_pct, 2),
            "is_above": (price_level >= current_price),
            "touch_count": touch_count,
            "is_active": True
        }

    def _detect_equal_highs_lows(
        self,
        df: pd.DataFrame,
        current_price: float,
        tolerance_dollars: float = 1.5
    ) -> List[Dict[str, Any]]:
        eq_zones = []
        swing_highs, swing_lows = TechnicalIndicators.find_swing_highs_and_lows(df, window=2)

        # Check Equal Highs
        for i in range(len(swing_highs)):
            for j in range(i + 1, len(swing_highs)):
                p1 = swing_highs[i]["price"]
                p2 = swing_highs[j]["price"]
                if abs(p1 - p2) <= tolerance_dollars:
                    avg_p = (p1 + p2) / 2.0
                    eq_zones.append(self._create_zone(
                        price_level=avg_p,
                        zone_type="EQUAL_HIGHS_CLUSTER",
                        timeframe="1H",
                        current_price=current_price,
                        touch_count=2,
                        base_strength=82.0
                    ))

        # Check Equal Lows
        for i in range(len(swing_lows)):
            for j in range(i + 1, len(swing_lows)):
                p1 = swing_lows[i]["price"]
                p2 = swing_lows[j]["price"]
                if abs(p1 - p2) <= tolerance_dollars:
                    avg_p = (p1 + p2) / 2.0
                    eq_zones.append(self._create_zone(
                        price_level=avg_p,
                        zone_type="EQUAL_LOWS_CLUSTER",
                        timeframe="1H",
                        current_price=current_price,
                        touch_count=2,
                        base_strength=82.0
                    ))

        return eq_zones

    def _detect_fair_value_gaps(self, df: pd.DataFrame, current_price: float) -> List[Dict[str, Any]]:
        """Detects 3-bar Fair Value Gaps (Bullish & Bearish Imbalances)."""
        fvg_zones = []
        highs = df["high"].values
        lows = df["low"].values
        n = len(df)

        for i in range(2, n):
            # Bullish FVG: Low of bar 0 > High of bar 2
            if lows[i] > highs[i - 2]:
                gap_low = highs[i - 2]
                gap_high = lows[i]
                mid_p = (gap_low + gap_high) / 2.0
                fvg_zones.append(self._create_zone(
                    price_level=mid_p,
                    zone_type="BULLISH_FAIR_VALUE_GAP",
                    timeframe="1H",
                    current_price=current_price,
                    touch_count=1,
                    base_strength=72.0
                ))

            # Bearish FVG: High of bar 0 < Low of bar 2
            elif highs[i] < lows[i - 2]:
                gap_low = highs[i]
                gap_high = lows[i - 2]
                mid_p = (gap_low + gap_high) / 2.0
                fvg_zones.append(self._create_zone(
                    price_level=mid_p,
                    zone_type="BEARISH_FAIR_VALUE_GAP",
                    timeframe="1H",
                    current_price=current_price,
                    touch_count=1,
                    base_strength=72.0
                ))

        return fvg_zones

    def _cluster_zones(self, zones: List[Dict[str, Any]], current_price: float) -> List[Dict[str, Any]]:
        """Merges zones within $1.50 of each other to prevent clutter."""
        if not zones:
            return []

        sorted_zones = sorted(zones, key=lambda z: z["price"])
        clustered = []
        curr_cluster = [sorted_zones[0]]

        for z in sorted_zones[1:]:
            last_z = curr_cluster[-1]
            if abs(z["price"] - last_z["price"]) <= 1.5:
                curr_cluster.append(z)
            else:
                # Merge curr_cluster into single representative zone
                clustered.append(self._merge_cluster(curr_cluster, current_price))
                curr_cluster = [z]

        if curr_cluster:
            clustered.append(self._merge_cluster(curr_cluster, current_price))

        return clustered

    def _merge_cluster(self, cluster: List[Dict[str, Any]], current_price: float) -> Dict[str, Any]:
        if len(cluster) == 1:
            return cluster[0]

        best = max(cluster, key=lambda z: z["strength"])
        avg_price = np.mean([z["price"] for z in cluster])
        total_touches = sum(z.get("touch_count", 1) for z in cluster)

        merged = self._create_zone(
            price_level=float(avg_price),
            zone_type=best["zone_type"],
            timeframe=best["timeframe"],
            current_price=current_price,
            touch_count=total_touches,
            base_strength=best["strength"] + 5.0
        )
        return merged
