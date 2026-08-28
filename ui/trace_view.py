"""Trace exploration and analysis view."""

import streamlit as st
from src.storage.database import Database
from src.storage.repositories import TraceRepository


def render():
    """Render trace explorer view."""
    st.title("🔍 Trace Explorer")
    
    st.markdown("Browse and analyze execution traces from your pipelines.")
    
    # Trace selection
    st.subheader("Select Trace")
    
    try:
        db = Database()
        repo = TraceRepository(db)
        traces = repo.list_all(limit=100)
        
        if not traces:
            st.info("No traces found. Run a pipeline first!")
            return
        
        # Trace selector
        trace_options = {f"{t.trace_id[:12]}... ({t.pipeline_name})" : t.trace_id for t in traces}
        selected = st.selectbox("Choose a trace", list(trace_options.keys()))
        selected_trace_id = trace_options[selected]
        
        # Load selected trace
        trace = repo.get(selected_trace_id)
        
        if not trace:
            st.error("Trace not found")
            return
        
        st.divider()
        
        # Trace overview
        st.subheader("📋 Trace Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Trace ID", trace.trace_id[:12] + "...")
        with col2:
            st.metric("Pipeline", trace.pipeline_name)
        with col3:
            st.metric("Status", trace.status)
        with col4:
            st.metric("Spans", len(trace.spans))
        
        st.divider()
        
        # Spans timeline
        st.subheader("⏱️ Execution Timeline")
        
        total_latency = trace.total_latency_ms or 0
        
        for i, span in enumerate(trace.spans):
            # Progress bar for latency
            latency_pct = (span.latency_ms / total_latency * 100) if total_latency > 0 else 0
            
            with st.expander(
                f"**Step {i}: {span.step_name}** | {span.status} | {span.latency_ms:.0f}ms"
            ):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Status", span.status)
                with col2:
                    st.metric("Latency", f"{span.latency_ms:.0f}ms")
                with col3:
                    judge_score = span.judge_score if span.judge_score is not None else "N/A"
                    st.metric("Judge Score", judge_score)
                with col4:
                    st.metric("Confidence", f"{span.confidence:.2f}" if span.confidence else "N/A")
                
                st.progress(latency_pct / 100, text=f"{latency_pct:.1f}% of total latency")
                
                if span.input_data:
                    st.write("**Input Data:**")
                    st.json(span.input_data)
                
                if span.output_data:
                    st.write("**Output Data:**")
                    st.json(span.output_data)
                
                if span.prompt:
                    with st.expander("View Prompt"):
                        st.text(span.prompt)
                
                if span.raw_response:
                    with st.expander("View Raw Response"):
                        st.text(span.raw_response)
                
                if span.error:
                    st.error(f"Error: {span.error}")
        
        st.divider()
        
        # Statistics
        st.subheader("📊 Trace Statistics")
        
        stats = trace.get_statistics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**Total Latency:** {trace.total_latency_ms:.0f}ms")
        with col2:
            avg_score = sum(s.judge_score for s in trace.spans if s.judge_score) / len([s for s in trace.spans if s.judge_score]) if any(s.judge_score for s in trace.spans) else 0
            st.write(f"**Avg Judge Score:** {avg_score:.2f}")
        with col3:
            failed_spans = len([s for s in trace.spans if s.status == "FAILED"])
            st.write(f"**Failed Spans:** {failed_spans}/{len(trace.spans)}")
        
        # Export options
        st.divider()
        
        st.subheader("📥 Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Export as JSON"):
                trace_json = trace.model_dump(mode='json')
                st.download_button(
                    label="Download JSON",
                    data=str(trace_json),
                    file_name=f"trace_{trace.trace_id[:8]}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("🗑️ Delete Trace"):
                repo.delete(trace.trace_id)
                st.success("Trace deleted")
                st.rerun()
        
    except Exception as e:
        st.error(f"Error loading traces: {e}")
