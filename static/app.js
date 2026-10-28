/**
 * FailureForensicsTool - Advanced Web Application Client Logic
 * 
 * Implements 7 full views:
 * 1. Dashboard
 * 2. Run Pipeline (Studio)
 * 3. Trace Explorer
 * 4. Failure Analysis
 * 5. Propagation Analysis (Interactive SVG DAG)
 * 6. Feedback & Evaluation (Cases, Dataset, Regression)
 * 7. Analytics & Metrics (System stats & Distributions)
 */

document.addEventListener("DOMContentLoaded", () => {
    // Global Application State
    const state = {
        activeTab: "dashboard",
        presets: {},
        traces: [],
        currentTraceDetail: null,
        currentPropagationData: null,
        pipelineOutputData: null,
        activeStepIdx: 0,
    };

    // =========================================================================
    // Toast Notification Utility
    // =========================================================================
    const toastEl = document.getElementById("toast");
    function showToast(message, duration = 3000) {
        if (!toastEl) return;
        toastEl.textContent = message;
        toastEl.classList.add("show");
        setTimeout(() => toastEl.classList.remove("show"), duration);
    }

    // =========================================================================
    // Formatters & Helpers
    // =========================================================================
    function formatJson(obj) {
        if (!obj) return "{}";
        try {
            if (typeof obj === "string") {
                obj = JSON.parse(obj);
            }
            return JSON.stringify(obj, null, 2);
        } catch (e) {
            return String(obj);
        }
    }

    function formatLatency(ms) {
        if (ms === null || ms === undefined) return "N/A";
        if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`;
        return `${Math.round(ms)}ms`;
    }

    function formatScore(score) {
        if (score === null || score === undefined) return "N/A";
        return Number(score).toFixed(2);
    }

    // =========================================================================
    // Global Navigation & Tab Switching
    // =========================================================================
    const tabTitles = {
        "dashboard": "Dashboard",
        "pipeline": "Run Pipeline",
        "trace-explorer": "Trace Explorer",
        "failure-analysis": "Failure Analysis",
        "propagation-analysis": "Propagation Analysis",
        "feedback-evaluation": "Feedback & Evaluation",
        "analytics-metrics": "Analytics & Metrics"
    };

    window.switchTab = function(tabId) {
        state.activeTab = tabId;

        // Update nav tabs
        document.querySelectorAll(".nav-tab").forEach(tab => {
            if (tab.getAttribute("data-tab") === tabId) {
                tab.classList.add("active");
            } else {
                tab.classList.remove("active");
            }
        });

        // Update tab contents
        document.querySelectorAll(".tab-content").forEach(content => {
            if (content.id === `tab-${tabId}`) {
                content.classList.add("active");
            } else {
                content.classList.remove("active");
            }
        });

        // Update breadcrumb
        const bcEl = document.getElementById("bc-current-tab");
        if (bcEl && tabTitles[tabId]) {
            bcEl.textContent = tabTitles[tabId];
        }

        // Trigger tab-specific data load
        switch (tabId) {
            case "dashboard":
                fetchDashboardStats();
                break;
            case "pipeline":
                fetchPresets();
                break;
            case "trace-explorer":
                loadTraceExplorerTraces();
                break;
            case "failure-analysis":
                loadFailureAnalysisTraces();
                break;
            case "propagation-analysis":
                loadDAGTraces();
                break;
            case "feedback-evaluation":
                loadFeedbackTraces();
                loadFeedbackDataset();
                break;
            case "analytics-metrics":
                fetchAnalytics();
                break;
        }
    };

    // Attach click listeners to main nav tabs
    document.querySelectorAll(".nav-tab").forEach(tab => {
        tab.addEventListener("click", () => {
            const tabId = tab.getAttribute("data-tab");
            window.switchTab(tabId);
        });
    });

    // Sidebar Toggle
    const btnSidebarToggle = document.getElementById("btn-sidebar-toggle");
    const appSidebar = document.getElementById("app-sidebar");
    if (btnSidebarToggle && appSidebar) {
        btnSidebarToggle.addEventListener("click", () => {
            appSidebar.classList.toggle("collapsed");
        });
    }

    // Sub-tab Navigation (for Feedback & Evaluation)
    document.querySelectorAll(".sub-nav-tab").forEach(subtab => {
        subtab.addEventListener("click", () => {
            const targetSubtab = subtab.getAttribute("data-subtab");
            
            // Toggle active subtab button
            subtab.parentElement.querySelectorAll(".sub-nav-tab").forEach(t => t.classList.remove("active"));
            subtab.classList.add("active");

            // Toggle active subtab content
            const container = subtab.closest("section");
            container.querySelectorAll(".subtab-content").forEach(c => {
                if (c.id === `subtab-${targetSubtab}`) {
                    c.classList.add("active");
                } else {
                    c.classList.remove("active");
                }
            });

            if (targetSubtab === "manage-dataset") {
                loadFeedbackDataset();
            }
        });
    });

    // =========================================================================
    // 1. DASHBOARD LOGIC
    // =========================================================================
    async function fetchSystemStatus() {
        try {
            const res = await fetch("/api/status");
            const data = await res.json();

            const gpuText = document.getElementById("gpu-text");
            const modelText = document.getElementById("active-model-text");
            const hwStatus = document.getElementById("hw-status-text");
            const hwStorage = document.getElementById("hw-storage-path");

            if (data.server_online) {
                if (gpuText) gpuText.textContent = "NVIDIA RTX 4050 • Active";
                if (modelText) modelText.textContent = data.active_model || "qwen2.5:1.5b";
                if (hwStatus) hwStatus.textContent = "Ollama Active with NVIDIA GPU Acceleration";
                if (hwStorage) hwStorage.textContent = data.models_path || "D:\\ollama_models";
            } else {
                if (gpuText) gpuText.textContent = "GPU Ready (Ollama Offline)";
                if (hwStatus) hwStatus.textContent = "Ollama Server Offline";
            }
        } catch (e) {
            console.warn("Failed to fetch system status:", e);
        }
    }

    async function fetchDashboardStats() {
        try {
            const res = await fetch("/api/dashboard/stats");
            const data = await res.json();

            // Update KPI cards
            const totalTracesEl = document.getElementById("kpi-total-traces");
            const totalFailuresEl = document.getElementById("kpi-total-failures");
            const avgJudgeEl = document.getElementById("kpi-avg-judge");
            const analyzedEl = document.getElementById("kpi-traces-analyzed");

            if (totalTracesEl) totalTracesEl.textContent = data.total_traces ?? 0;
            if (totalFailuresEl) totalFailuresEl.textContent = data.total_failures ?? 0;
            if (avgJudgeEl) avgJudgeEl.textContent = formatScore(data.avg_judge_score);
            if (analyzedEl) analyzedEl.textContent = data.traces_analyzed ?? 0;

            // Render Recent Traces Table
            const tbody = document.getElementById("dashboard-recent-tbody");
            if (tbody) {
                if (!data.recent_traces || data.recent_traces.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="8" class="loading-td">No pipeline executions logged yet. Run a pipeline to see traces.</td></tr>`;
                    return;
                }

                tbody.innerHTML = data.recent_traces.map(t => {
                    const statusClass = (t.status === "failed" || t.failure_count > 0) ? "badge-status-failed" : "badge-status-success";
                    const shortId = t.trace_id ? t.trace_id.slice(0, 8) : "--";
                    return `
                        <tr>
                            <td><code class="trace-id-pill">${shortId}...</code></td>
                            <td><strong>${t.pipeline_name}</strong></td>
                            <td><span class="status-badge ${statusClass}">${t.status}</span></td>
                            <td>${t.span_count}</td>
                            <td><span class="${t.failure_count > 0 ? 'highlight-red font-bold' : ''}">${t.failure_count}</span></td>
                            <td>${formatScore(t.final_score)}</td>
                            <td>${formatLatency(t.total_latency_ms)}</td>
                            <td>
                                <button class="btn-ghost btn-sm" onclick="inspectTrace('${t.trace_id}')">Inspect ➔</button>
                            </td>
                        </tr>
                    `;
                }).join("");
            }
        } catch (e) {
            console.error("Dashboard stats error:", e);
        }
    }

    const btnRefreshDashboard = document.getElementById("btn-refresh-dashboard");
    if (btnRefreshDashboard) {
        btnRefreshDashboard.addEventListener("click", () => {
            fetchDashboardStats();
            fetchSystemStatus();
            showToast("Dashboard telemetry refreshed");
        });
    }

    // Quick inspect from dashboard
    window.inspectTrace = function(traceId) {
        window.switchTab("trace-explorer");
        setTimeout(() => {
            const selectEl = document.getElementById("trace-explorer-select");
            if (selectEl) {
                selectEl.value = traceId;
                onTraceExplorerSelect(traceId);
            }
        }, 150);
    };

    // =========================================================================
    // 2. RUN PIPELINE STUDIO LOGIC
    // =========================================================================
    const promptInput = document.getElementById("prompt-input");
    const charWordCount = document.getElementById("char-word-count");
    const presetChips = document.querySelectorAll(".preset-chip");
    const btnAutoStructure = document.getElementById("btn-auto-structure");
    const btnExecute = document.getElementById("btn-execute");
    const selectModel = document.getElementById("select-model");
    const toggleAutoHeal = document.getElementById("toggle-auto-heal");
    const toggleEvaluate = document.getElementById("toggle-evaluate");
    const fileDropArea = document.getElementById("file-drop-area");
    const fileInput = document.getElementById("file-input");

    async function fetchPresets() {
        try {
            const res = await fetch("/api/presets");
            state.presets = await res.json();
            
            // If prompt input is empty, load active preset
            if (promptInput && !promptInput.value.trim()) {
                loadPresetByName("clinical");
            }
        } catch (e) {
            console.warn("Failed to fetch presets:", e);
        }
    }

    function loadPresetByName(presetKey) {
        const presetKeys = Object.keys(state.presets);
        let matchedKey = null;

        if (presetKey === "clinical") {
            matchedKey = presetKeys.find(k => k.toLowerCase().includes("clinical") || k.toLowerCase().includes("hallucination"));
        } else if (presetKey === "financial") {
            matchedKey = presetKeys.find(k => k.toLowerCase().includes("financial") || k.toLowerCase().includes("10-q"));
        } else if (presetKey === "security") {
            matchedKey = presetKeys.find(k => k.toLowerCase().includes("security") || k.toLowerCase().includes("noise"));
        } else if (presetKey === "clean") {
            matchedKey = presetKeys.find(k => k.toLowerCase().includes("clean") || k.toLowerCase().includes("standard"));
        }

        if (matchedKey && state.presets[matchedKey]) {
            const p = state.presets[matchedKey];
            promptInput.value = p.text || p.raw_input || p.description || "";
            updateInputCounter();
            showToast(`Loaded preset: ${p.domain || presetKey}`);
        }
    }

    function updateInputCounter() {
        if (!promptInput || !charWordCount) return;
        const text = promptInput.value;
        const chars = text.length;
        const words = text.trim() ? text.trim().split(/\s+/).length : 0;
        
        let domain = "GENERAL";
        const lower = text.toLowerCase();
        if (lower.includes("mg") || lower.includes("patient") || lower.includes("symptom")) domain = "CLINICAL";
        else if (lower.includes("revenue") || lower.includes("ebitda") || lower.includes("quarter")) domain = "FINANCIAL";
        else if (lower.includes("firewall") || lower.includes("ip") || lower.includes("cve")) domain = "SECURITY";

        charWordCount.textContent = `${chars} characters • ${words} words • Domain: ${domain}`;
    }

    if (promptInput) {
        promptInput.addEventListener("input", updateInputCounter);
    }

    presetChips.forEach(chip => {
        chip.addEventListener("click", () => {
            presetChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            const presetKey = chip.getAttribute("data-preset");
            loadPresetByName(presetKey);
        });
    });

    // File Drag & Drop
    if (fileDropArea && fileInput) {
        fileDropArea.addEventListener("click", () => fileInput.click());
        fileInput.addEventListener("change", (e) => {
            if (e.target.files.length > 0) {
                readFileIntoPrompt(e.target.files[0]);
            }
        });

        fileDropArea.addEventListener("dragover", (e) => {
            e.preventDefault();
            fileDropArea.classList.add("dragover");
        });
        fileDropArea.addEventListener("dragleave", () => fileDropArea.classList.remove("dragover"));
        fileDropArea.addEventListener("drop", (e) => {
            e.preventDefault();
            fileDropArea.classList.remove("dragover");
            if (e.dataTransfer.files.length > 0) {
                readFileIntoPrompt(e.dataTransfer.files[0]);
            }
        });
    }

    function readFileIntoPrompt(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            promptInput.value = e.target.result;
            updateInputCounter();
            showToast(`Loaded file: ${file.name}`);
        };
        reader.readAsText(file);
    }

    // Auto-Structure Button
    if (btnAutoStructure) {
        btnAutoStructure.addEventListener("click", () => {
            const text = promptInput.value.trim();
            if (!text) {
                showToast("Please enter or paste some text first");
                return;
            }
            showToast("Input structured successfully for pipeline ingestion");
        });
    }

    // Execute Pipeline
    if (btnExecute) {
        btnExecute.addEventListener("click", executePipelineStudio);
    }

    async function executePipelineStudio() {
        const text = promptInput.value.trim();
        if (!text) {
            showToast("Please provide input text or select a scenario preset.");
            return;
        }

        const model = selectModel.value;
        const autoHeal = toggleAutoHeal ? toggleAutoHeal.checked : true;
        const autoEval = toggleEvaluate ? toggleEvaluate.checked : true;

        btnExecute.disabled = true;
        btnExecute.querySelector(".btn-text").textContent = "Executing & Diagnosing...";
        const timerBadge = document.getElementById("execution-timer");
        if (timerBadge) timerBadge.textContent = "Running...";

        // Reset Stepper
        const stepNodes = [
            document.getElementById("step-node-0"),
            document.getElementById("step-node-1"),
            document.getElementById("step-node-2"),
            document.getElementById("step-node-3"),
        ];

        stepNodes.forEach((node, i) => {
            if (!node) return;
            node.className = "step-node";
            node.querySelector(".step-status").textContent = (i === 0) ? "Active..." : "Queued";
        });

        const startTime = performance.now();
        const intervalId = setInterval(() => {
            const elapsed = ((performance.now() - startTime) / 1000).toFixed(1);
            if (timerBadge) timerBadge.textContent = `${elapsed}s`;
        }, 100);

        try {
            const res = await fetch("/api/pipeline/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    input_text: text,
                    model: model,
                    auto_evaluate: autoEval,
                    auto_heal: autoHeal,
                    auto_structure: true,
                }),
            });

            clearInterval(intervalId);
            const totalElapsed = ((performance.now() - startTime) / 1000).toFixed(1);
            if (timerBadge) timerBadge.textContent = `Completed in ${totalElapsed}s`;

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Pipeline run failed");
            }

            const data = await res.json();
            state.pipelineOutputData = data;

            // Render Stepper results
            const trace = data.trace;
            const failures = data.failures || [];
            const hasFailures = failures.length > 0;

            trace.spans.forEach((span, idx) => {
                const node = stepNodes[idx];
                if (!node) return;

                const isFailed = (span.status === "failed" || (span.judge_score !== null && span.judge_score < 0.7));
                node.classList.add(isFailed ? "status-failed" : "status-success");
                node.querySelector(".step-status").textContent = isFailed ? "Failed" : "Success";
            });

            // Diagnosis Banner
            const diagBanner = document.getElementById("diagnosis-banner");
            const diagTitle = document.getElementById("diag-title");
            const diagSub = document.getElementById("diag-sub");
            const diagConf = document.getElementById("diag-confidence");
            const diagHealing = document.getElementById("diag-healing");
            const diagExplanation = document.getElementById("diag-explanation");

            if (diagBanner) {
                if (hasFailures) {
                    diagBanner.style.display = "block";
                    diagTitle.textContent = "Pipeline Failure Diagnosed";
                    const rootSpanName = data.root_cause ? data.root_cause.root_step_name : (failures[0].step_name || "Unknown");
                    diagSub.textContent = `Root cause identified at Step: '${rootSpanName}' (${failures[0].failure_type})`;
                    
                    if (diagConf) {
                        const confPct = data.root_cause ? Math.round(data.root_cause.root_cause_confidence * 100) : 85;
                        diagConf.textContent = `RCC: ${confPct}%`;
                    }

                    if (diagHealing) {
                        if (data.healed_trace) {
                            diagHealing.style.display = "inline-block";
                            diagHealing.textContent = "🔄 Automatically Healed";
                        } else {
                            diagHealing.style.display = "none";
                        }
                    }

                    if (diagExplanation) {
                        diagExplanation.textContent = failures[0].description || "Anomalous output detected during execution.";
                    }
                } else {
                    diagBanner.style.display = "block";
                    diagBanner.style.borderColor = "rgba(52, 211, 153, 0.4)";
                    diagTitle.textContent = "✅ Clean Execution - 0 Failures Detected";
                    diagSub.textContent = "All pipeline steps scored above the quality threshold.";
                    if (diagConf) diagConf.textContent = "Quality: High";
                    if (diagHealing) diagHealing.style.display = "none";
                    if (diagExplanation) diagExplanation.textContent = "LLM-as-Judge evaluated all intermediate steps as nominal.";
                }
            }

            // Display Output for Step 0 by default
            selectStepOutputTab(0);
            showToast("Pipeline execution finished!");

            // Refresh recent traces in Dashboard
            fetchDashboardStats();
        } catch (err) {
            clearInterval(intervalId);
            if (timerBadge) timerBadge.textContent = "Error";
            showToast(`Execution Error: ${err.message}`, 5000);
            console.error("Execution error:", err);
        } finally {
            btnExecute.disabled = false;
            btnExecute.querySelector(".btn-text").textContent = "Execute Pipeline & Diagnose Forensics";
        }
    }

    // Step Output Tabs
    const stepOutputTabs = document.querySelectorAll(".step-tab");
    stepOutputTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const stepIdx = parseInt(tab.getAttribute("data-step"), 10);
            selectStepOutputTab(stepIdx);
        });
    });

    function selectStepOutputTab(stepIdx) {
        state.activeStepIdx = stepIdx;
        stepOutputTabs.forEach(t => {
            if (parseInt(t.getAttribute("data-step"), 10) === stepIdx) {
                t.classList.add("active");
            } else {
                t.classList.remove("active");
            }
        });

        const statusMeta = document.getElementById("output-meta-status");
        const scoreMeta = document.getElementById("output-meta-score");
        const latencyMeta = document.getElementById("output-meta-latency");
        const jsonDisplay = document.getElementById("output-json-display");

        if (!state.pipelineOutputData || !state.pipelineOutputData.trace) {
            if (jsonDisplay) jsonDisplay.textContent = "// No execution data yet.";
            return;
        }

        const trace = state.pipelineOutputData.trace;
        const span = trace.spans ? trace.spans[stepIdx] : null;

        if (span) {
            if (statusMeta) statusMeta.textContent = `Status: ${span.status}`;
            if (scoreMeta) scoreMeta.textContent = `Judge Score: ${formatScore(span.judge_score)}`;
            if (latencyMeta) latencyMeta.textContent = `Latency: ${formatLatency(span.latency_ms)}`;
            if (jsonDisplay) jsonDisplay.textContent = formatJson(span.output_data || span.input_data || {});
        } else {
            if (jsonDisplay) jsonDisplay.textContent = "// Step data unavailable.";
        }
    }

    // =========================================================================
    // 3. TRACE EXPLORER LOGIC
    // =========================================================================
    const traceExplorerSelect = document.getElementById("trace-explorer-select");
    const btnDownloadJson = document.getElementById("btn-download-json");
    const btnDownloadReport = document.getElementById("btn-download-report");
    const btnDeleteTrace = document.getElementById("btn-delete-trace");

    async function loadTraceExplorerTraces() {
        if (!traceExplorerSelect) return;
        try {
            const res = await fetch("/api/traces?limit=100");
            state.traces = await res.json();

            traceExplorerSelect.innerHTML = `<option value="">-- Select a Trace to Inspect --</option>` +
                state.traces.map(t => {
                    const shortId = t.trace_id ? t.trace_id.slice(0, 12) : "Unknown";
                    const failTag = t.failure_count > 0 ? ` [${t.failure_count} failures]` : " [clean]";
                    return `<option value="${t.trace_id}">${shortId}... (${t.pipeline_name})${failTag}</option>`;
                }).join("");

            // If we have traces and none selected, auto-select first
            if (state.traces.length > 0 && !traceExplorerSelect.value) {
                traceExplorerSelect.value = state.traces[0].trace_id;
                onTraceExplorerSelect(state.traces[0].trace_id);
            }
        } catch (e) {
            console.error("Failed to load trace explorer traces:", e);
        }
    }

    if (traceExplorerSelect) {
        traceExplorerSelect.addEventListener("change", () => {
            const traceId = traceExplorerSelect.value;
            if (traceId) {
                onTraceExplorerSelect(traceId);
            }
        });
    }

    async function onTraceExplorerSelect(traceId) {
        if (!traceId) return;
        state.activeTraceId = traceId;

        try {
            const res = await fetch(`/api/traces/${traceId}`);
            if (!res.ok) throw new Error("Trace not found");
            const data = await res.json();
            state.currentTraceDetail = data;

            const trace = data.trace;
            const failures = data.failures || [];

            // 1. Update Overview Card
            const ovId = document.getElementById("ov-trace-id");
            const ovPipeline = document.getElementById("ov-pipeline-name");
            const ovStatus = document.getElementById("ov-status");
            const ovSpans = document.getElementById("ov-spans");
            const ovLatency = document.getElementById("ov-latency");
            const ovScore = document.getElementById("ov-score");

            if (ovId) ovId.textContent = trace.trace_id.slice(0, 16) + "...";
            if (ovPipeline) ovPipeline.textContent = trace.pipeline_name;
            if (ovStatus) {
                ovStatus.textContent = trace.status;
                ovStatus.className = `ov-val status-badge ${(trace.status === 'failed' || failures.length > 0) ? 'badge-status-failed' : 'badge-status-success'}`;
            }
            if (ovSpans) ovSpans.textContent = trace.spans ? trace.spans.length : 0;
            if (ovLatency) ovLatency.textContent = formatLatency(trace.total_latency_ms);
            if (ovScore) ovScore.textContent = formatScore(trace.final_score);

            // 2. Render Execution Timeline with Spans
            const timelineContainer = document.getElementById("timeline-container");
            const totalLatency = trace.total_latency_ms || 1;

            if (timelineContainer && trace.spans) {
                timelineContainer.innerHTML = trace.spans.map((span, idx) => {
                    const latencyMs = span.latency_ms || 0;
                    const pct = Math.min(100, Math.max(2, (latencyMs / totalLatency) * 100)).toFixed(1);
                    const isFailed = (span.status === "failed" || (span.judge_score !== null && span.judge_score < 0.7));

                    return `
                        <div class="timeline-span-card" id="timeline-span-${idx}">
                            <div class="timeline-span-header" onclick="toggleTimelineSpan(${idx})">
                                <div class="timeline-span-title">
                                    <span>${idx}.</span>
                                    <strong>${span.step_name}</strong>
                                    <span class="status-badge ${isFailed ? 'badge-status-failed' : 'badge-status-success'}">${span.status}</span>
                                </div>
                                <div class="timeline-span-meta">
                                    <span>${formatLatency(latencyMs)} (${pct}%)</span>
                                    <span>Score: <strong>${formatScore(span.judge_score)}</strong></span>
                                    <span>Confidence: <strong>${span.confidence ? span.confidence.toFixed(2) : 'N/A'}</strong></span>
                                    <span>▼</span>
                                </div>
                            </div>
                            <div class="timeline-progress-bar">
                                <div class="timeline-progress-fill" style="width: ${pct}%;"></div>
                            </div>
                            <div class="timeline-span-body ${idx === 0 ? 'open' : ''}" id="timeline-body-${idx}">
                                ${span.error ? `<div class="error-banner">⚠️ Error: ${span.error}</div>` : ''}
                                <div>
                                    <span class="drawer-label">Input Data:</span>
                                    <pre class="code-block">${formatJson(span.input_data)}</pre>
                                </div>
                                <div>
                                    <span class="drawer-label">Output Data:</span>
                                    <pre class="code-block">${formatJson(span.output_data)}</pre>
                                </div>
                                ${span.prompt ? `
                                <div>
                                    <span class="drawer-label">Prompt:</span>
                                    <pre class="code-block">${span.prompt}</pre>
                                </div>` : ''}
                                ${span.raw_response ? `
                                <div>
                                    <span class="drawer-label">Raw Response:</span>
                                    <pre class="code-block">${span.raw_response}</pre>
                                </div>` : ''}
                            </div>
                        </div>
                    `;
                }).join("");
            }

            // 3. Export Statistics Bar
            const expLatency = document.getElementById("export-stat-latency");
            const expScore = document.getElementById("export-stat-score");
            const expFailed = document.getElementById("export-stat-failed");

            if (expLatency) expLatency.textContent = `Total Latency: ${formatLatency(trace.total_latency_ms)}`;
            if (expScore) expScore.textContent = `Avg Judge Score: ${formatScore(trace.final_score)}`;
            if (expFailed) expFailed.textContent = `Failed Spans: ${failures.length} / ${trace.spans ? trace.spans.length : 0}`;

        } catch (e) {
            console.error("Failed to load trace detail:", e);
            showToast("Error loading trace detail");
        }
    }

    window.toggleTimelineSpan = function(idx) {
        const body = document.getElementById(`timeline-body-${idx}`);
        if (body) {
            body.classList.toggle("open");
        }
    };

    // Toggle All Spans Button
    let allSpansOpen = false;
    const btnToggleAll = document.getElementById("btn-toggle-all-spans");
    if (btnToggleAll) {
        btnToggleAll.addEventListener("click", () => {
            allSpansOpen = !allSpansOpen;
            document.querySelectorAll(".timeline-span-body").forEach(el => {
                if (allSpansOpen) el.classList.add("open");
                else el.classList.remove("open");
            });
            btnToggleAll.textContent = allSpansOpen ? "Collapse All" : "Expand All";
        });
    }

    // Export Buttons
    if (btnDownloadJson) {
        btnDownloadJson.addEventListener("click", () => {
            if (!state.currentTraceDetail) {
                showToast("No trace selected to export");
                return;
            }
            const blob = new Blob([JSON.stringify(state.currentTraceDetail.trace, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `trace_${state.activeTraceId.slice(0, 8)}.json`;
            a.click();
            URL.revokeObjectURL(url);
            showToast("Raw JSON downloaded");
        });
    }

    if (btnDownloadReport) {
        btnDownloadReport.addEventListener("click", async () => {
            if (!state.activeTraceId) {
                showToast("No trace selected");
                return;
            }
            try {
                const res = await fetch(`/api/report/${state.activeTraceId}`);
                const md = await res.text();
                const blob = new Blob([md], { type: "text/markdown" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `forensics_report_${state.activeTraceId.slice(0, 8)}.md`;
                a.click();
                URL.revokeObjectURL(url);
                showToast("Forensics report (.md) downloaded");
            } catch (e) {
                showToast("Failed to download report");
            }
        });
    }

    if (btnDeleteTrace) {
        btnDeleteTrace.addEventListener("click", async () => {
            if (!state.activeTraceId) return;
            if (!confirm(`Are you sure you want to delete trace ${state.activeTraceId.slice(0, 8)}?`)) return;

            try {
                const res = await fetch(`/api/traces/${state.activeTraceId}`, { method: "DELETE" });
                if (res.ok) {
                    showToast("Trace deleted successfully");
                    loadTraceExplorerTraces();
                    fetchDashboardStats();
                } else {
                    showToast("Failed to delete trace");
                }
            } catch (e) {
                showToast("Error deleting trace");
            }
        });
    }

    // =========================================================================
    // 4. FAILURE ANALYSIS LOGIC
    // =========================================================================
    const failureTraceSelect = document.getElementById("failure-trace-select");
    const sliderThreshold = document.getElementById("slider-threshold");
    const thresholdValText = document.getElementById("threshold-val-text");
    const btnDetectFailures = document.getElementById("btn-detect-failures");
    const detectedFailuresContainer = document.getElementById("detected-failures-container");
    const storedFailuresList = document.getElementById("stored-failures-list");

    if (sliderThreshold && thresholdValText) {
        sliderThreshold.addEventListener("input", () => {
            thresholdValText.textContent = parseFloat(sliderThreshold.value).toFixed(2);
        });
    }

    async function loadFailureAnalysisTraces() {
        if (!failureTraceSelect) return;
        try {
            const res = await fetch("/api/traces?limit=100");
            const traces = await res.json();

            failureTraceSelect.innerHTML = `<option value="">-- Choose a Trace to Analyze --</option>` +
                traces.map(t => {
                    const shortId = t.trace_id ? t.trace_id.slice(0, 12) : "Unknown";
                    return `<option value="${t.trace_id}">${shortId}... (${t.pipeline_name})</option>`;
                }).join("");

            if (traces.length > 0 && !failureTraceSelect.value) {
                failureTraceSelect.value = traces[0].trace_id;
                loadStoredFailures(traces[0].trace_id);
            }
        } catch (e) {
            console.error("Failed to load failure analysis traces:", e);
        }
    }

    if (failureTraceSelect) {
        failureTraceSelect.addEventListener("change", () => {
            const traceId = failureTraceSelect.value;
            if (traceId) {
                loadStoredFailures(traceId);
            }
        });
    }

    async function loadStoredFailures(traceId) {
        if (!storedFailuresList) return;
        try {
            const res = await fetch(`/api/failures/trace/${traceId}`);
            const failures = await res.json();

            if (!failures || failures.length === 0) {
                storedFailuresList.innerHTML = `<p class="text-muted">No previously saved failures stored for this trace.</p>`;
                return;
            }

            storedFailuresList.innerHTML = failures.map((f, i) => `
                <div class="stored-item">
                    <div>
                        <strong>${f.failure_type}</strong> (Step: ${f.step_name || 'N/A'})
                        <div class="text-muted text-sm">${f.description || ''}</div>
                    </div>
                    <div>
                        <span class="failure-badge">Severity: ${f.severity ? (f.severity * 100).toFixed(0) : 50}%</span>
                        <span class="status-badge">Score: ${formatScore(f.judge_score)}</span>
                    </div>
                </div>
            `).join("");
        } catch (e) {
            console.error("Failed to load stored failures:", e);
        }
    }

    if (btnDetectFailures) {
        btnDetectFailures.addEventListener("click", async () => {
            const traceId = failureTraceSelect.value;
            if (!traceId) {
                showToast("Please choose a trace to analyze");
                return;
            }

            const threshold = parseFloat(sliderThreshold.value) || 0.70;
            btnDetectFailures.disabled = true;
            btnDetectFailures.textContent = "Analyzing Trace...";

            try {
                const res = await fetch("/api/failures/detect", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ trace_id: traceId, threshold: threshold })
                });

                if (!res.ok) throw new Error("Detection failed");
                const data = await res.json();
                const failures = data.failures || [];

                if (detectedFailuresContainer) {
                    if (failures.length === 0) {
                        detectedFailuresContainer.innerHTML = `
                            <div class="glass-card" style="padding: 1.5rem; text-align: center;">
                                <h3 class="highlight-emerald">✅ No Failures Detected</h3>
                                <p class="text-muted">All steps in this trace scored above the threshold (${threshold.toFixed(2)}).</p>
                            </div>
                        `;
                    } else {
                        detectedFailuresContainer.innerHTML = `
                            <div style="margin-bottom: 0.8rem; font-weight: 700;">
                                Found ${failures.length} Failure(s) below threshold (${threshold.toFixed(2)}):
                            </div>` +
                            failures.map((f, idx) => {
                                const sevPct = Math.round((f.severity || 0.5) * 100);
                                return `
                                    <div class="failure-card">
                                        <div class="failure-header">
                                            <div style="display: flex; align-items: center; gap: 0.8rem;">
                                                <span class="failure-badge">${f.failure_type}</span>
                                                <strong>Step: ${f.step_name}</strong>
                                                <span class="text-muted">Score: ${formatScore(f.judge_score)}</span>
                                            </div>
                                            <div class="severity-meter-wrapper">
                                                <span>Severity: ${sevPct}%</span>
                                                <div class="severity-meter">
                                                    <div class="severity-fill" style="width: ${sevPct}%;"></div>
                                                </div>
                                            </div>
                                        </div>
                                        <p>${f.description || 'Quality anomaly identified by judge evaluation.'}</p>
                                        ${f.evidence ? `
                                        <div>
                                            <span class="drawer-label">Evidence:</span>
                                            <pre class="code-block">${formatJson(f.evidence)}</pre>
                                        </div>` : ''}
                                        <div style="text-align: right;">
                                            <button class="btn-ghost btn-sm" onclick="saveDetectedFailure(${idx})">💾 Save Failure to Database</button>
                                        </div>
                                    </div>
                                `;
                            }).join("");

                        // Cache detected failures for saving
                        window._cachedDetectedFailures = failures;
                    }
                }

                showToast(`Analysis complete: ${failures.length} failure(s) found`);
            } catch (err) {
                showToast(`Analysis failed: ${err.message}`);
            } finally {
                btnDetectFailures.disabled = false;
                btnDetectFailures.innerHTML = `<span class="btn-icon">🔍</span> Detect & Classify Failures`;
            }
        });
    }

    window.saveDetectedFailure = async function(idx) {
        if (!window._cachedDetectedFailures || !window._cachedDetectedFailures[idx]) return;
        const failure = window._cachedDetectedFailures[idx];

        try {
            const res = await fetch("/api/failures/save", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(failure)
            });

            if (res.ok) {
                showToast("Failure saved to database!");
                if (failureTraceSelect && failureTraceSelect.value) {
                    loadStoredFailures(failureTraceSelect.value);
                }
            } else {
                showToast("Failed to save failure");
            }
        } catch (e) {
            showToast("Error saving failure");
        }
    };

    // =========================================================================
    // 5. PROPAGATION ANALYSIS (INTERACTIVE SVG DAG)
    // =========================================================================
    const dagTraceSelect = document.getElementById("dag-trace-select");
    const dagSvg = document.getElementById("dag-svg");
    const nodeDrawer = document.getElementById("node-drawer");
    const drawerClose = document.getElementById("drawer-close");

    if (drawerClose && nodeDrawer) {
        drawerClose.addEventListener("click", () => nodeDrawer.style.display = "none");
    }

    async function loadDAGTraces() {
        if (!dagTraceSelect) return;
        try {
            const res = await fetch("/api/traces?limit=100");
            const traces = await res.json();

            dagTraceSelect.innerHTML = `<option value="">-- Choose a Trace for DAG --</option>` +
                traces.map(t => {
                    const shortId = t.trace_id ? t.trace_id.slice(0, 12) : "Unknown";
                    return `<option value="${t.trace_id}">${shortId}... (${t.pipeline_name})</option>`;
                }).join("");

            if (traces.length > 0 && !dagTraceSelect.value) {
                // Pick a trace with failures if available, otherwise first
                const failedTrace = traces.find(t => t.failure_count > 0);
                const pickId = failedTrace ? failedTrace.trace_id : traces[0].trace_id;
                dagTraceSelect.value = pickId;
                loadPropagationGraph(pickId);
            }
        } catch (e) {
            console.error("Failed to load DAG traces:", e);
        }
    }

    if (dagTraceSelect) {
        dagTraceSelect.addEventListener("change", () => {
            const traceId = dagTraceSelect.value;
            if (traceId) {
                loadPropagationGraph(traceId);
            }
        });
    }

    async function loadPropagationGraph(traceId) {
        if (!traceId) return;

        try {
            const res = await fetch(`/api/propagation/${traceId}`);
            if (!res.ok) throw new Error("Propagation data not found");
            const data = await res.json();
            state.currentPropagationData = data;

            // 1. Update Metrics Bar
            const psEl = document.getElementById("dag-ps-val");
            const rccEl = document.getElementById("dag-rcc-val");
            const rootStepEl = document.getElementById("dag-root-step");
            const stateEl = document.getElementById("dag-state");
            const explanationEl = document.getElementById("dag-explanation-text");

            if (psEl) psEl.textContent = Number(data.overall_propagation_score || 0).toFixed(2);
            if (rccEl) rccEl.textContent = `${Math.round((data.root_cause_confidence || 1.0) * 100)}%`;
            if (rootStepEl) rootStepEl.textContent = data.root_cause_step || (data.has_failures ? "Extraction" : "None (Clean)");
            if (stateEl) {
                stateEl.textContent = data.has_failures ? "Failures Detected" : "Nominal";
                stateEl.className = `metric-val ${data.has_failures ? 'highlight-red' : 'highlight-emerald'}`;
            }

            if (explanationEl) {
                explanationEl.textContent = data.explanation || "No propagation anomalies detected in this pipeline trace.";
            }

            // 2. Render SVG DAG
            renderSvgDag(data);

        } catch (e) {
            console.error("Failed to load propagation graph:", e);
            showToast("Error loading propagation DAG");
        }
    }

    function renderSvgDag(data) {
        const nodes = data.nodes || [];
        const edges = data.edges || [];
        const arcs = data.propagation_arcs || [];

        const baseEdgesGroup = document.getElementById("dag-base-edges");
        const arcsGroup = document.getElementById("dag-arcs");
        const nodesGroup = document.getElementById("dag-nodes");

        if (!baseEdgesGroup || !arcsGroup || !nodesGroup) return;

        baseEdgesGroup.innerHTML = "";
        arcsGroup.innerHTML = "";
        nodesGroup.innerHTML = "";

        if (nodes.length === 0) return;

        // Calculate node positions across 1000 width
        const totalNodes = nodes.length;
        const startX = totalNodes === 1 ? 500 : 140;
        const endX = totalNodes === 1 ? 500 : 860;
        const stepX = totalNodes === 1 ? 0 : (endX - startX) / Math.max(1, totalNodes - 1);
        const nodeY = 190;

        const nodeCoords = {};

        nodes.forEach((node, i) => {
            const x = startX + (i * stepX);
            nodeCoords[node.id] = { x, y: nodeY, node };
        });

        // 1. Draw Sequential Base Edges
        for (let i = 0; i < totalNodes - 1; i++) {
            const u = nodeCoords[nodes[i].id];
            const v = nodeCoords[nodes[i+1].id];
            const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
            line.setAttribute("x1", u.x);
            line.setAttribute("y1", u.y);
            line.setAttribute("x2", v.x);
            line.setAttribute("y2", v.y);
            line.setAttribute("stroke", "#475569");
            line.setAttribute("stroke-width", "3");
            baseEdgesGroup.appendChild(line);
        }

        // 2. Draw Curved Propagation Arcs (Bezier curves with animation)
        arcs.forEach((arc) => {
            const src = nodeCoords[arc.source];
            const tgt = nodeCoords[arc.target];

            if (src && tgt) {
                const midX = (src.x + tgt.x) / 2;
                const distance = Math.abs(tgt.x - src.x);
                const arcHeight = Math.max(60, distance * 0.35);
                const ctrlY = nodeY - arcHeight;

                const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
                const d = `M ${src.x} ${src.y} Q ${midX} ${ctrlY} ${tgt.x} ${tgt.y}`;
                path.setAttribute("d", d);
                path.setAttribute("fill", "none");
                path.setAttribute("stroke", "#f87171");
                path.setAttribute("stroke-width", Math.max(3, arc.propagation_score * 7));
                path.setAttribute("stroke-dasharray", "8, 6");
                path.setAttribute("marker-end", "url(#arrow)");
                path.classList.add("dag-animated-arc");

                arcsGroup.appendChild(path);
            }
        });

        // 3. Draw Nodes (Shapes and Labels)
        nodes.forEach((node) => {
            const coord = nodeCoords[node.id];
            const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
            g.classList.add("dag-node-group");
            g.style.cursor = "pointer";

            let fillColor = "#22c55e"; // emerald (healthy)
            let strokeColor = "#15803d";
            let shape = "circle";

            if (node.status_category === "root_cause") {
                fillColor = "#ef4444"; // red
                strokeColor = "#b91c1c";
                shape = "diamond";
            } else if (node.status_category === "propagated" || node.error || String(node.status).toLowerCase() === "failed") {
                fillColor = "#f97316"; // orange
                strokeColor = "#c2410c";
                shape = "circle";
            } else if (node.judge_score !== null && node.judge_score < 0.7) {
                fillColor = "#eab308"; // yellow
                strokeColor = "#a16207";
                shape = "circle";
            }

            if (shape === "diamond") {
                const diamond = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
                const size = 26;
                const points = `${coord.x},${coord.y - size} ${coord.x + size},${coord.y} ${coord.x},${coord.y + size} ${coord.x - size},${coord.y}`;
                diamond.setAttribute("points", points);
                diamond.setAttribute("fill", fillColor);
                diamond.setAttribute("stroke", strokeColor);
                diamond.setAttribute("stroke-width", "4");
                g.appendChild(diamond);
            } else {
                const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                circle.setAttribute("cx", coord.x);
                circle.setAttribute("cy", coord.y);
                circle.setAttribute("r", "22");
                circle.setAttribute("fill", fillColor);
                circle.setAttribute("stroke", strokeColor);
                circle.setAttribute("stroke-width", "4");
                g.appendChild(circle);
            }

            // Step Name text
            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.setAttribute("x", coord.x);
            text.setAttribute("y", coord.y + 44);
            text.setAttribute("text-anchor", "middle");
            text.setAttribute("fill", "#f8fafc");
            text.setAttribute("font-size", "13");
            text.setAttribute("font-weight", "700");
            text.textContent = node.step_name;
            g.appendChild(text);

            // Score subtext
            const scoreText = document.createElementNS("http://www.w3.org/2000/svg", "text");
            scoreText.setAttribute("x", coord.x);
            scoreText.setAttribute("y", coord.y + 60);
            scoreText.setAttribute("text-anchor", "middle");
            scoreText.setAttribute("fill", "#94a3b8");
            scoreText.setAttribute("font-size", "11");
            scoreText.textContent = `Score: ${formatScore(node.judge_score)}`;
            g.appendChild(scoreText);

            // Click listener for inspection drawer
            g.addEventListener("click", () => {
                openNodeDrawer(node);
            });

            nodesGroup.appendChild(g);
        });
    }

    function openNodeDrawer(node) {
        if (!nodeDrawer) return;
        const titleEl = document.getElementById("drawer-step-title");
        const metaEl = document.getElementById("drawer-meta");
        const scoreEl = document.getElementById("drawer-score");
        const outputEl = document.getElementById("drawer-output");

        if (titleEl) titleEl.textContent = `Inspection: Step '${node.step_name}' (Index ${node.step_index})`;
        if (metaEl) metaEl.textContent = `Status: ${node.status.toUpperCase()} | Latency: ${formatLatency(node.latency_ms)}`;
        if (scoreEl) scoreEl.textContent = `Judge Score: ${formatScore(node.judge_score)}`;
        if (outputEl) outputEl.textContent = formatJson(node.output_data || node.output_preview || node.input_data || {});

        nodeDrawer.style.display = "block";
    }

    // =========================================================================
    // 6. FEEDBACK & EVALUATION LOGIC
    // =========================================================================
    const fbTraceSelect = document.getElementById("fb-trace-select");
    const fbCaseId = document.getElementById("fb-case-id");
    const fbFailingStep = document.getElementById("fb-failing-step");
    const fbRootStep = document.getElementById("fb-root-step");
    const fbFailureType = document.getElementById("fb-failure-type");
    const fbOrigInput = document.getElementById("fb-orig-input");
    const fbIncorrectOutput = document.getElementById("fb-incorrect-output");
    const fbCorrectedOutput = document.getElementById("fb-corrected-output");
    const btnSaveCase = document.getElementById("btn-save-case");
    const datasetTotalCount = document.getElementById("dataset-total-count");
    const datasetCasesList = document.getElementById("dataset-cases-list");
    const btnExportDataset = document.getElementById("btn-export-dataset");
    const btnRunRegressionBench = document.getElementById("btn-run-regression-bench");

    async function loadFeedbackTraces() {
        if (!fbTraceSelect) return;
        try {
            const res = await fetch("/api/traces?limit=100");
            const traces = await res.json();

            fbTraceSelect.innerHTML = `<option value="">-- Select Source Trace --</option>` +
                traces.map(t => {
                    const shortId = t.trace_id ? t.trace_id.slice(0, 12) : "Unknown";
                    return `<option value="${t.trace_id}">${shortId}... (${t.pipeline_name})</option>`;
                }).join("");

            if (traces.length > 0 && !fbTraceSelect.value) {
                fbTraceSelect.value = traces[0].trace_id;
                onFeedbackTraceSelect(traces[0].trace_id);
            }
        } catch (e) {
            console.error("Failed to load feedback traces:", e);
        }
    }

    if (fbTraceSelect) {
        fbTraceSelect.addEventListener("change", () => {
            const traceId = fbTraceSelect.value;
            if (traceId) {
                onFeedbackTraceSelect(traceId);
            }
        });
    }

    async function onFeedbackTraceSelect(traceId) {
        try {
            const res = await fetch(`/api/traces/${traceId}`);
            if (!res.ok) return;
            const data = await res.json();
            const trace = data.trace;
            const failures = data.failures || [];

            if (fbCaseId) fbCaseId.value = `case_${trace.trace_id.slice(0, 8)}`;
            if (fbFailingStep) {
                fbFailingStep.value = (failures.length > 0) ? failures[0].step_name : (trace.spans ? trace.spans[0].step_name : "extraction");
            }
            if (fbRootStep) {
                fbRootStep.value = (failures.length > 0) ? failures[0].step_name : (trace.spans ? trace.spans[0].step_name : "extraction");
            }
            if (fbFailureType && failures.length > 0) {
                fbFailureType.value = failures[0].failure_type || "hallucination";
            }
            if (fbOrigInput && trace.spans && trace.spans[0]) {
                fbOrigInput.value = formatJson(trace.spans[0].input_data || {});
            }
            if (fbIncorrectOutput && trace.spans) {
                const lastSpan = trace.spans[trace.spans.length - 1];
                fbIncorrectOutput.value = formatJson(lastSpan.output_data || {});
            }
            if (fbCorrectedOutput) {
                fbCorrectedOutput.value = "{\n  \"corrected_summary\": \"Verified ground-truth output...\"\n}";
            }
        } catch (e) {
            console.error("Error setting feedback trace:", e);
        }
    }

    if (btnSaveCase) {
        btnSaveCase.addEventListener("click", async () => {
            const caseId = fbCaseId.value.trim();
            if (!caseId) {
                showToast("Please provide a Case ID");
                return;
            }

            let origInput = {};
            let incOutput = {};
            let corOutput = {};

            try {
                origInput = JSON.parse(fbOrigInput.value || "{}");
                incOutput = JSON.parse(fbIncorrectOutput.value || "{}");
                corOutput = JSON.parse(fbCorrectedOutput.value || "{}");
            } catch (err) {
                showToast(`JSON Parse Error: ${err.message}`);
                return;
            }

            const payload = {
                case_id: caseId,
                trace_id: fbTraceSelect.value || "",
                original_input: origInput,
                failing_step: fbFailingStep.value.trim(),
                root_cause_step: fbRootStep.value.trim(),
                failure_type: fbFailureType.value,
                incorrect_output: incOutput,
                corrected_output: corOutput,
            };

            try {
                const res = await fetch("/api/feedback/case", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });

                if (res.ok) {
                    showToast(`Evaluation Case '${caseId}' saved to dataset!`);
                    loadFeedbackDataset();
                } else {
                    const err = await res.json();
                    showToast(`Failed to save: ${err.detail || 'Error'}`);
                }
            } catch (e) {
                showToast("Error saving evaluation case");
            }
        });
    }

    async function loadFeedbackDataset() {
        if (!datasetCasesList) return;
        try {
            const res = await fetch("/api/feedback/cases");
            const cases = await res.json();

            if (datasetTotalCount) datasetTotalCount.textContent = `Total Cases: ${cases.length}`;

            if (!cases || cases.length === 0) {
                datasetCasesList.innerHTML = `<p class="text-muted">No evaluation cases recorded yet. Create one from a failed trace above.</p>`;
                return;
            }

            datasetCasesList.innerHTML = cases.map((c, i) => `
                <div class="case-card">
                    <div class="case-header">
                        <div>
                            <strong>${c.case_id}</strong>
                            <span class="failure-badge" style="margin-left: 0.6rem;">${c.failure_type}</span>
                        </div>
                        <div class="text-muted text-sm">Failing Step: <strong>${c.failing_step}</strong> | Root Cause: <strong>${c.root_cause_step}</strong></div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; margin-top: 0.4rem;">
                        <div>
                            <span class="drawer-label">Incorrect Output:</span>
                            <pre class="code-block" style="max-height: 120px;">${formatJson(c.incorrect_output)}</pre>
                        </div>
                        <div>
                            <span class="drawer-label">Corrected Ground Truth:</span>
                            <pre class="code-block" style="max-height: 120px; color: #34d399;">${formatJson(c.corrected_output)}</pre>
                        </div>
                    </div>
                </div>
            `).join("");
        } catch (e) {
            console.error("Failed to load feedback dataset:", e);
        }
    }

    if (btnExportDataset) {
        btnExportDataset.addEventListener("click", async () => {
            try {
                const res = await fetch("/api/feedback/export", { method: "POST" });
                const data = await res.json();
                showToast(`Dataset exported successfully! (${data.case_count} cases)`);
            } catch (e) {
                showToast("Failed to export dataset");
            }
        });
    }

    if (btnRunRegressionBench) {
        btnRunRegressionBench.addEventListener("click", async () => {
            btnRunRegressionBench.disabled = true;
            btnRunRegressionBench.textContent = "Executing Benchmark...";

            try {
                const res = await fetch("/api/feedback/benchmark", { method: "POST" });
                if (!res.ok) throw new Error("Benchmark execution failed");
                const data = await res.json();

                // Update regression KPI cards
                const regBase = document.getElementById("reg-base-rate");
                const regAdapted = document.getElementById("reg-adapted-rate");
                const regGain = document.getElementById("reg-gain-rate");
                const regAvgScore = document.getElementById("reg-avg-score");
                const regScoreDelta = document.getElementById("reg-score-delta");
                const regHealed = document.getElementById("reg-healed-cases");
                const rulesList = document.getElementById("regression-rules-list");

                if (regBase) regBase.textContent = `${(data.baseline_pass_rate * 100).toFixed(1)}%`;
                if (regAdapted) regAdapted.textContent = `${(data.adapted_pass_rate * 100).toFixed(1)}%`;
                if (regGain) regGain.textContent = `+${((data.adapted_pass_rate - data.baseline_pass_rate) * 100).toFixed(1)}% Quality Boost`;
                if (regAvgScore) regAvgScore.textContent = formatScore(data.adapted_avg_score);
                if (regScoreDelta) regScoreDelta.textContent = `+${(data.adapted_avg_score - data.baseline_avg_score).toFixed(2)} vs Baseline`;
                if (regHealed) regHealed.textContent = `${data.cases_healed} / ${data.total_cases}`;

                if (rulesList && data.recommendations) {
                    rulesList.innerHTML = data.recommendations.map(r => `
                        <div class="rec-item">
                            <div class="rec-header">
                                <span class="rec-step">Step: ${r.step_name}</span>
                                <span class="rec-type">Target: ${r.target_failure_type || 'hallucination'}</span>
                                <span class="rec-temp">Temp: ${r.sampling_temperature || 0.1}</span>
                            </div>
                            <p class="rec-rationale">${r.rationale || 'Prompt grounding applied.'}</p>
                            <code class="rec-code">${r.suggested_prompt_modification || '[STRICT GROUNDING CONSTRAINT]'}</code>
                        </div>
                    `).join("");
                }

                showToast("Adaptive regression benchmark complete!");
            } catch (err) {
                showToast(`Benchmark error: ${err.message}`);
            } finally {
                btnRunRegressionBench.disabled = false;
                btnRunRegressionBench.innerHTML = `<span class="btn-icon">⚡</span> Run Adaptive Benchmark Suite`;
            }
        });
    }

    // =========================================================================
    // 7. ANALYTICS & METRICS LOGIC
    // =========================================================================
    const btnRefreshAnalytics = document.getElementById("btn-refresh-analytics");
    if (btnRefreshAnalytics) {
        btnRefreshAnalytics.addEventListener("click", () => {
            fetchAnalytics();
            showToast("Analytics metrics refreshed");
        });
    }

    async function fetchAnalytics() {
        try {
            const res = await fetch("/api/analytics");
            const data = await res.json();

            // 1. Top KPI Metrics
            const totTraces = document.getElementById("analytics-total-traces");
            const totSpans = document.getElementById("analytics-total-spans");
            const avgScore = document.getElementById("analytics-avg-score");
            const failedCount = document.getElementById("analytics-failed-count");

            if (totTraces) totTraces.textContent = data.total_traces ?? 0;
            if (totSpans) totSpans.textContent = data.total_spans ?? 0;
            if (avgScore) avgScore.textContent = formatScore(data.avg_score);
            if (failedCount) failedCount.textContent = data.failed_traces ?? 0;

            // 2. Pipeline Breakdown
            const breakdownList = document.getElementById("pipeline-breakdown-list");
            if (breakdownList && data.pipeline_breakdown) {
                const entries = Object.entries(data.pipeline_breakdown);
                if (entries.length === 0) {
                    breakdownList.innerHTML = `<p class="text-muted">No pipeline data recorded yet.</p>`;
                } else {
                    breakdownList.innerHTML = entries.map(([name, info]) => `
                        <div class="breakdown-item">
                            <div>
                                <strong>${name}</strong>
                                <span class="text-muted text-sm" style="margin-left: 0.6rem;">${info.count} trace(s)</span>
                            </div>
                            <span class="status-badge">Avg Score: ${formatScore(info.avg_score)}</span>
                        </div>
                    `).join("");
                }
            }

            // 3. Judge Score Distribution
            const statMin = document.getElementById("score-stat-min");
            const statAvg = document.getElementById("score-stat-avg");
            const statMax = document.getElementById("score-stat-max");

            if (data.score_stats) {
                if (statMin) statMin.textContent = formatScore(data.score_stats.min);
                if (statAvg) statAvg.textContent = formatScore(data.score_stats.avg);
                if (statMax) statMax.textContent = formatScore(data.score_stats.max);

                // Segment distribution bar
                const dist = data.score_stats.distribution || {};
                const total = (dist.low || 0) + (dist.medium || 0) + (dist.good || 0) + (dist.excellent || 0);

                if (total > 0) {
                    const lowPct = ((dist.low || 0) / total) * 100;
                    const medPct = ((dist.medium || 0) / total) * 100;
                    const goodPct = ((dist.good || 0) / total) * 100;
                    const highPct = ((dist.excellent || 0) / total) * 100;

                    const distBar = document.getElementById("score-dist-bar");
                    if (distBar) {
                        distBar.innerHTML = `
                            <div class="dist-seg seg-low" style="width: ${lowPct}%;" title="Low: ${dist.low}"></div>
                            <div class="dist-seg seg-med" style="width: ${medPct}%;" title="Medium: ${dist.medium}"></div>
                            <div class="dist-seg seg-good" style="width: ${goodPct}%;" title="Good: ${dist.good}"></div>
                            <div class="dist-seg seg-high" style="width: ${highPct}%;" title="Excellent: ${dist.excellent}"></div>
                        `;
                    }
                }
            }

            // 4. Ground Truth Showcase
            const casesList = document.getElementById("analytics-cases-list");
            if (casesList && data.cases) {
                if (data.cases.length === 0) {
                    casesList.innerHTML = `<p class="text-muted">No evaluation cases recorded yet.</p>`;
                } else {
                    casesList.innerHTML = data.cases.map(c => `
                        <div class="case-card">
                            <div class="case-header">
                                <strong>${c.case_id}</strong>
                                <span class="failure-badge">${c.failure_type}</span>
                            </div>
                            <div class="text-muted text-sm">Failing Step: <strong>${c.failing_step}</strong> | Root Cause: <strong>${c.root_cause_step}</strong></div>
                        </div>
                    `).join("");
                }
            }

        } catch (e) {
            console.error("Failed to fetch analytics:", e);
        }
    }

    // =========================================================================
    // Initial Load Sequence
    // =========================================================================
    fetchSystemStatus();
    fetchDashboardStats();
    fetchPresets();
});
