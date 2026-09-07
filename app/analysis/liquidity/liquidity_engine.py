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

        # 7. ICT Killzone & Liquidity Sweeps Detection
        now_utc = datetime.now(timezone.utc)
        killzone_info = SessionCalculator.get_ict_killzone_status(now_utc)
        
        pdh_val = float(df_1d["high"].iloc[-2]) if not df_1d.empty and len(df_1d) >= 2 else 0.0
        pdl_val = float(df_1d["low"].iloc[-2]) if not df_1d.empty and len(df_1d) >= 2 else 0.0
        active_sweeps = self._detect_liquidity_sweeps(
            df=active_df,
            current_price=price,
            session_data=session_data,
            pdh=pdh_val,
            pdl=pdl_val
        )

        # Separate above and below
        liquidity_above = [z for z in clustered_zones if z["is_above"]]
        liquidity_below = [z for z in clustered_zones if not z["is_above"]]

        # Sort: Above sorted ascending by price (closest first), Below sorted descending by price (closest first)
        liquidity_above.sort(key=lambda z: z["price"])
        liquidity_below.sort(key=lambda z: z["price"], reverse=True)

        # Compute aggregate liquidity score & order flow imbalance
        avg_strength = np.mean([z["strength"] for z in clustered_zones]) if clustered_zones else 50.0
        total_demand_strength = sum(z["strength"] for z in liquidity_below)
        total_supply_strength = sum(z["strength"] for z in liquidity_above)
        total_strength = total_demand_strength + total_supply_strength
        demand_pct = round((total_demand_strength / total_strength * 100.0), 1) if total_strength > 0 else 50.0
        supply_pct = round(100.0 - demand_pct, 1)

        # Generate 24-level Horizontal Volume & Order-Flow Profile
        horizontal_profile = self.generate_horizontal_profile(price, clustered_zones)

        # Generate comprehensive quantitative order-flow narrative
        nearest_res = liquidity_above[0]["price"] if liquidity_above else (price + 15.0)
        nearest_sup = liquidity_below[0]["price"] if liquidity_below else (price - 15.0)
        res_dist = round(abs(nearest_res - price), 1)
        sup_dist = round(abs(price - nearest_sup), 1)
        imbalance_desc = f"Net Institutional Accumulation ({demand_pct}% Bid Depth vs {supply_pct}% Ask)" if demand_pct >= supply_pct else f"Net Institutional Distribution ({supply_pct}% Ask Pressure vs {demand_pct}% Bid)"
        
        sweep_desc = f" | Active Sweep: {active_sweeps[0]['description']}" if active_sweeps else ""
        narrative = (
            f"Order-flow structure indicates {imbalance_desc}{sweep_desc}. "
            f"Active spot auction (${price:.2f}) is bounded between immediate overhead supply liquidity at ${nearest_res:.2f} (+{res_dist} pts) "
            f"and underlying institutional demand defense at ${nearest_sup:.2f} (-{sup_dist} pts)."
        )

        return {
            "current_price": price,
            "liquidity_above": liquidity_above[:8],
            "liquidity_below": liquidity_below[:8],
            "all_zones": clustered_zones,
            "horizontal_profile": horizontal_profile,
            "demand_depth_pct": demand_pct,
            "supply_depth_pct": supply_pct,
            "order_flow_bias": "BULLISH_ORDER_FLOW" if demand_pct >= supply_pct else "BEARISH_ORDER_FLOW",
            "order_flow_narrative": narrative,
            "immediate_resistance": nearest_res,
            "immediate_support": nearest_sup,
            "active_sessions": SessionCalculator.get_active_sessions(now_utc),
            "session_ranges": session_data,
            "killzone": killzone_info,
            "active_sweeps": active_sweeps,
            "aggregate_liquidity_score": round(float(avg_strength), 1),
            "total_zones_detected": len(clustered_zones)
        }

    def _detect_liquidity_sweeps(
        self,
        df: Any,
        current_price: float,
        session_data: Optional[Dict[str, Any]] = None,
        pdh: float = 0.0,
        pdl: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Detects Buy-Side (BSL) and Sell-Side (SSL) Liquidity Sweeps / Judas Swings."""
        sweeps = []
        session_data = session_data or {}
        
        if isinstance(df, list):
            if len(df) < 2:
                return sweeps
            df = pd.DataFrame(df)

        if not isinstance(df, pd.DataFrame) or df.empty or len(df) < 2:
            return sweeps

        recent_bars = df.iloc[-min(5, len(df)):]
        recent_high = float(recent_bars["high"].max())
        recent_low = float(recent_bars["low"].min())
        curr_close = float(df["close"].iloc[-1])

        levels_to_check = []
        if pdh > 0: levels_to_check.append(("PDH (Previous Day High)", pdh, "HIGH"))
        if pdl > 0: levels_to_check.append(("PDL (Previous Day Low)", pdl, "LOW"))

        for s_name, s_info in session_data.items():
            if s_info.get("high", 0) > 0:
                levels_to_check.append((f"{s_name} Session High", s_info["high"], "HIGH"))
            if s_info.get("low", 0) > 0:
                levels_to_check.append((f"{s_name} Session Low", s_info["low"], "LOW"))

        # Also check against recent swing points in the dataframe itself if no external levels
        if not levels_to_check and len(df) >= 2:
            prev_high = float(df["high"].iloc[-2])
            prev_low = float(df["low"].iloc[-2])
            levels_to_check.append(("Prior High", prev_high, "HIGH"))
            levels_to_check.append(("Prior Low", prev_low, "LOW"))

        for name, lvl, side in levels_to_check:
            # BSL Sweep: High pierced level but close rejected back below level
            if side == "HIGH" and recent_high > lvl and curr_close < lvl:
                wick_size = round(recent_high - lvl, 2)
                if 0.2 <= wick_size <= 15.0:
                    sweeps.append({
                        "type": "BSL_SWEEP_REVERSAL",
                        "level_swept": name,
                        "level_price": lvl,
                        "wick_high": recent_high,
                        "wick_depth": wick_size,
                        "bias": "BEARISH",
                        "sweep_price": recent_high,
                        "description": f"Buy-Side Liquidity sweep above {name} (${lvl:.2f}) with bearish rejection"
                    })

            # SSL Sweep: Low pierced level but close rejected back above level
            elif side == "LOW" and recent_low < lvl and curr_close > lvl:
                wick_size = round(lvl - recent_low, 2)
                if 0.2 <= wick_size <= 15.0:
                    sweeps.append({
                        "type": "SSL_SWEEP_REVERSAL",
                        "level_swept": name,
                        "level_price": lvl,
                        "wick_low": recent_low,
                        "wick_depth": wick_size,
                        "bias": "BULLISH",
                        "sweep_price": recent_low,
                        "description": f"Sell-Side Liquidity sweep below {name} (${lvl:.2f}) with bullish rejection"
                    })

        return sweeps


    def generate_horizontal_profile(self, current_price: float, zones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generates continuous horizontal price-depth bins around spot price for order-flow visualization."""
        if current_price <= 0:
            current_price = 4400.0

        # Create 25 price bins spanning -1.2% to +1.2% (approx +/- $50 on gold)
        step = max(1.5, round((current_price * 0.024) / 24, 1))
        bins = []
        base_low = round(current_price - (12 * step), 1)

        for i in range(25):
            p = round(base_low + (i * step), 2)
            is_above = (p >= current_price)
            side = "SUPPLY" if is_above else "DEMAND"
            
            # Find closest structural zone
            dist_to_zones = [abs(p - z["price"]) for z in zones]
            min_dist = min(dist_to_zones) if dist_to_zones else 999.0
            closest_z = zones[dist_to_zones.index(min_dist)] if dist_to_zones and min_dist < (step * 1.5) else None

            # Compute intensity: baseline + proximity to structural zone
            base_intensity = 35.0 + (abs(12 - i) * 1.8) # natural resting distribution
            if closest_z:
                zone_boost = closest_z.get("strength", 60.0) * 0.55
                intensity = min(98.0, base_intensity + zone_boost)
                zone_name = closest_z.get("zone_type", "").replace("_", " ")
            else:
                intensity = max(20.0, min(80.0, base_intensity))
                zone_name = "Supply Liquidity Wall" if is_above else "Resting Demand Block"

            bins.append({
                "price": p,
                "price_formatted": f"${p:.2f}",
                "side": side,
                "strength": round(intensity, 1),
                "volume_intensity": round(intensity, 1),
                "volume_weight": round(intensity / 50.0, 2),
                "is_current_level": abs(p - current_price) <= (step / 2.0),
                "type": zone_name,
                "zone_tag": zone_name,
                "distance_pts": round(abs(p - current_price), 1),
                "is_above": is_above
            })

        return bins

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

        # Timeframe weight
        tf_weight = 12.0 if timeframe in ["1W", "1D"] else 6.0 if timeframe in ["4H", "H4"] else 2.0
        # Proximity adjustment
        prox_adj = 10.0 if dist_pct < 0.4 else 5.0 if dist_pct < 1.0 else -8.0 if dist_pct > 2.5 else 0.0
        # Touch count multiplier
        touch_adj = min(14.0, (touch_count - 1) * 6.0)

        raw_strength = base_strength + tf_weight + prox_adj + touch_adj
        # Add slight natural deterministic dispersion based on price decimals to avoid duplicate static integers
        dispersion = ((int(price_level * 100) % 7) - 3) * 1.5
        strength = max(30.0, min(97.0, raw_strength + dispersion))

        # Range buffer (approx $1.50 - $2.50 range for gold)
        range_buffer = 1.2 if timeframe in ["15m", "5m"] else 2.2 if timeframe in ["1W", "1D"] else 1.8
        zone_low = round(price_level - range_buffer, 2)
        zone_high = round(price_level + range_buffer, 2)

        # Classification & volume tag
        if strength >= 85:
            classification = "VERY_HIGH"
            vol_weight = "VERY HIGH (Major Institutional Pool)"
        elif strength >= 70:
            classification = "HIGH"
            vol_weight = "HIGH (Order Block Imbalance)"
        elif strength >= 55:
            classification = "MODERATE"
            vol_weight = "MODERATE (Liquidity Cluster)"
        else:
            classification = "LOW"
            vol_weight = "NORMAL (Minor Equal Level)"

        return {
            "price": round(price_level, 2),
            "zone_range_low": zone_low,
            "zone_range_high": zone_high,
            "zone_range_display": f"{zone_low:.2f} - {zone_high:.2f}",
            "zone_type": zone_type,
            "timeframe": timeframe,
            "strength": round(strength, 1),
            "classification": classification,
            "volume_weight": vol_weight,
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
                        base_strength=78.0
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
                        base_strength=78.0
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
        """Merges zones within $1.80 of each other to prevent clutter."""
        if not zones:
            return []

        sorted_zones = sorted(zones, key=lambda z: z["price"])
        clustered = []
        curr_cluster = [sorted_zones[0]]

        for z in sorted_zones[1:]:
            last_z = curr_cluster[-1]
            if abs(z["price"] - last_z["price"]) <= 1.8:
                curr_cluster.append(z)
            else:
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
            base_strength=best["strength"] + 4.0
        )
        return merged
