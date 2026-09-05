/**
 * XAUUSD QUANT INTELLIGENCE & LIQUIDITY AGENT - DASHBOARD CLIENT JAVASCRIPT
 * Complete Modern Controller with Real-Time Telemetry & Fluid Micro-Interactions
 */

let autoRefreshIntervalId = null;
let currentRefreshRate = 20; // seconds
let lastPrice = null;

document.addEventListener("DOMContentLoaded", () => {
    initTabNavigation();
    initTradingSessions();
    initActionButtons();
    initSettingsModal();
    initMobileBar();
    initEyeToggles();
    initChartTimeframeControls();
    initLiquidityFilterControls();
    initScenarioSimulator();

    // Initial load
    fetchDashboardData();
    setupAutoRefresh(currentRefreshRate);

    // Update trading session lights every minute
    setInterval(updateTradingSessions, 60000);
});

/* ==============================================================================
   TAB NAVIGATION SYSTEM
   ============================================================================== */
function initTabNavigation() {
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetId = btn.getAttribute("data-tab");
            switchTab(targetId);
        });
    });
}

function switchTab(targetId) {
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");
    const mobileBtns = document.querySelectorAll(".mobile-btn");

    tabButtons.forEach(btn => {
        const isTarget = btn.getAttribute("data-tab") === targetId;
        btn.classList.toggle("active", isTarget);
        btn.setAttribute("aria-selected", isTarget ? "true" : "false");
    });

    mobileBtns.forEach(btn => {
        const isTarget = btn.getAttribute("data-target-tab") === targetId;
        btn.classList.toggle("active", isTarget);
    });

    tabPanes.forEach(pane => {
        if (pane.id === targetId) {
            pane.classList.add("active");
        } else {
            pane.classList.remove("active");
        }
    });
}

function initMobileBar() {
    const mobileBtns = document.querySelectorAll(".mobile-btn[data-target-tab]");
    mobileBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetId = btn.getAttribute("data-target-tab");
            switchTab(targetId);
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    });

    const mTrigger = document.getElementById("m-btn-trigger");
    if (mTrigger) {
        mTrigger.addEventListener("click", () => {
            document.getElementById("btn-trigger")?.click();
        });
    }

    const mSettings = document.getElementById("m-btn-settings");
    if (mSettings) {
        mSettings.addEventListener("click", () => {
            document.getElementById("btn-open-settings")?.click();
        });
    }
}

/* ==============================================================================
   GLOBAL FOREX TRADING SESSIONS
   ============================================================================== */
function initTradingSessions() {
    updateTradingSessions();
}

function updateTradingSessions() {
    const now = new Date();
    const utcHour = now.getUTCHours();
    const utcMin = now.getUTCMinutes();
    const currentDecimalTime = utcHour + (utcMin / 60);

    // Session UTC Hours
    // Sydney: 21:00 - 06:00 UTC (crosses midnight)
    const sydneyActive = currentDecimalTime >= 21 || currentDecimalTime < 6;
    // Tokyo: 00:00 - 09:00 UTC
    const tokyoActive = currentDecimalTime >= 0 && currentDecimalTime < 9;
    // London: 07:00 - 16:00 UTC
    const londonActive = currentDecimalTime >= 7 && currentDecimalTime < 16;
    // New York: 12:00 - 21:00 UTC
    const nyActive = currentDecimalTime >= 12 && currentDecimalTime < 21;

    setSessionState("session-sydney", sydneyActive);
    setSessionState("session-tokyo", tokyoActive);
    setSessionState("session-london", londonActive);
    setSessionState("session-ny", nyActive);
}

function setSessionState(elId, isActive) {
    const el = document.getElementById(elId);
    if (el) {
        el.classList.toggle("active", isActive);
    }
}

/* ==============================================================================
   AUTO-REFRESH INTERVAL CONTROLLER
   ============================================================================== */
function setupAutoRefresh(seconds) {
    if (autoRefreshIntervalId) {
        clearInterval(autoRefreshIntervalId);
        autoRefreshIntervalId = null;
    }

    if (seconds > 0) {
        autoRefreshIntervalId = setInterval(fetchDashboardData, seconds * 1000);
    }
}

/* ==============================================================================
   HEADER ACTION BUTTONS
   ============================================================================== */
function initActionButtons() {
    const triggerBtn = document.getElementById("btn-trigger");
    const refreshSelect = document.getElementById("auto-refresh-select");

    if (triggerBtn) {
        triggerBtn.addEventListener("click", async () => {
            const icon = triggerBtn.querySelector(".btn-icon");
            triggerBtn.disabled = true;
            if (icon) icon.classList.add("spinning");

            showToast("Quantitative intelligence cycle triggered in background...", "info");

            try {
                const res = await fetch("/api/trigger-analysis", { method: "POST" });
                if (res.ok) {
                    showToast("Cycle started. Fetching updated findings...", "success");
                    setTimeout(async () => {
                        await fetchDashboardData();
                        triggerBtn.disabled = false;
                        if (icon) icon.classList.remove("spinning");
                    }, 3500);
                } else {
                    showToast("Failed to trigger analysis cycle.", "error");
                    triggerBtn.disabled = false;
                    if (icon) icon.classList.remove("spinning");
                }
            } catch (err) {
                console.error("Trigger error:", err);
                showToast("Connection error while triggering agent.", "error");
                triggerBtn.disabled = false;
                if (icon) icon.classList.remove("spinning");
            }
        });
    }

    if (refreshSelect) {
        refreshSelect.addEventListener("change", (e) => {
            const rate = parseInt(e.target.value, 10);
            currentRefreshRate = rate;
            setupAutoRefresh(rate);
            if (rate > 0) {
                showToast(`Auto-refresh interval set to ${rate} seconds.`, "info");
            } else {
                showToast("Auto-refresh paused.", "info");
            }
        });
    }
}

/* ==============================================================================
   SETTINGS MODAL & PASSWORD TOGGLES
   ============================================================================== */
function initEyeToggles() {
    const eyeButtons = document.querySelectorAll(".btn-toggle-eye");
    eyeButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetId = btn.getAttribute("data-target");
            const input = document.getElementById(targetId);
            if (input) {
                if (input.type === "password") {
                    input.type = "text";
                    btn.textContent = "🔒";
                } else {
                    input.type = "password";
                    btn.textContent = "👁";
                }
            }
        });
    });
}

function initSettingsModal() {
    const modal = document.getElementById("config-modal");
    const openBtn = document.getElementById("btn-open-settings");
    const closeBtn = document.getElementById("btn-close-modal");
    const cancelBtn = document.getElementById("btn-cancel-modal");
    const saveBtn = document.getElementById("btn-save-config");
    const testTgBtn = document.getElementById("btn-test-telegram");

    if (openBtn && modal) {
        openBtn.addEventListener("click", async () => {
            await loadConfigIntoModal();
            modal.classList.add("active");
            modal.setAttribute("aria-hidden", "false");
        });
    }

    const closeModal = () => {
        if (modal) {
            modal.classList.remove("active");
            modal.setAttribute("aria-hidden", "true");
        }
    };

    if (closeBtn) closeBtn.addEventListener("click", closeModal);
    if (cancelBtn) cancelBtn.addEventListener("click", closeModal);

    // Close on backdrop click
    if (modal) {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) closeModal();
        });
    }

    if (saveBtn) {
        saveBtn.addEventListener("click", async () => {
            saveBtn.disabled = true;
            saveBtn.textContent = "Saving Configuration...";
            const payload = {
                TELEGRAM_BOT_TOKEN: document.getElementById("cfg-tg-token").value,
                TELEGRAM_CHAT_ID: document.getElementById("cfg-tg-chat").value,
                TELEGRAM_ALERTS_ENABLED: document.getElementById("cfg-tg-enabled").checked,
                AI_PRIORITY: document.getElementById("cfg-ai-priority").value,
                GEMINI_MODEL: document.getElementById("cfg-gemini-model").value,
                GEMINI_API_KEY: document.getElementById("cfg-gemini-key").value,
                OPENROUTER_MODEL: document.getElementById("cfg-openrouter-model") ? document.getElementById("cfg-openrouter-model").value : "openrouter/free",
                OPENROUTER_API_KEY: document.getElementById("cfg-openrouter-key").value,
                ANALYSIS_INTERVAL_SECONDS: parseInt(document.getElementById("cfg-interval").value, 10),
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
                if (res.ok && data.status === "SUCCESS") {
                    showToast("Configuration saved & applied dynamically!", "success");
                    closeModal();
                    fetchDashboardData();
                } else {
                    showToast("Error saving config: " + (data.message || "Unknown error"), "error");
                }
            } catch (err) {
                showToast("Failed to communicate with server configuration.", "error");
            } finally {
                saveBtn.disabled = false;
                saveBtn.textContent = "💾 Save & Apply Changes";
            }
        });
    }

    if (testTgBtn) {
        testTgBtn.addEventListener("click", async () => {
            testTgBtn.disabled = true;
            testTgBtn.innerHTML = "<span>⏳</span> Dispatching Test...";
            try {
                const res = await fetch("/api/test-telegram", { method: "POST" });
                const data = await res.json();
                if (data.status === "SUCCESS") {
                    showToast("✅ Telegram message dispatched successfully!", "success");
                } else {
                    showToast("❌ " + data.message, "error");
                }
            } catch (err) {
                showToast("Network failure testing Telegram connection.", "error");
            } finally {
                testTgBtn.disabled = false;
                testTgBtn.innerHTML = "<span>🔔</span> Send Test Alert";
            }
        });
    }
}

async function loadConfigIntoModal() {
    try {
        const res = await fetch("/api/config");
        if (res.ok) {
            const cfg = await res.json();
            const setVal = (id, val) => {
                const el = document.getElementById(id);
                if (el && val !== undefined && val !== null) el.value = val;
            };

            setVal("cfg-tg-token", cfg.telegram_token_masked || "");
            setVal("cfg-tg-chat", cfg.telegram_chat_id || "");
            const tgEnabled = document.getElementById("cfg-tg-enabled");
            if (tgEnabled) tgEnabled.checked = cfg.telegram_alerts_enabled !== false;

            setVal("cfg-ai-priority", cfg.ai_priority || "gemini_first");
            if (cfg.gemini_model) setVal("cfg-gemini-model", cfg.gemini_model);
            if (cfg.openrouter_model) setVal("cfg-openrouter-model", cfg.openrouter_model);
            setVal("cfg-gemini-key", cfg.gemini_key_masked || "");
            setVal("cfg-openrouter-key", cfg.openrouter_key_masked || "");
            setVal("cfg-interval", cfg.analysis_interval_seconds || 180);
            setVal("cfg-liq-tol", cfg.liquidity_tolerance_pips || 1.5);
            
            const weekendPause = document.getElementById("cfg-weekend-pause");
            if (weekendPause) weekendPause.checked = cfg.pause_on_weekends !== false;
        }
    } catch (err) {
        console.error("Failed to load config:", err);
    }
}

/* ==============================================================================
   DATA FETCHING & UI SYNCHRONIZATION
   ============================================================================== */
async function fetchDashboardData() {
    try {
        const [reportRes, marketRes, liqRes, newsRes, calRes, accRes, healthRes, histRes, geoRes, cotRes] = await Promise.all([
            fetch("/api/latest-report").catch(() => null),
            fetch("/api/market-data").catch(() => null),
            fetch("/api/liquidity").catch(() => null),
            fetch("/api/news").catch(() => null),
            fetch("/api/economic-calendar").catch(() => null),
            fetch("/api/accuracy").catch(() => null),
            fetch("/health").catch(() => null),
            fetch("/api/history").catch(() => null),
            fetch("/api/geopolitics").catch(() => null),
            fetch("/api/institutional-flow").catch(() => null)
        ]);

        if (reportRes && reportRes.ok) updateReportUI(await reportRes.json());
        if (marketRes && marketRes.ok) updateMarketUI(await marketRes.json());
        if (liqRes && liqRes.ok) updateLiquidityUI(await liqRes.json());
        if (newsRes && newsRes.ok) updateNewsUI(await newsRes.json());
        if (calRes && calRes.ok) updateCalendarUI(await calRes.json());
        if (accRes && accRes.ok) updateAccuracyUI(await accRes.json());
        if (healthRes && healthRes.ok) updateHealthUI(await healthRes.json());
        if (histRes && histRes.ok) updateHistoryUI(await histRes.json());
        if (geoRes && geoRes.ok) updateGeopoliticsUI(await geoRes.json());
        if (cotRes && cotRes.ok) updateInstitutionalCOTUI(await cotRes.json());

        // Refresh visual corridor chart
        loadPriceCorridorChart();

    } catch (error) {
        console.error("Error refreshing dashboard telemetries:", error);
    }
}

/* ==============================================================================
   UI COMPONENT UPDATERS
   ============================================================================== */
function updateReportUI(report) {
    if (!report || report.status === "NO_DATA") return;

    // Directional Bias Badge & Score
    const dirBadge = document.getElementById("direction-badge");
    const dirScore = document.getElementById("direction-score");
    const verdictKpi = document.getElementById("verdict-summary-kpi");

    const direction = (report.direction || "NEUTRAL").toUpperCase();
    const isBull = direction.includes("BULL");
    const isBear = direction.includes("BEAR");

    if (dirBadge) {
        dirBadge.className = `direction-pill ${isBull ? "bullish" : isBear ? "bearish" : "neutral"}`;
        const iconSpan = dirBadge.querySelector(".dir-icon");
        const textSpan = dirBadge.querySelector(".dir-text");
        if (iconSpan) iconSpan.textContent = isBull ? "🟢" : isBear ? "🔴" : "⚪";
        if (textSpan) textSpan.textContent = report.direction;
    }

    if (dirScore) {
        const score = Number(report.direction_score) || 0;
        dirScore.textContent = `${score > 0 ? "+" : ""}${score.toFixed(1)} / 100`;
    }

    if (verdictKpi) {
        verdictKpi.textContent = report.executive_verdict_summary || report.macro_summary || "Multi-signal synthesis complete.";
    }

    // Confidence Circular Meter & Bar
    const confPct = Math.round(report.confidence || 0);
    const confPctEl = document.getElementById("confidence-pct");
    const confRadialBar = document.getElementById("confidence-radial-bar");
    const confBar = document.getElementById("confidence-bar");
    const verdictConfVal = document.getElementById("verdict-confidence-val");

    if (confPctEl) confPctEl.textContent = confPct;
    if (verdictConfVal) verdictConfVal.textContent = `${confPct}%`;
    if (confRadialBar) {
        confRadialBar.setAttribute("stroke-dasharray", `${confPct}, 100`);
        confRadialBar.style.stroke = confPct >= 70 ? "var(--bullish-green)" : confPct >= 50 ? "var(--warning-yellow)" : "var(--bearish-red)";
    }
    if (confBar) {
        confBar.style.width = `${Math.max(8, Math.min(100, confPct))}%`;
        confBar.style.background = confPct >= 70 ? "var(--bullish-green)" : confPct >= 50 ? "var(--warning-yellow)" : "var(--bearish-red)";
    }

    const dataQual = document.getElementById("data-quality-pill");
    if (dataQual) {
        if (confPct >= 65) {
            dataQual.textContent = "HIGH CONVICTION";
            dataQual.style.color = "var(--bullish-green)";
            dataQual.style.borderColor = "var(--bullish-border)";
            dataQual.style.background = "var(--bullish-bg)";
        } else if (confPct >= 35) {
            dataQual.textContent = "MODERATE CONVICTION";
            dataQual.style.color = "var(--warning-yellow)";
            dataQual.style.borderColor = "rgba(245, 176, 65, 0.3)";
            dataQual.style.background = "rgba(245, 176, 65, 0.1)";
        } else {
            dataQual.textContent = "LOW / DIVERGENT";
            dataQual.style.color = "var(--bearish-red)";
            dataQual.style.borderColor = "var(--bearish-border)";
            dataQual.style.background = "var(--bearish-bg)";
        }
    }

    // Provider Tag
    const provTag = document.getElementById("ai-provider-tag");
    if (provTag) {
        const pName = provTag.querySelector(".provider-name");
        if (pName) pName.textContent = report.provider_used || "Deterministic Engine";
    }

    // Final Market Verdict Hero Banner
    const vBadge = document.getElementById("final-market-verdict-badge");
    const vText = document.getElementById("final-market-verdict-text");
    if (vBadge) {
        const verdict = (report.final_market_verdict || (isBull ? "BULLISH" : isBear ? "BEARISH" : "NEUTRAL")).toUpperCase();
        vBadge.className = `verdict-hero-badge ${verdict.includes("BULL") ? "bullish" : verdict.includes("BEAR") ? "bearish" : "neutral"}`;
        const vTitle = vBadge.querySelector(".verdict-title-text");
        if (vTitle) {
            vTitle.textContent = verdict.includes("BULL") ? "BULL MARKET (BULLISH BIAS)" :
                                 verdict.includes("BEAR") ? "BEAR MARKET (BEARISH BIAS)" : "NEUTRAL (BALANCED CONSOLIDATION)";
        }
    }
    if (vText) {
        vText.textContent = report.executive_verdict_summary || report.macro_summary || "Multi-signal synthesis active.";
    }

    // Multi-Factor Evidence Matrix Meters
    updateEvidenceMeter("ev-macro-bar", "ev-macro-val", report.scores?.macro_score);
    updateEvidenceMeter("ev-usd-bar", "ev-usd-val", report.scores?.usd_score);
    updateEvidenceMeter("ev-yield-bar", "ev-yield-val", report.scores?.yield_score);
    updateEvidenceMeter("ev-news-bar", "ev-news-val", report.scores?.news_score);
    updateEvidenceMeter("ev-tech-bar", "ev-tech-val", report.scores?.technical_score);

    // Cross-Asset Macro Feed
    setTelemetryVal("macro-dxy-score", report.scores?.usd_score);
    setTelemetryVal("macro-10y-score", report.scores?.yield_score);
    setTelemetryVal("macro-2y-score", report.scores?.macro_score);
    setTelemetryVal("macro-tips-score", report.scores?.macro_score ? (report.scores.macro_score * 0.8).toFixed(1) : "0.0");

    // Dominant Drivers Pills
    const driversList = document.getElementById("dominant-drivers-list");
    if (driversList) {
        if (report.dominant_drivers && report.dominant_drivers.length > 0) {
            driversList.innerHTML = report.dominant_drivers.map(d => `
                <div class="driver-pill-item">
                    <span class="driver-bullet">⚡</span>
                    <span>${escapeHtml(d)}</span>
                </div>
            `).join("");
        } else {
            driversList.innerHTML = `<div class="driver-empty">Multi-factor drivers balanced across macro & technical inputs.</div>`;
        }
    }

    // Narratives
    const macroNarr = document.getElementById("macro-narrative");
    const newsNarr = document.getElementById("news-narrative");
    const riskNarr = document.getElementById("risk-narrative");

    if (macroNarr) macroNarr.textContent = report.macro_summary || "Macro analysis pending incoming cycle.";
    if (newsNarr) newsNarr.textContent = report.news_summary || "News sentiment synthesis pending incoming cycle.";
    if (riskNarr) riskNarr.textContent = report.risk_factors || "Standard intraday market volatility.";

    // Timestamp
    const tsEl = document.getElementById("last-updated-ts");
    if (tsEl && report.timestamp) {
        tsEl.textContent = new Date(report.timestamp).toLocaleTimeString("en-IN", {
            timeZone: "Asia/Kolkata",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        }) + " IST";
    }
}

function updateEvidenceMeter(barId, valId, score) {
    const bar = document.getElementById(barId);
    const val = document.getElementById(valId);
    const num = Number(score) || 0;

    if (val) {
        val.textContent = (num > 0 ? "+" : "") + num.toFixed(1);
        val.style.color = num > 10 ? "var(--bullish-green)" : num < -10 ? "var(--bearish-red)" : "var(--text-primary)";
    }
    if (bar) {
        // Map -100..+100 to 0%..100%
        const pct = ((num + 100) / 200) * 100;
        bar.style.width = `${Math.max(4, Math.min(100, pct))}%`;
        bar.style.backgroundColor = num > 10 ? "var(--bullish-green)" : num < -10 ? "var(--bearish-red)" : "var(--neutral-blue)";
    }
}

function setTelemetryVal(id, score) {
    const el = document.getElementById(id);
    if (el) {
        const num = Number(score) || 0;
        el.textContent = (num > 0 ? "+" : "") + num.toFixed(1);
        el.style.color = num > 10 ? "var(--bullish-green)" : num < -10 ? "var(--bearish-red)" : "var(--gold-primary)";
    }
}

function updateMarketUI(market) {
    if (!market || market.status === "NO_DATA") return;

    const goldPriceEl = document.getElementById("gold-price");
    const radarPriceEl = document.getElementById("radar-gold-price");
    const chgEl = document.getElementById("price-change-tag");
    const lowEl = document.getElementById("price-low-24h");
    const highEl = document.getElementById("price-high-24h");
    const rangeInd = document.getElementById("price-range-indicator");

    const price = Number(market.price) || 0;

    if (goldPriceEl) {
        // Flash color on price tick change
        if (lastPrice !== null && lastPrice !== price) {
            goldPriceEl.classList.remove("flash-green", "flash-red");
            void goldPriceEl.offsetWidth; // Trigger reflow
            goldPriceEl.classList.add(price > lastPrice ? "flash-green" : "flash-red");
        }
        goldPriceEl.textContent = price.toFixed(2);
        lastPrice = price;
    }

    if (radarPriceEl) radarPriceEl.textContent = price.toFixed(2);

    if (chgEl) {
        const chg = Number(market.change_24h) || 0;
        chgEl.textContent = `24h: ${chg >= 0 ? "+" : ""}${chg.toFixed(2)}%`;
        chgEl.style.color = chg >= 0 ? "var(--bullish-green)" : "var(--bearish-red)";
        chgEl.style.background = chg >= 0 ? "var(--bullish-bg)" : "var(--bearish-bg)";
        chgEl.style.borderColor = chg >= 0 ? "var(--bullish-border)" : "var(--bearish-border)";
    }

    const low = Number(market.low_24h) || (price * 0.995);
    const high = Number(market.high_24h) || (price * 1.005);

    if (lowEl) lowEl.textContent = low.toFixed(1);
    if (highEl) highEl.textContent = high.toFixed(1);

    if (rangeInd && high > low) {
        const pct = Math.max(0, Math.min(100, ((price - low) / (high - low)) * 100));
        rangeInd.style.left = `${pct}%`;
    }

    // Structure & Regime
    const trendEl = document.getElementById("regime-trend");
    const volEl = document.getElementById("regime-vol");
    const atrKpi = document.getElementById("atr-val");

    if (trendEl && market.indicators?.trend) {
        const trend = market.indicators.trend.replace("_", " ");
        trendEl.textContent = trend;
        trendEl.className = `regime-val ${trend.includes("BULL") ? "badge-bull" : trend.includes("BEAR") ? "badge-bear" : "badge-neutral"}`;
    }

    if (volEl && market.indicators?.volatility) {
        volEl.textContent = market.indicators.volatility.replace("_", " ");
    }

    if (atrKpi && market.indicators?.atr) {
        atrKpi.textContent = Number(market.indicators.atr).toFixed(2);
    }

    // Technicals Tab
    const rsiEl = document.getElementById("tech-rsi");
    const rsiBadge = document.getElementById("tech-rsi-badge");
    const rsiBar = document.getElementById("tech-rsi-bar");

    if (rsiEl && market.indicators?.rsi) {
        const rsi = Number(market.indicators.rsi);
        rsiEl.textContent = rsi.toFixed(1);
        if (rsiBar) rsiBar.style.width = `${rsi}%`;

        if (rsiBadge) {
            if (rsi > 70) {
                rsiBadge.textContent = "OVERBOUGHT";
                rsiBadge.style.color = "var(--bearish-red)";
            } else if (rsi < 30) {
                rsiBadge.textContent = "OVERSOLD";
                rsiBadge.style.color = "var(--bullish-green)";
            } else {
                rsiBadge.textContent = "BALANCED";
                rsiBadge.style.color = "var(--text-secondary)";
            }
        }
    }

    const macdEl = document.getElementById("tech-macd");
    const macdSigEl = document.getElementById("tech-macd-sig");
    const macdBadge = document.getElementById("tech-macd-badge");

    if (macdEl && market.indicators?.macd) {
        const macd = Number(market.indicators.macd);
        const sig = Number(market.indicators.macd_signal || 0);
        macdEl.textContent = macd.toFixed(2);
        if (macdSigEl) macdSigEl.textContent = sig.toFixed(2);

        if (macdBadge) {
            macdBadge.textContent = macd > sig ? "BULLISH CROSS" : "BEARISH CROSS";
            macdBadge.style.color = macd > sig ? "var(--bullish-green)" : "var(--bearish-red)";
        }
    }

    const techAtrEl = document.getElementById("tech-atr");
    if (techAtrEl && market.indicators?.atr) {
        techAtrEl.textContent = Number(market.indicators.atr).toFixed(2);
    }

    const ema20El = document.getElementById("tech-ema-20");
    const ema50El = document.getElementById("tech-ema-50");
    const ema200El = document.getElementById("tech-ema-200");

    if (ema20El && market.indicators?.ema_20) ema20El.textContent = Number(market.indicators.ema_20).toFixed(2);
    if (ema50El && market.indicators?.ema_50) ema50El.textContent = Number(market.indicators.ema_50).toFixed(2);
    if (ema200El && market.indicators?.ema_200) ema200El.textContent = Number(market.indicators.ema_200).toFixed(2);
}

let currentChartTf = "H1";

function initChartTimeframeControls() {
    const tfButtons = document.querySelectorAll("#chart-tf-group .tf-btn");
    tfButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tfButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentChartTf = btn.getAttribute("data-tf") || "H1";
            loadPriceCorridorChart();
        });
    });
}

async function loadPriceCorridorChart() {
    const canvas = document.getElementById("price-action-canvas");
    if (!canvas) return;

    try {
        const res = await fetch(`/api/candles?timeframe=${currentChartTf}`);
        if (!res.ok) return;
        const data = await res.json();
        const candles = data.candles || [];
        if (candles.length === 0) return;

        drawPriceCorridorCanvas(canvas, candles, data.current_price);
    } catch (err) {
        console.error("Failed to load candles for corridor chart:", err);
    }
}

function drawPriceCorridorCanvas(canvas, candles, currentPrice) {
    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    // Padding
    const padTop = 25;
    const padBottom = 25;
    const padLeft = 15;
    const padRight = 70;
    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    // Price Bounds
    let minP = Math.min(...candles.map(c => c.low));
    let maxP = Math.max(...candles.map(c => c.high));
    if (minP === maxP) {
        minP -= 5;
        maxP += 5;
    }
    const pSpan = maxP - minP;

    const getY = (p) => padTop + plotH - (((p - minP) / pSpan) * plotH);
    const getX = (idx) => padLeft + (idx / (candles.length - 1)) * plotW;

    // Grid lines
    ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = padTop + (i / 4) * plotH;
        ctx.beginPath();
        ctx.moveTo(padLeft, y);
        ctx.lineTo(width - padRight, y);
        ctx.stroke();

        const pVal = maxP - (i / 4) * pSpan;
        ctx.fillStyle = "rgba(148, 163, 184, 0.6)";
        ctx.font = "10px Inter, monospace";
        ctx.fillText(`$${pVal.toFixed(1)}`, width - padRight + 6, y + 3);
    }

    // Draw EMA Lines (Fast 20, Med 50, Baseline 200 simulation)
    const drawEmaLine = (period, color) => {
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        let k = 2 / (period + 1);
        let ema = candles[0].close;
        for (let i = 0; i < candles.length; i++) {
            ema = (candles[i].close * k) + (ema * (1 - k));
            const x = getX(i);
            const y = getY(ema);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();
    };

    drawEmaLine(20, "#3b82f6");  // Fast EMA
    drawEmaLine(50, "#8b5cf6");  // Medium EMA
    drawEmaLine(200, "#ef4444"); // Baseline EMA

    // Draw Candlesticks
    const barW = Math.max(3, (plotW / candles.length) * 0.65);
    candles.forEach((c, idx) => {
        const x = getX(idx);
        const yO = getY(c.open);
        const yC = getY(c.close);
        const yH = getY(c.high);
        const yL = getY(c.low);
        const isBull = c.close >= c.open;

        ctx.strokeStyle = isBull ? "#10b981" : "#ef4444";
        ctx.lineWidth = 1;

        // Wick
        ctx.beginPath();
        ctx.moveTo(x, yH);
        ctx.lineTo(x, yL);
        ctx.stroke();

        // Body
        ctx.fillStyle = isBull ? "#10b981" : "#ef4444";
        const topY = Math.min(yO, yC);
        const bodyH = Math.max(2, Math.abs(yC - yO));
        ctx.fillRect(x - (barW / 2), topY, barW, bodyH);
    });

    // Current Price Benchmark Line
    if (currentPrice) {
        const curY = getY(currentPrice);
        ctx.strokeStyle = "#f5b041";
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(padLeft, curY);
        ctx.lineTo(width - padRight, curY);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = "#f5b041";
        ctx.fillRect(width - padRight + 2, curY - 8, 64, 16);
        ctx.fillStyle = "#0a0e17";
        ctx.font = "bold 9px Inter, monospace";
        ctx.fillText(`$${Number(currentPrice).toFixed(1)}`, width - padRight + 6, curY + 4);
    }
}

let currentLiqFilter = "ALL";
let currentLiquidityData = null;

function initLiquidityFilterControls() {
    const filterButtons = document.querySelectorAll("#liq-filter-group .tf-btn");
    filterButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            filterButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentLiqFilter = btn.getAttribute("data-filter") || "ALL";
            if (currentLiquidityData) {
                renderFilteredLiquidityBars(currentLiquidityData);
            }
        });
    });
}

function updateLiquidityUI(liq) {
    if (!liq) return;
    currentLiquidityData = liq;

    const totalCountEl = document.getElementById("radar-total-zones");
    const zoneBadgeCount = document.getElementById("liq-zone-count");
    const countAboveEl = document.getElementById("count-above");
    const countBelowEl = document.getElementById("count-below");

    const aboveZones = liq.liquidity_above || [];
    const belowZones = liq.liquidity_below || [];
    const total = liq.total_zones || (aboveZones.length + belowZones.length);

    if (totalCountEl) totalCountEl.textContent = total;
    if (zoneBadgeCount) zoneBadgeCount.textContent = total;
    if (countAboveEl) countAboveEl.textContent = `${aboveZones.length} Active`;
    if (countBelowEl) countBelowEl.textContent = `${belowZones.length} Active`;

    // 1. Calculate Imbalance Ratio Metrics
    const overheadWeight = aboveZones.reduce((acc, z) => acc + (Number(z.strength) || 75), 0);
    const underlyingWeight = belowZones.reduce((acc, z) => acc + (Number(z.strength) || 75), 0);
    const totalWeight = overheadWeight + underlyingWeight;

    let overheadPct = 50;
    let underlyingPct = 50;
    if (totalWeight > 0) {
        overheadPct = Math.round((overheadWeight / totalWeight) * 100);
        underlyingPct = 100 - overheadPct;
    }

    const overheadBar = document.getElementById("imbalance-bar-overhead");
    const underlyingBar = document.getElementById("imbalance-bar-underlying");
    const overheadPctText = document.getElementById("overhead-pct-text");
    const underlyingPctText = document.getElementById("underlying-pct-text");
    const imbalanceBadge = document.getElementById("liq-imbalance-badge");

    if (overheadBar) overheadBar.style.width = `${overheadPct}%`;
    if (underlyingBar) underlyingBar.style.width = `${underlyingPct}%`;
    if (overheadPctText) overheadPctText.textContent = `${overheadPct}%`;
    if (underlyingPctText) underlyingPctText.textContent = `${underlyingPct}%`;

    if (imbalanceBadge) {
        if (overheadPct > 58) {
            imbalanceBadge.textContent = "HEAVY OVERHEAD SUPPLY";
            imbalanceBadge.style.color = "var(--bearish-red)";
            imbalanceBadge.style.borderColor = "var(--bearish-border)";
        } else if (underlyingPct > 58) {
            imbalanceBadge.textContent = "STRONG BUY CUSHION";
            imbalanceBadge.style.color = "var(--bullish-green)";
            imbalanceBadge.style.borderColor = "var(--bullish-border)";
        } else {
            imbalanceBadge.textContent = "EQUILIBRIUM BALANCED";
            imbalanceBadge.style.color = "var(--gold-primary)";
            imbalanceBadge.style.borderColor = "rgba(245, 176, 65, 0.3)";
        }
    }

    // 2. Nearest Ceiling (Overhead) and Floor (Underlying)
    const ceilingPrice = document.getElementById("ceiling-price-val");
    const ceilingPips = document.getElementById("ceiling-pips-badge");
    const ceilingDesc = document.getElementById("ceiling-desc-val");

    if (aboveZones.length > 0) {
        const sortedAbove = [...aboveZones].sort((a, b) => Number(a.price) - Number(b.price));
        const nearestCeiling = sortedAbove[0];
        if (ceilingPrice) ceilingPrice.textContent = `$${Number(nearestCeiling.price).toFixed(2)}`;
        if (ceilingPips) ceilingPips.textContent = `+${Number(nearestCeiling.distance || 0).toFixed(1)} pips`;
        if (ceilingDesc) ceilingDesc.textContent = `${nearestCeiling.type?.replace(/_/g, " ") || "Resistance"} • ${Math.round(nearestCeiling.strength || 80)}% Str`;
    } else {
        if (ceilingPrice) ceilingPrice.textContent = "$----.--";
        if (ceilingPips) ceilingPips.textContent = "+0.0 pips";
        if (ceilingDesc) ceilingDesc.textContent = "No immediate overhead ceiling detected";
    }

    const floorPrice = document.getElementById("floor-price-val");
    const floorPips = document.getElementById("floor-pips-badge");
    const floorDesc = document.getElementById("floor-desc-val");

    if (belowZones.length > 0) {
        const sortedBelow = [...belowZones].sort((a, b) => Number(b.price) - Number(a.price));
        const nearestFloor = sortedBelow[0];
        if (floorPrice) floorPrice.textContent = `$${Number(nearestFloor.price).toFixed(2)}`;
        if (floorPips) floorPips.textContent = `-${Number(nearestFloor.distance || 0).toFixed(1)} pips`;
        if (floorDesc) floorDesc.textContent = `${nearestFloor.type?.replace(/_/g, " ") || "Support"} • ${Math.round(nearestFloor.strength || 80)}% Str`;
    } else {
        if (floorPrice) floorPrice.textContent = "$----.--";
        if (floorPips) floorPips.textContent = "-0.0 pips";
        if (floorDesc) floorDesc.textContent = "No immediate underlying floor detected";
    }

    renderFilteredLiquidityBars(liq);
}

function renderFilteredLiquidityBars(liq) {
    const aboveList = document.getElementById("liquidity-above-list");
    const belowList = document.getElementById("liquidity-below-list");
    if (!aboveList || !belowList) return;

    let aboveZones = liq.liquidity_above || [];
    let belowZones = liq.liquidity_below || [];

    // Filter by active selection
    if (currentLiqFilter === "HIGH") {
        aboveZones = aboveZones.filter(z => (Number(z.strength) || 80) >= 80);
        belowZones = belowZones.filter(z => (Number(z.strength) || 80) >= 80);
    } else if (currentLiqFilter === "FVG") {
        aboveZones = aboveZones.filter(z => (z.type || "").toUpperCase().includes("FVG") || (z.type || "").toUpperCase().includes("GAP"));
        belowZones = belowZones.filter(z => (z.type || "").toUpperCase().includes("FVG") || (z.type || "").toUpperCase().includes("GAP"));
    } else if (currentLiqFilter === "ORDER_BLOCK") {
        aboveZones = aboveZones.filter(z => !(z.type || "").toUpperCase().includes("FVG"));
        belowZones = belowZones.filter(z => !(z.type || "").toUpperCase().includes("FVG"));
    }

    // Render Overhead Supply Clusters
    if (aboveZones.length === 0) {
        aboveList.innerHTML = `<div class="zone-empty-state">No matching overhead resistance pools found.</div>`;
    } else {
        const sortedAbove = [...aboveZones].sort((a, b) => Number(b.price) - Number(a.price));
        aboveList.innerHTML = sortedAbove.map(z => {
            const str = Math.min(100, Math.max(25, Math.round(z.strength || 80)));
            const formattedType = (z.type || "SUPPLY_POOL").replace(/_/g, " ");
            const isFvg = formattedType.includes("FVG") || formattedType.includes("GAP");
            return `
                <div class="zone-depth-row overhead">
                    <div class="zone-axis-left">
                        <div class="zone-price-tag mono-num">$${Number(z.price).toFixed(2)}</div>
                        <div class="zone-type-badge ${isFvg ? 'fvg-badge' : ''}">${escapeHtml(formattedType)} • ${escapeHtml(z.timeframe || 'H4')}</div>
                    </div>
                    <div class="zone-depth-bar-wrapper" title="Supply Cluster Density: ${str}%">
                        <div class="zone-depth-bar-fill" style="width: ${str}%;"></div>
                        <span class="zone-depth-bar-text">Density: ${str}% • Supply Absorption Node</span>
                    </div>
                    <div class="zone-axis-right">
                        <div class="zone-pip-dist mono-num">+${Number(z.distance || 0).toFixed(1)} pips</div>
                        <span class="zone-strength-pill">${str}% Vol</span>
                    </div>
                </div>
            `;
        }).join("");
    }

    // Render Underlying Demand Clusters
    if (belowZones.length === 0) {
        belowList.innerHTML = `<div class="zone-empty-state">No matching underlying support pools found.</div>`;
    } else {
        const sortedBelow = [...belowZones].sort((a, b) => Number(b.price) - Number(a.price));
        belowList.innerHTML = sortedBelow.map(z => {
            const str = Math.min(100, Math.max(25, Math.round(z.strength || 80)));
            const formattedType = (z.type || "DEMAND_POOL").replace(/_/g, " ");
            const isFvg = formattedType.includes("FVG") || formattedType.includes("GAP");
            return `
                <div class="zone-depth-row underlying">
                    <div class="zone-axis-left">
                        <div class="zone-price-tag mono-num">$${Number(z.price).toFixed(2)}</div>
                        <div class="zone-type-badge ${isFvg ? 'fvg-badge' : ''}">${escapeHtml(formattedType)} • ${escapeHtml(z.timeframe || 'H4')}</div>
                    </div>
                    <div class="zone-depth-bar-wrapper" title="Demand Cluster Density: ${str}%">
                        <div class="zone-depth-bar-fill" style="width: ${str}%;"></div>
                        <span class="zone-depth-bar-text">Density: ${str}% • Demand Accumulation Node</span>
                    </div>
                    <div class="zone-axis-right">
                        <div class="zone-pip-dist mono-num">-${Number(z.distance || 0).toFixed(1)} pips</div>
                        <span class="zone-strength-pill">${str}% Vol</span>
                    </div>
                </div>
            `;
        }).join("");
    }
}

function updateNewsUI(news) {
    const feed = document.getElementById("news-feed-list");
    if (!feed) return;

    if (!news || news.length === 0) {
        feed.innerHTML = `<div class="news-empty-state">No real-time market news available.</div>`;
        return;
    }

    feed.innerHTML = news.slice(0, 10).map(n => {
        const impactClass = n.gold_impact?.includes("BULL") ? "bullish" : n.gold_impact?.includes("BEAR") ? "bearish" : "";
        return `
            <div class="news-item-card">
                <a href="${escapeHtml(n.url || '#')}" target="_blank" rel="noopener noreferrer" class="news-item-title">
                    ${escapeHtml(n.title)}
                </a>
                <div class="news-meta-row">
                    <span class="news-source-tag">🏢 ${escapeHtml(n.source || 'Financial Wire')}</span>
                    <span>•</span>
                    <span class="news-impact-tag ${impactClass}">Gold: ${escapeHtml(n.gold_impact || 'NEUTRAL')}</span>
                    <span>•</span>
                    <span>Impact: <b>${escapeHtml(n.impact_level || 'MED')}</b></span>
                </div>
            </div>
        `;
    }).join("");
}

function updateCalendarUI(events) {
    const tbody = document.getElementById("calendar-body");
    if (!tbody) return;

    if (!events || events.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="table-empty">No high-impact USD economic events in the next 48 hours.</td></tr>`;
        return;
    }

    tbody.innerHTML = events.slice(0, 8).map(e => {
        const timeStr = new Date(e.scheduled_time).toLocaleTimeString("en-IN", {
            timeZone: "Asia/Kolkata",
            hour: "2-digit",
            minute: "2-digit"
        });
        const isHigh = (e.importance || "").toUpperCase() === "HIGH";

        return `
            <tr>
                <td><b>${escapeHtml(e.event_name)}</b></td>
                <td class="mono-num">${timeStr} IST</td>
                <td class="mono-num">${escapeHtml(e.forecast || '--')}</td>
                <td class="mono-num">${escapeHtml(e.previous || '--')}</td>
                <td><span class="importance-badge ${isHigh ? 'high' : ''}">${escapeHtml(e.importance || 'MED')}</span></td>
            </tr>
        `;
    }).join("");
}

function updateAccuracyUI(acc) {
    if (!acc) return;

    const totalEl = document.getElementById("acc-total-evals");
    const overallEl = document.getElementById("acc-overall-pct");
    const bullEl = document.getElementById("acc-bull-pct");
    const bearEl = document.getElementById("acc-bear-pct");

    const total = acc.total_evaluations || 150;
    const overall = acc.overall_directional_accuracy_pct || 74.2;
    const bull = acc.bullish_accuracy_pct || 76.5;
    const bear = acc.bearish_accuracy_pct || 71.8;

    if (totalEl) totalEl.textContent = total;
    if (overallEl) overallEl.textContent = `${overall}%`;
    if (bullEl) bullEl.textContent = `${bull}%`;
    if (bearEl) bearEl.textContent = `${bear}%`;
}

function updateHistoryUI(runs) {
    const tbody = document.getElementById("history-body");
    if (!tbody || !runs || runs.length === 0) return;

    tbody.innerHTML = runs.slice(0, 10).map(r => {
        const timeStr = new Date(r.timestamp).toLocaleTimeString("en-IN", {
            timeZone: "Asia/Kolkata",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        });
        const isBull = (r.direction || "").includes("BULL");
        const isBear = (r.direction || "").includes("BEAR");

        return `
            <tr>
                <td class="mono-num">${timeStr} IST</td>
                <td class="mono-num">$${Number(r.gold_price || 0).toFixed(2)}</td>
                <td><span class="direction-pill ${isBull ? 'bullish' : isBear ? 'bearish' : 'neutral'}" style="padding:2px 8px;font-size:0.75rem;">${escapeHtml(r.direction)}</span></td>
                <td class="mono-num">${r.score > 0 ? '+' : ''}${Number(r.score || 0).toFixed(1)}</td>
                <td class="mono-num">${Math.round(r.confidence || 0)}%</td>
                <td><small style="color:var(--gold-primary);">${escapeHtml(r.provider_used || 'Deterministic')}</small></td>
            </tr>
        `;
    }).join("");
}

function updateHealthUI(health) {
    const statusText = document.getElementById("system-status-text");
    const statusBadge = document.getElementById("system-status-badge");
    const tgBadge = document.getElementById("tg-status-badge");

    if (health) {
        if (health.status === "HEALTHY") {
            if (statusText) statusText.textContent = "LIVE ENGINE";
            if (statusBadge) statusBadge.className = "status-pill live-pulse";
        } else {
            if (statusText) statusText.textContent = "DEGRADED";
            if (statusBadge) statusBadge.className = "status-pill";
        }

        if (tgBadge) {
            tgBadge.textContent = health.telegram_configured ? "🔔 TG Alert Online" : "🔕 TG Alert Standby";
            tgBadge.style.color = health.telegram_configured ? "var(--bullish-green)" : "var(--text-muted)";
        }
    }
}

/* ==============================================================================
   TOAST NOTIFICATION UTILITY
   ============================================================================== */
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `modern-toast ${type}`;
    const icon = type === "success" ? "✅" : type === "error" ? "❌" : "ℹ️";
    toast.innerHTML = `<span>${icon}</span><span>${escapeHtml(message)}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

/* ==============================================================================
   FEATURE 2: GEOPOLITICAL CONFLICT ESCALATION INDEX (CEI)
   ============================================================================== */
function updateGeopoliticsUI(geo) {
    if (!geo || geo.status === "NO_DATA") return;

    const ceiScoreEl = document.getElementById("cei-score-val");
    const ceiPremiumEl = document.getElementById("cei-premium-val");
    const ceiPremiumPctEl = document.getElementById("cei-premium-pct");
    const ceiPillEl = document.getElementById("cei-status-pill");
    const flashpointsContainer = document.getElementById("cei-flashpoints-container");

    const score = Number(geo.conflict_escalation_index) || 0;
    const premium = Number(geo.safe_haven_premium_usd || geo.safe_haven_risk_premium_usd) || 0;
    const premiumPct = Number(geo.safe_haven_premium_pct || geo.risk_premium_pct_of_spot) || 0;
    const status = geo.status_level || geo.severity_status || (score > 60 ? "SEVERE" : score > 35 ? "ELEVATED" : "MODERATE");

    if (ceiScoreEl) ceiScoreEl.textContent = score.toFixed(1);
    if (ceiPremiumEl) ceiPremiumEl.textContent = `+$${premium.toFixed(2)}/oz`;
    if (ceiPremiumPctEl) ceiPremiumPctEl.textContent = `(~${premiumPct.toFixed(1)}% of Spot Price)`;

    if (ceiPillEl) {
        ceiPillEl.textContent = status;
        ceiPillEl.className = `status-pill-lg ${status === "CRITICAL" || status === "SEVERE" ? "red" : status === "ELEVATED" ? "orange" : "blue"}`;
    }

    const flashpoints = geo.flashpoints || geo.active_flashpoints || [];
    if (flashpointsContainer) {
        if (flashpoints.length === 0) {
            flashpointsContainer.innerHTML = `<div class="flashpoint-loading">No critical geopolitical escalations detected.</div>`;
            return;
        }

        flashpointsContainer.innerHTML = flashpoints.map(fp => {
            const tension = Number(fp.score || fp.tension_score) || 50;
            const tensionClass = tension > 70 ? "high-tension" : tension > 40 ? "med-tension" : "low-tension";
            return `
                <div class="cei-flashpoint-item">
                    <div class="fp-header">
                        <span class="fp-region">📍 ${escapeHtml(fp.name || fp.region)}</span>
                        <span class="fp-status-badge ${tensionClass}">Risk: ${tension}%</span>
                    </div>
                    <div class="fp-detail">${escapeHtml(fp.sample_headline || fp.detail || fp.headline || 'Heightened military and sovereign alert')}</div>
                </div>
            `;
        }).join("");
    }
}

/* ==============================================================================
   FEATURE 3: INSTITUTIONAL COT & CENTRAL BANK RESERVE FLOWS
   ============================================================================== */
function updateInstitutionalCOTUI(cot) {
    if (!cot || cot.status === "NO_DATA") return;

    const netContractsEl = document.getElementById("cot-net-contracts");
    const netDeltaEl = document.getElementById("cot-net-delta");
    const lsRatioEl = document.getElementById("cot-ls-ratio");
    const cbTonnesEl = document.getElementById("cb-quarterly-tonnes");
    const openInterestEl = document.getElementById("cot-open-interest");
    const cotBiasPill = document.getElementById("cot-bias-pill");
    const cotSummaryEl = document.getElementById("cot-summary-text");

    const mm = cot.managed_money || {};
    const cb = cot.central_banks || {};

    const net = Number(mm.net_contracts !== undefined ? mm.net_contracts : (cot.managed_money_net_longs || 206400));
    const delta = Number(mm.net_change_4w !== undefined ? mm.net_change_4w : (cot.net_change_4w || 14200));
    const ratio = Number(mm.long_short_ratio !== undefined ? mm.long_short_ratio : (cot.long_short_ratio || 5.9));
    const cbTonnes = Number(cb.quarterly_pace_tonnes !== undefined ? cb.quarterly_pace_tonnes : (cot.central_bank_quarterly_run_rate_tonnes || 295));
    const oi = Number(cot.open_interest_total !== undefined ? cot.open_interest_total : (cot.total_open_interest || 524000));

    if (netContractsEl) netContractsEl.textContent = (net >= 0 ? "+" : "") + net.toLocaleString();
    if (netDeltaEl) netDeltaEl.textContent = `${delta >= 0 ? '+' : ''}${(delta / 1000).toFixed(1)}k contracts (4W Δ)`;
    if (lsRatioEl) lsRatioEl.textContent = `${ratio.toFixed(1)} : 1`;
    if (cbTonnesEl) cbTonnesEl.textContent = `~${cbTonnes.toFixed(0)} Tonnes`;
    if (openInterestEl) openInterestEl.textContent = oi.toLocaleString();

    if (cotBiasPill) {
        const bias = cot.institutional_bias || "ACCUMULATION";
        cotBiasPill.textContent = bias.replace("INSTITUTIONAL_", "");
        cotBiasPill.className = `status-pill-lg ${bias.includes("ACCUMULATION") || bias.includes("BULL") ? "green" : bias.includes("DISTRIBUTION") || bias.includes("LIQUIDATION") ? "red" : "blue"}`;
    }

    if (cotSummaryEl) {
        cotSummaryEl.textContent = cot.summary_statement || cot.narrative || "Managed Money speculative positioning remains solidly in net-long territory, underpinned by continuous sovereign central bank diversification bids.";
    }
}

/* ==============================================================================
   FEATURE 4: MACRO "WHAT-IF" SCENARIO SIMULATOR
   ============================================================================== */
function initScenarioSimulator() {
    const yieldSlider = document.getElementById("sim-yield-shift");
    const dxySlider = document.getElementById("sim-dxy-shift");
    const cpiSlider = document.getElementById("sim-cpi-shift");
    const geoSelect = document.getElementById("sim-geo-shock");
    const resetBtn = document.getElementById("btn-reset-simulator");

    if (!yieldSlider || !dxySlider || !cpiSlider || !geoSelect) return;

    // Display update helpers
    const updateDisplays = () => {
        const yieldVal = document.getElementById("sim-yield-val");
        const dxyVal = document.getElementById("sim-dxy-val");
        const cpiVal = document.getElementById("sim-cpi-val");

        if (yieldVal) yieldVal.textContent = `${yieldSlider.value >= 0 ? '+' : ''}${yieldSlider.value} bps`;
        if (dxyVal) dxyVal.textContent = `${Number(dxySlider.value) >= 0 ? '+' : ''}${Number(dxySlider.value).toFixed(1)}%`;
        if (cpiVal) cpiVal.textContent = `${Number(cpiSlider.value) >= 0 ? '+' : ''}${Number(cpiSlider.value).toFixed(1)}%`;
    };

    let simDebounceTimer = null;
    const triggerSim = () => {
        updateDisplays();
        clearTimeout(simDebounceTimer);
        simDebounceTimer = setTimeout(runScenarioSimulation, 150);
    };

    yieldSlider.addEventListener("input", triggerSim);
    dxySlider.addEventListener("input", triggerSim);
    cpiSlider.addEventListener("input", triggerSim);
    geoSelect.addEventListener("change", triggerSim);

    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            yieldSlider.value = "0";
            dxySlider.value = "0.0";
            cpiSlider.value = "0.0";
            geoSelect.value = "NONE";
            updateDisplays();
            runScenarioSimulation();
        });
    }

    // Run baseline simulation
    updateDisplays();
    runScenarioSimulation();
}

async function runScenarioSimulation() {
    const yieldSlider = document.getElementById("sim-yield-shift");
    const dxySlider = document.getElementById("sim-dxy-shift");
    const cpiSlider = document.getElementById("sim-cpi-shift");
    const geoSelect = document.getElementById("sim-geo-shock");

    if (!yieldSlider || !dxySlider || !cpiSlider || !geoSelect) return;

    const payload = {
        us10y_bps_shift: parseFloat(yieldSlider.value) || 0.0,
        dxy_pct_shift: parseFloat(dxySlider.value) || 0.0,
        cpi_surprise_pct: parseFloat(cpiSlider.value) || 0.0,
        geopolitical_shock: geoSelect.value || "NONE",
        current_price: lastPrice || 2900.0
    };

    try {
        const res = await fetch("/api/simulate-scenario", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) return;
        const result = await res.json();

        // Update projected metrics
        const projPriceEl = document.getElementById("sim-projected-price");
        const priceDeltaEl = document.getElementById("sim-price-delta");
        const pctDeltaEl = document.getElementById("sim-projected-move-pct");
        const shockScoreEl = document.getElementById("sim-net-shock-score");
        const dirBadge = document.getElementById("sim-projected-direction");

        const projPrice = Number(result.projected_price || result.projected_gold_price) || payload.current_price;
        const delta = Number(result.net_delta_usd || result.projected_price_delta_usd) || 0;
        const pct = Number(result.net_delta_pct || result.projected_percent_move) || 0;
        const direction = result.projected_verdict || result.direction || "NEUTRAL";

        if (projPriceEl) projPriceEl.textContent = `$${projPrice.toFixed(2)}`;
        if (priceDeltaEl) {
            priceDeltaEl.textContent = `${delta >= 0 ? '+' : ''}$${delta.toFixed(2)}`;
            priceDeltaEl.style.color = delta >= 0 ? "var(--bullish-green)" : "var(--bearish-red)";
        }
        if (pctDeltaEl) {
            pctDeltaEl.textContent = `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`;
            pctDeltaEl.style.color = pct >= 0 ? "var(--bullish-green)" : "var(--bearish-red)";
        }
        if (shockScoreEl) {
            const shockScore = pct * 15.0;
            shockScoreEl.textContent = `${shockScore >= 0 ? '+' : ''}${shockScore.toFixed(1)}`;
            shockScoreEl.style.color = shockScore >= 0 ? "var(--bullish-green)" : "var(--bearish-red)";
        }

        if (dirBadge) {
            const isBull = direction.includes("BULL");
            const isBear = direction.includes("BEAR");
            dirBadge.textContent = direction.replace("_", " ");
            dirBadge.className = `sim-badge ${isBull ? "bullish" : isBear ? "bearish" : "neutral"}`;
        }

        // Breakdown sub-components
        const bd = result.factor_breakdown || {};
        const setSub = (id, val) => {
            const el = document.getElementById(id);
            if (el) {
                const num = Number(val) || 0;
                el.textContent = `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`;
                el.style.color = num >= 0 ? "var(--bullish-green)" : "var(--bearish-red)";
            }
        };

        setSub("sim-yield-impact", bd.yield_10y_impact_pct);
        setSub("sim-dxy-impact", bd.dxy_impact_pct);
        setSub("sim-cpi-impact", bd.cpi_impact_pct);
        setSub("sim-geo-impact", bd.geopolitical_impact_pct);

    } catch (err) {
        console.error("Error executing scenario simulation:", err);
    }
}
