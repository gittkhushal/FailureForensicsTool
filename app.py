"""
FailureForensicsTool: Main Streamlit Application Entry Point

A general framework for failure analysis and root-cause diagnosis
in multi-step AI pipelines.
"""

import streamlit as st
from pathlib import Path

# Configure Streamlit
st.set_page_config(
    page_title="FailureForensicsTool",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Set working directory
import sys
sys.path.insert(0, str(Path(__file__).parent))

# Import UI modules
from ui import dashboard, pipeline_view, trace_view, failure_view, propagation_view, analytics_view, feedback_view
from ui.style import inject_custom_styles


def main():
    """Main application entry point."""
    inject_custom_styles()
    st.title("🔍 FailureForensicsTool")
    st.markdown("""
    ## Failure Analysis and Root-Cause Diagnosis in Multi-Step AI Pipelines
    
    A general framework for observability, evaluation, and failure analysis in AI pipelines.
    """)
    
    # Sidebar navigation
    with st.sidebar:
        st.title("📍 Navigation")
        page = st.radio(
            "Select Page",
            [
                "Dashboard",
                "Run Pipeline",
                "Trace Explorer",
                "Failure Analysis",
                "Propagation Analysis",
                "Feedback & Evaluation",
                "Analytics & Metrics"
            ]
        )
        
        st.divider()
        
        # System info
        st.markdown("""
        ### ℹ️ About
        
        **FailureForensicsTool** provides:
        - 🔍 Trace collection & analysis
        - 🎯 Judge-based evaluation
        - 🔴 Failure detection
        - 🌊 Propagation analysis
        - 🎲 Root cause diagnosis
        
        **Status:** Phase 12 UI Complete
        """)
    
    # Route to appropriate page
    try:
        if page == "Dashboard":
            dashboard.render()
        elif page == "Run Pipeline":
            pipeline_view.render()
        elif page == "Trace Explorer":
            trace_view.render()
        elif page == "Failure Analysis":
            failure_view.render()
        elif page == "Propagation Analysis":
            propagation_view.render()
        elif page == "Feedback & Evaluation":
            feedback_view.render()
        elif page == "Analytics & Metrics":
            analytics_view.render()
    except Exception as e:
        st.error(f"Error loading page: {e}")
        st.write("Please ensure Ollama is running and database is initialized.")


if __name__ == "__main__":
    main()
