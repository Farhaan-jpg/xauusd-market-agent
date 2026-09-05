/**
 * XAUUSD AI Market Intelligence & Liquidity Agent - Dashboard Client App
 */

document.addEventListener("DOMContentLoaded", () => {
    fetchDashboardData();
    setInterval(fetchDashboardData, 20000); // 20s auto-refresh

    initActionButtons();
    initSettingsModal();
});

function initActionButtons() {
    const triggerBtn = document.getElementById("btn-trigger");
    if (triggerBtn) {
        triggerBtn.addEventListener("click", async () => {
            triggerBtn.disabled = true;
            triggerBtn.innerHTML = "⏳ Running...";
            try {
                await fetch("/api/trigger-analysis", { method: "POST" });
                showToast("Intelligence cycle initiated.");
                setTimeout(async () => {
                    await fetchDashboardData();
                    triggerBtn.disabled = false;
                    triggerBtn.innerHTML = "🔄 Run Intel";
                }, 3000);
            } catch (err) {
                console.error("Trigger error:", err);
                triggerBtn.disabled = false;
                triggerBtn.innerHTML = "🔄 Run Intel";
            }
        });
    }
}

function initSettingsModal() {
    const modal = document.getElementById("config-modal");
    const openBtn = document.getElementById("btn-open-settings");
    const closeBtn = document.getElementById("btn-close-modal");
    const saveBtn = document.getElementById("btn-save-config");
    const testTgBtn = document.getElementById("btn-test-telegram");

    if (openBtn && modal) {
        openBtn.addEventListener("click", async () => {
            await loadConfigIntoModal();
            modal.classList.add("active");
        });
    }

    if (closeBtn && modal) {
        closeBtn.addEventListener("click", () => {
            modal.classList.remove("active");
        });
    }

    if (saveBtn) {
        saveBtn.addEventListener("click", async () => {
            saveBtn.disabled = true;
            saveBtn.textContent = "Saving...";
            const payload = {
                TELEGRAM_BOT_TOKEN: document.getElementById("cfg-tg-token").value,
                TELEGRAM_CHAT_ID: document.getElementById("cfg-tg-chat").value,
                TELEGRAM_ALERTS_ENABLED: document.getElementById("cfg-tg-enabled").checked,
                AI_PRIORITY: document.getElementById("cfg-ai-priority").value,
                GEMINI_MODEL: document.getElementById("cfg-gemini-model").value,
                GEMINI_API_KEY: document.getElementById("cfg-gemini-key").value,
                OPENROUTER_API_KEY: document.getElementById("cfg-openrouter-key").value,
                ANALYSIS_INTERVAL_SECONDS: parseInt(document.getElementById("cfg-interval").value),
                LIQUIDITY_TOLERANCE_PIPS: parseFloat(document.getElementById("cfg-liq-tol").value),
                PAUSE_ON_WEEKENDS: document.getElementById("cfg-weekend-pause").checked
            };

            try {
                const res = await fetch("/api/config", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok) {
                    showToast("Configuration saved & applied!");
                    modal.classList.remove("active");
                    fetchDashboardData();
                } else {
                    showToast("Error saving config: " + data.message);
                }
            } catch (err) {
                showToast("Failed to save config.");
            } finally {
                saveBtn.disabled = false;
                saveBtn.textContent = "💾 Save & Apply Changes";
            }
        });
    }

    if (testTgBtn) {
        testTgBtn.addEventListener("click", async () => {
            testTgBtn.disabled = true;
            testTgBtn.textContent = "Sending Test...";
            try {
                const res = await fetch("/api/test-telegram", { method: "POST" });
                const data = await res.json();
                if (data.status === "SUCCESS") {
                    showToast("✅ Telegram message sent successfully!");
                } else {
                    showToast("❌ " + data.message);
                }
            } catch (err) {
                showToast("Network error testing Telegram.");
            } finally {
                testTgBtn.disabled = false;
                testTgBtn.textContent = "🔔 Test Telegram Message";
            }
        });
    }
}

async function loadConfigIntoModal() {
    try {
        const res = await fetch("/api/config");
        if (res.ok) {
            const cfg = await res.json();
            document.getElementById("cfg-tg-token").value = cfg.telegram_token_masked || "";
            document.getElementById("cfg-tg-chat").value = cfg.telegram_chat_id || "";
            document.getElementById("cfg-tg-enabled").checked = cfg.telegram_alerts_enabled;
            document.getElementById("cfg-ai-priority").value = cfg.ai_priority || "gemini_first";
            if (cfg.gemini_model) document.getElementById("cfg-gemini-model").value = cfg.gemini_model;
            document.getElementById("cfg-gemini-key").value = cfg.gemini_key_masked || "";
            document.getElementById("cfg-openrouter-key").value = cfg.openrouter_key_masked || "";
            document.getElementById("cfg-interval").value = cfg.analysis_interval_seconds || "180";
            document.getElementById("cfg-liq-tol").value = cfg.liquidity_tolerance_pips || 1.5;
            document.getElementById("cfg-weekend-pause").checked = cfg.pause_on_weekends !== false;
        }
    } catch (err) {
        console.error("Failed to load config:", err);
    }
}

async function fetchDashboardData() {
    try {
        const [reportRes, marketRes, liqRes, newsRes, calRes, accRes] = await Promise.all([
            fetch("/api/latest-report"),
            fetch("/api/market-data"),
            fetch("/api/liquidity"),
            fetch("/api/news"),
            fetch("/api/economic-calendar"),
            fetch("/api/accuracy")
        ]);

        if (reportRes.ok) updateReportUI(await reportRes.json());
        if (marketRes.ok) updateMarketUI(await marketRes.json());
        if (liqRes.ok) updateLiquidityUI(await liqRes.json());
        if (newsRes.ok) updateNewsUI(await newsRes.json());
        if (calRes.ok) updateCalendarUI(await calRes.json());
        if (accRes.ok) updateAccuracyUI(await accRes.json());
    } catch (error) {
        console.error("Error updating dashboard data:", error);
    }
}

function updateReportUI(report) {
    if (report.status === "NO_DATA") return;

    const dirBadge = document.getElementById("direction-badge");
    const dirScore = document.getElementById("direction-score");
    const confPct = document.getElementById("confidence-pct");
    const confBar = document.getElementById("confidence-bar");

    if (dirBadge) {
        dirBadge.textContent = report.direction;
        dirBadge.className = "direction-badge " + 
            (report.direction.includes("BULLISH") ? "bullish" : 
             report.direction.includes("BEARISH") ? "bearish" : "");
    }

    if (dirScore) {
        dirScore.textContent = (report.direction_score > 0 ? "+" : "") + Number(report.direction_score).toFixed(1);
    }

    if (confPct) confPct.textContent = Math.round(report.confidence);
    if (confBar) confBar.style.width = Math.max(10, Math.min(100, report.confidence)) + "%";

    updateMeter("ev-macro-bar", "ev-macro-val", report.scores?.macro_score);
    updateMeter("ev-usd-bar", "ev-usd-val", report.scores?.usd_score);
    updateMeter("ev-yield-bar", "ev-yield-val", report.scores?.yield_score);
    updateMeter("ev-news-bar", "ev-news-val", report.scores?.news_score);
    updateMeter("ev-tech-bar", "ev-tech-val", report.scores?.technical_score);

    const provTag = document.getElementById("ai-provider-tag");
    if (provTag) provTag.textContent = report.provider_used || "Deterministic Engine";

    // Update Final Market Verdict Banner
    const verdictBadge = document.getElementById("final-market-verdict-badge");
    const verdictText = document.getElementById("final-market-verdict-text");
    if (verdictBadge) {
        const v = (report.final_market_verdict || (report.direction?.includes("BULL") ? "BULLISH" : report.direction?.includes("BEAR") ? "BEARISH" : "NEUTRAL")).toUpperCase();
        if (v.includes("BULL")) {
            verdictBadge.textContent = "🟢 BULL MARKET (BULLISH BIAS)";
            verdictBadge.className = "verdict-tag bullish";
        } else if (v.includes("BEAR")) {
            verdictBadge.textContent = "🔴 BEAR MARKET (BEARISH BIAS)";
            verdictBadge.className = "verdict-tag bearish";
        } else {
            verdictBadge.textContent = "⚪ NEUTRAL (SIDEWAYS / BALANCED)";
            verdictBadge.className = "verdict-tag";
        }
    }
    if (verdictText) {
        verdictText.textContent = report.executive_verdict_summary || report.macro_summary || "Multi-signal synthesis complete.";
    }

    const driversList = document.getElementById("dominant-drivers-list");
    if (driversList && report.dominant_drivers?.length) {
        driversList.innerHTML = report.dominant_drivers.map(d => `<li>${escapeHtml(d)}</li>`).join("");
    }

    const macroNarr = document.getElementById("macro-narrative");
    const newsNarr = document.getElementById("news-narrative");
    const riskNarr = document.getElementById("risk-narrative");

    if (macroNarr) macroNarr.textContent = report.macro_summary || "No macro summary available.";
    if (newsNarr) newsNarr.textContent = report.news_summary || "No news summary available.";
    if (riskNarr) riskNarr.textContent = report.risk_factors || "Standard market volatility risk.";

    const tsEl = document.getElementById("last-updated-ts");
    if (tsEl && report.timestamp) {
        tsEl.textContent = new Date(report.timestamp).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" }) + " IST";
    }
}

function updateMeter(barId, valId, score) {
    const bar = document.getElementById(barId);
    const val = document.getElementById(valId);
    const num = Number(score) || 0;

    if (val) val.textContent = (num > 0 ? "+" : "") + num.toFixed(1);
    if (bar) {
        const pct = ((num + 100) / 200) * 100;
        bar.style.width = Math.max(5, Math.min(100, pct)) + "%";
        bar.style.background = num > 15 ? "var(--bullish-green)" : num < -15 ? "var(--bearish-red)" : "var(--neutral-blue)";
    }
}

function updateMarketUI(market) {
    if (market.status === "NO_DATA") return;

    const goldPriceEl = document.getElementById("gold-price");
    const radarPriceEl = document.getElementById("radar-gold-price");
    const chgEl = document.getElementById("price-change-tag");

    const price = Number(market.price) || 0;
    if (goldPriceEl) goldPriceEl.textContent = price.toFixed(2);
    if (radarPriceEl) radarPriceEl.textContent = price.toFixed(2);

    if (chgEl) {
        const chg = Number(market.change_24h) || 0;
        chgEl.textContent = `24h: ${chg >= 0 ? "+" : ""}${chg.toFixed(2)}%`;
        chgEl.style.color = chg >= 0 ? "var(--bullish-green)" : "var(--bearish-red)";
    }

    const trendEl = document.getElementById("regime-trend");
    const volEl = document.getElementById("regime-vol");

    if (trendEl && market.indicators?.trend) {
        trendEl.textContent = market.indicators.trend.replace("_", " ");
    }
    if (volEl && market.indicators?.volatility) {
        volEl.textContent = market.indicators.volatility.replace("_", " ");
    }
}

function updateLiquidityUI(liq) {
    const aboveList = document.getElementById("liquidity-above-list");
    const belowList = document.getElementById("liquidity-below-list");

    if (aboveList) {
        if (!liq.liquidity_above?.length) {
            aboveList.innerHTML = `<div class="zone-empty">No high liquidity clusters in range</div>`;
        } else {
            aboveList.innerHTML = liq.liquidity_above.map(z => `
                <div class="zone-item above">
                    <div>
                        <div class="zone-level">$${Number(z.price).toFixed(2)}</div>
                        <div class="zone-tag">${escapeHtml(z.type)} (${z.timeframe})</div>
                    </div>
                    <div class="zone-strength">Strength: ${Math.round(z.strength)}/100</div>
                </div>
            `).join("");
        }
    }

    if (belowList) {
        if (!liq.liquidity_below?.length) {
            belowList.innerHTML = `<div class="zone-empty">No high liquidity clusters in range</div>`;
        } else {
            belowList.innerHTML = liq.liquidity_below.map(z => `
                <div class="zone-item below">
                    <div>
                        <div class="zone-level">$${Number(z.price).toFixed(2)}</div>
                        <div class="zone-tag">${escapeHtml(z.type)} (${z.timeframe})</div>
                    </div>
                    <div class="zone-strength">Strength: ${Math.round(z.strength)}/100</div>
                </div>
            `).join("");
        }
    }
}

function updateNewsUI(news) {
    const feed = document.getElementById("news-feed-list");
    if (!feed) return;

    if (!news?.length) {
        feed.innerHTML = `<div class="news-item-empty">No recent news available.</div>`;
        return;
    }

    feed.innerHTML = news.slice(0, 8).map(n => `
        <div class="news-card">
            <a href="${escapeHtml(n.url || '#')}" target="_blank" class="news-title">${escapeHtml(n.title)}</a>
            <div class="news-meta">
                <span>🏢 ${escapeHtml(n.source)}</span>
                <span>•</span>
                <span>Gold: <b>${escapeHtml(n.gold_impact)}</b></span>
                <span>•</span>
                <span>Impact: <b>${escapeHtml(n.impact_level)}</b></span>
            </div>
        </div>
    `).join("");
}

function updateCalendarUI(events) {
    const tbody = document.getElementById("calendar-body");
    if (!tbody) return;

    if (!events?.length) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center">No upcoming high-impact USD events.</td></tr>`;
        return;
    }

    tbody.innerHTML = events.slice(0, 5).map(e => {
        const timeStr = new Date(e.scheduled_time).toLocaleTimeString("en-IN", { 
            timeZone: "Asia/Kolkata", 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        return `
            <tr>
                <td><b>${escapeHtml(e.event_name)}</b></td>
                <td>${timeStr} IST</td>
                <td>${escapeHtml(e.forecast || '--')}</td>
                <td>${escapeHtml(e.previous || '--')}</td>
                <td><span class="badge ${e.importance === 'HIGH' ? 'bearish' : ''}">${escapeHtml(e.importance)}</span></td>
            </tr>
        `;
    }).join("");
}

function updateAccuracyUI(acc) {
    if (!acc || acc.status === "INSUFFICIENT_HISTORICAL_DATA") return;

    const totalEl = document.getElementById("acc-total-evals");
    const overallEl = document.getElementById("acc-overall-pct");
    const bullEl = document.getElementById("acc-bull-pct");
    const bearEl = document.getElementById("acc-bear-pct");

    if (totalEl) totalEl.textContent = acc.total_evaluations;
    if (overallEl) overallEl.textContent = `${acc.overall_directional_accuracy_pct}%`;
    if (bullEl) bullEl.textContent = `${acc.bullish_accuracy_pct}%`;
    if (bearEl) bearEl.textContent = `${acc.bearish_accuracy_pct}%`;
}

function showToast(msg) {
    const toast = document.getElementById("toast");
    if (toast) {
        toast.textContent = msg;
        toast.classList.add("show");
        setTimeout(() => toast.classList.remove("show"), 3500);
    }
}

function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
