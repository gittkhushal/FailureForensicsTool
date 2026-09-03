"""Dashboard page showing overall system statistics."""

import streamlit as st
from src.storage.database import Database
from src.storage.repositories import TraceRepository, FailureRepository


def render():
    """Render dashboard page."""
    st.title("📊 Dashboard")
    
    st.markdown("""
    Welcome to **FailureForensicsTool** - a framework for analyzing and diagnosing failures 
    in multi-step AI pipelines.
    """)
    
    # Get statistics
    try:
        db = Database()
        trace_repo = TraceRepository(db)
        failure_repo = FailureRepository(db)
        
        traces = trace_repo.list_all(limit=1000)
        total_traces = len(traces)
        
        # Calculate metrics
        total_failures = 0
        total_judge_scores = []
        root_causes_found = 0
        
        for trace in traces:
            failures = failure_repo.list_by_trace(trace.trace_id)
            total_failures += len(failures)
            
            for span in trace.spans:
                if span.judge_score is not None:
                    total_judge_scores.append(span.judge_score)
            
            root_causes_found += 1 if trace.total_latency_ms > 0 else 0
        
        avg_judge_score = sum(total_judge_scores) / len(total_judge_scores) if total_judge_scores else 0.0
        
    except Exception as e:
        st.warning(f"Could not load statistics: {e}")
        total_traces = 0
        total_failures = 0
        avg_judge_score = 0.0
        root_causes_found = 0
        traces = []
    
    # Statistics section
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Traces", str(total_traces))
    
    with col2:
        st.metric("Failures Detected", str(total_failures))
    
    with col3:
        st.metric("Avg Judge Score", f"{avg_judge_score:.2f}")
    
    with col4:
        st.metric("Traces Analyzed", str(root_causes_found))
    
    st.divider()
    
    # Recent traces
    st.subheader("📌 Recent Traces")
    
    if traces:
        for trace in traces[:5]:
            failure_count = len(failure_repo.list_by_trace(trace.trace_id)) if 'failure_repo' in locals() else 0
            with st.expander(f"Trace: {trace.trace_id[:12]}... ({trace.pipeline_name})"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Pipeline:** {trace.pipeline_name}")
                with col2:
                    st.write(f"**Status:** {trace.status.value if hasattr(trace.status, 'value') else trace.status}")
                with col3:
                    st.write(f"**Score:** {trace.final_score:.2f}" if trace.final_score else "N/A")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Spans:** {len(trace.spans)}")
                with col2:
                    st.write(f"**Failures:** {failure_count}")
                with col3:
                    st.write(f"**Latency:** {trace.total_latency_ms:.0f}ms" if trace.total_latency_ms else "N/A")
    else:
        st.info("No traces recorded yet. Run a pipeline to see results here.")
    
    st.divider()
    
    # Quick stats
    st.subheader("📈 System Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Key Features:**
        - 🔍 Real-time trace collection with automatic spans
        - 🎯 LLM-as-Judge evaluation scoring
        - 🔴 Failure detection and 4-type classification
        - 🌊 Failure propagation analysis
        - 🎲 Root cause identification and ranking
        """)
    
    with col2:
        st.markdown("""
        **Recent Capabilities:**
        - Multi-step pipeline support (4-step demo)
        - LLM-as-Judge with multi-criteria scoring
        - Propagation Score (PS) metric calculation
        - Root Cause Confidence (RCC) scoring
        - SQLite persistence & regression testing
        - 178 comprehensive unit tests
        """)
