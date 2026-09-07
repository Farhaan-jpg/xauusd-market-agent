/**
 * XAUUSD AI AGENT — CLIENT DASHBOARD CONTROLLER
 * Minimal, ultra-responsive, real-time news capture & analysis updater.
 */

let refreshIntervalId = null;
let currentRefreshRate = 10; // seconds
let knownNewsFingerprints = new Set();

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initSessions();
    initRadarSubNav();
    initVerticalChart();
    initActionButtons();
    initSettingsDrawer();
    
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
        const [reportRes, marketRes, newsRes, macroRes, liqRes, calRes, geoRes, cotRes] = await Promise.allSettled([
            fetch("/api/latest-report").then(r => r.json()),
            fetch("/api/market-data").then(r => r.json()),
            fetch("/api/news").then(r => r.json()),
            fetch("/api/macro").then(r => r.json()),
            fetch("/api/liquidity").then(r => r.json()),
            fetch("/api/economic-calendar").then(r => r.json()),
            fetch("/api/geopolitics").then(r => r.json()),
            fetch("/api/institutional-flow").then(r => r.json())
        ]);

        if (reportRes.status === "fulfilled") updateExecutiveReport(reportRes.value);
        if (marketRes.status === "fulfilled") updateMarketData(marketRes.value);
        if (newsRes.status === "fulfilled") updateNewsStream(newsRes.value);
        if (macroRes.status === "fulfilled") updateMacroData(macroRes.value);
        if (liqRes.status === "fulfilled") updateLiquidityData(liqRes.value);
        if (calRes.status === "fulfilled") updateCalendarData(calRes.value);
        if (geoRes.status === "fulfilled") updateGeopolitics(geoRes.value);
        if (cotRes.status === "fulfilled") updateInstitutionalFlow(cotRes.value);

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

    // Actionable Trading Posture Flag
    const postureEl = document.getElementById("hero-action-posture");
    const postureIcon = document.getElementById("hero-posture-icon");
    const postureText = document.getElementById("hero-posture-text");
    if (postureEl && postureText) {
        if (conf < 60 || dir === "NEUTRAL") {
            postureEl.className = "action-posture-badge wait";
            if (postureIcon) postureIcon.textContent = "⚠️";
            postureText.textContent = "TACTICAL POSTURE: WAIT / CONSOLIDATION (Low Conviction — Liquidity Defense)";
        } else if (dir.includes("BULL")) {
            postureEl.className = "action-posture-badge long";
            if (postureIcon) postureIcon.textContent = "🚀";
            postureText.textContent = `TACTICAL POSTURE: ACTIVE LONG CONVICTION (${conf}% Conviction — Target Overhead Supply Liquidity)`;
        } else {
            postureEl.className = "action-posture-badge short";
            if (postureIcon) postureIcon.textContent = "🔻";
            postureText.textContent = `TACTICAL POSTURE: ACTIVE SHORT CONVICTION (${conf}% Conviction — Target Underlying Demand Liquidity)`;
        }
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
    if (priceEl && data.price !== undefined) {
        const p = Number(data.price);
        const decStr = p.toString().split('.')[1] || "";
        priceEl.textContent = decStr.length > 2 ? p.toFixed(3) : p.toFixed(2);
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

    if (lowEl && data.low_24h !== undefined) {
        const l = Number(data.low_24h);
        lowEl.textContent = l >= 1000 ? l.toFixed(1) : l.toFixed(2);
    }
    if (highEl && data.high_24h !== undefined) {
        const h = Number(data.high_24h);
        highEl.textContent = h >= 1000 ? h.toFixed(1) : h.toFixed(2);
    }

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

    // US 10-Year Yield
    const us10yVal = data.us_10y_yield?.value !== undefined ? data.us_10y_yield.value : 
                     data.us10y?.yield_pct !== undefined ? data.us10y.yield_pct : 
                     data.us10y?.price !== undefined ? data.us10y.price : 4.78;
    const us10yChg = data.us_10y_yield?.change_pct !== undefined ? data.us_10y_yield.change_pct : 
                     data.us10y?.change_pct || 0.0;
    const us10yBias = data.us_10y_yield?.gold_bias || (us10yChg < 0 ? "BULLISH" : us10yChg > 0 ? "BEARISH" : "NEUTRAL");

    const el10y = document.getElementById("macro-us10y-val");
    if (el10y) el10y.textContent = `${Number(us10yVal).toFixed(2)}%`;
    const badge10y = document.getElementById("macro-us10y-bias");
    if (badge10y) {
        badge10y.textContent = us10yBias;
        badge10y.className = `macro-badge ${us10yBias === 'BULLISH' ? 'bull' : us10yBias === 'BEARISH' ? 'bear' : ''}`;
    }

    // US Dollar Index (DXY)
    const dxyVal = data.dxy_index?.value !== undefined ? data.dxy_index.value :
                   data.dxy?.price !== undefined ? data.dxy.price : 99.16;
    const dxyChg = data.dxy_index?.change_pct !== undefined ? data.dxy_index.change_pct :
                   data.dxy?.change_pct || 0.0;
    const dxyBias = data.dxy_index?.gold_bias || (dxyChg < 0 ? "BULLISH" : dxyChg > 0 ? "BEARISH" : "NEUTRAL");

    const elDxy = document.getElementById("macro-dxy-val");
    if (elDxy) elDxy.textContent = Number(dxyVal).toFixed(2);
    const badgeDxy = document.getElementById("macro-dxy-bias");
    if (badgeDxy) {
        badgeDxy.textContent = dxyBias;
        badgeDxy.className = `macro-badge ${dxyBias === 'BULLISH' ? 'bull' : dxyBias === 'BEARISH' ? 'bear' : ''}`;
    }

    // Real Yields (TIPS)
    const tipsVal = data.tips_real_yield?.value !== undefined ? data.tips_real_yield.value :
                    Number(us10yVal - 2.15).toFixed(2);
    const tipsChg = data.tips_real_yield?.change_pct !== undefined ? data.tips_real_yield.change_pct :
                    data.tip?.change_pct || 0.0;
    const tipsBias = data.tips_real_yield?.gold_bias || (tipsChg > 0 ? "BULLISH" : "NEUTRAL");

    const elTips = document.getElementById("macro-tips-val");
    if (elTips) elTips.textContent = `${Number(tipsVal).toFixed(2)}%`;
    const badgeTips = document.getElementById("macro-tips-bias");
    if (badgeTips) {
        badgeTips.textContent = tipsBias;
        badgeTips.className = `macro-badge ${tipsBias === 'BULLISH' ? 'bull' : 'neutral'}`;
    }

    // VIX Index
    const vixVal = data.vix_index?.value !== undefined ? data.vix_index.value :
                   data.vix?.price !== undefined ? data.vix.price : 14.53;
    const elVix = document.getElementById("macro-vix-val");
    if (elVix) elVix.textContent = Number(vixVal).toFixed(2);
    const badgeVix = document.getElementById("macro-vix-bias");
    if (badgeVix) {
        badgeVix.textContent = vixVal > 20 ? "ELEVATED" : "NORMAL";
        badgeVix.className = `macro-badge ${vixVal > 20 ? 'bull' : ''}`;
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

function updateInstitutionalFlow(data) {
    if (!data) return;

    // Badge
    const biasBadge = document.getElementById("cot-bias-badge");
    if (biasBadge && data.institutional_bias) {
        const isAcc = data.institutional_bias.includes("ACCUMULATION");
        const isLiq = data.institutional_bias.includes("LIQUIDATION");
        biasBadge.textContent = data.bias_label || (isAcc ? "SMART-MONEY ACCUMULATION" : isLiq ? "HEAVY LIQUIDATION" : "BALANCED POSITIONING");
        biasBadge.className = `badge-neutral ${isAcc ? 'bull' : isLiq ? 'bear' : ''}`;
    }

    // Hedge fund net position
    const netEl = document.getElementById("cot-net-contracts");
    const ratioEl = document.getElementById("cot-ratio");
    if (data.managed_money) {
        const net = data.managed_money.net_contracts || 0;
        const sign = net > 0 ? "+" : "";
        if (netEl) netEl.textContent = `${sign}${(net / 1000).toFixed(1)}k Contracts`;
        if (ratioEl && data.managed_money.long_short_ratio) {
            ratioEl.textContent = `L/S Ratio: ${Number(data.managed_money.long_short_ratio).toFixed(1)}x`;
        }
    }

    // Central bank run rate
    const cbPaceEl = document.getElementById("cot-cb-pace");
    const cbBanksEl = document.getElementById("cot-top-banks");
    if (data.central_banks) {
        const annualPace = data.central_banks.annual_pace_tonnes || data.central_banks.annualized_demand_tonnes || 
                           (data.central_banks.quarterly_pace_tonnes ? data.central_banks.quarterly_pace_tonnes * 4 : 1140);
        if (cbPaceEl) {
            cbPaceEl.textContent = `${Math.round(annualPace)} T/yr`;
        }
        const buyers = data.central_banks.top_accumulators || data.central_banks.top_buyers || [];
        if (cbBanksEl && Array.isArray(buyers) && buyers.length > 0) {
            const shortNames = buyers.slice(0, 3).map(b => (b.country || "").split(' ')[0]).filter(Boolean).join(' • ');
            cbBanksEl.textContent = shortNames || "PBoC • RBI • NBP";
        }
    }

    // Historical Percentile
    const pctEl = document.getElementById("cot-percentile-val");
    if (pctEl && data.managed_money && data.managed_money.percentile_rank !== undefined) {
        const pct = Math.round(data.managed_money.percentile_rank);
        pctEl.textContent = `${pct}th Percentile (${pct >= 70 ? 'Bullish Dominance' : pct <= 30 ? 'Bearish' : 'Neutral'})`;
        pctEl.className = `geo-stat-val ${pct >= 70 ? 'color-green' : pct <= 30 ? 'color-red' : 'color-gold'}`;
    }

    // Narrative
    const sumEl = document.getElementById("cot-summary-text");
    const narrativeText = data.narrative || data.summary_statement || data.summary;
    if (sumEl && narrativeText) {
        sumEl.textContent = narrativeText;
    }
}

let currentActiveRadarView = "view-horizontal";
let activeCandleTimeframe = "H1";
let cachedCandlesData = null;
let cachedLiquidityData = null;
let candleMousePos = null;

/* ==============================================================================
   4A. RADAR SUB-NAVIGATION & MULTI-CHART CONTROLLER
   ============================================================================== */
function initRadarSubNav() {
    const subButtons = document.querySelectorAll(".radar-sub-btn");
    const subPanels = document.querySelectorAll(".radar-view-panel");

    subButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetView = btn.getAttribute("data-view");
            currentActiveRadarView = targetView;

            subButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            subPanels.forEach(panel => {
                panel.classList.toggle("active", panel.id === targetView);
            });

            if (targetView === "view-vertical") {
                loadAndRenderVerticalCandles(activeCandleTimeframe);
            } else if (targetView === "view-horizontal" && cachedLiquidityData) {
                const liveDomPrice = parseFloat(document.getElementById("live-gold-price")?.textContent) || null;
                const curPrice = cachedLiquidityData.current_price || liveDomPrice || 4430.00;
                renderHorizontalProfile(cachedLiquidityData.horizontal_profile, curPrice);
            }
        });
    });
}

/* ==============================================================================
   4B. HORIZONTAL LIQUIDITY DEPTH PROFILE
   ============================================================================== */
function renderHorizontalProfile(profile, curPrice) {
    const container = document.getElementById("horizontal-profile-chart");
    if (!container) return;

    if (!Array.isArray(profile) || profile.length === 0) {
        // Fallback synthetic profile centered on curPrice
        profile = [];
        for (let i = 12; i >= -12; i--) {
            const p = curPrice + (i * 4.0);
            const isAbove = i > 0;
            const str = Math.min(96, Math.max(35, Math.round(50 + Math.abs(i) * 3.5 + Math.sin(i * 1.5) * 15)));
            profile.push({
                price: p,
                label: `$${p.toFixed(1)}`,
                type: isAbove ? (i > 6 ? "SUPPLY_WALL" : "FAIR_VALUE_GAP") : (i < -6 ? "DEMAND_WALL" : "FAIR_VALUE_GAP"),
                strength: str,
                volume_weight: (str / 50).toFixed(2),
                distance_pts: Math.abs(p - curPrice).toFixed(1),
                is_above: isAbove
            });
        }
    }

    // Sort buckets top to bottom (descending by price)
    const sorted = [...profile].sort((a, b) => b.price - a.price);

    let html = `<div class="profile-ladder-grid">`;
    let spotInserted = false;

    sorted.forEach(b => {
        // Insert spot marker when crossing current price
        if (!spotInserted && b.price <= curPrice) {
            html += `
                <div class="profile-spot-laser-row">
                    <div class="laser-line-left"></div>
                    <div class="laser-spot-pill">
                        <span class="laser-icon">📍</span>
                        <span class="laser-label">LIVE SPOT:</span>
                        <span class="laser-price">$${curPrice.toFixed(2)}</span>
                    </div>
                    <div class="laser-line-right"></div>
                </div>
            `;
            spotInserted = true;
        }

        const isAbove = b.price > curPrice;
        const dist = Math.abs(b.price - curPrice).toFixed(1);
        const strength = Math.round(b.strength || 65);
        const barCls = isAbove ? "supply-bar" : "demand-bar";
        const typeLabel = (b.type || (isAbove ? "SUPPLY POOL" : "DEMAND POOL")).replace(/_/g, " ");

        html += `
            <div class="profile-bucket-row ${isAbove ? 'overhead' : 'underlying'}" 
                 data-price="${b.price.toFixed(2)}" 
                 data-type="${escapeHtml(typeLabel)}" 
                 data-strength="${strength}" 
                 data-dist="${dist}" 
                 data-weight="${b.volume_weight || '1.0'}">
                <div class="bucket-price-col">
                    <span class="bucket-price">$${Number(b.price).toFixed(2)}</span>
                    <span class="bucket-dist">${isAbove ? '+' : '-'}${dist} pts</span>
                </div>
                <div class="bucket-bar-track">
                    <div class="bucket-bar-fill ${barCls}" style="width: ${strength}%;">
                        <span class="bar-fill-text">${strength}% Depth</span>
                    </div>
                </div>
                <div class="bucket-meta-col">
                    <span class="bucket-type-tag ${isAbove ? 'tag-supply' : 'tag-demand'}">${escapeHtml(typeLabel)}</span>
                    <span class="bucket-vol-weight">x${b.volume_weight || '1.0'} vol</span>
                </div>
            </div>
        `;
    });

    if (!spotInserted) {
        html += `
            <div class="profile-spot-laser-row">
                <div class="laser-line-left"></div>
                <div class="laser-spot-pill">
                    <span class="laser-icon">📍</span>
                    <span class="laser-label">LIVE SPOT:</span>
                    <span class="laser-price">$${curPrice.toFixed(2)}</span>
                </div>
                <div class="laser-line-right"></div>
            </div>
        `;
    }

    html += `</div>`;
    container.innerHTML = html;
}

/* ==============================================================================
   4C. VERTICAL CANDLESTICK & LIQUIDITY ZONE RADAR
   ============================================================================== */
function initVerticalChart() {
    const tfButtons = document.querySelectorAll(".tf-btn");
    tfButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tfButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activeCandleTimeframe = btn.getAttribute("data-tf") || "H1";
            loadAndRenderVerticalCandles(activeCandleTimeframe);
        });
    });

    const canvas = document.getElementById("vertical-candle-canvas");
    if (canvas) {
        canvas.addEventListener("mousemove", (e) => {
            const rect = canvas.getBoundingClientRect();
            candleMousePos = {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top,
                canvasWidth: rect.width,
                canvasHeight: rect.height
            };
            if (cachedCandlesData) {
                drawCandlestickCanvas(cachedCandlesData);
            }
        });

        canvas.addEventListener("mouseleave", () => {
            candleMousePos = null;
            const tooltip = document.getElementById("candle-tooltip");
            if (tooltip) tooltip.style.display = "none";
            if (cachedCandlesData) {
                drawCandlestickCanvas(cachedCandlesData);
            }
        });

        window.addEventListener("resize", () => {
            if (currentActiveRadarView === "view-vertical" && cachedCandlesData) {
                drawCandlestickCanvas(cachedCandlesData);
            }
        });
    }
}

async function loadAndRenderVerticalCandles(tf) {
    try {
        const res = await fetch(`/api/candles?timeframe=${tf || activeCandleTimeframe}`);
        if (!res.ok) return;
        const data = await res.json();
        cachedCandlesData = data;
        drawCandlestickCanvas(data);
    } catch (e) {
        console.debug("Failed to load candles:", e);
    }
}

function drawCandlestickCanvas(data) {
    const canvas = document.getElementById("vertical-candle-canvas");
    if (!canvas || !data || !Array.isArray(data.candles) || data.candles.length === 0) return;

    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const width = rect.width || 860;
    const height = rect.height || 360;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.resetTransform();
    ctx.scale(dpr, dpr);

    // Padding
    const padTop = 20;
    const padBottom = 35;
    const padLeft = 15;
    const padRight = 75; // for price axis

    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    // Determine min/max price
    const candles = data.candles;
    let minPrice = Infinity;
    let maxPrice = -Infinity;

    candles.forEach(c => {
        if (c.low < minPrice) minPrice = c.low;
        if (c.high > maxPrice) maxPrice = c.high;
    });

    const overlays = Array.isArray(data.liquidity_overlays) ? data.liquidity_overlays : [];
    overlays.forEach(ov => {
        if (ov.range_low && ov.range_low < minPrice) minPrice = ov.range_low;
        if (ov.range_high && ov.range_high > maxPrice) maxPrice = ov.range_high;
        if (ov.price && ov.price < minPrice) minPrice = ov.price;
        if (ov.price && ov.price > maxPrice) maxPrice = ov.price;
    });

    const curPrice = data.current_price || (candles[candles.length - 1] ? candles[candles.length - 1].close : 4430.0);
    if (curPrice < minPrice) minPrice = curPrice;
    if (curPrice > maxPrice) maxPrice = curPrice;

    // Add 3% buffer
    const priceSpan = (maxPrice - minPrice) || 10;
    minPrice -= priceSpan * 0.05;
    maxPrice += priceSpan * 0.05;

    const priceToY = (p) => padTop + plotH - ((p - minPrice) / (maxPrice - minPrice)) * plotH;
    const yToPrice = (y) => minPrice + ((padTop + plotH - y) / plotH) * (maxPrice - minPrice);

    // 1. Background
    ctx.fillStyle = "#0a0d14";
    ctx.fillRect(0, 0, width, height);

    // 2. Horizontal Grid Lines & Price Axis
    const numGridLines = 6;
    ctx.textAlign = "left";
    ctx.font = "10px JetBrains Mono, monospace";

    for (let i = 0; i <= numGridLines; i++) {
        const y = padTop + (plotH / numGridLines) * i;
        const p = yToPrice(y);

        ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(padLeft, y);
        ctx.lineTo(width - padRight, y);
        ctx.stroke();

        ctx.fillStyle = "rgba(255, 255, 255, 0.35)";
        ctx.fillText(`$${p.toFixed(1)}`, width - padRight + 8, y + 3);
    }
    ctx.setLineDash([]);

    // 3. Liquidity Zone Overlays
    overlays.forEach(ov => {
        const topY = priceToY(ov.range_high || ov.price + 2.0);
        const botY = priceToY(ov.range_low || ov.price - 2.0);
        const boxH = Math.max(4, botY - topY);

        ctx.fillStyle = ov.color || "rgba(244, 63, 94, 0.15)";
        ctx.fillRect(padLeft, topY, plotW, boxH);

        ctx.strokeStyle = ov.border_color || "rgba(244, 63, 94, 0.4)";
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);
        ctx.strokeRect(padLeft, topY, plotW, boxH);
        ctx.setLineDash([]);

        // Zone Tag
        ctx.fillStyle = ov.border_color || "#f43f5e";
        ctx.font = "9px Inter, sans-serif";
        ctx.fillText(ov.title || ov.type, padLeft + 6, topY + Math.min(boxH - 2, 11));
    });

    // 4. Candlesticks
    const barCount = candles.length;
    const barWidth = Math.max(3, (plotW / barCount) * 0.7);
    const barSpacing = plotW / barCount;

    candles.forEach((c, idx) => {
        const x = padLeft + (idx * barSpacing) + (barSpacing / 2);
        const isBull = c.close >= c.open;
        const color = isBull ? "#10b981" : "#f43f5e";

        // High-Low Wick
        const yHigh = priceToY(c.high);
        const yLow = priceToY(c.low);

        ctx.strokeStyle = color;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(x, yHigh);
        ctx.lineTo(x, yLow);
        ctx.stroke();

        // Open-Close Body
        const yOpen = priceToY(c.open);
        const yClose = priceToY(c.close);
        const bodyTop = Math.min(yOpen, yClose);
        const bodyH = Math.max(2, Math.abs(yOpen - yClose));

        ctx.fillStyle = color;
        ctx.fillRect(x - (barWidth / 2), bodyTop, barWidth, bodyH);
    });

    // 5. Time Axis (Bottom)
    ctx.fillStyle = "rgba(255, 255, 255, 0.35)";
    ctx.font = "9px JetBrains Mono, monospace";
    ctx.textAlign = "center";
    const timeStep = Math.max(1, Math.floor(barCount / 6));

    for (let i = 0; i < barCount; i += timeStep) {
        const c = candles[i];
        if (!c || !c.time) continue;
        const x = padLeft + (i * barSpacing) + (barSpacing / 2);
        const d = new Date(c.time * 1000);
        const timeStr = `${d.getUTCHours().toString().padStart(2, '0')}:${d.getUTCMinutes().toString().padStart(2, '0')}`;
        ctx.fillText(timeStr, x, height - 10);
    }

    // 6. Live Spot Laser Line & Right Badge
    const spotY = priceToY(curPrice);
    if (spotY >= padTop && spotY <= padTop + plotH) {
        ctx.strokeStyle = "#f59e0b";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([5, 3]);
        ctx.beginPath();
        ctx.moveTo(padLeft, spotY);
        ctx.lineTo(width - padRight, spotY);
        ctx.stroke();
        ctx.setLineDash([]);

        // Gold Badge
        ctx.fillStyle = "#f59e0b";
        ctx.fillRect(width - padRight + 2, spotY - 9, padRight - 6, 18);
        ctx.fillStyle = "#000000";
        ctx.font = "bold 9px JetBrains Mono, monospace";
        ctx.textAlign = "center";
        ctx.fillText(`$${curPrice.toFixed(2)}`, width - (padRight / 2), spotY + 3);
    }

    // 7. Interactive Crosshair & Tooltip
    if (candleMousePos && candleMousePos.x >= padLeft && candleMousePos.x <= width - padRight && candleMousePos.y >= padTop && candleMousePos.y <= padTop + plotH) {
        const mx = candleMousePos.x;
        const my = candleMousePos.y;

        // Draw crosshair lines
        ctx.strokeStyle = "rgba(255, 255, 255, 0.4)";
        ctx.lineWidth = 0.8;
        ctx.setLineDash([2, 2]);

        ctx.beginPath();
        ctx.moveTo(mx, padTop);
        ctx.lineTo(mx, padTop + plotH);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(padLeft, my);
        ctx.lineTo(width - padRight, my);
        ctx.stroke();
        ctx.setLineDash([]);

        // Hover price pill on Y axis
        const hoverPrice = yToPrice(my);
        ctx.fillStyle = "#3b82f6";
        ctx.fillRect(width - padRight + 2, my - 8, padRight - 6, 16);
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 9px JetBrains Mono, monospace";
        ctx.textAlign = "center";
        ctx.fillText(`$${hoverPrice.toFixed(2)}`, width - (padRight / 2), my + 3);

        // Find nearest candle
        const candleIdx = Math.min(barCount - 1, Math.max(0, Math.floor((mx - padLeft) / barSpacing)));
        const hoveredCandle = candles[candleIdx];

        if (hoveredCandle) {
            const tooltip = document.getElementById("candle-tooltip");
            if (tooltip) {
                const isBull = hoveredCandle.close >= hoveredCandle.open;
                const d = new Date(hoveredCandle.time * 1000);
                tooltip.style.display = "block";
                tooltip.style.left = `${Math.min(width - 200, Math.max(20, mx + 15))}px`;
                tooltip.style.top = `${Math.min(height - 110, Math.max(10, my - 30))}px`;
                tooltip.innerHTML = `
                    <div class="tt-time">${d.toUTCString().slice(5, 22)} UTC</div>
                    <div class="tt-row"><span>Open:</span> <b>$${hoveredCandle.open.toFixed(2)}</b></div>
                    <div class="tt-row"><span>High:</span> <b class="color-green">$${hoveredCandle.high.toFixed(2)}</b></div>
                    <div class="tt-row"><span>Low:</span> <b class="color-red">$${hoveredCandle.low.toFixed(2)}</b></div>
                    <div class="tt-row"><span>Close:</span> <b class="${isBull ? 'color-green' : 'color-red'}">$${hoveredCandle.close.toFixed(2)}</b></div>
                `;
            }
        }
    }
}

/* ==============================================================================
   4D. MAIN LIQUIDITY UPDATER
   ============================================================================== */
function updateLiquidityData(data) {
    if (!data) return;
    cachedLiquidityData = data;

    const liveDomPrice = parseFloat(document.getElementById("live-gold-price")?.textContent) || null;
    const curPrice = data.current_price || liveDomPrice || 4430.00;
    
    // Depth Ratio Bar
    const bidPct = data.demand_depth_pct || 54;
    const askPct = data.supply_depth_pct || (100 - bidPct);
    
    const bidPctEl = document.getElementById("liq-bid-pct");
    const askPctEl = document.getElementById("liq-ask-pct");
    const bidFillEl = document.getElementById("liq-bid-fill");
    const askFillEl = document.getElementById("liq-ask-fill");
    const imbTagEl = document.getElementById("liq-imbalance-ratio-tag");

    if (bidPctEl) bidPctEl.textContent = `${bidPct}%`;
    if (askPctEl) askPctEl.textContent = `${askPct}%`;
    if (bidFillEl) bidFillEl.style.width = `${bidPct}%`;
    if (askFillEl) askFillEl.style.width = `${askPct}%`;
    if (imbTagEl) {
        imbTagEl.textContent = bidPct > askPct ? "Net Institutional Accumulation" : "Net Institutional Distribution";
    }

    // Render Horizontal Profile
    renderHorizontalProfile(data.horizontal_profile, curPrice);

    // If Vertical Radar is active, update candles or current price
    if (currentActiveRadarView === "view-vertical" && cachedCandlesData) {
        cachedCandlesData.current_price = curPrice;
        drawCandlestickCanvas(cachedCandlesData);
    }

    // Spot Price Anchor in Ladder
    const spotEl = document.getElementById("ladder-spot-price");
    if (spotEl) {
        const decStr = curPrice.toString().split('.')[1] || "";
        spotEl.textContent = `$${decStr.length > 2 ? curPrice.toFixed(3) : curPrice.toFixed(2)}`;
    }

    // Orderflow Bias Pill
    const biasPill = document.getElementById("liq-orderflow-bias");
    const biasText = document.getElementById("liq-orderflow-text");
    if (biasPill && biasText) {
        const isBull = data.order_flow_bias !== "BEARISH_ORDER_FLOW";
        biasPill.className = `orderflow-bias-pill ${isBull ? '' : 'bearish'}`;
        biasText.textContent = isBull ? "BULLISH ORDER-FLOW" : "BEARISH ORDER-FLOW";
    }

    // Supply items (Above Price)
    const supplyList = document.getElementById("ladder-supply-items");
    if (supplyList && Array.isArray(data.liquidity_above)) {
        if (data.liquidity_above.length === 0) {
            supplyList.innerHTML = `<div class="empty-state-mini">No overhead supply pools detected.</div>`;
        } else {
            supplyList.innerHTML = data.liquidity_above.map(z => {
                const dist = Math.abs(z.price - curPrice).toFixed(1);
                const strength = Math.round(z.strength || 85);
                return `
                    <div class="ladder-row">
                        <div class="ladder-depth-bar" style="width: ${strength}%;"></div>
                        <div class="ladder-left">
                            <span class="ladder-price">$${Number(z.price).toFixed(2)}</span>
                            <span class="ladder-dist">+${dist} pts</span>
                        </div>
                        <div class="ladder-mid">
                            <span class="ladder-type-name">${escapeHtml(z.type.replace(/_/g, ' '))}</span>
                            <span class="ladder-sub-detail">${escapeHtml(z.sweep_risk || 'Resistance Pool')} • ${z.timeframe || 'H1'}</span>
                        </div>
                        <div class="ladder-right">
                            <span class="ladder-strength-badge">${strength}% Depth</span>
                        </div>
                    </div>
                `;
            }).join("");
        }
    }

    // Demand items (Below Price)
    const demandList = document.getElementById("ladder-demand-items");
    if (demandList && Array.isArray(data.liquidity_below)) {
        if (data.liquidity_below.length === 0) {
            demandList.innerHTML = `<div class="empty-state-mini">No resting demand pools detected.</div>`;
        } else {
            demandList.innerHTML = data.liquidity_below.map(z => {
                const dist = Math.abs(curPrice - z.price).toFixed(1);
                const strength = Math.round(z.strength || 85);
                return `
                    <div class="ladder-row">
                        <div class="ladder-depth-bar" style="width: ${strength}%;"></div>
                        <div class="ladder-left">
                            <span class="ladder-price">$${Number(z.price).toFixed(2)}</span>
                            <span class="ladder-dist">-${dist} pts</span>
                        </div>
                        <div class="ladder-mid">
                            <span class="ladder-type-name">${escapeHtml(z.type.replace(/_/g, ' '))}</span>
                            <span class="ladder-sub-detail">${escapeHtml(z.sweep_risk || 'Support Pool')} • ${z.timeframe || 'H1'}</span>
                        </div>
                        <div class="ladder-right">
                            <span class="ladder-strength-badge">${strength}% Depth</span>
                        </div>
                    </div>
                `;
            }).join("");
        }
    }

    // 3 Intelligence Metric Boxes
    const immRes = document.getElementById("liq-imm-res");
    const resDist = document.getElementById("liq-res-dist");
    if (immRes && data.immediate_resistance) {
        immRes.textContent = `$${Number(data.immediate_resistance).toFixed(2)}`;
        if (resDist) resDist.textContent = `+${Math.abs(data.immediate_resistance - curPrice).toFixed(1)} pts away`;
    }

    const immSup = document.getElementById("liq-imm-sup");
    const supDist = document.getElementById("liq-sup-dist");
    if (immSup && data.immediate_support) {
        immSup.textContent = `$${Number(data.immediate_support).toFixed(2)}`;
        if (supDist) supDist.textContent = `-${Math.abs(curPrice - data.immediate_support).toFixed(1)} pts away`;
    }

    const imbVal = document.getElementById("liq-imbalance-val");
    if (imbVal) {
        imbVal.textContent = data.order_flow_bias === "BULLISH_ORDER_FLOW" ? `+${bidPct}% Buy Depth` : `-${askPct}% Sell Pressure`;
        imbVal.className = `intel-val ${data.order_flow_bias === "BULLISH_ORDER_FLOW" ? 'color-green' : 'color-red'}`;
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
   6. SETTINGS & TELEGRAM DRAWER CONTROLLER
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
                GEMINI_MODEL: document.getElementById("cfg-gemini-model")?.value.trim(),
                OPENROUTER_API_KEY: document.getElementById("cfg-openrouter-key")?.value.trim(),
                OPENROUTER_MODEL: document.getElementById("cfg-openrouter-model")?.value.trim(),
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

    // Test AI connection
    const btnTestAi = document.getElementById("btn-test-ai");
    if (btnTestAi) {
        btnTestAi.addEventListener("click", async () => {
            const origText = btnTestAi.innerHTML;
            btnTestAi.innerHTML = `<span>⏳</span> Testing AI Engine...`;
            btnTestAi.disabled = true;
            try {
                const prov = document.getElementById("cfg-ai-provider")?.value || "gemini_first";
                const res = await fetch("/api/test-ai", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ provider: prov })
                });
                const data = await res.json();
                if (data.status === "SUCCESS") {
                    showToast(`✅ ${data.provider} Active (${data.latency_ms}ms)! Verdict: ${data.verdict}`);
                } else {
                    showToast(`⚠️ AI Warning: ${data.message || "Failed to reach model"}`);
                }
            } catch (e) {
                showToast("❌ Network error connecting to AI endpoint.");
            } finally {
                btnTestAi.innerHTML = origText;
                btnTestAi.disabled = false;
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
        const geminiKey = document.getElementById("cfg-gemini-key");
        const geminiModel = document.getElementById("cfg-gemini-model");
        const openrouterKey = document.getElementById("cfg-openrouter-key");
        const openrouterModel = document.getElementById("cfg-openrouter-model");
        const syncInt = document.getElementById("cfg-sync-interval");

        if (tgToken) tgToken.placeholder = cfg.telegram_token_masked || "123456:ABC-DEF...";
        if (tgChat && cfg.telegram_chat_id) tgChat.value = cfg.telegram_chat_id;
        if (tgEnable) tgEnable.checked = cfg.telegram_alerts_enabled;
        if (aiProv && cfg.ai_priority) aiProv.value = cfg.ai_priority;
        if (geminiKey) geminiKey.placeholder = cfg.gemini_key_masked || "AIzaSy... (Paste Google AI Studio key)";
        if (geminiModel && cfg.gemini_model) geminiModel.value = cfg.gemini_model;
        if (openrouterKey) openrouterKey.placeholder = cfg.openrouter_key_masked || "sk-or-v1-... (Paste OpenRouter key)";
        if (openrouterModel && cfg.openrouter_model) openrouterModel.value = cfg.openrouter_model;
        if (syncInt && cfg.analysis_interval_seconds) syncInt.value = cfg.analysis_interval_seconds;
    } catch (e) {
        console.debug("Config load error:", e);
    }
}

/* ==============================================================================
   7. NOTIFICATION HELPERS
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
