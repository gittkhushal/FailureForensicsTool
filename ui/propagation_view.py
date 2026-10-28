"""Failure propagation analysis and interactive DAG visualization view."""

import streamlit as st
import plotly.graph_objects as go
from typing import List, Optional

from src.storage.database import Database
from src.storage.repositories import TraceRepository, FailureRepository
from src.failure.propagation import PropagationAnalyzer
from src.failure.root_cause import RootCauseEngine
from src.failure.explanation import ExplanationGenerator
from src.models.trace_models import Trace, Span
from src.models.failure_models import Failure, PropagationAnalysis


def create_propagation_dag_figure(
    trace: Trace,
    failure: Failure,
    analysis: PropagationAnalysis,
) -> go.Figure:
    """
    Construct an interactive Plotly Directed Acyclic Graph (DAG) of failure propagation.
    
    Args:
        trace: Execution trace containing spans
        failure: Originating failure
        analysis: Propagation analysis with affected spans and paths
        
    Returns:
        Plotly Figure object
    """
    spans = sorted(trace.spans, key=lambda s: s.step_index)
    num_spans = len(spans)
    
    if num_spans == 0:
        fig = go.Figure()
        fig.update_layout(title="No spans in trace to visualize")
        return fig
        
    # Build coordinates for nodes along horizontal pipeline axis
    # X coordinates spread evenly; Y set to 0.0 with minor arc offsets
    x_coords = [i * 3.0 for i in range(num_spans)]
    y_coords = [0.0 for _ in range(num_spans)]
    span_id_to_idx = {s.span_id: i for i, s in enumerate(spans)}
    
    # Classify each span to determine node color and status label
    node_colors = []
    node_borders = []
    node_symbols = []
    hover_texts = []
    node_labels = []
    
    # Calculate propagation map: target_span_id -> max propagation_score
    path_scores = {p.target_span_id: p.propagation_score for p in analysis.paths}
    
    for s in spans:
        is_source = (s.span_id == failure.span_id)
        is_affected = (s.span_id in analysis.affected_spans)
        judge_score = s.judge_score if s.judge_score is not None else 0.5
        score_str = f"{s.judge_score:.2f}" if s.judge_score is not None else "N/A"
        
        if is_source:
            # Source of failure / Root Cause candidate
            node_colors.append("#ef4444")  # Vivid Red
            node_borders.append("#991b1b")
            node_symbols.append("diamond")
            status_tag = "🔴 ROOT FAILURE"
        elif is_affected:
            ps_val = path_scores.get(s.span_id, 0.0)
            if ps_val >= 0.3:
                node_colors.append("#f97316")  # Vivid Orange
                node_borders.append("#c2410c")
                node_symbols.append("circle")
                status_tag = f"🟠 PROPAGATED (PS: {ps_val:.2f})"
            else:
                node_colors.append("#eab308")  # Yellow
                node_borders.append("#a16207")
                node_symbols.append("circle")
                status_tag = f"🟡 AFFECTED (PS: {ps_val:.2f})"
        elif judge_score >= 0.7:
            node_colors.append("#22c55e")  # Emerald Green
            node_borders.append("#15803d")
            node_symbols.append("circle")
            status_tag = "🟢 HEALTHY"
        else:
            node_colors.append("#3b82f6")  # Blue
            node_borders.append("#1d4ed8")
            node_symbols.append("circle")
            status_tag = "🔵 NOMINAL"
            
        node_labels.append(f"<b>{s.step_name}</b><br>Score: {score_str}")
        
        # Rich HTML tooltip
        output_snippet = str(s.output_data or "")[:150].replace("<", "&lt;").replace(">", "&gt;")
        hover_texts.append(
            f"<b>Step:</b> {s.step_name} (Index {s.step_index})<br>"
            f"<b>Status:</b> {status_tag}<br>"
            f"<b>Judge Score:</b> {score_str}<br>"
            f"<b>Latency:</b> {s.latency_ms:.1f}ms<br>"
            f"<b>Output Excerpt:</b> {output_snippet}..."
        )
        
    fig = go.Figure()
    
    # 1. Draw base pipeline flow line (connecting consecutive steps in grey)
    for i in range(num_spans - 1):
        fig.add_trace(go.Scatter(
            x=[x_coords[i], x_coords[i+1]],
            y=[y_coords[i], y_coords[i+1]],
            mode='lines',
            line=dict(color='#64748b', width=2, dash='solid'),
            hoverinfo='none',
            showlegend=False,
        ))
        
    # 2. Draw active propagation paths as curved arcs with thickness scaling by PS
    for path in analysis.paths:
        if path.source_span_id in span_id_to_idx and path.target_span_id in span_id_to_idx:
            src_i = span_id_to_idx[path.source_span_id]
            tgt_i = span_id_to_idx[path.target_span_id]
            
            x0, y0 = x_coords[src_i], y_coords[src_i]
            x1, y1 = x_coords[tgt_i], y_coords[tgt_i]
            
            # Midpoint arc height based on distance
            dist = tgt_i - src_i
            arc_y = 0.5 + (dist * 0.25)
            mid_x = (x0 + x1) / 2.0
            
            # Quadratic curve approximation
            curve_x = [x0, (x0 + mid_x)/2, mid_x, (mid_x + x1)/2, x1]
            curve_y = [y0, arc_y * 0.75, arc_y, arc_y * 0.75, y1]
            
            line_width = max(2.5, min(7.0, path.propagation_score * 8.0))
            
            fig.add_trace(go.Scatter(
                x=curve_x,
                y=curve_y,
                mode='lines',
                line=dict(
                    color='rgba(239, 68, 68, 0.85)',
                    width=line_width,
                    dash='dash' if path.propagation_score < 0.2 else 'solid',
                ),
                name=f"PS: {path.propagation_score:.2f}",
                hoverinfo='text',
                hovertext=(
                    f"<b>Propagation Transmission:</b><br>"
                    f"From: {spans[src_i].step_name} ➔ To: {spans[tgt_i].step_name}<br>"
                    f"<b>Propagation Score (PS):</b> {path.propagation_score:.2f}<br>"
                    f"<b>Distance:</b> {dist} step(s)"
                ),
                showlegend=False,
            ))
            
            # Annotation marker for edge PS
            fig.add_annotation(
                x=mid_x,
                y=arc_y,
                text=f"<b>PS: {path.propagation_score:.2f}</b>",
                showarrow=False,
                font=dict(size=11, color="#ffffff"),
                bgcolor="#dc2626",
                bordercolor="#ffffff",
                borderwidth=1,
                borderpad=3,
                opacity=0.95,
            )

    # 3. Draw Nodes (Spans)
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='markers+text',
        marker=dict(
            size=44,
            color=node_colors,
            symbol=node_symbols,
            line=dict(color=node_borders, width=3),
        ),
        text=node_labels,
        textposition="bottom center",
        hoverinfo='text',
        hovertext=hover_texts,
        showlegend=False,
    ))
    
    # Layout adjustments
    fig.update_layout(
        title=dict(
            text=f"<b>Failure Propagation Flow (Overall PS: {analysis.overall_propagation_score:.2f})</b>",
            font=dict(size=18, color="#f8fafc"),
        ),
        paper_bgcolor='rgba(15, 23, 42, 0.8)',
        plot_bgcolor='rgba(15, 23, 42, 0.8)',
        showlegend=False,
        hovermode='closest',
        margin=dict(b=80, l=40, r=40, t=60),
        xaxis=dict(
            showgrid=False, 
            zeroline=False, 
            showticklabels=False,
            range=[-1.5, (num_spans - 1) * 3.0 + 1.5]
        ),
        yaxis=dict(
            showgrid=False, 
            zeroline=False, 
            showticklabels=False,
            range=[-1.2, 1.8]
        ),
        height=380,
    )
    
    return fig


def render():
    """Render propagation analysis view."""
    st.title("🌊 Failure Propagation Analysis & DAG Visualization")
    
    st.markdown(
        "Analyze how quality degradation originating in an upstream step propagates "
        "through downstream pipeline components, quantified by the novel **Propagation Score (PS)**."
    )
    
    try:
        db = Database()
        trace_repo = TraceRepository(db)
        failure_repo = FailureRepository(db)
        traces = trace_repo.list_all(limit=100)
        
        if not traces:
            st.info("No execution traces found in the database. Run a pipeline in 'Run Pipeline' first.")
            return
        
        trace_options = {f"{t.trace_id[:12]}... ({t.pipeline_name})" : t.trace_id for t in traces}
        selected = st.selectbox("Choose a Trace to Inspect", list(trace_options.keys()))
        selected_trace_id = trace_options[selected]
        
        trace = trace_repo.get(selected_trace_id)
        
        if not trace:
            st.error("Trace not found")
            return
        
        st.divider()
        
        # Retrieve failures for trace
        failures = failure_repo.list_by_trace(selected_trace_id)
        
        if not failures:
            st.info(
                "ℹ️ No failures detected for this trace yet. "
                "Visit 'Failure Analysis' to run detection on this trace first."
            )
            return
        
        # Failure selector
        failure_options = {
            f"{f.failure_type.value} in [{f.step_name}] (Severity: {f.severity:.2f})": f 
            for f in failures
        }
        selected_failure_key = st.selectbox(
            "Select Originating Failure for Propagation Analysis",
            list(failure_options.keys())
        )
        selected_failure = failure_options[selected_failure_key]
        
        st.divider()
        
        # Run propagation analysis
        analyzer = PropagationAnalyzer()
        analysis = analyzer.analyze(selected_failure, trace)
        
        # Run root cause diagnosis for explanation
        rc_engine = RootCauseEngine()
        root_cause = rc_engine.analyze(selected_failure, trace, analysis)
        
        # 1. High-Level Metrics
        st.subheader("📈 Propagation Impact Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Overall Propagation Score", f"{analysis.overall_propagation_score:.2f}")
        with col2:
            st.metric("Downstream Steps Affected", len(analysis.affected_spans))
        with col3:
            st.metric("Active Transmission Paths", len(analysis.paths))
        with col4:
            st.metric("Root Cause Confidence (RCC)", f"{root_cause.root_cause_confidence:.1%}")
        
        st.divider()
        
        # 2. Interactive Network DAG Graph
        st.subheader("🗺️ Interactive Propagation Network DAG")
        st.caption(
            "Visual Directed Acyclic Graph showing failure flow. "
            "Hover over nodes and arcs to inspect step quality, latency, and transmission scores."
        )
        
        fig = create_propagation_dag_figure(trace, selected_failure, analysis)
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # 3. Root Cause Diagnostic Summary
        st.subheader("🎲 Root Cause Diagnostic Summary")
        expl_gen = ExplanationGenerator()
        summary_text = expl_gen.generate_summary(selected_failure, trace, root_cause)
        
        col_summary, col_rcc = st.columns([3, 1])
        with col_summary:
            st.info(f"**Diagnosis:** {summary_text}")
            st.write(f"**Root Step:** `{root_cause.root_step_name}` | **Span ID:** `{root_cause.root_span_id}`")
            st.write(f"**Reasoning:** {root_cause.reasoning}")
        with col_rcc:
            st.metric("Root Cause Confidence", f"{root_cause.root_cause_confidence:.1%}")
            if root_cause.evidence:
                st.caption(f"Local Severity: {root_cause.evidence.get('local_severity', 0.0):.2f}")
                st.caption(f"Downstream Impact: {root_cause.evidence.get('downstream_impact', 0.0):.2f}")
                
        # Report download button
        from src.failure.report_exporter import ForensicsReportExporter
        report_md = ForensicsReportExporter.generate_markdown(
            trace=trace,
            failure=selected_failure,
            propagation=analysis,
            root_cause=root_cause,
        )
        st.download_button(
            label="📥 Download Forensics Investigation Report (.md)",
            data=report_md,
            file_name=f"propagation_forensics_{trace.trace_id[:8]}.md",
            mime="text/markdown",
            use_container_width=True,
        )
        
        st.divider()
        
        # 4. Detailed Propagation Paths Breakdown
        if analysis.paths:
            st.subheader(f"🔗 Transmission Path Breakdown ({len(analysis.paths)} paths)")
            for i, path in enumerate(analysis.paths):
                source_span = next((s for s in trace.spans if s.span_id == path.source_span_id), None)
                target_span = next((s for s in trace.spans if s.span_id == path.target_span_id), None)
                src_name = source_span.step_name if source_span else "Unknown"
                tgt_name = target_span.step_name if target_span else "Unknown"
                
                with st.expander(f"Path {i+1}: {src_name} ➔ {tgt_name} (PS: {path.propagation_score:.2f})", expanded=(i == 0)):
                    col_p1, col_p2, col_p3 = st.columns(3)
                    with col_p1:
                        st.write(f"**Origin Step:** `{src_name}`")
                        st.write(f"Source Score: `{path.evidence.get('source_score', 0.0):.2f}`")
                    with col_p2:
                        st.write(f"**Target Step:** `{tgt_name}`")
                        st.write(f"Target Score: `{path.evidence.get('target_score', 0.0):.2f}`")
                    with col_p3:
                        st.metric("Propagation Score", f"{path.propagation_score:.2f}")
                        st.caption(f"Distance Decay Factor: {1.0 / (1.0 + path.evidence.get('distance', 1) * 0.1):.2f}")
                    
                    if path.evidence:
                        st.json(path.evidence)
        else:
            st.info("No downstream propagation paths recorded for this failure.")
            
    except Exception as e:
        st.error(f"Error rendering propagation view: {e}")
        import traceback
        st.code(traceback.format_exc())
