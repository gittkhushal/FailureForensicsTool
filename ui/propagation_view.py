"""Failure propagation analysis view."""

import streamlit as st
from src.storage.database import Database
from src.storage.repositories import TraceRepository, FailureRepository
from src.failure.propagation import PropagationAnalyzer
from src.failure.detector import FailureDetector


def render():
    """Render propagation analysis view."""
    st.title("🌊 Propagation Analysis")
    
    st.markdown("Analyze how failures propagate through pipeline steps.")
    
    # Trace selection
    st.subheader("Select Trace")
    
    try:
        db = Database()
        trace_repo = TraceRepository(db)
        failure_repo = FailureRepository(db)
        traces = trace_repo.list_all(limit=100)
        
        if not traces:
            st.info("No traces found")
            return
        
        trace_options = {f"{t.trace_id[:12]}... ({t.pipeline_name})" : t.trace_id for t in traces}
        selected = st.selectbox("Choose a trace", list(trace_options.keys()))
        selected_trace_id = trace_options[selected]
        
        trace = trace_repo.get(selected_trace_id)
        
        if not trace:
            st.error("Trace not found")
            return
        
        st.divider()
        
        # Get failures for this trace
        failures = failure_repo.list_by_trace(selected_trace_id)
        
        if not failures:
            st.info("No failures detected for this trace. Analyze in Failure Analysis view first.")
            return
        
        # Failure selection
        failure_options = {f"{f.failure_type.value} ({f.step_name})" : f for f in failures}
        selected_failure_key = st.selectbox(
            "Select failure to analyze propagation",
            list(failure_options.keys())
        )
        selected_failure = failure_options[selected_failure_key]
        
        st.divider()
        
        # Analyze propagation
        if st.button("📊 Analyze Propagation", type="primary"):
            with st.spinner("Analyzing failure propagation..."):
                analyzer = PropagationAnalyzer()
                analysis = analyzer.analyze(selected_failure, trace)
                
                st.success("✅ Propagation analysis complete!")
                
                st.divider()
                
                # Overview
                st.subheader("📈 Propagation Overview")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Propagation Score", f"{analysis.overall_propagation_score:.2f}")
                with col2:
                    st.metric("Affected Spans", len(analysis.affected_spans))
                with col3:
                    st.metric("Propagation Paths", len(analysis.paths))
                
                st.divider()
                
                # Affected spans
                if analysis.affected_spans:
                    st.subheader("🎯 Affected Downstream Spans")
                    
                    for span_id in analysis.affected_spans:
                        span = next((s for s in trace.spans if s.span_id == span_id), None)
                        if span:
                            judge_score_str = f"{span.judge_score:.2f}" if span.judge_score else "N/A"
                            st.write(
                                f"**{span.step_name}** | "
                                f"Score: {judge_score_str}"
                            )
                
                st.divider()
                
                # Propagation paths
                if analysis.paths:
                    st.subheader("🔗 Propagation Paths")
                    
                    for i, path in enumerate(analysis.paths):
                        source_span = next((s for s in trace.spans if s.span_id == path.source_span_id), None)
                        target_span = next((s for s in trace.spans if s.span_id == path.target_span_id), None)
                        
                        source_name = source_span.step_name if source_span else "Unknown"
                        target_name = target_span.step_name if target_span else "Unknown"
                        
                        with st.expander(
                            f"Path {i+1}: {source_name} → {target_name} "
                            f"(PS: {path.propagation_score:.2f})"
                        ):
                            st.write(f"**Source Span:** {path.source_span_id}")
                            st.write(f"**Target Span:** {path.target_span_id}")
                            st.write(f"**Propagation Score:** {path.propagation_score:.2f}")
                            
                            if path.evidence:
                                st.write("**Evidence:**")
                                st.json(path.evidence)
                
                st.divider()
                
                # Visualization
                st.subheader("📊 Propagation Flow")
                
                # Simple text visualization
                flow_text = "Source Failure"
                for path in sorted(analysis.paths, key=lambda p: p.propagation_score, reverse=True)[:5]:
                    flow_text += f" → {path.propagation_score:.2f}"
                
                st.write(flow_text)
                
    except Exception as e:
        st.error(f"Error: {e}")
