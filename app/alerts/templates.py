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
        cot_bias: str = "BALANCED_POSITIONING",
        scalp_bias: str = "",
        day_trade_bias: str = "",
        vwap: float = 0.0,
        market_structure: str = ""
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
            e_name = e.get("event_name", "") if isinstance(e, dict) else getattr(e, "event_name", "")
            e_imp = e.get("importance", "") if isinstance(e, dict) else getattr(e, "importance", "")
            events_str += f"\n  • <b>{esc(e_name)}</b> [{esc(e_imp)}]"
        if not events_str: events_str = "\n  • No critical events in next 24h"

        summary_text = executive_verdict_summary or macro_summary

        scalp_section = ""
        if scalp_bias or day_trade_bias:
            vwap_str = f" | VWAP: <b>${vwap:.2f}</b>" if vwap > 0 else ""
            scalp_section = f"""━━━━━━━━━━━━━━━━━━━━
<b>⚡ SCALPING & DAY TRADING BIAS:</b>
• Scalp Bias (5M): <b>{esc(scalp_bias or 'MOMENTUM_ALIGNMENT')}</b>
• Day Trade Bias (15M): <b>{esc(day_trade_bias or 'STRUCTURE_FOLLOW')}</b>{vwap_str}
• Market Structure: <b>{esc(market_structure or 'RANGING')}</b>"""

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
{scalp_section}
━━━━━━━━━━━━━━━━━━━━
📝 <b>EXECUTIVE ANALYSIS:</b>
{esc(summary_text)}
━━━━━━━━━━━━━━━━━━━━
<b>📈 EVIDENCE MATRIX & GEOPOLITICS:</b>
• Technical Score (50%): <b>{tech_score:+.1f}</b> ({esc(trend.replace('_', ' '))})
• Real-Time News (20%): <b>{news_score:+.1f}</b>
• Macro Score (15%): <b>{macro_score:+.1f}</b> (USD: {usd_score:+.1f}, Yields: {yield_score:+.1f})
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
<i>ℹ️ Real-time scalping & day-trading market intelligence. Not financial advice.</i>"""
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
            e_name = e.get("event_name", "") if isinstance(e, dict) else getattr(e, "event_name", "")
            e_time = str(e.get("scheduled_time", "") if isinstance(e, dict) else getattr(e, "scheduled_time", ""))[:16]
            e_imp = e.get("importance", "HIGH") if isinstance(e, dict) else getattr(e, "importance", "HIGH")
            events_str += f"\n  • <b>{esc(e_name)}</b> ({esc(e_time)}) - [{esc(e_imp)}]"
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

    @staticmethod
    def scalp_command_response(
        price: float,
        scalp_bias: str,
        day_trade_bias: str,
        overall_trend: str,
        market_structure: str,
        vwap: float,
        tech_score: float,
        rsi_15m: float,
        supertrend: str = "",
        killzone: str = "",
        sweep_warning: str = ""
    ) -> str:
        esc = TelegramBot.escape
        dir_emoji = "🟢" if "BULL" in scalp_bias else "🔴" if "BEAR" in scalp_bias else "⚪"
        vwap_diff = price - vwap if vwap > 0 else 0
        vwap_pos = "ABOVE" if vwap_diff >= 0 else "BELOW"
        
        sweep_section = ""
        if sweep_warning:
            sweep_section = f"\n⚠️ <b>LIQUIDITY SWEEP / JUDAS:</b> {esc(sweep_warning)}"

        return f"""⚡ <b>REAL-TIME XAUUSD SCALP RADAR (5M / 15M)</b>
📅 <i>{get_formatted_time()}</i>
━━━━━━━━━━━━━━━━━━━━
💰 <b>Spot Price:</b> ${price:.2f}
{dir_emoji} <b>5M Scalp Bias:</b> <b>{esc(scalp_bias)}</b>
🎯 <b>15M Day Bias:</b> <b>{esc(day_trade_bias)}</b>
━━━━━━━━━━━━━━━━━━━━
<b>📊 TECHNICAL & STRUCTURE DYNAMICS:</b>
• Market Structure: <b>{esc(market_structure or 'RANGING')}</b>
• Session VWAP: <b>${vwap:.2f}</b> ({vwap_pos} by ${abs(vwap_diff):.2f})
• SuperTrend: <b>{esc(supertrend or 'NEUTRAL')}</b>
• 15M RSI: <b>{rsi_15m:.1f}</b>
• 1H Higher Timeframe: <b>{esc(overall_trend.replace('_', ' '))}</b> (Score: {tech_score:+.1f})
• Active Killzone: <b>{esc(killzone or 'OFF_HOURS')}</b>{sweep_section}
━━━━━━━━━━━━━━━━━━━━
<i>⚡ Quick-reaction intraday telemetry. Manage risk tightly.</i>""".strip()

    @staticmethod
    def levels_command_response(
        price: float,
        liquidity_above: list,
        liquidity_below: list,
        session_high: float = 0.0,
        session_low: float = 0.0,
        asian_high: float = 0.0,
        asian_low: float = 0.0,
        adr: float = 0.0
    ) -> str:
        esc = TelegramBot.escape
        above_str = ""
        for z in liquidity_above[:3]:
            above_str += f"\n  🔴 <b>${z['price']:.2f}</b> - {esc(z['zone_type'])} (Str: {z['strength']:.0f})"
        if not above_str: above_str = "\n  • No immediate resistance clusters"

        below_str = ""
        for z in liquidity_below[:3]:
            below_str += f"\n  🟢 <b>${z['price']:.2f}</b> - {esc(z['zone_type'])} (Str: {z['strength']:.0f})"
        if not below_str: below_str = "\n  • No immediate support clusters"

        session_str = ""
        if session_high > 0 and session_low > 0:
            session_str = f"""━━━━━━━━━━━━━━━━━━━━
<b>🎯 KEY INTRADAY BENCHMARKS:</b>
• Day High: <b>${session_high:.2f}</b> | Day Low: <b>${session_low:.2f}</b>"""
            if asian_high > 0 and asian_low > 0:
                session_str += f"\n• Asian High: <b>${asian_high:.2f}</b> | Asian Low: <b>${asian_low:.2f}</b>"
            if adr > 0:
                session_str += f"\n• Average Daily Range (ADR): <b>${adr:.2f}</b>"

        return f"""🎯 <b>XAUUSD KEY LIQUIDITY & ORDERFLOW LEVELS</b>
📅 <i>{get_formatted_time()}</i>
━━━━━━━━━━━━━━━━━━━━
💰 <b>Current Spot:</b> ${price:.2f}

<b>🔺 BUY-SIDE LIQUIDITY / RESISTANCE (BSL):</b>{above_str}

<b>🔻 SELL-SIDE LIQUIDITY / SUPPORT (SSL):</b>{below_str}
{session_str}
━━━━━━━━━━━━━━━━━━━━
<i>🌊 High-volume institutional resting liquidity clusters.</i>""".strip()

    @staticmethod
    def killzone_command_response(
        killzone_info: dict,
        current_price: float,
        recent_sweeps: list = None
    ) -> str:
        esc = TelegramBot.escape
        active_kz = killzone_info.get("active_killzone")
        is_active = killzone_info.get("is_active", False)
        kz_name = killzone_info.get("killzone_name", "None")
        next_kz = killzone_info.get("next_killzone", "None")
        starts_in = killzone_info.get("starts_in_minutes", 0)

        status_badge = f"🟢 <b>ACTIVE: {esc(kz_name)}</b>" if is_active else f"⚪ <b>OFF-HOURS / REGULAR SESSION</b>"
        
        sweeps_str = ""
        if recent_sweeps:
            for s in recent_sweeps[:2]:
                sweeps_str += f"\n  • ⚠️ <b>{esc(s.get('type', 'SWEEP'))}</b> at ${s.get('sweep_price', 0):.2f} ({esc(s.get('description', ''))})"
        if not sweeps_str:
            sweeps_str = "\n  • No major Judas swing / sweep detected in last 3h"

        return f"""🏛 <b>ICT SESSION & KILLZONE TELEMETRY</b>
📅 <i>{get_formatted_time()}</i>
━━━━━━━━━━━━━━━━━━━━
💰 <b>Spot Price:</b> ${current_price:.2f}
Status: {status_badge}
━━━━━━━━━━━━━━━━━━━━
<b>⏰ ICT SESSION SCHEDULE (UTC):</b>
• <b>Asian Range:</b> 00:00 - 06:00 UTC (05:30 - 11:30 IST)
• <b>London Open:</b> 07:00 - 10:00 UTC (12:30 - 15:30 IST) <i>[Judas High Risk]</i>
• <b>NY AM Open:</b> 12:00 - 15:00 UTC (17:30 - 20:30 IST) <i>[Volatility Expansion]</i>
• <b>London Close:</b> 15:00 - 17:00 UTC (20:30 - 22:30 IST) <i>[Profit Taking / Reversals]</i>

<b>⏳ NEXT KILLZONE:</b>
• <b>{esc(next_kz)}</b> (Starts in ~{starts_in} min)

<b>🌊 RECENT LIQUIDITY PURGES:</b>{sweeps_str}
━━━━━━━━━━━━━━━━━━━━
<i>Institutional time & price algorithm window tracking.</i>""".strip()

    @staticmethod
    def dxy_command_response(
        dxy_price: float,
        dxy_change: float,
        dxy_trend: str,
        us10y_yield: float,
        us10y_change: float,
        divergence_status: str,
        divergence_desc: str,
        gold_price: float,
        gold_change: float
    ) -> str:
        esc = TelegramBot.escape
        div_emoji = "🟢" if "BULLISH" in divergence_status else "🔴" if "BEARISH" in divergence_status else "⚪"
        return f"""💵 <b>DXY & US10Y INTERMARKET DIVERGENCE ENGINE</b>
📅 <i>{get_formatted_time()}</i>
━━━━━━━━━━━━━━━━━━━━
💰 <b>XAUUSD:</b> ${gold_price:.2f} ({gold_change:+.2f}%)
💵 <b>US Dollar Index (DXY):</b> {dxy_price:.2f} ({dxy_change:+.2f}%) - <b>{esc(dxy_trend)}</b>
📈 <b>US 10-Year Treasury Yield:</b> {us10y_yield:.3f}% ({us10y_change:+.2f}%)
━━━━━━━━━━━━━━━━━━━━
{div_emoji} <b>INTERMARKET DIVERGENCE VERDICT:</b>
<b>{esc(divergence_status)}</b>

📝 <b>Mechanism Analysis:</b>
{esc(divergence_desc)}
━━━━━━━━━━━━━━━━━━━━
<i>Macro correlation tracking: Gold typically holds inverse correlation with DXY & Yields.</i>""".strip()

    @staticmethod
    def help_command_response() -> str:
        return """🤖 <b>XAUUSD MARKET AGENT - INTERACTIVE RADAR</b>
━━━━━━━━━━━━━━━━━━━━
Available Commands:
• <b>/scalp</b> - Real-time 5M/15M scalping & day trade bias, VWAP, SuperTrend & structure
• <b>/levels</b> - Buy-side (BSL) & sell-side (SSL) liquidity pools, orderblocks & intraday levels
• <b>/killzone</b> - Current ICT Killzone window status, Judas swing alerts & schedule
• <b>/dxy</b> - US Dollar Index (DXY) & 10Y Yield correlation divergence engine
• <b>/verdict</b> - Full institutional executive market direction & intelligence report
• <b>/news</b> - Real-time breaking high-impact headlines with recency weighting
• <b>/help</b> - Show this command list

━━━━━━━━━━━━━━━━━━━━
<i>Tip: Webhook signals from TradingView are automatically relayed to this channel.</i>""".strip()

    @staticmethod
    def tradingview_webhook_alert(
        ticker: str,
        action: str,
        price: float,
        timeframe: str = "5m",
        strategy_name: str = "TradingView Alert",
        message: str = ""
    ) -> str:
        esc = TelegramBot.escape
        act_emoji = "🟢" if "BUY" in action.upper() or "LONG" in action.upper() else "🔴" if "SELL" in action.upper() or "SHORT" in action.upper() else "⚡"
        msg_str = f"\n📝 <b>Details:</b> {esc(message)}" if message else ""
        return f"""{act_emoji} <b>TRADINGVIEW WEBHOOK INCOMING SIGNAL</b>
📅 <i>{get_formatted_time()}</i>
━━━━━━━━━━━━━━━━━━━━
🎯 <b>Strategy:</b> {esc(strategy_name)}
🏷 <b>Symbol:</b> {esc(ticker.upper())} ({esc(timeframe)})
⚡ <b>Action:</b> <b>{esc(action.upper())}</b>
💰 <b>Trigger Price:</b> ${price:.2f}{msg_str}
━━━━━━━━━━━━━━━━━━━━
<i>External chart automation trigger relayed via XAUUSD Market Agent.</i>""".strip()

    @staticmethod
    def pre_news_lockout_alert(
        event_name: str,
        minutes_to_event: int,
        scheduled_time: str,
        impact: str = "HIGH"
    ) -> str:
        esc = TelegramBot.escape
        return f"""⚠️ <b>PRE-NEWS VOLATILITY LOCKOUT WARNING</b>
📅 <i>{get_formatted_time()}</i>
━━━━━━━━━━━━━━━━━━━━
🛑 <b>High-Impact Red-Folder Event Imminent:</b>
• <b>{esc(event_name)}</b> [{esc(impact)}]
• Scheduled: <b>{esc(scheduled_time)}</b>
• Countdown: <b>T-Minus {minutes_to_event} minutes</b>

🔒 <b>SYSTEM PROTOCOL:</b>
High probability of institutional slippage, spread expansion, and two-way stop hunting. Caution is advised for tight scalp setups until 15 minutes post-release.
━━━━━━━━━━━━━━━━━━━━
<i>Institutional volatility protection protocol.</i>""".strip()


