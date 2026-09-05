"""Standardized Telegram alert templates for institutional market intelligence."""
from datetime import datetime, timezone
import zoneinfo
from app.config.settings import settings
from app.telegram.bot import TelegramBot

def get_formatted_time(dt: datetime = None) -> str:
    """Formats datetime into Asia/Kolkata timezone with IST indicator."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    try:
        ist_tz = zoneinfo.ZoneInfo(settings.TIMEZONE)
        local_dt = dt.astimezone(ist_tz)
        return local_dt.strftime("%d %b %Y, %I:%M %p IST")
    except Exception:
        return dt.strftime("%Y-%m-%d %H:%M UTC")

class AlertTemplates:
    """Formats rich, compliance-safe HTML messages for Telegram."""

    @staticmethod
    def periodic_report(
        price: float,
        direction: str,
        score: float,
        confidence: float,
        macro_score: float,
        usd_score: float,
        yield_score: float,
        news_score: float,
        tech_score: float,
        trend: str,
        volatility: str,
        liquidity_above: list,
        liquidity_below: list,
        dominant_drivers: list,
        macro_summary: str,
        news_summary: str,
        risk_factors: str,
        upcoming_events: list,
        provider_used: str,
        final_market_verdict: str = "",
        executive_verdict_summary: str = "",
        cei_score: float = 25.0,
        safe_haven_premium: float = 20.0,
        cot_bias: str = "BALANCED_POSITIONING"
    ) -> str:
        esc = TelegramBot.escape
        dir_emoji = "🟢" if "BULLISH" in direction else "🔴" if "BEARISH" in direction else "⚪"

        # Determine explicit verdict display (BULL / BEAR / NEUTRAL)
        v = (final_market_verdict or ("BULLISH" if "BULL" in direction else "BEARISH" if "BEAR" in direction else "NEUTRAL")).upper()
        if "BULL" in v:
            verdict_badge = "🟢 <b>BULL MARKET (BULLISH BIAS)</b>"
        elif "BEAR" in v:
            verdict_badge = "🔴 <b>BEAR MARKET (BEARISH BIAS)</b>"
        else:
            verdict_badge = "⚪ <b>NEUTRAL (SIDEWAYS / BALANCED)</b>"

        above_str = ""
        for z in liquidity_above[:2]:
            above_str += f"\n  • <b>${z['price']:.2f}</b> ({esc(z['zone_type'])}) - Strength: {z['strength']:.0f}/100"
        if not above_str: above_str = "\n  • None within immediate proximity"

        below_str = ""
        for z in liquidity_below[:2]:
            below_str += f"\n  • <b>${z['price']:.2f}</b> ({esc(z['zone_type'])}) - Strength: {z['strength']:.0f}/100"
        if not below_str: below_str = "\n  • None within immediate proximity"

        drivers_str = ""
        for d in dominant_drivers[:3]:
            drivers_str += f"\n  • {esc(d)}"

        events_str = ""
        for e in upcoming_events[:2]:
            events_str += f"\n  • <b>{esc(e.get('event_name', ''))}</b> [{esc(e.get('importance', ''))}]"
        if not events_str: events_str = "\n  • No critical events in next 24h"

        summary_text = executive_verdict_summary or macro_summary

        msg = f"""<b>🏛 XAUUSD MARKET INTELLIGENCE REPORT</b>
📅 <i>{get_formatted_time()}</i>
━━━━━━━━━━━━━━━━━━━━
💰 <b>XAUUSD Spot:</b> ${price:.2f}
{dir_emoji} <b>Market Direction:</b> <b>{esc(direction)}</b>
📊 <b>Direction Score:</b> {score:+.1f} / 100
🎯 <b>Confidence Level:</b> {confidence:.0f}%
━━━━━━━━━━━━━━━━━━━━
🎯 <b>FINAL MARKET VERDICT:</b>
{verdict_badge}

📝 <b>EXECUTIVE ANALYSIS:</b>
{esc(summary_text)}
━━━━━━━━━━━━━━━━━━━━
<b>📈 EVIDENCE MATRIX & GEOPOLITICS:</b>
• Macro Score: <b>{macro_score:+.1f}</b>
• USD Score: <b>{usd_score:+.1f}</b>
• Yield Score: <b>{yield_score:+.1f}</b>
• News Sentiment: <b>{news_score:+.1f}</b>
• Technical Score: <b>{tech_score:+.1f}</b> ({esc(trend.replace('_', ' '))})
• 🌍 Conflict Index (CEI): <b>{cei_score:.1f}/100</b> (+${safe_haven_premium:.2f}/oz Safe-Haven)
• 🏛 Institutional COT: <b>{esc(cot_bias.replace('_', ' '))}</b>
• Volatility: <b>{esc(volatility.replace('_', ' '))}</b>
━━━━━━━━━━━━━━━━━━━━
<b>🔑 DOMINANT DRIVERS:</b>{drivers_str}

<b>🌊 HIGH LIQUIDITY ABOVE:</b>{above_str}

<b>🛡 HIGH LIQUIDITY BELOW:</b>{below_str}
━━━━━━━━━━━━━━━━━━━━
<b>🧠 DETAILED AI INTELLIGENCE ({esc(provider_used)}):</b>
{esc(macro_summary)}

{esc(news_summary)}

<b>⚠️ KEY RISKS:</b>
{esc(risk_factors)}
━━━━━━━━━━━━━━━━━━━━
<b>📅 UPCOMING HIGH-IMPACT EVENTS:</b>{events_str}
━━━━━━━━━━━━━━━━━━━━
<i>ℹ️ Non-directional market intelligence. Not financial or trading advice.</i>"""
        return msg.strip()

    @staticmethod
    def session_open_briefing(
        session_name: str,
        price: float,
        direction: str,
        final_market_verdict: str,
        cei_score: float,
        safe_haven_premium: float,
        overnight_high: float,
        overnight_low: float,
        nearest_ceiling: Optional[Dict[str, Any]],
        nearest_floor: Optional[Dict[str, Any]],
        events_today: List[Dict[str, Any]],
        executive_summary: str
    ) -> str:
        esc = TelegramBot.escape
        icon = "🇬🇧" if "LONDON" in session_name.upper() else "🇺🇸" if "NEW YORK" in session_name.upper() else "🔔"
        
        events_str = ""
        for e in events_today[:3]:
            events_str += f"\n  • <b>{esc(e.get('event_name', ''))}</b> ({esc(e.get('scheduled_time', ''))[:16]}) - [{esc(e.get('importance', 'HIGH'))}]"
        if not events_str:
            events_str = "\n  • No major tier-1 releases scheduled for this session"

        ceil_str = f"${nearest_ceiling['price']:.2f} (+{nearest_ceiling.get('distance', 0):.1f} pips)" if nearest_ceiling else "None detected"
        floor_str = f"${nearest_floor['price']:.2f} (-{nearest_floor.get('distance', 0):.1f} pips)" if nearest_floor else "None detected"

        return f"""{icon} <b>PRE-MARKET {esc(session_name.upper())} OPEN BRIEFING</b>
📅 <i>{get_formatted_time()}</i>
━━━━━━━━━━━━━━━━━━━━
💰 <b>Opening Spot Price:</b> ${price:.2f}
🎯 <b>Market Verdict:</b> <b>{esc(final_market_verdict)} ({esc(direction)})</b>
🌍 <b>Conflict Escalation (CEI):</b> <b>{cei_score:.1f}/100</b> (Safe-Haven Premium: +${safe_haven_premium:.2f}/oz)
━━━━━━━━━━━━━━━━━━━━
<b>📊 OVERNIGHT SESSION STRUCTURE:</b>
• Range High: <b>${overnight_high:.2f}</b>
• Range Low:  <b>${overnight_low:.2f}</b>
• Nearest Resistance Magnet: <b>{ceil_str}</b>
• Nearest Support Cushion:   <b>{floor_str}</b>
━━━━━━━━━━━━━━━━━━━━
<b>📝 SESSION EXECUTIVE OUTLOOK:</b>
{esc(executive_summary)}
━━━━━━━━━━━━━━━━━━━━
<b>📅 UPCOMING HIGH-IMPACT CATALYSTS:</b>{events_str}
━━━━━━━━━━━━━━━━━━━━
<i>🏛 Automated institutional bell intelligence. Non-advisory research.</i>""".strip()

    @staticmethod
    def direction_change_alert(
        prev_direction: str,
        prev_score: float,
        new_direction: str,
        new_score: float,
        price: float,
        dominant_drivers: list
    ) -> str:
        esc = TelegramBot.escape
        dir_emoji = "🟢" if "BULLISH" in new_direction else "🔴" if "BEARISH" in new_direction else "⚪"

        drivers_str = ""
        for d in dominant_drivers[:2]:
            drivers_str += f"\n• {esc(d)}"

        return f"""🚨 <b>XAUUSD DIRECTION SHIFT ALERT</b>
📅 <i>{get_formatted_time()}</i>
━━━━━━━━━━━━━━━━━━━━
💰 <b>Current Price:</b> ${price:.2f}

Previous: <b>{esc(prev_direction)}</b> ({prev_score:+.1f})
Current:  {dir_emoji} <b>{esc(new_direction)}</b> ({new_score:+.1f})
━━━━━━━━━━━━━━━━━━━━
<b>Primary Drivers of Shift:</b>{drivers_str}
━━━━━━━━━━━━━━━━━━━━
<i>Strictly market intelligence. Never trade signals or execution instructions.</i>"""

    @staticmethod
    def high_impact_news_alert(
        title: str,
        source: str,
        gold_impact: str,
        impact_level: str,
        summary: str
    ) -> str:
        esc = TelegramBot.escape
        imp_emoji = "🚨" if impact_level == "CRITICAL" else "⚡"
        return f"""{imp_emoji} <b>HIGH-IMPACT NEWS INTEL</b>
📅 <i>{get_formatted_time()}</i>
━━━━━━━━━━━━━━━━━━━━
📰 <b>{esc(title)}</b>
🏢 <b>Source:</b> {esc(source)}
💥 <b>Impact Level:</b> {esc(impact_level)}
🟡 <b>Gold Sentiment:</b> <b>{esc(gold_impact)}</b>
━━━━━━━━━━━━━━━━━━━━
<b>Summary / Context:</b>
{esc(summary)}
━━━━━━━━━━━━━━━━━━━━
<i>Real-time automated news intelligence.</i>"""

    @staticmethod
    def liquidity_proximity_alert(
        zone_price: float,
        zone_type: str,
        strength: float,
        current_price: float,
        distance: float
    ) -> str:
        esc = TelegramBot.escape
        side = "ABOVE" if zone_price > current_price else "BELOW"
        return f"""🌊 <b>HIGH LIQUIDITY PROXIMITY ALERT</b>
📅 <i>{get_formatted_time()}</i>
━━━━━━━━━━━━━━━━━━━━
💰 <b>Current Price:</b> ${current_price:.2f}
🎯 <b>Approaching Zone:</b> ${zone_price:.2f} ({side})
🏷 <b>Zone Type:</b> {esc(zone_type)}
💪 <b>Liquidity Strength:</b> {strength:.0f} / 100
📏 <b>Distance:</b> ${distance:.2f} ({abs(distance/current_price)*100:.2f}%)
━━━━━━━━━━━━━━━━━━━━
<i>Price is approaching a high-significance structural liquidity cluster.</i>"""

