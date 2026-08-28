"""Failure detection and analysis view."""

import streamlit as st
from src.storage.database import Database
from src.storage.repositories import TraceRepository, FailureRepository
from src.failure.detector import FailureDetector
from src.failure.classifier import FailureClassifier
from src.evaluation.evaluator import Evaluator
from src.evaluation.judge import Judge


def render():
    """Render failure analysis view."""
    st.title("🔴 Failure Analysis")
    
    st.markdown("Detect and classify failures in execution traces.")
    
    # Configuration
    st.subheader("Configuration")
    
    threshold = st.slider(
        "Failure Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.05,
        help="Judge scores below this threshold are considered failures"
    )
    
    st.divider()
    
    # Trace selection
    st.subheader("Analyze Trace")
    
    try:
        db = Database()
        trace_repo = TraceRepository(db)
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
        
        # Run failure detection
        if st.button("🔍 Detect Failures", type="primary"):
            with st.spinner("Analyzing trace for failures..."):
                # Evaluate trace with judge
                judge = Judge()
                evaluator = Evaluator(judge=judge)
                evaluator.evaluate_trace(trace)
                
                # Detect failures
                detector = FailureDetector(threshold=threshold)
                failures = detector.detect(trace)
                
                # Classify failures
                classifier = FailureClassifier()
                failures = classifier.classify_batch(failures, trace)
                
                st.success(f"✅ Analysis complete! Found {len(failures)} failure(s)")
                
                st.divider()
                
                if failures:
                    # Display failures
                    st.subheader(f"📌 Detected Failures ({len(failures)})")
                    
                    failure_repo = FailureRepository(db)
                    
                    for i, failure in enumerate(failures):
                        with st.expander(
                            f"**Failure {i+1}:** {failure.failure_type.value} | "
                            f"Severity: {failure.severity:.2f}"
                        ):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.write(f"**Type:** {failure.failure_type.value}")
                            with col2:
                                st.write(f"**Severity:** {failure.severity:.2f}")
                            with col3:
                                st.write(f"**Judge Score:** {failure.judge_score:.2f}")
                            
                            st.write("**Description:**")
                            st.write(failure.description)
                            
                            if failure.evidence:
                                st.write("**Evidence:**")
                                st.json(failure.evidence)
                            
                            # Save failure
                            if st.button(f"💾 Save Failure {i+1}", key=f"save_{i}"):
                                failure_repo.save(failure)
                                st.success("Failure saved")
                else:
                    st.info("✅ No failures detected in this trace!")
        
        st.divider()
        
        # View existing failures
        st.subheader("📊 Existing Failures")
        
        failure_repo = FailureRepository(db)
        existing_failures = failure_repo.list_by_trace(selected_trace_id)
        
        if existing_failures:
            for failure in existing_failures:
                st.write(
                    f"**{failure.failure_type.value}** | "
                    f"Severity: {failure.severity:.2f} | "
                    f"Score: {failure.judge_score:.2f}"
                )
        else:
            st.info("No stored failures for this trace")
        
    except Exception as e:
        st.error(f"Error: {e}")
