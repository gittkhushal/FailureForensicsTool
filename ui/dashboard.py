"""Dashboard page showing overall system statistics."""

import streamlit as st
from src.storage.database import Database
from src.storage.repositories import TraceRepository


def render():
    """Render dashboard page."""
    st.title("📊 Dashboard")
    
    st.markdown("""
    Welcome to **FailureForensicsTool** - a framework for analyzing and diagnosing failures 
    in multi-step AI pipelines.
    """)
    
    # Statistics section
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Traces", "0", delta=None)
    
    with col2:
        st.metric("Failures Detected", "0", delta=None)
    
    with col3:
        st.metric("Avg Judge Score", "0.00", delta=None)
    
    with col4:
        st.metric("Root Causes Found", "0", delta=None)
    
    st.divider()
    
    # Recent traces
    st.subheader("📌 Recent Traces")
    
    try:
        db = Database()
        repo = TraceRepository(db)
        traces = repo.list_all(limit=5)
        
        if traces:
            for trace in traces:
                with st.expander(f"Trace: {trace.trace_id}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Pipeline:** {trace.pipeline_name}")
                    with col2:
                        st.write(f"**Status:** {trace.status}")
                    with col3:
                        st.write(f"**Score:** {trace.final_score:.2f}" if trace.final_score else "N/A")
                    
                    st.write(f"**Spans:** {len(trace.spans)}")
        else:
            st.info("No traces recorded yet")
    except Exception as e:
        st.warning(f"Could not load traces: {e}")
    
    st.divider()
    
    # Quick stats
    st.subheader("📈 System Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Key Features:**
        - 🔍 Real-time trace collection
        - 🎯 Judge-based evaluation
        - 🔴 Failure detection and classification
        - 🌊 Propagation analysis
        - 🎲 Root cause identification
        """)
    
    with col2:
        st.markdown("""
        **Recent Capabilities:**
        - Multi-step pipeline support
        - LLM-as-Judge evaluation
        - Propagation Score calculation
        - Root Cause Confidence scoring
        - Dataset management & regression testing
        """)
