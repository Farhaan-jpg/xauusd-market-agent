"""Geopolitical Conflict Escalation Index (CEI) and Safe-Haven Bullion Premium Engine."""
from typing import Any, Dict, List, Optional
import re
from app.core.logging import logger

# Regional Flashpoint Configurations & Keyword Signatures
REGIONAL_FLASHPOINTS = {
    "MIDDLE_EAST": {
        "name": "Middle East & Persian Gulf",
        "keywords": ["iran", "israel", "gaza", "lebanon", "hezbollah", "houthi", "red sea", "yemen", "strait of hormuz", "tehran", "tel aviv", "syria", "iraq"],
        "base_weight": 1.4,
        "chokepoint_risk": "High (Strait of Hormuz & Bab el-Mandeb energy/trade corridors)"
    },
    "EASTERN_EUROPE": {
        "name": "Eastern Europe & Black Sea",
        "keywords": ["ukraine", "russia", "kyiv", "moscow", "crimea", "black sea", "nato", "baltic", "kursk", "donbas", "nuclear doctrine"],
        "base_weight": 1.3,
        "chokepoint_risk": "Moderate (Grain & European natural gas / fertilizer supply)"
    },
    "ASIA_PACIFIC": {
        "name": "Taiwan Strait & South China Sea",
        "keywords": ["taiwan", "china", "beijing", "taipei", "south china sea", "philippines", "pla", "strait of malacca", "semiconductor blockade"],
        "base_weight": 1.2,
        "chokepoint_risk": "Severe (Global semiconductor & Pacific shipping choke-point)"
    },
    "GLOBAL_PROXIES": {
        "name": "Global Defense & Sovereign Sanctions",
        "keywords": ["sanctions", "embargo", "nuclear test", "ballistic missile", "arms deal", "drone attack", "sovereign default", "coup", "defense alert"],
        "base_weight": 1.0,
        "chokepoint_risk": "Broad Macro & Sovereign Credit Risk"
    }
}

ESCALATION_SEVERITY_KEYWORDS = {
    "CRITICAL": ["war declared", "invasion", "nuclear threat", "ballistic missile attack", "carrier strike group", "direct strike", "oil embargo", "martial law"],
    "HIGH": ["missile strike", "airstrike", "drone attack", "heavy casualties", "military mobilization", "blockade", "retaliation promised", "airspace closed"],
    "MODERATE": ["tensions rise", "sanctions imposed", "diplomatic breakdown", "military drills", "border skirmish", "warning issued", "ambassador recalled"],
    "DE_ESCALATION": ["ceasefire agreed", "peace talks", "hostage release", "treaty signed", "tensions ease", "diplomatic breakthrough", "troops withdraw"]
}

class GeopoliticalConflictEngine:
    """Calculates Conflict Escalation Index (0-100) and Safe-Haven Bullion Premium ($/oz)."""

    def analyze(self, news_items: List[Dict[str, Any]], gold_price: float = 2900.0) -> Dict[str, Any]:
        """Analyzes real-time news headlines to compute CEI, regional breakdown, and gold risk premium."""
        if not news_items:
            return self._default_state(gold_price)

        hotspot_scores = {k: 0.0 for k in REGIONAL_FLASHPOINTS.keys()}
        hotspot_mentions = {k: [] for k in REGIONAL_FLASHPOINTS.keys()}
        total_escalation_points = 0.0
        total_deescalation_points = 0.0

        for item in news_items:
            title = item.get("title", "").lower()
            category = item.get("category", "")
            
            # Check regional hotspots
            matched_region = None
            for reg_key, reg_cfg in REGIONAL_FLASHPOINTS.items():
                for kw in reg_cfg["keywords"]:
                    if kw in title:
                        matched_region = reg_key
                        hotspot_mentions[reg_key].append(item.get("title", "")[:70])
                        break
                if matched_region:
                    break

            # Evaluate escalation severity
            item_points = 0.0
            is_deescalation = False

            for crit_kw in ESCALATION_SEVERITY_KEYWORDS["CRITICAL"]:
                if crit_kw in title:
                    item_points += 25.0
                    break

            if item_points == 0.0:
                for high_kw in ESCALATION_SEVERITY_KEYWORDS["HIGH"]:
                    if high_kw in title:
                        item_points += 15.0
                        break

            if item_points == 0.0:
                for mod_kw in ESCALATION_SEVERITY_KEYWORDS["MODERATE"]:
                    if mod_kw in title:
                        item_points += 8.0
                        break

            for deesc_kw in ESCALATION_SEVERITY_KEYWORDS["DE_ESCALATION"]:
                if deesc_kw in title:
                    total_deescalation_points += 12.0
                    is_deescalation = True
                    break

            if category in ["WAR_CONFLICT", "GEOPOLITICAL"] and item_points == 0.0 and not is_deescalation:
                item_points += 10.0

            if matched_region and item_points > 0:
                weight = REGIONAL_FLASHPOINTS[matched_region]["base_weight"]
                hotspot_scores[matched_region] += (item_points * weight)
                total_escalation_points += (item_points * weight)
            elif item_points > 0:
                total_escalation_points += item_points

        # Base ambient geopolitical tension score (baseline ~ 20.0 in modern climate)
        ambient_base = 22.0
        net_raw_score = ambient_base + (total_escalation_points * 1.5) - (total_deescalation_points * 1.8)
        cei_score = max(5.0, min(98.0, round(net_raw_score, 1)))

        # Qualitative Level
        if cei_score >= 75.0:
            status_level = "CRITICAL"
            status_desc = "Severe Military Conflict & Broad Escalation"
            status_color = "#ef4444"
        elif cei_score >= 50.0:
            status_level = "ELEVATED"
            status_desc = "Active Regional Hostilities & Flashpoint Risk"
            status_color = "#f59e0b"
        elif cei_score >= 30.0:
            status_level = "MODERATE"
            status_desc = "Simmering Geopolitical Friction"
            status_color = "#3b82f6"
        else:
            status_level = "CALM"
            status_desc = "Low Geopolitical Threat Environment"
            status_color = "#10b981"

        # Safe-Haven Risk Premium calculation:
        # Typically represents 1.0% to 3.5% of gold spot price during active conflicts
        premium_pct = (cei_score / 100.0) * 0.028  # up to ~2.8% premium at max CEI
        safe_haven_premium_usd = round(gold_price * premium_pct, 2)

        # Build Regional Flashpoint Summary
        flashpoint_breakdown = []
        for reg_key, reg_cfg in REGIONAL_FLASHPOINTS.items():
            score = round(min(100.0, hotspot_scores[reg_key] * 2.5), 1)
            flashpoint_breakdown.append({
                "region_key": reg_key,
                "name": reg_cfg["name"],
                "score": score,
                "chokepoint_risk": reg_cfg["chokepoint_risk"],
                "recent_headlines_count": len(hotspot_mentions[reg_key]),
                "sample_headline": hotspot_mentions[reg_key][0] if hotspot_mentions[reg_key] else "No immediate escalation detected"
            })

        # Identify Primary Hotspot
        primary_hotspot = max(flashpoint_breakdown, key=lambda x: x["score"])

        return {
            "conflict_escalation_index": cei_score,
            "status_level": status_level,
            "status_description": status_desc,
            "status_color": status_color,
            "safe_haven_premium_usd": safe_haven_premium_usd,
            "safe_haven_premium_pct": round(premium_pct * 100, 2),
            "primary_hotspot": primary_hotspot["name"] if primary_hotspot["score"] > 15 else "Global Background Baseline",
            "flashpoints": flashpoint_breakdown
        }

    def _default_state(self, gold_price: float) -> Dict[str, Any]:
        return {
            "conflict_escalation_index": 25.0,
            "status_level": "MODERATE",
            "status_description": "Baseline Geopolitical Background Tension",
            "status_color": "#3b82f6",
            "safe_haven_premium_usd": round(gold_price * 0.007, 2),
            "safe_haven_premium_pct": 0.7,
            "primary_hotspot": "Middle East & Persian Gulf",
            "flashpoints": [
                {"region_key": k, "name": v["name"], "score": 20.0, "chokepoint_risk": v["chokepoint_risk"], "recent_headlines_count": 0, "sample_headline": "Baseline monitoring active"}
                for k, v in REGIONAL_FLASHPOINTS.items()
            ]
        }
