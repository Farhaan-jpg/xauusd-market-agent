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

            if (targetId === "tab-chart") {
                setTimeout(() => {
                    if (cachedLiquidityData) {
                        updateLiquidityData(cachedLiquidityData);
                    }
                }, 30);
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
        const [reportRes, marketRes, newsRes, macroRes, liqRes, calRes, geoRes, cotRes, setupsRes, regimeRes] = await Promise.allSettled([
            fetch("/api/latest-report").then(r => r.json()),
            fetch("/api/market-data").then(r => r.json()),
            fetch("/api/news").then(r => r.json()),
            fetch("/api/macro").then(r => r.json()),
            fetch("/api/liquidity").then(r => r.json()),
            fetch("/api/economic-calendar").then(r => r.json()),
            fetch("/api/geopolitics").then(r => r.json()),
            fetch("/api/institutional-flow").then(r => r.json()),
            fetch("/api/setups").then(r => r.json()),
            fetch("/api/regime").then(r => r.json())
        ]);

        if (reportRes.status === "fulfilled") updateExecutiveReport(reportRes.value);
        if (marketRes.status === "fulfilled") updateMarketData(marketRes.value);
        if (newsRes.status === "fulfilled") updateNewsStream(newsRes.value);
        if (macroRes.status === "fulfilled") updateMacroData(macroRes.value);
        if (liqRes.status === "fulfilled") updateLiquidityData(liqRes.value);
        if (calRes.status === "fulfilled") updateCalendarData(calRes.value);
        if (geoRes.status === "fulfilled") updateGeopolitics(geoRes.value);
        if (cotRes.status === "fulfilled") updateInstitutionalFlow(cotRes.value);
        if (setupsRes.status === "fulfilled") updateScalperSetups(setupsRes.value);
        if (regimeRes.status === "fulfilled") updateScalperRegime(regimeRes.value);

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
let cachedLiquidityData = null;

/* ==============================================================================
   4A. RADAR SUB-NAVIGATION CONTROLLER
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

            const liveDomPrice = parseFloat(document.getElementById("live-gold-price")?.textContent) || null;
            const curPrice = cachedLiquidityData?.current_price || liveDomPrice || 4430.00;

            if (targetView === "view-horizontal" && cachedLiquidityData) {
                renderHorizontalProfile(cachedLiquidityData.horizontal_profile, curPrice);
            } else if (targetView === "view-matrix" && cachedLiquidityData) {
                renderZonesMatrix(cachedLiquidityData, curPrice);
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
        const strength = Math.round(b.strength || b.volume_intensity || 65);
        const barCls = isAbove ? "supply-bar" : "demand-bar";
        const typeLabel = (b.type || b.zone_tag || (isAbove ? "SUPPLY WALL" : "DEMAND BLOCK")).replace(/_/g, " ");

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
   4C. INSTITUTIONAL ZONES MATRIX & ANALYTICS TABLE
   ============================================================================== */
function renderZonesMatrix(data, curPrice) {
    const tbody = document.getElementById("zones-matrix-tbody");
    if (!tbody || !data) return;

    const allAbove = Array.isArray(data.liquidity_above) ? data.liquidity_above : [];
    const allBelow = Array.isArray(data.liquidity_below) ? data.liquidity_below : [];
    const combined = [...allAbove, ...allBelow];

    if (combined.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #94a3b8; padding: 20px;">No active liquidity structures identified.</td></tr>`;
        return;
    }

    // Sort by price descending
    combined.sort((a, b) => b.price - a.price);

    tbody.innerHTML = combined.map(z => {
        const isAbove = z.price >= curPrice;
        const dist = Math.abs(z.price - curPrice).toFixed(1);
        const strength = Math.round(z.strength || 75);
        const tf = z.timeframe || "H1";
        const sideBadge = isAbove ? '<span style="color: #fda4af; font-weight: 700;">Overhead Supply</span>' : '<span style="color: #6ee7b7; font-weight: 700;">Resting Demand</span>';
        const sweepProb = strength >= 85 ? '<span style="color: #fb7185; font-weight: 700;">HIGH (85%+)</span>' : strength >= 65 ? '<span style="color: #fbbf24; font-weight: 700;">MODERATE (65%)</span>' : '<span style="color: #94a3b8;">LOW</span>';
        const tactical = isAbove ? 'Target for Buy-Side Stop Run & Reversal' : 'Support for Institutional Dip Buying';

        return `
            <tr>
                <td style="font-weight: 700; color: #ffffff;">${escapeHtml(z.type.replace(/_/g, ' '))}</td>
                <td style="font-family: var(--font-mono); font-weight: 700; color: #f59e0b;">$${Number(z.price).toFixed(2)} <span style="font-size: 0.68rem; color: #94a3b8;">(${isAbove ? '+' : '-'}${dist} pts)</span></td>
                <td>${sideBadge}</td>
                <td><span style="background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono); font-size: 0.7rem;">${tf}</span></td>
                <td>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="font-family: var(--font-mono); font-weight: 700;">${strength}%</span>
                        <div style="width: 50px; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; overflow: hidden;">
                            <div style="width: ${strength}%; height: 100%; background: ${isAbove ? '#f43f5e' : '#10b981'};"></div>
                        </div>
                    </div>
                </td>
                <td>${sweepProb}</td>
                <td style="color: #cbd5e1; font-size: 0.72rem;">${tactical}</td>
            </tr>
        `;
    }).join("");
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

    // Executive Order-Flow Narrative Report
    const summaryNarrativeEl = document.getElementById("liq-executive-summary-text");
    if (summaryNarrativeEl) {
        summaryNarrativeEl.textContent = data.order_flow_narrative || 
            `Order-flow structure indicates Net Institutional Accumulation (${bidPct}% Bid Depth vs ${askPct}% Ask). Active spot auction ($${curPrice.toFixed(2)}) is bounded between immediate overhead resistance and underlying demand defense.`;
    }

    // 4 Key Intelligence Metrics in Summary Header
    const immRes = document.getElementById("liq-imm-res");
    const resDist = document.getElementById("liq-res-dist");
    const nearestResVal = data.immediate_resistance || (data.liquidity_above && data.liquidity_above[0]?.price) || (curPrice + 14.5);
    if (immRes) {
        immRes.textContent = `$${Number(nearestResVal).toFixed(2)}`;
        if (resDist) resDist.textContent = `+${Math.abs(nearestResVal - curPrice).toFixed(1)} pts away`;
    }

    const immSup = document.getElementById("liq-imm-sup");
    const supDist = document.getElementById("liq-sup-dist");
    const nearestSupVal = data.immediate_support || (data.liquidity_below && data.liquidity_below[0]?.price) || (curPrice - 18.2);
    if (immSup) {
        immSup.textContent = `$${Number(nearestSupVal).toFixed(2)}`;
        if (supDist) supDist.textContent = `-${Math.abs(curPrice - nearestSupVal).toFixed(1)} pts away`;
    }

    const imbVal = document.getElementById("liq-imbalance-val");
    const imbSub = document.getElementById("liq-imbalance-sub");
    if (imbVal) {
        imbVal.textContent = `${bidPct}% Bid / ${askPct}% Ask`;
        imbVal.className = `intel-val ${bidPct >= askPct ? 'color-green' : 'color-red'}`;
        if (imbSub) imbSub.textContent = bidPct >= askPct ? "+ Net Buy Delta" : "- Net Sell Delta";
    }

    const sweepTargetEl = document.getElementById("liq-sweep-target");
    if (sweepTargetEl) {
        sweepTargetEl.textContent = `$${Number(nearestResVal).toFixed(2)}`;
    }

    // Render Horizontal Profile
    renderHorizontalProfile(data.horizontal_profile, curPrice);

    // Render Key Zones Matrix
    renderZonesMatrix(data, curPrice);

    // Orderflow Bias Pill
    const biasPill = document.getElementById("liq-orderflow-bias");
    const biasText = document.getElementById("liq-orderflow-text");
    if (biasPill && biasText) {
        const isBull = data.order_flow_bias !== "BEARISH_ORDER_FLOW";
        biasPill.className = `orderflow-bias-pill ${isBull ? '' : 'bearish'}`;
        biasText.textContent = isBull ? "BULLISH ACCUMULATION" : "BEARISH DISTRIBUTION";
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

    const btnPine = document.getElementById("btn-copy-pinescript");
    if (btnPine) {
        btnPine.addEventListener("click", async () => {
            try {
                const res = await fetch("/api/pine-script");
                if (res.ok) {
                    const text = await res.text();
                    await navigator.clipboard.writeText(text);
                    showToast("📋 Pine Script v5 copied to clipboard! Paste into TradingView Pine Editor.");
                } else {
                    showToast("⚠️ Could not generate Pine Script.");
                }
            } catch (e) {
                showToast("❌ Clipboard error copying script.");
            }
        });
    }
}

/* ==============================================================================
   5B. SCALPER & DAY TRADING SUITE UPDATERS
   ============================================================================== */
function updateScalperRegime(data) {
    if (!data || !data.regime) return;
    const r = data.regime;
    const badge = document.getElementById("scalp-regime-badge");
    const title = document.getElementById("scalp-regime-title");
    if (badge && title) {
        title.textContent = `REGIME: ${r.regime ? r.regime.replace(/_/g, " ") : "TRENDING EXPANSION"}`;
    }
    const weightsDesc = document.getElementById("scalp-weights-desc");
    if (weightsDesc && r.weights) {
        const w = r.weights;
        weightsDesc.textContent = `${Math.round((w.technical || 0.4)*100)}% Tech, ${Math.round((w.news || 0.2)*100)}% News, ${Math.round((w.liquidity || 0.25)*100)}% Liq, ${Math.round((w.macro || 0.15)*100)}% Macro`;
    }
}

function updateScalperSetups(data) {
    if (!data) return;
    
    // Confluence update if attached
    if (data.confluence) {
        updateScalperConfluence(data.confluence);
    }
    // Risk guardian update if attached
    if (data.risk_guardian) {
        const rgEl = document.getElementById("scalp-risk-guardian");
        if (rgEl) {
            const cond = data.risk_guardian.risk_condition || "NORMAL";
            rgEl.textContent = `${cond} (${Math.round(data.risk_guardian.adr_exhaustion_pct || 0)}% ADR)`;
            rgEl.style.color = cond === "CHOP_RISK" || cond === "EXHAUSTED" ? "#f43f5e" : "#10b981";
        }
        const adrEl = document.getElementById("scalp-adr-exhaust");
        if (adrEl) {
            adrEl.textContent = `${data.risk_guardian.adr_exhaustion_pct || 0}% (${data.risk_guardian.distance_to_adr_boundary_pts || 0} pts left)`;
        }
    }

    const setups = data.setups || [];
    const container = document.getElementById("scalp-setups-container");
    const countEl = document.getElementById("scalp-setups-count");
    if (countEl) countEl.textContent = `${setups.length} ACTIVE SETUP${setups.length === 1 ? '' : 'S'}`;

    if (!container) return;

    if (setups.length === 0) {
        container.innerHTML = `<div class="empty-state-mini">No high-probability trade setups active under current market regime. Capital preservation in effect.</div>`;
        return;
    }

    container.innerHTML = setups.map(s => {
        const isLong = s.direction === "LONG";
        const gradeColor = s.quality_grade === "A+" ? "#10b981" : s.quality_grade === "A" ? "#38bdf8" : "#f59e0b";
        
        return `
            <div style="background: rgba(255,255,255,0.03); border: 1px solid ${isLong ? 'rgba(16,185,129,0.3)' : 'rgba(244,63,94,0.3)'}; border-left: 4px solid ${isLong ? '#10b981' : '#f43f5e'}; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="background: ${isLong ? 'rgba(16,185,129,0.2)' : 'rgba(244,63,94,0.2)'}; color: ${isLong ? '#34d399' : '#fb7185'}; font-weight: 800; font-size: 0.75rem; padding: 2px 8px; border-radius: 4px;">${s.direction}</span>
                        <strong style="color: #ffffff; font-size: 0.9rem;">${escapeHtml(s.setup_name || s.setup_type)}</strong>
                    </div>
                    <span style="font-weight: 800; color: ${gradeColor}; font-size: 0.8rem; background: rgba(0,0,0,0.4); padding: 2px 8px; border-radius: 4px; border: 1px solid ${gradeColor};">Grade: ${s.quality_grade}</span>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin: 10px 0; background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px; font-size: 0.75rem; font-family: var(--font-mono);">
                    <div>
                        <span style="color: #94a3b8; display: block; font-size: 0.65rem;">ENTRY</span>
                        <b style="color: #38bdf8;">$${s.entry_zone ? s.entry_zone[0] : s.entry_price}</b>
                    </div>
                    <div>
                        <span style="color: #94a3b8; display: block; font-size: 0.65rem;">STOP LOSS</span>
                        <b style="color: #f43f5e;">$${s.invalidation_sl}</b>
                    </div>
                    <div>
                        <span style="color: #94a3b8; display: block; font-size: 0.65rem;">TP1 [1:1.5]</span>
                        <b style="color: #34d399;">$${s.target_tp1}</b>
                    </div>
                    <div>
                        <span style="color: #94a3b8; display: block; font-size: 0.65rem;">R:R</span>
                        <b style="color: #fbbf24;">1:${s.reward_risk_ratio || 2.0}</b>
                    </div>
                </div>

                <div style="font-size: 0.75rem; color: #cbd5e1; line-height: 1.4;">
                    <span>⚡ <b>Catalyst:</b> ${escapeHtml(s.catalyst || s.invalidation_reason || "Confluence alignment confirmed.")}</span>
                </div>
            </div>
        `;
    }).join("");
}

function updateScalperConfluence(conf) {
    if (!conf) return;
    const gradeEl = document.getElementById("scalp-confluence-grade");
    if (gradeEl) {
        gradeEl.textContent = `GRADE: ${conf.confluence_grade || '--'}`;
        gradeEl.style.color = conf.confluence_grade === "A+" ? "#10b981" : conf.confluence_grade === "A" ? "#38bdf8" : "#f59e0b";
    }

    const pctEl = document.getElementById("scalp-confluence-pct");
    const barEl = document.getElementById("scalp-confluence-bar");
    const pct = conf.confluence_score !== undefined ? conf.confluence_score : (conf.confluence_pct || 0);
    if (pctEl) pctEl.textContent = `${pct}%`;
    if (barEl) barEl.style.width = `${pct}%`;

    const factorsEl = document.getElementById("scalp-aligned-factors");
    if (factorsEl) {
        const aligned = conf.aligned_factors || [];
        if (aligned.length === 0) {
            factorsEl.innerHTML = `<div class="empty-state-mini">Evaluating market factors...</div>`;
        } else {
            factorsEl.innerHTML = aligned.map(f => `
                <div style="display: flex; align-items: center; gap: 6px; font-size: 0.78rem; color: #e2e8f0; margin-bottom: 5px;">
                    <span style="color: #10b981;">✓</span>
                    <span>${escapeHtml(f)}</span>
                </div>
            `).join("");
        }
    }

    const vwapEl = document.getElementById("scalp-vwap-dist");
    if (vwapEl && conf.factors && conf.factors.vwap_5m) {
        vwapEl.textContent = conf.factors.vwap_5m.aligned ? "Above VWAP (Bullish)" : "Below VWAP (Bearish)";
        vwapEl.style.color = conf.factors.vwap_5m.aligned ? "#10b981" : "#f43f5e";
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
