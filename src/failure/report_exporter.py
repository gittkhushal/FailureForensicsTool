"""
Forensics Investigation Report Generator and Exporter.

Produces structured, audit-ready Markdown and HTML reports for any pipeline execution trace.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from src.models.trace_models import Trace
from src.models.failure_models import Failure, PropagationAnalysis, RootCauseAnalysis


class ForensicsReportExporter:
    """Generates comprehensive investigation reports for pipeline failures."""

    @staticmethod
    def generate_markdown(
        trace: Trace,
        failure: Optional[Failure] = None,
        propagation: Optional[PropagationAnalysis] = None,
        root_cause: Optional[RootCauseAnalysis] = None,
    ) -> str:
        """Generate a complete GitHub-flavored Markdown investigation report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_badge = "FAILED" if trace.status.value.lower() == "failed" else "HEALTHY"
        
        md = []
        md.append(f"# 🔍 Pipeline Forensics Investigation Report")
        md.append(f"**Generated:** `{timestamp}` | **Trace ID:** `{trace.trace_id}` | **Status:** `{status_badge}`\n")
        md.append("---")
        
        # 1. Executive Summary
        md.append("## 1. Executive Diagnostic Summary\n")
        md.append(f"- **Pipeline Name:** `{trace.pipeline_name}`")
        md.append(f"- **Total Spans:** `{len(trace.spans)}`")
        md.append(f"- **Total Latency:** `{trace.total_latency_ms:.1f}ms`")
        md.append(f"- **Final Quality Score:** `{f'{trace.final_score:.2f}' if trace.final_score else 'N/A'}`")
        
        if failure and root_cause:
            md.append(f"- **Primary Root Cause:** Step `{root_cause.root_step_name}`")
            md.append(f"- **Root Cause Confidence (RCC):** `{root_cause.root_cause_confidence:.1%}`")
            if propagation:
                md.append(f"- **Propagation Score (PS):** `{propagation.overall_propagation_score:.2f}` ({len(propagation.affected_spans)} downstream steps impacted)")
            md.append(f"\n> **Diagnostic Finding:** {root_cause.reasoning}\n")
        else:
            md.append("\n> **Diagnostic Finding:** No critical failures detected. Execution completed within healthy parameters.\n")
            
        md.append("---")
        
        # 2. Propagation Analysis & Impact
        if propagation and propagation.paths:
            md.append("## 2. Failure Propagation Graph & Transmission Paths\n")
            md.append("| Transmission Path | Propagation Score (PS) | Source Score | Target Score | Evidence |")
            md.append("|:---|:---:|:---:|:---:|:---|")
            for p in propagation.paths:
                src_score = p.evidence.get("source_score", 0.0)
                tgt_score = p.evidence.get("target_score", 0.0)
                desc = p.evidence.get("classification_rationale", "Downstream degradation")
                md.append(f"| `{p.source_span_id[:8]}` ➔ `{p.target_span_id[:8]}` | **{p.propagation_score:.2f}** | {src_score:.2f} | {tgt_score:.2f} | {desc} |")
            md.append("\n---")
            
        # 3. Detailed Step-by-Step Span Audit
        md.append("## 3. Sequential Step Execution Audit\n")
        for i, span in enumerate(trace.spans):
            judge_val = f"{span.judge_score:.2f}" if span.judge_score is not None else "N/A"
            icon = "🔴" if (span.judge_score is not None and span.judge_score < 0.7) else "🟢"
            md.append(f"### {icon} Step {i}: `{span.step_name}` (Status: {span.status.value})")
            md.append(f"- **Latency:** `{span.latency_ms:.1f}ms` | **Judge Score:** `{judge_val}`")
            err = getattr(span, "error", None) or getattr(span, "error_message", None)
            if err:
                md.append(f"- **Error / Anomaly:** `{err}`")
            md.append("```json")
            md.append(f"// Output Data:")
            md.append(str(span.output_data)[:400] + ("..." if len(str(span.output_data)) > 400 else ""))
            md.append("```\n")
            
        md.append("---")
        
        # 4. Corrective Action Plan
        md.append("## 4. Closed-Loop Remediation & Adaptive Recommendations\n")
        if failure:
            md.append(f"To prevent recurrence of `{failure.failure_type.value}` in step `{failure.step_name}`:\n")
            md.append("1. **Apply Grounding Constraints:** Inject `[STRICT GROUNDING MANDATE]` into prompt template.")
            md.append("2. **Lower Temperature:** Reduce sampling temperature to `0.2` for deterministic entity parsing.")
            md.append("3. **Regression Testing:** Persist this trace as an evaluation case in `EvaluationDataset`.\n")
        else:
            md.append("Pipeline is currently operating within expected confidence bounds. No immediate parameter adjustments required.")
            
        return "\n".join(md)
