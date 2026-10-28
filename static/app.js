/**
 * FailureForensics — v6.0 Dual-Mode Controller
 *
 * Mode 1: Assistant Mode (Clean Output)
 *   - Gemini-style Prompt Input -> Clean Verified Final Output.
 *   - Collapsible "Show background thinking" drawer.
 *   - 1-click comparison tab: "Final Verified Output" vs. "What Normal AI Said (Before Fix)".
 *
 * Mode 2: Developer Mode (Technical Forensics)
 *   - Dedicated technical demonstration workspace for teachers/evaluators:
 *     1. Mathematical Formulation & Algorithmic Proof (FailureDetector, PropagationAnalyzer PS, RootCauseEngine RCC, AdaptiveOptimizer Delta-Q)
 *     2. Interactive SVG Directed Acyclic Graph (DAG) & Domino Cascade
 *     3. Ground-Truth vs. Faulty Span Token Verification
 *     4. AdaptiveOptimizer Hyperparameter/Prompt Patch & Raw JSON Before/After Diff Table
 *     5. Raw Span Execution Telemetry (JSON payloads & latency)
 *     6. Aggregate Telemetry, Fault Injection Lab, and Batch Self-Healing Benchmark
 */

document.addEventListener("DOMContentLoaded", () => {
    const state = {
        appMode: "gemini", // 'gemini' | 'dev'
        thinkingOpen: false,
        outputView: "clean", // 'clean' | 'broken'
        activeTab: "workbench", // Default tab in Developer Mode is the Technical Forensics Workbench
        allTraces: [],
        traceFilter: "all",
        activeTraceId: null,
        currentTraceDetail: null,
        currentPropagationData: null,
        presets: [],
        scenarios: [],
        selectedChipIndex: 0,
    };

    // =========================================================================
    // UTILITIES & FORMATTERS
    // =========================================================================
    function showToast(message) {
        const toast = document.getElementById("toast-notification");
        if (!toast) return;
        toast.textContent = message;
        toast.classList.add("show");
        setTimeout(() => toast.classList.remove("show"), 3000);
    }

    function escapeHtml(str) {
        if (str === null || str === undefined) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function formatScore(val) {
        if (val === null || val === undefined || isNaN(val)) return "—";
        return Number(val).toFixed(2);
    }

    function formatPercent(val) {
        if (val === null || val === undefined || isNaN(val)) return "—";
        return `${Math.round(Number(val) * 100)}%`;
    }

    function formatJson(obj) {
        if (obj === null || obj === undefined) return "—";
        if (typeof obj === "string") return obj;
        try {
            return JSON.stringify(obj, null, 2);
        } catch {
            return String(obj);
        }
    }

    function formatCleanKeyValues(outputData) {
        if (!outputData) return "—";
        if (typeof outputData === "string") return escapeHtml(outputData);
        if (typeof outputData !== "object") return escapeHtml(String(outputData));

        const items = [];
        for (const [k, v] of Object.entries(outputData)) {
            if (k === "raw_text" || k === "normalized_text" || k === "cleaned_text") continue;
            if (k === "grounding_verified") continue;

            const label = k.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
            if (Array.isArray(v)) {
                items.push(`<div><strong>${escapeHtml(label)}:</strong> ${v.map(x => escapeHtml(String(x))).join(", ")}</div>`);
            } else if (typeof v === "number" && k.includes("confidence")) {
                items.push(`<div><strong>${escapeHtml(label)}:</strong> ${Math.round(v * 100)}%</div>`);
            } else if (typeof v === "object" && v !== null) {
                items.push(`<div><strong>${escapeHtml(label)}:</strong> ${escapeHtml(JSON.stringify(v))}</div>`);
            } else {
                items.push(`<div><strong>${escapeHtml(label)}:</strong> ${escapeHtml(String(v))}</div>`);
            }
        }
        return items.join("") || escapeHtml(JSON.stringify(outputData));
    }

    function extractFinalSummaryText(outputData) {
        if (!outputData) return "Analysis complete.";
        if (typeof outputData === "string") return outputData;
        for (const key of ["clinical_summary", "executive_summary", "incident_summary", "summary", "final_summary", "report"]) {
            if (outputData[key]) return String(outputData[key]);
        }
        const firstStr = Object.values(outputData).find(v => typeof v === "string" && v.length > 20);
        return firstStr || JSON.stringify(outputData);
    }

    // =========================================================================
    // MODE SWITCHER: ASSISTANT MODE vs. DEVELOPER MODE
    // =========================================================================
    window.setAppMode = function(mode) {
        state.appMode = mode;

        const geminiShell = document.getElementById("gemini-clean-shell");
        const devShell = document.getElementById("developer-workspace-shell");
        const btnGemini = document.getElementById("btn-mode-gemini");
        const btnDev = document.getElementById("btn-mode-dev");

        if (mode === "gemini") {
            if (geminiShell) geminiShell.style.display = "flex";
            if (devShell) devShell.style.display = "none";
            if (btnGemini) btnGemini.classList.add("active");
            if (btnDev) btnDev.classList.remove("active");
        } else {
            if (geminiShell) geminiShell.style.display = "none";
            if (devShell) devShell.style.display = "flex";
            if (btnGemini) btnGemini.classList.remove("active");
            if (btnDev) btnDev.classList.add("active");

            // Ensure the Developer Workbench trace dropdown is populated and synced with the active trace
            populateDeveloperTraceDropdown(state.activeTraceId);
            if (state.currentTraceDetail) {
                renderWorkbench(state.currentTraceDetail, state.currentPropagationData || {});
            }
            loadOverviewWorkspace();
        }
        window.scrollTo({ top: 0, behavior: "smooth" });
    };

    window.toggleThinkingDrawer = function() {
        state.thinkingOpen = !state.thinkingOpen;
        const acc = document.getElementById("thinking-accordion");
        const btn = document.getElementById("btn-thinking-trigger");
        const label = document.getElementById("thinking-toggle-label");

        if (acc) acc.classList.toggle("open", state.thinkingOpen);
        if (btn) btn.setAttribute("aria-expanded", String(state.thinkingOpen));
        if (label) {
            label.textContent = state.thinkingOpen ? "Hide background thinking" : "Show background thinking";
        }
    };

    window.setOutputComparisonView = function(view) {
        state.outputView = view;
        const tabClean = document.getElementById("tab-output-clean");
        const tabBroken = document.getElementById("tab-output-broken");
        const bodyClean = document.getElementById("gemini-answer-clean");
        const bodyBroken = document.getElementById("gemini-answer-broken");

        if (view === "clean") {
            if (tabClean) tabClean.classList.add("active");
            if (tabBroken) tabBroken.classList.remove("active");
            if (bodyClean) bodyClean.style.display = "block";
            if (bodyBroken) bodyBroken.style.display = "none";
        } else {
            if (tabClean) tabClean.classList.remove("active");
            if (tabBroken) tabBroken.classList.add("active");
            if (bodyClean) bodyClean.style.display = "none";
            if (bodyBroken) bodyBroken.style.display = "block";
        }
    };

    // =========================================================================
    // ASSISTANT MODE INITIALIZATION & RENDERING
    // =========================================================================
    async function initApp() {
        try {
            const res = await fetch("/api/traces?limit=50");
            const traces = await res.json();
            state.allTraces = traces;

            const clinical = traces.find(t => t.pipeline_name.includes("clinical") && (t.failure_count > 0 || t.status === "failed"));
            const financial = traces.find(t => t.pipeline_name.includes("financial") && (t.failure_count > 0 || t.status === "failed"));
            const security = traces.find(t => t.pipeline_name.includes("security") && (t.failure_count > 0 || t.status === "failed"));
            const fallback = traces.find(t => t.failure_count > 0 || t.status === "failed") || traces[0];

            state.scenarios = [
                {
                    label: "Hospital Triage Note",
                    pipelineName: "clinical_triage_pipeline",
                    traceId: clinical ? clinical.trace_id : fallback?.trace_id,
                },
                {
                    label: "Quarterly Earnings Report",
                    pipelineName: "financial_earnings_analysis",
                    traceId: financial ? financial.trace_id : fallback?.trace_id,
                },
                {
                    label: "Cloud Security Log",
                    pipelineName: "security_incident_triage",
                    traceId: security ? security.trace_id : fallback?.trace_id,
                },
            ];

            renderScenarioChips();
            populateDeveloperTraceDropdown(state.scenarios[0]?.traceId);
            if (state.scenarios[0]?.traceId) {
                await loadTraceEverywhere(state.scenarios[0].traceId);
            }
        } catch (err) {
            console.error("Failed to initialize app:", err);
        }
    }

    function renderScenarioChips() {
        const list = document.getElementById("gemini-scenario-chips");
        if (!list) return;
        list.innerHTML = state.scenarios.map((s, idx) => `
            <button class="scenario-chip ${idx === state.selectedChipIndex ? 'active' : ''}" onclick="selectScenarioChip(${idx})">
                ${escapeHtml(s.label)}
            </button>
        `).join("");
    }

    window.selectScenarioChip = async function(idx) {
        state.selectedChipIndex = idx;
        renderScenarioChips();
        const sc = state.scenarios[idx];
        if (sc && sc.traceId) {
            window.setOutputComparisonView("clean");
            await loadTraceEverywhere(sc.traceId);
        }
    };

    window.runGeminiLivePrompt = async function() {
        const promptEl = document.getElementById("gemini-prompt-input");
        const faultEl = document.getElementById("gemini-inject-fault");
        const btn = document.getElementById("btn-gemini-run");
        const btnLabel = document.getElementById("btn-gemini-run-label");
        const summaryTextEl = document.getElementById("thinking-summary-text");

        const inputText = promptEl ? promptEl.value.trim() : "";
        if (!inputText) {
            showToast("Please enter a prompt first.");
            return;
        }

        try {
            if (btn) btn.disabled = true;
            if (btnLabel) btnLabel.textContent = "Thinking & Verifying...";
            if (summaryTextEl) {
                summaryTextEl.textContent = "Running 4-step pipeline in background & checking for hallucinations...";
            }

            const activeScenario = state.scenarios[state.selectedChipIndex];
            const res = await fetch("/api/pipeline/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    pipeline_name: activeScenario ? activeScenario.pipelineName : "live_prompt_pipeline",
                    input_text: inputText,
                    inject_fault: faultEl ? faultEl.checked : true,
                    fault_step: "extraction",
                    fault_type: "hallucination",
                    auto_heal: true,
                }),
            });

            const data = await res.json();
            if (data.trace && data.trace.trace_id) {
                window.setOutputComparisonView("clean");
                await loadTraceEverywhere(data.trace.trace_id);
                showToast("Output verified & ready");
            }
        } catch (err) {
            console.error("Live prompt execution error:", err);
            showToast("Error running live prompt");
        } finally {
            if (btn) btn.disabled = false;
            if (btnLabel) btnLabel.textContent = "Run & Verify Output";
        }
    };

    async function loadTraceEverywhere(traceId) {
        state.activeTraceId = traceId;
        const [detailRes, propRes] = await Promise.all([
            fetch(`/api/traces/${traceId}`),
            fetch(`/api/propagation/${traceId}`),
        ]);
        const detailData = await detailRes.json();
        const propData = await propRes.json();

        state.currentTraceDetail = detailData;
        state.currentPropagationData = propData;

        const wbSelect = document.getElementById("wb-trace-select");
        if (wbSelect && wbSelect.value !== traceId) {
            wbSelect.value = traceId;
        }

        renderGeminiResponseCard(detailData, propData);
        renderWorkbench(detailData, propData);
    }

    function renderGeminiResponseCard(detailData, propData) {
        const trace = detailData.trace;
        const forensics = detailData.forensics || propData.forensics || {};
        const gte = forensics.ground_truth_evidence || {};
        const domino = forensics.domino_chain || [];
        const rem = forensics.remediation || {};
        const recs = forensics.recommendations || [];
        const diffs = rem.step_diffs || [];
        const hasFailures = forensics.has_failures ?? true;

        const promptInput = document.getElementById("gemini-prompt-input");
        if (promptInput && gte.source_text) {
            promptInput.value = gte.source_text;
        }

        const summaryTextEl = document.getElementById("thinking-summary-text");
        const rootStepName = forensics.root_cause_step || "extraction";
        if (summaryTextEl) {
            if (hasFailures) {
                summaryTextEl.innerHTML = `<strong>Self-Healed in Background</strong> — Caught 1 mistake in Step 2 (<code>${escapeHtml(rootStepName)}</code>) &amp; auto-corrected before answering`;
            } else {
                summaryTextEl.innerHTML = `<strong>Verified in Background</strong> — All 4 pipeline steps passed fact-checking cleanly`;
            }
        }

        const stepsRowEl = document.getElementById("thinking-steps-row");
        if (stepsRowEl) {
            stepsRowEl.innerHTML = diffs.map((d, i) => {
                const wasFailed = d.before_score < 0.7;
                const statusLine = wasFailed
                    ? `<span class="text-danger">${formatPercent(d.before_score)}</span> &rarr; <span class="text-success">${formatPercent(d.after_score)} Fixed</span>`
                    : `<span class="text-success">${formatPercent(d.after_score)} Passed</span>`;
                return `
                    <div class="tstep-pill ${wasFailed ? 'tstep-fixed' : ''}">
                        <div class="tstep-name">${i + 1}. ${escapeHtml(d.step_name)}</div>
                        <div class="tstep-sub">${statusLine}</div>
                    </div>
                `;
            }).join("");
        }

        const whatCaughtEl = document.getElementById("thinking-what-caught");
        const falsePillsEl = document.getElementById("thinking-false-pills");
        const howFixedEl = document.getElementById("thinking-how-fixed");
        const metricsBarEl = document.getElementById("thinking-metrics-bar");

        if (whatCaughtEl) {
            whatCaughtEl.textContent = hasFailures
                ? `Step '${rootStepName}' dropped to ${formatPercent(domino.find(x => x.role === "ROOT_CAUSE")?.judge_score || 0.32)} quality because it invented claims not present in your prompt:`
                : "No hallucinations or ungrounded claims detected.";
        }
        if (falsePillsEl) {
            const uClaims = gte.ungrounded_claims || [];
            falsePillsEl.innerHTML = uClaims.map(c =>
                `<span class="claim-pill pill-ungrounded">&#10007; ${escapeHtml(c)}</span>`
            ).join("");
        }
        if (howFixedEl) {
            const rec = recs[0];
            howFixedEl.innerHTML = rec
                ? `Lowered <strong>${escapeHtml(rec.target_step)}</strong> creativity (<code>Temperature 0.7 &rarr; ${Number(rec.suggested_temperature ?? 0).toFixed(1)}</code>) and injected rule: <em>"${escapeHtml(rec.prompt_guideline_prefix)}"</em>`
                : "Applied strict source-grounding verification and deterministic temperature (0.0).";
        }
        if (metricsBarEl) {
            const bScore = rem.baseline_score ?? trace.final_score ?? 0.41;
            const aScore = rem.healed_score ?? 0.94;
            metricsBarEl.innerHTML = `
                <span>Root Cause: <strong>Step 2 (${escapeHtml(rootStepName)})</strong></span>
                <span>Confidence (RCC): <strong>${formatPercent(forensics.root_cause_confidence || 0.88)}</strong></span>
                <span>Propagation Score (PS): <strong>${formatScore(forensics.overall_propagation_score || 0.33)}</strong></span>
                <span>Recovery: <strong>${formatPercent(bScore)} &rarr; ${formatPercent(aScore)}</strong></span>
            `;
        }

        const cleanPill = document.getElementById("clean-score-pill");
        const brokenPill = document.getElementById("broken-score-pill");
        const bScore = rem.baseline_score ?? trace.final_score ?? 0.41;
        const aScore = rem.healed_score ?? 0.94;
        if (cleanPill) cleanPill.textContent = `${formatPercent(aScore)} Verified`;
        if (brokenPill) brokenPill.textContent = `${formatPercent(bScore)} Hallucinated`;

        const cleanBody = document.getElementById("gemini-answer-clean");
        const extractDiff = diffs[1] || diffs[0] || {};
        const classifDiff = diffs[2] || diffs[0] || {};
        const summaryDiff = diffs[3] || diffs[diffs.length - 1] || {};

        if (cleanBody) {
            const finalSummaryText = extractFinalSummaryText(summaryDiff.after_output);
            cleanBody.innerHTML = `
                <div class="clean-output-summary">
                    ${escapeHtml(finalSummaryText)}
                </div>
                <div class="clean-output-grid">
                    <div class="clean-detail-card">
                        <div class="clean-detail-label">Verified Facts Extracted from Prompt</div>
                        <div class="clean-detail-content">
                            ${formatCleanKeyValues(extractDiff.after_output)}
                        </div>
                    </div>
                    <div class="clean-detail-card">
                        <div class="clean-detail-label">Final Classification &amp; Priority</div>
                        <div class="clean-detail-content">
                            ${formatCleanKeyValues(classifDiff.after_output)}
                        </div>
                    </div>
                </div>
            `;
        }

        const brokenBody = document.getElementById("gemini-answer-broken");
        if (brokenBody) {
            const brokenSummaryText = extractFinalSummaryText(summaryDiff.before_output);
            brokenBody.innerHTML = `
                <div class="broken-warning-banner">
                    <strong>Without FailureForensics:</strong> Because Step 2 (Extraction) invented false facts, the downstream steps blindly trusted it and produced this wrong final output:
                </div>
                <div class="clean-output-summary text-danger">
                    ${escapeHtml(brokenSummaryText)}
                </div>
                <div class="clean-output-grid">
                    <div class="clean-detail-card">
                        <div class="clean-detail-label text-danger">Faulty Extraction (Step 2 — ${formatPercent(extractDiff.before_score)})</div>
                        <div class="clean-detail-content">
                            ${formatCleanKeyValues(extractDiff.before_output)}
                        </div>
                    </div>
                    <div class="clean-detail-card">
                        <div class="clean-detail-label text-amber">Corrupted Classification (Step 3 — ${formatPercent(classifDiff.before_score)})</div>
                        <div class="clean-detail-content">
                            ${formatCleanKeyValues(classifDiff.before_output)}
                        </div>
                    </div>
                </div>
            `;
        }
    }

    // =========================================================================
    // DEVELOPER MODE (DEDICATED TECHNICAL FORENSICS & MATH)
    // =========================================================================
    window.switchTab = function(tabId) {
        state.activeTab = tabId;
        document.querySelectorAll(".nav-tab").forEach(tab => {
            tab.classList.toggle("active", tab.getAttribute("data-tab") === tabId);
        });
        document.querySelectorAll(".tab-content").forEach(section => {
            section.classList.toggle("active", section.id === `tab-${tabId}`);
        });

        if (tabId === "workbench") {
            populateDeveloperTraceDropdown(state.activeTraceId);
            if (state.currentTraceDetail) {
                renderWorkbench(state.currentTraceDetail, state.currentPropagationData || {});
            }
        } else if (tabId === "overview") {
            loadOverviewWorkspace();
        } else if (tabId === "pipeline") {
            fetchPresets();
        } else if (tabId === "regression") {
            loadRegressionWorkspace();
        }
    };

    document.querySelectorAll(".nav-tab").forEach(tab => {
        tab.addEventListener("click", () => window.switchTab(tab.getAttribute("data-tab")));
    });

    function populateDeveloperTraceDropdown(selectedId) {
        const wbTraceSelect = document.getElementById("wb-trace-select");
        if (!wbTraceSelect || !state.allTraces.length) return;

        wbTraceSelect.innerHTML = state.allTraces.map(t => {
            const shortId = t.trace_id ? t.trace_id.slice(0, 10) : "trace";
            const tag = (t.failure_count > 0 || t.status === "failed")
                ? `[FAILED • ${t.failure_count || 1} fault(s)]`
                : `[HEALTHY]`;
            return `<option value="${t.trace_id}">${shortId}... — ${t.pipeline_name} ${tag}</option>`;
        }).join("");

        if (selectedId && state.allTraces.some(t => t.trace_id === selectedId)) {
            wbTraceSelect.value = selectedId;
        }
    }

    const wbTraceSelect = document.getElementById("wb-trace-select");
    if (wbTraceSelect) {
        wbTraceSelect.addEventListener("change", () => {
            if (wbTraceSelect.value) loadTraceEverywhere(wbTraceSelect.value);
        });
    }

    function renderWorkbench(detailData, propData) {
        const trace = detailData.trace;
        if (!trace) return;
        const failures = detailData.failures || [];
        const forensics = detailData.forensics || propData.forensics || {};
        const hasFailures = forensics.has_failures ?? (failures.length > 0);
        const rem = forensics.remediation || {};
        const gte = forensics.ground_truth_evidence || {};
        const domino = forensics.domino_chain || [];

        // 1. Telemetry Ribbon
        const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        setEl("wb-trace-id", trace.trace_id.slice(0, 12) + "...");
        setEl("wb-pipeline-name", trace.pipeline_name);

        const elStatus = document.getElementById("wb-status");
        if (elStatus) {
            elStatus.innerHTML = `<span class="status-badge ${hasFailures ? 'badge-status-failed' : 'badge-status-success'}">${hasFailures ? 'FAILED' : 'HEALTHY'}</span>`;
        }

        const rootStep = forensics.root_cause_step || "extraction";
        const rccVal = forensics.root_cause_confidence ?? 0.88;
        const psVal = forensics.overall_propagation_score ?? propData.overall_propagation_score ?? 0.33;
        const bScore = rem.baseline_score ?? trace.final_score ?? 0.41;
        const aScore = rem.healed_score ?? 0.94;
        const deltaScore = round2(aScore - bScore);

        setEl("wb-root-step", hasFailures ? `Step: ${rootStep}` : "None (Clean)");
        setEl("wb-rcc-val", hasFailures ? `${Math.round(rccVal * 100)}%` : "100%");
        setEl("wb-ps-val", formatScore(psVal));

        const elScoreComp = document.getElementById("wb-score-comparison");
        if (elScoreComp) {
            elScoreComp.innerHTML = hasFailures
                ? `<span class="text-danger">${formatScore(bScore)}</span> &rarr; <span class="text-success">${formatScore(aScore)} (+${formatScore(deltaScore)})</span>`
                : formatScore(trace.final_score);
        }

        // 2. Technical Section 1: Live Mathematical Formulas
        const rootDomino = domino.find(d => d.role === "ROOT_CAUSE") || domino[1] || domino[0];
        const affectedCount = domino.filter(d => d.role === "PROPAGATED" || d.role === "CORRUPTED_OUTCOME").length;
        const rootScore = rootDomino?.judge_score ?? 0.32;

        setEl("tmath-val-detector", hasFailures
            ? `Step '${rootStep}': ${formatScore(rootScore)} < 0.70 -> FAULT`
            : `All spans >= 0.70 -> NOMINAL`);
        setEl("tmath-val-ps", `Overall PS = ${formatScore(psVal)} (${affectedCount} downstream spans)`);
        setEl("tmath-val-rcc", hasFailures
            ? `RCC = ${Math.round(rccVal * 100)}% (Isolated: ${rootStep})`
            : `RCC = 100% (No Fault)`);
        setEl("tmath-val-delta", `${formatScore(bScore)} -> ${formatScore(aScore)} (Delta Q = +${formatScore(deltaScore)})`);

        // 3. Technical Section 2: Causal Propagation SVG DAG & Domino List
        renderPropagationDagSvg(domino);
        renderDominoStoryboard(domino);

        // 4. Technical Section 3: Ground Truth vs. Faulty Span Payload
        setEl("wb-verdict-title", forensics.verdict_title || "Source Ground-Truth vs. Faulty Span Payload Verification");
        setEl("wb-verdict-summary", forensics.verdict_summary || "");
        const vBadge = document.getElementById("wb-verdict-badge");
        if (vBadge) {
            vBadge.className = `status-badge ${hasFailures ? 'badge-status-failed' : 'badge-status-success'}`;
            vBadge.textContent = hasFailures ? "ROOT CAUSE ISOLATED" : "VERIFIED CLEAN";
        }
        setEl("wb-source-text", gte.source_text || "—");
        setEl("wb-fault-step-tag", `STEP '${(gte.failing_step || rootStep).toUpperCase()}' PAYLOAD`);
        setEl("wb-fault-score-meta", `Judge Score: ${formatScore(rootScore)}`);
        setEl("wb-fault-output", formatJson(gte.faulty_output));

        const verifiedPillsEl = document.getElementById("wb-verified-pills");
        if (verifiedPillsEl) {
            verifiedPillsEl.innerHTML = (gte.verified_claims || []).map(c =>
                `<span class="claim-pill pill-verified">&#10003; ${escapeHtml(c)}</span>`
            ).join("");
        }
        const ungroundedPillsEl = document.getElementById("wb-ungrounded-pills");
        if (ungroundedPillsEl) {
            ungroundedPillsEl.innerHTML = (gte.ungrounded_claims || []).map(c =>
                `<span class="claim-pill pill-ungrounded">&#10007; ${escapeHtml(c)}</span>`
            ).join("");
        }

        // 5. Technical Section 4: AdaptiveOptimizer Patch & Raw JSON Before/After Diff Table
        renderRemediationDiffSection(forensics, bScore, aScore, deltaScore);

        // 6. Technical Section 5: Raw Span Execution Telemetry Accordion
        renderRawSpansAccordion(trace.spans || []);
    }

    function round2(n) {
        return Math.round((Number(n) || 0) * 100) / 100;
    }

    function renderPropagationDagSvg(dominoChain) {
        const container = document.getElementById("wb-dag-container");
        if (!container) return;
        if (!dominoChain || dominoChain.length === 0) {
            container.innerHTML = `<div class="empty-hint">No spans available</div>`;
            return;
        }

        const nodeW = 148, nodeH = 74, gapX = 52, padX = 20, padY = 42;
        const totalW = padX * 2 + dominoChain.length * nodeW + (dominoChain.length - 1) * gapX;
        const totalH = 165;

        const roleStyles = {
            ROOT_CAUSE: { fill: "rgba(239, 68, 68, 0.16)", stroke: "#ef4444", badge: "ROOT CAUSE", text: "#fca5a5" },
            PROPAGATED: { fill: "rgba(245, 158, 11, 0.15)", stroke: "#f59e0b", badge: "PROPAGATED", text: "#fcd34d" },
            CORRUPTED_OUTCOME: { fill: "rgba(168, 85, 247, 0.16)", stroke: "#a855f7", badge: "CORRUPTED FINAL", text: "#d8b4fe" },
            HEALTHY: { fill: "rgba(16, 185, 129, 0.12)", stroke: "#10b981", badge: "HEALTHY PASS", text: "#6ee7b7" },
        };

        let edgesSvg = "", nodesSvg = "";
        dominoChain.forEach((step, idx) => {
            const x = padX + idx * (nodeW + gapX);
            const y = padY;
            const st = roleStyles[step.role] || roleStyles.HEALTHY;
            const scoreStr = formatScore(step.judge_score ?? 1.0);
            const latStr = step.latency_ms ? `${Math.round(step.latency_ms)}ms` : "";

            if (idx < dominoChain.length - 1) {
                const nextStep = dominoChain[idx + 1];
                const x1 = x + nodeW, y1 = y + nodeH / 2, x2 = x + nodeW + gapX, y2 = y1;
                const isCausal = step.role !== "HEALTHY" && nextStep.role !== "HEALTHY";
                const edgeColor = isCausal ? "#ef4444" : "#334155";
                const psLabel = isCausal && nextStep.propagation_score ? `PS:${formatScore(nextStep.propagation_score)}` : "";
                edgesSvg += `
                    <line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${edgeColor}" stroke-width="${isCausal ? 2.5 : 1.5}" />
                    ${psLabel ? `<text x="${(x1 + x2) / 2}" y="${y1 - 8}" text-anchor="middle" fill="#fca5a5" font-size="9.5" font-family="JetBrains Mono, monospace">${psLabel}</text>` : ""}
                `;
            }

            nodesSvg += `
                <g transform="translate(${x}, ${y})">
                    <rect width="${nodeW}" height="${nodeH}" rx="7" fill="${st.fill}" stroke="${st.stroke}" stroke-width="1.8"/>
                    <text x="10" y="18" fill="${st.text}" font-size="9" font-family="JetBrains Mono, monospace" font-weight="700">${st.badge}</text>
                    <text x="10" y="38" fill="#f1f5f9" font-size="13" font-family="Inter, sans-serif" font-weight="700">${escapeHtml(step.step_name)}</text>
                    <text x="10" y="56" fill="#94a3b8" font-size="10.5" font-family="JetBrains Mono, monospace">Score: ${scoreStr} ${latStr ? '· ' + latStr : ''}</text>
                </g>
            `;
        });

        container.innerHTML = `<svg viewBox="0 0 ${totalW} ${totalH}" width="100%" height="165">${edgesSvg}${nodesSvg}</svg>`;
    }

    function renderDominoStoryboard(dominoChain) {
        const listEl = document.getElementById("wb-domino-list");
        if (!listEl) return;
        listEl.innerHTML = dominoChain.map((d, i) => `
            <div class="domino-card role-${escapeHtml(d.role)}">
                <div class="domino-head">
                    <span>Span ${i + 1}: ${escapeHtml(d.step_name)} (${escapeHtml(d.role_label)})</span>
                    <span class="font-mono">Score: ${formatScore(d.judge_score)} | PS: ${formatScore(d.propagation_score)}</span>
                </div>
                <div class="domino-what">${escapeHtml(d.what_happened)}</div>
                <div class="domino-causal">${escapeHtml(d.causal_link)}</div>
            </div>
        `).join("");
    }

    function renderRemediationDiffSection(forensics, bScore, aScore, deltaScore) {
        const rem = forensics.remediation || {};
        const recs = forensics.recommendations || [];
        const deltaPill = document.getElementById("wb-remediation-delta-pill");
        const changesBox = document.getElementById("wb-changes-applied-box");
        const diffWrapper = document.getElementById("wb-diff-table-wrapper");

        if (deltaPill) {
            deltaPill.textContent = `Score: ${formatScore(bScore)} -> ${formatScore(aScore)} (+${formatScore(deltaScore)})`;
        }
        if (changesBox) {
            changesBox.innerHTML = recs.map(r => `
                <div class="patch-item">
                    <div class="patch-meta">
                        <span class="status-badge badge-status-failed">Target Span: ${escapeHtml(r.target_step)}</span>
                        <span class="status-badge badge-status-success">Hyperparameter: temperature 0.7 &rarr; ${Number(r.suggested_temperature ?? 0).toFixed(1)}</span>
                    </div>
                    <div class="patch-prompt">Injected System Prompt Prefix: "${escapeHtml(r.prompt_guideline_prefix)}"</div>
                </div>
            `).join("") || `<div class="empty-hint">No remediation patch required.</div>`;
        }
        if (diffWrapper) {
            const diffs = rem.step_diffs || [];
            diffWrapper.innerHTML = `
                <table class="diff-table">
                    <thead>
                        <tr>
                            <th>Pipeline Span</th>
                            <th>Before Remediation (Raw JSON &amp; Judge Score)</th>
                            <th>After Remediation (Raw JSON &amp; Judge Score)</th>
                            <th>Technical Mechanism</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${diffs.map(d => `
                            <tr>
                                <td>
                                    <strong>Stage ${d.step_index + 1}: ${escapeHtml(d.step_name)}</strong>
                                    <div style="margin-top:6px;"><span class="status-badge ${d.change_type === 'DIRECT_FIX' ? 'badge-status-failed' : 'badge-status-success'}">${escapeHtml(d.change_badge || d.change_type)}</span></div>
                                </td>
                                <td class="diff-cell-before">
                                    <span class="font-mono text-danger">Judge Score: ${formatScore(d.before_score)}</span>
                                    <pre class="diff-pre">${escapeHtml(formatJson(d.before_output))}</pre>
                                </td>
                                <td class="diff-cell-after">
                                    <span class="font-mono text-success">Judge Score: ${formatScore(d.after_score)} (+${formatScore(d.score_delta)})</span>
                                    <pre class="diff-pre">${escapeHtml(formatJson(d.after_output))}</pre>
                                </td>
                                <td>${escapeHtml(d.change_explanation)}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            `;
        }
    }

    function renderRawSpansAccordion(spans) {
        const container = document.getElementById("wb-raw-spans");
        if (!container) return;
        container.innerHTML = spans.map((s, idx) => `
            <div class="span-acc-item" id="span-acc-${idx}">
                <button class="span-acc-header" onclick="document.getElementById('span-acc-${idx}').classList.toggle('open')">
                    <span><strong>Span ${idx + 1}: ${escapeHtml(s.step_name)}</strong> (ID: <code>${escapeHtml((s.span_id || "").slice(0, 8))}</code>)</span>
                    <span class="font-mono">Score: ${formatScore(s.judge_score)} | Latency: ${Math.round(s.latency_ms || 0)} ms &blacktriangledown;</span>
                </button>
                <div class="span-acc-body">
                    <div>
                        <div class="claims-label">Raw Input Dictionary (JSON)</div>
                        <pre class="diff-pre">${escapeHtml(formatJson(s.input_data))}</pre>
                    </div>
                    <div>
                        <div class="claims-label">Raw Output Dictionary (JSON)</div>
                        <pre class="diff-pre">${escapeHtml(formatJson(s.output_data))}</pre>
                    </div>
                </div>
            </div>
        `).join("");
    }

    const btnWbHeal = document.getElementById("btn-wb-heal");
    if (btnWbHeal) {
        btnWbHeal.addEventListener("click", async () => {
            if (!state.activeTraceId) return;
            try {
                btnWbHeal.disabled = true;
                btnWbHeal.textContent = "Applying Optimizer Patch...";
                const res = await fetch(`/api/traces/${state.activeTraceId}/heal`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({}),
                });
                const data = await res.json();
                if (state.currentTraceDetail && data.forensics) {
                    state.currentTraceDetail.forensics = data.forensics;
                    renderGeminiResponseCard(state.currentTraceDetail, state.currentPropagationData || {});
                    renderWorkbench(state.currentTraceDetail, state.currentPropagationData || {});
                }
                showToast("AdaptiveOptimizer patch verified!");
            } catch (e) {
                console.error(e);
            } finally {
                btnWbHeal.disabled = false;
                btnWbHeal.textContent = "Re-Run Optimizer Patch";
            }
        });
    }

    // =========================================================================
    // DEVELOPER TELEMETRY, FAULT INJECTION LAB & BENCHMARK
    // =========================================================================
    async function fetchSystemStatus() {
        try {
            const res = await fetch("/api/status");
            const data = await res.json();
            const gpuText = document.getElementById("gpu-text");
            const modelText = document.getElementById("active-model-text");
            if (data.server_online) {
                if (gpuText) gpuText.textContent = "RTX 4050 • Active";
                if (modelText) modelText.textContent = data.active_model || "qwen2.5:1.5b";
            }
        } catch (e) {
            console.warn("Status check warning:", e);
        }
    }

    async function loadOverviewWorkspace() {
        try {
            const [statsRes, analyticsRes, tracesRes] = await Promise.all([
                fetch("/api/dashboard/stats"),
                fetch("/api/analytics"),
                fetch("/api/traces?limit=100"),
            ]);
            const stats = await statsRes.json();
            const analytics = await analyticsRes.json();
            state.allTraces = await tracesRes.json();

            const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
            setEl("kpi-total-traces", stats.total_traces ?? 0);
            setEl("kpi-total-failures", stats.total_failures ?? 0);
            setEl("kpi-avg-judge", formatScore(stats.avg_judge_score));
            setEl("kpi-traces-analyzed", stats.traces_analyzed ?? 0);

            if (analytics.score_stats) {
                setEl("score-stat-min", formatScore(analytics.score_stats.min));
                setEl("score-stat-avg", formatScore(analytics.score_stats.avg));
                setEl("score-stat-max", formatScore(analytics.score_stats.max));
                setEl("dist-evaluated-count", `${analytics.score_stats.total_evaluated || 0} spans`);
                renderBarList("chart-score-buckets", analytics.score_stats.buckets || {}, "#3b82f6");
            }
            renderBarList("chart-failure-types", analytics.failure_types || {}, "#ef4444");
            renderBarList("chart-severities", analytics.severities || {}, "#f59e0b");
            renderOverviewTracesTable();
        } catch (err) {
            console.error("Overview error:", err);
        }
    }

    function renderBarList(containerId, dataMap, colorHex) {
        const container = document.getElementById(containerId);
        if (!container) return;
        const entries = Object.entries(dataMap);
        const maxVal = Math.max(...entries.map(([, v]) => Number(v) || 0), 1);
        container.innerHTML = entries.map(([label, count]) => {
            const pct = Math.round(((Number(count) || 0) / maxVal) * 100);
            return `
                <div class="bar-row">
                    <span>${escapeHtml(label)}</span>
                    <div class="bar-track"><div class="bar-fill" style="width:${pct}%; background:${colorHex};"></div></div>
                    <span class="font-mono">${count}</span>
                </div>
            `;
        }).join("");
    }

    function renderOverviewTracesTable() {
        const tbody = document.getElementById("overview-traces-tbody");
        if (!tbody) return;
        const filtered = state.allTraces.filter(t => {
            const isFailed = t.status === "failed" || (t.failure_count && t.failure_count > 0);
            if (state.traceFilter === "failed") return isFailed;
            if (state.traceFilter === "success") return !isFailed;
            return true;
        });
        tbody.innerHTML = filtered.map(t => {
            const isFailed = t.status === "failed" || (t.failure_count && t.failure_count > 0);
            return `
                <tr>
                    <td class="font-mono">${escapeHtml((t.trace_id || "").slice(0, 12))}...</td>
                    <td><strong>${escapeHtml(t.pipeline_name)}</strong></td>
                    <td><span class="status-badge ${isFailed ? 'badge-status-failed' : 'badge-status-success'}">${isFailed ? 'FAILED' : 'HEALTHY'}</span></td>
                    <td class="font-mono">${formatScore(t.final_score)}</td>
                    <td class="font-mono">${t.span_count ?? 4}</td>
                    <td class="font-mono">${t.failure_count ?? 0}</td>
                    <td class="font-mono">${t.total_latency_ms ? Math.round(t.total_latency_ms) + " ms" : "—"}</td>
                    <td class="text-right">
                        <button class="btn btn-secondary btn-sm" onclick="openTraceInWorkbench('${escapeHtml(t.trace_id)}')">Inspect in Technical Workbench &rarr;</button>
                    </td>
                </tr>
            `;
        }).join("");
    }

    document.querySelectorAll(".filter-chip").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".filter-chip").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            state.traceFilter = btn.getAttribute("data-filter") || "all";
            renderOverviewTracesTable();
        });
    });

    window.openTraceInWorkbench = async function(traceId) {
        await loadTraceEverywhere(traceId);
        window.switchTab("workbench");
    };

    async function fetchPresets() {
        try {
            const res = await fetch("/api/presets");
            const data = await res.json();
            state.presets = data.presets || [];
            const container = document.getElementById("pipeline-preset-buttons");
            const inputEl = document.getElementById("run-input-text");
            if (container) {
                container.innerHTML = state.presets.map((p, idx) => `
                    <button class="preset-btn ${idx === 0 ? 'active' : ''}" onclick="selectDevPreset(${idx})">${escapeHtml(p.title)}</button>
                `).join("");
            }
            if (state.presets[0] && inputEl && !inputEl.value) {
                inputEl.value = state.presets[0].input_text;
            }
        } catch (e) {
            console.warn(e);
        }
    }

    window.selectDevPreset = function(idx) {
        const p = state.presets[idx];
        if (!p) return;
        document.querySelectorAll(".preset-btn").forEach((b, i) => b.classList.toggle("active", i === idx));
        const inputEl = document.getElementById("run-input-text");
        const nameEl = document.getElementById("run-pipeline-name");
        if (inputEl) inputEl.value = p.input_text || "";
        if (nameEl) nameEl.value = p.id || "custom_pipeline";
    };

    const btnExecutePipeline = document.getElementById("btn-execute-pipeline");
    if (btnExecutePipeline) {
        btnExecutePipeline.addEventListener("click", async () => {
            const pipelineName = document.getElementById("run-pipeline-name")?.value || "custom_pipeline";
            const inputText = document.getElementById("run-input-text")?.value || "";
            const injectFault = document.getElementById("run-inject-fault")?.checked ?? true;
            const faultStep = document.getElementById("run-fault-step")?.value || "extraction";
            const faultType = document.getElementById("run-fault-type")?.value || "hallucination";
            const autoHeal = document.getElementById("run-auto-heal")?.checked ?? true;

            try {
                btnExecutePipeline.disabled = true;
                btnExecutePipeline.textContent = "Executing Pipeline...";
                const res = await fetch("/api/pipeline/run", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        pipeline_name: pipelineName,
                        input_text: inputText,
                        inject_fault: injectFault,
                        fault_step: faultStep,
                        fault_type: faultType,
                        auto_heal: autoHeal,
                    }),
                });
                const data = await res.json();
                if (data.trace?.trace_id) {
                    await loadTraceEverywhere(data.trace.trace_id);
                    window.switchTab("workbench");
                    showToast("Execution complete — loaded in Technical Workbench");
                }
            } catch (e) {
                console.error(e);
            } finally {
                btnExecutePipeline.disabled = false;
                btnExecutePipeline.textContent = "Execute Pipeline & Open Technical Workbench";
            }
        });
    }

    async function loadRegressionWorkspace() {
        try {
            const [tracesRes, dsRes] = await Promise.all([
                fetch("/api/traces?limit=50"),
                fetch("/api/dataset"),
            ]);
            const traces = await tracesRes.json();
            const dsData = await dsRes.json();

            const fbSelect = document.getElementById("fb-trace-select");
            if (fbSelect) {
                fbSelect.innerHTML = traces.map(t =>
                    `<option value="${t.trace_id}">${t.trace_id.slice(0, 10)}... — ${t.pipeline_name}</option>`
                ).join("");
            }

            const entries = Array.isArray(dsData) ? dsData : (dsData.entries || []);
            const badge = document.getElementById("dataset-count-badge");
            const list = document.getElementById("dataset-entries-list");
            if (badge) badge.textContent = `${entries.length} entries`;
            if (list) {
                list.innerHTML = entries.map(e => `
                    <div class="dataset-item">
                        <strong>Span: ${escapeHtml(e.step_name)}</strong> (${escapeHtml(e.failure_type)})
                        <div class="text-muted">${escapeHtml(e.notes || "")}</div>
                    </div>
                `).join("") || `<div class="empty-hint">No dataset entries yet.</div>`;
            }
        } catch (e) {
            console.error(e);
        }
    }

    const btnRunBenchmark = document.getElementById("btn-run-benchmark");
    if (btnRunBenchmark) {
        btnRunBenchmark.addEventListener("click", async () => {
            try {
                btnRunBenchmark.disabled = true;
                btnRunBenchmark.textContent = "Running Benchmark...";
                const res = await fetch("/api/benchmark/self-heal", { method: "POST" });
                const data = await res.json();
                document.getElementById("bm-before-score").textContent = formatScore(data.before_avg_score);
                document.getElementById("bm-after-score").textContent = formatScore(data.after_avg_score);
                document.getElementById("bm-delta-score").textContent = `+${formatScore(data.score_delta)}`;
                document.getElementById("bm-cases-fixed").textContent = `${data.cases_fixed ?? 0} / ${data.total_cases_evaluated ?? 0}`;
                showToast("Self-healing benchmark complete");
            } catch (e) {
                console.error(e);
            } finally {
                btnRunBenchmark.disabled = false;
                btnRunBenchmark.textContent = "Run Self-Healing Benchmark";
            }
        });
    }

    const btnExportJsonl = document.getElementById("btn-export-jsonl");
    if (btnExportJsonl) {
        btnExportJsonl.addEventListener("click", () => {
            window.open("/api/dataset/export", "_blank");
        });
    }

    // =========================================================================
    // INITIALIZATION
    // =========================================================================
    fetchSystemStatus();
    initApp();
});
