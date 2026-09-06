/**
 * XAUUSD AI AGENT — CLIENT DASHBOARD CONTROLLER
 * Minimal, ultra-responsive, real-time news capture & analysis updater.
 */

let refreshIntervalId = null;
let currentRefreshRate = 10; // seconds
let knownNewsFingerprints = new Set();
let chartData = null;
let activeTimeframe = "H1";

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initSessions();
    initActionButtons();
    initSettingsDrawer();
    initChartControls();
    
    // Initial data fetch
    fetchFullDashboard();
    setupAutoRefresh(currentRefreshRate);

    // Update market sessions every minute
    setInterval(initSessions, 60000);
});

/* ==============================================================================
   1. TAB SWITCHER
   ============================================================================== */
function initTabs() {
    const tabButtons = document.querySelectorAll(".seg-btn");
    const tabPanes = document.querySelectorAll(".content-panel");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetId = btn.getAttribute("data-tab");
            
            tabButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            tabPanes.forEach(pane => {
                pane.classList.toggle("active", pane.id === targetId);
            });

            // If switching to chart tab, resize/redraw chart
            if (targetId === "tab-chart") {
                renderChart();
            }
        });
    });

    const btnViewAllNews = document.getElementById("btn-view-all-news");
    if (btnViewAllNews) {
        btnViewAllNews.addEventListener("click", () => {
            const newsTabBtn = document.querySelector('.seg-btn[data-tab="tab-news"]');
            if (newsTabBtn) newsTabBtn.click();
        });
    }

    const btnCloseBanner = document.getElementById("btn-close-banner");
    if (btnCloseBanner) {
        btnCloseBanner.addEventListener("click", () => {
            const banner = document.getElementById("breaking-banner");
            if (banner) banner.style.display = "none";
        });
    }
}

/* ==============================================================================
   2. TRADING SESSIONS
   ============================================================================== */
function initSessions() {
    const now = new Date();
    const utcHour = now.getUTCHours() + (now.getUTCMinutes() / 60);

    // London: 07:00 - 16:00 UTC
    const isLondon = utcHour >= 7 && utcHour < 16;
    // New York: 12:00 - 21:00 UTC
    const isNY = utcHour >= 12 && utcHour < 21;
    // Tokyo: 00:00 - 09:00 UTC
    const isTokyo = utcHour >= 0 && utcHour < 9;

    setSessionActive("sess-lon", isLondon);
    setSessionActive("sess-ny", isNY);
    setSessionActive("sess-tok", isTokyo);
}

function setSessionActive(id, active) {
    const el = document.getElementById(id);
    if (el) el.classList.toggle("active", active);
}

/* ==============================================================================
   3. AUTO-REFRESH & DATA FETCHING
   ============================================================================== */
function setupAutoRefresh(seconds) {
    if (refreshIntervalId) {
        clearInterval(refreshIntervalId);
        refreshIntervalId = null;
    }
    if (seconds > 0) {
        refreshIntervalId = setInterval(fetchFullDashboard, seconds * 1000);
    }
}

async function fetchFullDashboard() {
    try {
        const [reportRes, marketRes, newsRes, macroRes, liqRes, calRes, geoRes] = await Promise.allSettled([
            fetch("/api/latest-report").then(r => r.json()),
            fetch("/api/market-data").then(r => r.json()),
            fetch("/api/news").then(r => r.json()),
            fetch("/api/macro").then(r => r.json()),
            fetch("/api/liquidity").then(r => r.json()),
            fetch("/api/economic-calendar").then(r => r.json()),
            fetch("/api/geopolitics").then(r => r.json())
        ]);

        if (reportRes.status === "fulfilled") updateExecutiveReport(reportRes.value);
        if (marketRes.status === "fulfilled") updateMarketData(marketRes.value);
        if (newsRes.status === "fulfilled") updateNewsStream(newsRes.value);
        if (macroRes.status === "fulfilled") updateMacroData(macroRes.value);
        if (liqRes.status === "fulfilled") updateLiquidityData(liqRes.value);
        if (calRes.status === "fulfilled") updateCalendarData(calRes.value);
        if (geoRes.status === "fulfilled") updateGeopolitics(geoRes.value);

        // Fetch chart candles in background
        fetchChartCandles(activeTimeframe);

    } catch (err) {
        console.error("Dashboard refresh error:", err);
    }
}

/* ==============================================================================
   4. UI COMPONENT UPDATERS
   ============================================================================== */
function updateExecutiveReport(data) {
    if (!data || data.status === "NO_DATA") return;

    // Verdict Badge & Direction
    const dir = data.direction || "NEUTRAL";
    const score = (data.direction_score !== undefined) ? data.direction_score : (data.score || 0.0);
    const conf = Math.round(data.confidence || 75);

    const badge = document.getElementById("hero-verdict-badge");
    const badgeText = document.getElementById("hero-verdict-text");
    if (badge && badgeText) {
        badge.className = `verdict-badge ${dir.toLowerCase()}`;
        const sign = score > 0 ? "+" : "";
        badgeText.textContent = `${dir} (${sign}${score.toFixed(1)})`;
    }

    // Confidence Ring
    const confVal = document.getElementById("hero-conf-val");
    const confFill = document.getElementById("hero-conf-fill");
    if (confVal) confVal.textContent = `${conf}%`;
    if (confFill) {
        confFill.setAttribute("stroke-dasharray", `${conf}, 100`);
        confFill.style.stroke = conf >= 80 ? "#10b981" : conf >= 60 ? "#f59e0b" : "#f43f5e";
    }

    // Verdict Narrative
    const narrative = document.getElementById("hero-verdict-summary");
    if (narrative) {
        narrative.textContent = data.executive_verdict_summary || data.news_summary || data.macro_summary || "Multi-signal quantitative convergence active.";
    }

    // Telemetry strip
    const teleScore = document.getElementById("tele-score");
    if (teleScore) teleScore.textContent = `${score > 0 ? "+" : ""}${score.toFixed(1)}`;

    const teleMacro = document.getElementById("tele-macro");
    if (teleMacro && data.scores) {
        const ms = data.scores.macro_score || 0;
        teleMacro.textContent = ms > 15 ? "BULLISH" : ms < -15 ? "BEARISH" : "NEUTRAL";
    }

    const teleNews = document.getElementById("tele-news");
    if (teleNews && data.scores) {
        const ns = data.scores.news_score || 0;
        teleNews.textContent = ns > 15 ? "BULLISH" : ns < -15 ? "BEARISH" : "NEUTRAL";
    }

    const teleProvider = document.getElementById("tele-provider");
    if (teleProvider) teleProvider.textContent = data.provider_used || "AI Synthesizer";

    const teleTime = document.getElementById("tele-synctime");
    if (teleTime) {
        const now = new Date();
        teleTime.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }

    // Catalyst Tags
    const tagsContainer = document.getElementById("hero-catalyst-tags");
    if (tagsContainer) {
        const drivers = data.dominant_drivers || [];
        if (drivers.length > 0) {
            tagsContainer.innerHTML = drivers.map(d => {
                const isBull = d.toLowerCase().includes("bull") || d.toLowerCase().includes("cut") || d.toLowerCase().includes("war") || d.toLowerCase().includes("escalat");
                const isBear = d.toLowerCase().includes("bear") || d.toLowerCase().includes("hike") || d.toLowerCase().includes("strong dollar");
                const cls = isBull ? "tag-pill bull" : isBear ? "tag-pill bear" : "tag-pill";
                return `<span class="${cls}">⚡ ${escapeHtml(d)}</span>`;
            }).join("");
        }
    }

    // Dominant Drivers List
    const driversList = document.getElementById("dominant-drivers-list");
    if (driversList && data.dominant_drivers) {
        driversList.innerHTML = data.dominant_drivers.slice(0, 4).map(drv => {
            const isBull = !drv.toLowerCase().includes("bear") && !drv.toLowerCase().includes("drop");
            return `
                <div class="driver-item">
                    <span class="driver-name">${escapeHtml(drv)}</span>
                    <span class="driver-impact ${isBull ? 'bull' : 'bear'}">${isBull ? '+ BULL' : '- BEAR'}</span>
                </div>
            `;
        }).join("");
    }

    // Supporting Factors
    const suppList = document.getElementById("supporting-factors-list");
    if (suppList && data.supporting_factors) {
        suppList.innerHTML = data.supporting_factors.slice(0, 3).map(f => `<li>• ${escapeHtml(f)}</li>`).join("");
    }

    // Contradicting Factors
    const contList = document.getElementById("contradicting-factors-list");
    if (contList && data.contradicting_factors) {
        contList.innerHTML = data.contradicting_factors.slice(0, 3).map(f => `<li>• ${escapeHtml(f)}</li>`).join("");
    }
}

function updateMarketData(data) {
    if (!data || data.status === "NO_DATA") return;

    const priceEl = document.getElementById("live-gold-price");
    if (priceEl && data.price) {
        priceEl.textContent = Number(data.price).toFixed(2);
    }

    const changeEl = document.getElementById("live-price-change");
    if (changeEl && data.change_24h !== undefined) {
        const chg = Number(data.change_24h);
        const sign = chg >= 0 ? "+" : "";
        changeEl.textContent = `${sign}${chg.toFixed(2)}%`;
        changeEl.className = `change-tag ${chg < 0 ? 'negative' : ''}`;
    }

    // Mini range bar
    const lowEl = document.getElementById("mini-low");
    const highEl = document.getElementById("mini-high");
    const fillEl = document.getElementById("mini-range-fill");

    if (lowEl && data.low_24h) lowEl.textContent = Math.round(data.low_24h);
    if (highEl && data.high_24h) highEl.textContent = Math.round(data.high_24h);

    if (fillEl && data.price && data.low_24h && data.high_24h && data.high_24h > data.low_24h) {
        const pct = ((data.price - data.low_24h) / (data.high_24h - data.low_24h)) * 100;
        fillEl.style.width = `${Math.max(5, Math.min(95, pct))}%`;
    }
}

function updateNewsStream(newsItems) {
    if (!Array.isArray(newsItems) || newsItems.length === 0) return;

    // Check for newly captured news articles
    let newlyDetected = [];
    newsItems.forEach(item => {
        const id = item.title;
        if (!knownNewsFingerprints.has(id)) {
            knownNewsFingerprints.add(id);
            newlyDetected.push(item);
        }
    });

    // If a new critical or high impact article arrived, flash the breaking banner
    if (newlyDetected.length > 0 && knownNewsFingerprints.size > newsItems.length) {
        const topNew = newlyDetected.find(n => n.impact_level === "CRITICAL" || n.impact_level === "HIGH") || newlyDetected[0];
        showBreakingBanner(topNew.title);
        showToast(`⚡ New News Captured: ${topNew.title.substring(0, 50)}...`);
    }

    // Mini preview list (Overview Tab)
    const previewContainer = document.getElementById("news-preview-container");
    if (previewContainer) {
        previewContainer.innerHTML = newsItems.slice(0, 3).map(item => {
            const timeAgo = formatTimeAgo(item.published_time);
            const imp = item.impact_level || "MEDIUM";
            const goldImp = item.gold_impact || "NEUTRAL";
            const isBull = goldImp === "BULLISH";
            const isBear = goldImp === "BEARISH";

            return `
                <a href="${escapeHtml(item.url || '#')}" target="_blank" rel="noopener" class="news-card-mini">
                    <div class="news-mini-top">
                        <span class="news-impact-tag ${imp.toLowerCase()}">${imp}</span>
                        <span class="news-time">${timeAgo}</span>
                    </div>
                    <div class="news-mini-title">${escapeHtml(item.title)}</div>
                    <span class="news-mini-bias ${isBull ? 'bull' : isBear ? 'bear' : ''}">
                        ${isBull ? '🟢 Bullish for Gold' : isBear ? '🔴 Bearish for Gold' : '⚪ Neutral'}
                    </span>
                </a>
            `;
        }).join("");
    }

    // Full News Stream (News Tab)
    const fullStream = document.getElementById("full-news-stream");
    if (fullStream) {
        let bullCount = 0, bearCount = 0, critCount = 0;

        fullStream.innerHTML = newsItems.map(item => {
            if (item.gold_impact === "BULLISH") bullCount++;
            if (item.gold_impact === "BEARISH") bearCount++;
            if (item.impact_level === "CRITICAL") critCount++;

            const timeAgo = formatTimeAgo(item.published_time);
            const imp = item.impact_level || "MEDIUM";
            const isBull = item.gold_impact === "BULLISH";
            const isBear = item.gold_impact === "BEARISH";

            return `
                <div class="news-stream-card">
                    <div class="news-card-header">
                        <div class="news-badges-left">
                            <span class="news-impact-tag ${imp.toLowerCase()}">${imp}</span>
                            <span class="news-mini-bias ${isBull ? 'bull' : isBear ? 'bear' : ''}">
                                ${isBull ? 'BULLISH' : isBear ? 'BEARISH' : 'NEUTRAL'}
                            </span>
                            <span class="news-source-tag">${escapeHtml(item.source || 'Financial Wire')}</span>
                        </div>
                        <span class="news-time">${timeAgo}</span>
                    </div>
                    <a href="${escapeHtml(item.url || '#')}" target="_blank" rel="noopener" class="news-card-title">
                        ${escapeHtml(item.title)}
                    </a>
                </div>
            `;
        }).join("");

        // Update counts
        const elBull = document.getElementById("full-news-bull-count");
        const elBear = document.getElementById("full-news-bear-count");
        const elCrit = document.getElementById("full-news-crit-count");
        const elBias = document.getElementById("full-news-bias");

        if (elBull) elBull.textContent = bullCount;
        if (elBear) elBear.textContent = bearCount;
        if (elCrit) elCrit.textContent = critCount;
        if (elBias) {
            elBias.textContent = bullCount > bearCount ? "BULLISH" : bearCount > bullCount ? "BEARISH" : "NEUTRAL";
            elBias.className = `metric-val ${bullCount > bearCount ? 'color-green' : bearCount > bullCount ? 'color-red' : ''}`;
        }
    }
}

function updateMacroData(data) {
    if (!data) return;

    if (data.us_10y_yield) {
        const el = document.getElementById("macro-us10y-val");
        if (el) el.textContent = `${Number(data.us_10y_yield.value).toFixed(2)}%`;
        const badge = document.getElementById("macro-us10y-bias");
        if (badge) {
            const b = data.us_10y_yield.gold_bias;
            badge.textContent = b;
            badge.className = `macro-badge ${b === 'BULLISH' ? 'bull' : b === 'BEARISH' ? 'bear' : ''}`;
        }
    }

    if (data.dxy_index) {
        const el = document.getElementById("macro-dxy-val");
        if (el) el.textContent = Number(data.dxy_index.value).toFixed(2);
        const badge = document.getElementById("macro-dxy-bias");
        if (badge) {
            const b = data.dxy_index.gold_bias;
            badge.textContent = b;
            badge.className = `macro-badge ${b === 'BULLISH' ? 'bull' : b === 'BEARISH' ? 'bear' : ''}`;
        }
    }

    if (data.tips_real_yield) {
        const el = document.getElementById("macro-tips-val");
        if (el) el.textContent = `${Number(data.tips_real_yield.value).toFixed(2)}%`;
        const badge = document.getElementById("macro-tips-bias");
        if (badge) {
            const b = data.tips_real_yield.gold_bias;
            badge.textContent = b;
            badge.className = `macro-badge ${b === 'BULLISH' ? 'bull' : b === 'BEARISH' ? 'bear' : ''}`;
        }
    }

    if (data.vix_index) {
        const el = document.getElementById("macro-vix-val");
        if (el) el.textContent = Number(data.vix_index.value).toFixed(2);
    }
}

function updateGeopolitics(data) {
    if (!data) return;

    const ceiEl = document.getElementById("geo-cei-badge");
    if (ceiEl && data.conflict_escalation_index !== undefined) {
        ceiEl.textContent = `CEI: ${data.conflict_escalation_index.toFixed(0)}/100`;
    }

    const premEl = document.getElementById("geo-premium-val");
    if (premEl && data.safe_haven_premium_usd !== undefined) {
        premEl.textContent = `+$${data.safe_haven_premium_usd.toFixed(2)} / oz`;
    }

    const summaryEl = document.getElementById("geo-summary-text");
    if (summaryEl && data.summary) {
        summaryEl.textContent = data.summary;
    }
}

function updateLiquidityData(data) {
    if (!data) return;

    const supplyContainer = document.getElementById("supply-zones-list");
    if (supplyContainer && Array.isArray(data.liquidity_above)) {
        if (data.liquidity_above.length === 0) {
            supplyContainer.innerHTML = `<div class="empty-state-mini">No overhead supply clusters found.</div>`;
        } else {
            supplyContainer.innerHTML = data.liquidity_above.slice(0, 4).map(z => `
                <div class="liq-row">
                    <span class="liq-price">$${Number(z.price).toFixed(2)}</span>
                    <span class="liq-type">${z.type.replace('_', ' ')} (+${z.distance.toFixed(1)} pts)</span>
                </div>
            `).join("");
        }
    }

    const demandContainer = document.getElementById("demand-zones-list");
    if (demandContainer && Array.isArray(data.liquidity_below)) {
        if (data.liquidity_below.length === 0) {
            demandContainer.innerHTML = `<div class="empty-state-mini">No resting demand clusters found.</div>`;
        } else {
            demandContainer.innerHTML = data.liquidity_below.slice(0, 4).map(z => `
                <div class="liq-row">
                    <span class="liq-price">$${Number(z.price).toFixed(2)}</span>
                    <span class="liq-type">${z.type.replace('_', ' ')} (-${z.distance.toFixed(1)} pts)</span>
                </div>
            `).join("");
        }
    }
}

function updateCalendarData(events) {
    const container = document.getElementById("calendar-events-container");
    if (!container || !Array.isArray(events)) return;

    if (events.length === 0) {
        container.innerHTML = `<div class="empty-state-mini">No high-impact economic releases scheduled for the next 48h.</div>`;
        return;
    }

    container.innerHTML = events.slice(0, 6).map(e => {
        const timeStr = new Date(e.scheduled_time).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
        const imp = e.importance || "HIGH";

        return `
            <div class="cal-event-card">
                <div class="cal-left">
                    <span class="cal-flag">${e.country === 'USD' ? '🇺🇸' : '🌐'}</span>
                    <div class="cal-details">
                        <span class="cal-name">${escapeHtml(e.event_name)}</span>
                        <span class="cal-time">${timeStr} UTC</span>
                    </div>
                </div>
                <div class="cal-right">
                    <span class="cal-impact-badge ${imp.toLowerCase()}">${imp}</span>
                </div>
            </div>
        `;
    }).join("");
}

/* ==============================================================================
   5. INSTANT NEWS SYNC BUTTON ACTION
   ============================================================================== */
function initActionButtons() {
    const btnSync = document.getElementById("btn-quick-sync");
    if (btnSync) {
        btnSync.addEventListener("click", async () => {
            btnSync.classList.add("spinning");
            showToast("⚡ Fetching fresh feeds & running AI synthesis...");

            try {
                const res = await fetch("/api/sync-news?force_analysis=true", { method: "POST" });
                const json = await res.json();
                
                if (json.status === "SUCCESS") {
                    showToast(`✅ Synced! Found ${json.new_articles_count} new news items. Verdict: ${json.direction}`);
                    await fetchFullDashboard();
                } else {
                    showToast("⚠️ Sync encountered a minor issue.");
                }
            } catch (err) {
                showToast("❌ Sync failed. Check network.");
            } finally {
                btnSync.classList.remove("spinning");
            }
        });
    }

    const btnForceNews = document.getElementById("btn-force-news-sync");
    if (btnForceNews) {
        btnForceNews.addEventListener("click", () => {
            btnSync?.click();
        });
    }
}

/* ==============================================================================
   6. CHART ENGINE (CLEAN CANVAS RENDERING)
   ============================================================================== */
function initChartControls() {
    const tfBtns = document.querySelectorAll(".tf-btn");
    tfBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tfBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activeTimeframe = btn.getAttribute("data-tf");
            fetchChartCandles(activeTimeframe);
        });
    });

    window.addEventListener("resize", () => {
        if (document.getElementById("tab-chart")?.classList.contains("active")) {
            renderChart();
        }
    });
}

async function fetchChartCandles(tf) {
    try {
        const res = await fetch(`/api/candles?timeframe=${tf}`);
        if (!res.ok) return;
        chartData = await res.json();
        renderChart();
    } catch (e) {
        console.debug("Candle fetch error:", e);
    }
}

function renderChart() {
    const canvas = document.getElementById("xauusd-chart-canvas");
    if (!canvas || !chartData || !chartData.candles || chartData.candles.length === 0) return;

    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;

    ctx.clearRect(0, 0, width, height);

    const candles = chartData.candles;
    let minPrice = Infinity;
    let maxPrice = -Infinity;

    candles.forEach(c => {
        if (c.low < minPrice) minPrice = c.low;
        if (c.high > maxPrice) maxPrice = c.high;
    });

    const padding = (maxPrice - minPrice) * 0.1 || 2.0;
    minPrice -= padding;
    maxPrice += padding;

    const getY = p => height - ((p - minPrice) / (maxPrice - minPrice)) * height;
    const step = width / candles.length;
    const candleWidth = Math.max(3, step * 0.65);

    // Draw Liquidity Overlays
    if (chartData.liquidity_overlays) {
        chartData.liquidity_overlays.forEach(ov => {
            const yHigh = getY(ov.range_high || (ov.price + 2));
            const yLow = getY(ov.range_low || (ov.price - 2));
            const bandHeight = Math.max(3, yLow - yHigh);

            ctx.fillStyle = ov.color || "rgba(245, 158, 11, 0.15)";
            ctx.fillRect(0, yHigh, width, bandHeight);

            ctx.strokeStyle = ov.border_color || "#f59e0b";
            ctx.lineWidth = 1;
            ctx.strokeRect(0, yHigh, width, bandHeight);
        });
    }

    // Draw Candlesticks
    candles.forEach((c, idx) => {
        const x = idx * step + (step / 2);
        const yOpen = getY(c.open);
        const yClose = getY(c.close);
        const yHigh = getY(c.high);
        const yLow = getY(c.low);

        const isBull = c.close >= c.open;
        const color = isBull ? "#10b981" : "#f43f5e";

        // Wick
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(x, yHigh);
        ctx.lineTo(x, yLow);
        ctx.stroke();

        // Body
        ctx.fillStyle = color;
        const topY = Math.min(yOpen, yClose);
        const bodyH = Math.max(2, Math.abs(yClose - yOpen));
        ctx.fillRect(x - (candleWidth / 2), topY, candleWidth, bodyH);
    });

    // Draw Spot Price Line
    if (chartData.current_price) {
        const curY = getY(chartData.current_price);
        ctx.strokeStyle = "#f59e0b";
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(0, curY);
        ctx.lineTo(width, curY);
        ctx.stroke();
        ctx.setLineDash([]);

        // Label
        ctx.fillStyle = "#f59e0b";
        ctx.font = "bold 10px 'JetBrains Mono'";
        ctx.fillText(`$${chartData.current_price.toFixed(2)}`, width - 65, curY - 4);
    }
}

/* ==============================================================================
   7. SETTINGS & TELEGRAM DRAWER CONTROLLER
   ============================================================================== */
function initSettingsDrawer() {
    const btnOpen = document.getElementById("btn-open-settings");
    const btnClose = document.getElementById("btn-close-drawer");
    const overlay = document.getElementById("settings-drawer-overlay");
    const drawer = document.getElementById("settings-drawer");

    const toggleDrawer = (open) => {
        overlay?.classList.toggle("active", open);
        drawer?.classList.toggle("active", open);
        if (open) loadConfigIntoDrawer();
    };

    btnOpen?.addEventListener("click", () => toggleDrawer(true));
    btnClose?.addEventListener("click", () => toggleDrawer(false));
    overlay?.addEventListener("click", () => toggleDrawer(false));

    // Save settings
    const btnSave = document.getElementById("btn-save-drawer-settings");
    if (btnSave) {
        btnSave.addEventListener("click", async () => {
            const payload = {
                TELEGRAM_BOT_TOKEN: document.getElementById("cfg-tg-token")?.value.trim(),
                TELEGRAM_CHAT_ID: document.getElementById("cfg-tg-chatid")?.value.trim(),
                TELEGRAM_ALERTS_ENABLED: document.getElementById("cfg-tg-enable")?.checked,
                AI_PRIORITY: document.getElementById("cfg-ai-provider")?.value,
                GEMINI_API_KEY: document.getElementById("cfg-gemini-key")?.value.trim(),
                ANALYSIS_INTERVAL_SECONDS: parseInt(document.getElementById("cfg-sync-interval")?.value || "10")
            };

            const statusEl = document.getElementById("drawer-status-msg");
            if (statusEl) statusEl.textContent = "Saving...";

            try {
                const res = await fetch("/api/config", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.status === "SUCCESS") {
                    if (statusEl) statusEl.textContent = "✅ Applied successfully!";
                    currentRefreshRate = payload.ANALYSIS_INTERVAL_SECONDS;
                    setupAutoRefresh(currentRefreshRate);
                    showToast("Settings updated!");
                    setTimeout(() => toggleDrawer(false), 800);
                } else {
                    if (statusEl) statusEl.textContent = "❌ Failed to save.";
                }
            } catch (e) {
                if (statusEl) statusEl.textContent = "❌ Network error.";
            }
        });
    }

    // Test Telegram message
    const btnTestTg = document.getElementById("btn-test-telegram");
    if (btnTestTg) {
        btnTestTg.addEventListener("click", async () => {
            btnTestTg.textContent = "Sending...";
            try {
                const res = await fetch("/api/test-telegram", { method: "POST" });
                const data = await res.json();
                if (data.status === "SUCCESS") {
                    showToast("✅ Telegram message sent successfully!");
                } else {
                    showToast(`❌ Telegram error: ${data.message}`);
                }
            } catch (e) {
                showToast("❌ Network error connecting to Telegram.");
            } finally {
                btnTestTg.textContent = "📨 Send Test Telegram Message";
            }
        });
    }
}

async function loadConfigIntoDrawer() {
    try {
        const res = await fetch("/api/config");
        if (!res.ok) return;
        const cfg = await res.json();

        const tgToken = document.getElementById("cfg-tg-token");
        const tgChat = document.getElementById("cfg-tg-chatid");
        const tgEnable = document.getElementById("cfg-tg-enable");
        const aiProv = document.getElementById("cfg-ai-provider");
        const syncInt = document.getElementById("cfg-sync-interval");

        if (tgToken) tgToken.placeholder = cfg.telegram_token_masked || "123456:ABC-DEF...";
        if (tgChat && cfg.telegram_chat_id) tgChat.value = cfg.telegram_chat_id;
        if (tgEnable) tgEnable.checked = cfg.telegram_alerts_enabled;
        if (aiProv && cfg.ai_priority) aiProv.value = cfg.ai_priority;
        if (syncInt && cfg.analysis_interval_seconds) syncInt.value = cfg.analysis_interval_seconds;
    } catch (e) {
        console.debug("Config load error:", e);
    }
}

/* ==============================================================================
   8. NOTIFICATION HELPERS
   ============================================================================== */
function showBreakingBanner(headline) {
    const banner = document.getElementById("breaking-banner");
    const text = document.getElementById("breaking-headline");
    if (banner && text) {
        text.textContent = headline;
        banner.style.display = "flex";
    }
}

function showToast(msg) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = msg;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function formatTimeAgo(isoStr) {
    if (!isoStr) return "Just now";
    try {
        const date = new Date(isoStr);
        const diffMs = Date.now() - date.getTime();
        const mins = Math.floor(diffMs / 60000);
        if (mins < 1) return "Just now";
        if (mins < 60) return `${mins}m ago`;
        const hrs = Math.floor(mins / 60);
        if (hrs < 24) return `${hrs}h ago`;
        return `${Math.floor(hrs / 24)}d ago`;
    } catch {
        return "Recent";
    }
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
