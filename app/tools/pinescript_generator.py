"""TradingView Pine Script v5 Indicator Generator exporting dynamic levels, Killzones, and HUD."""
from typing import Any, Dict, List, Optional

class PineScriptGenerator:
    """Generates ready-to-paste TradingView Pine Script v5 indicator scripts."""

    @staticmethod
    def generate_script(
        current_price: float,
        direction: str,
        score: float,
        liquidity_above: List[Dict[str, Any]],
        liquidity_below: List[Dict[str, Any]],
        asian_high: float = 0.0,
        asian_low: float = 0.0
    ) -> str:
        """Constructs a complete Pine Script v5 indicator code string."""
        above_lines = ""
        for i, z in enumerate(liquidity_above[:3]):
            p = z.get("price", current_price + 10.0)
            tag = z.get("zone_type", "RESISTANCE")
            above_lines += f'    line.new(bar_index - 30, {p:.2f}, bar_index + 10, {p:.2f}, color=color.new(color.red, 20), width=2, style=line.style_dashed)\n'
            above_lines += f'    label.new(bar_index + 10, {p:.2f}, "BSL: {tag} (${p:.2f})", color=color.new(color.red, 80), textcolor=color.white, size=size.small)\n'

        below_lines = ""
        for i, z in enumerate(liquidity_below[:3]):
            p = z.get("price", current_price - 10.0)
            tag = z.get("zone_type", "SUPPORT")
            below_lines += f'    line.new(bar_index - 30, {p:.2f}, bar_index + 10, {p:.2f}, color=color.new(color.green, 20), width=2, style=line.style_dashed)\n'
            below_lines += f'    label.new(bar_index + 10, {p:.2f}, "SSL: {tag} (${p:.2f})", color=color.new(color.green, 80), textcolor=color.white, size=size.small)\n'

        asian_range_code = ""
        if asian_high > 0 and asian_low > 0:
            asian_range_code = f"""
// === ASIAN RANGE HIGH / LOW ===
var line asianH = na
var line asianL = na
line.delete(asianH)
line.delete(asianL)
asianH := line.new(bar_index - 40, {asian_high:.2f}, bar_index + 10, {asian_high:.2f}, color=color.new(color.yellow, 30), width=2)
asianL := line.new(bar_index - 40, {asian_low:.2f}, bar_index + 10, {asian_low:.2f}, color=color.new(color.yellow, 30), width=2)
label.new(bar_index + 10, {asian_high:.2f}, "Asian High (${asian_high:.2f})", color=color.new(color.yellow, 80), textcolor=color.white, size=size.small)
label.new(bar_index + 10, {asian_low:.2f}, "Asian Low (${asian_low:.2f})", color=color.new(color.yellow, 80), textcolor=color.white, size=size.small)
"""

        return f"""//@version=5
indicator("XAUUSD Market Agent - Live Intelligence HUD", overlay=true, max_lines_count=100, max_labels_count=100)

// === REAL-TIME AGENT VERDICT TELEMETRY ===
var table hud = table.new(position.top_right, 2, 4, bgcolor=color.new(color.black, 20), border_color=color.gray, border_width=1)
if barstate.islast
    table.cell(hud, 0, 0, "AGENT BIAS", text_color=color.white, bgcolor=color.new(color.black, 40), text_size=size.small)
    table.cell(hud, 1, 0, "{direction} ({score:+.1f})", text_color={"color.green" if score > 0 else "color.red" if score < 0 else "color.yellow"}, text_size=size.small)
    table.cell(hud, 0, 1, "SPOT ANCHOR", text_color=color.white, text_size=size.small)
    table.cell(hud, 1, 1, "${current_price:.2f}", text_color=color.white, text_size=size.small)

// === DYNAMIC INSTITUTIONAL LIQUIDITY LEVELS ===
if barstate.islast
{above_lines}
{below_lines}
{asian_range_code}

// === INTRADAY SESSION VWAP ===
vwapVal = ta.vwap(hlc3)
plot(vwapVal, "Session VWAP", color=color.orange, linewidth=2)
"""
