"""Analytics and evaluation dashboard."""

import streamlit as st
from src.storage.database import Database
from src.storage.repositories import TraceRepository, EvaluationRepository


def render():
    """Render analytics view."""
    st.title("📊 Analytics & Evaluation")
    
    st.markdown("System-wide analytics and evaluation metrics.")
    
    try:
        db = Database()
        trace_repo = TraceRepository(db)
        eval_repo = EvaluationRepository(db)
        
        # Tabs for different analytics
        tab1, tab2, tab3 = st.tabs(["System Stats", "Evaluation Cases", "Regression Results"])
        
        # System Statistics
        with tab1:
            st.subheader("📈 System Statistics")
            
            traces = trace_repo.list_all(limit=1000)
            
            if traces:
                # Overall metrics
                col1, col2, col3, col4 = st.columns(4)
                
                total_traces = len(traces)
                total_spans = sum(len(t.spans) for t in traces)
                avg_score = sum(t.final_score for t in traces if t.final_score) / len([t for t in traces if t.final_score]) if any(t.final_score for t in traces) else 0
                
                with col1:
                    st.metric("Total Traces", total_traces)
                with col2:
                    st.metric("Total Spans", total_spans)
                with col3:
                    st.metric("Avg Score", f"{avg_score:.2f}")
                with col4:
                    failed = sum(1 for t in traces if t.status == "FAILED")
                    st.metric("Failed Traces", failed)
                
                st.divider()
                
                # Pipeline breakdown
                st.subheader("Pipeline Breakdown")
                
                pipelines = {}
                for trace in traces:
                    if trace.pipeline_name not in pipelines:
                        pipelines[trace.pipeline_name] = {"count": 0, "avg_score": 0}
                    pipelines[trace.pipeline_name]["count"] += 1
                    if trace.final_score:
                        pipelines[trace.pipeline_name]["avg_score"] += trace.final_score
                
                for pipeline, stats in pipelines.items():
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**{pipeline}**")
                    with col2:
                        avg = stats["avg_score"] / stats["count"] if stats["count"] > 0 else 0
                        st.write(f"{stats['count']} traces | Avg: {avg:.2f}")
                
                st.divider()
                
                # Judge score distribution
                st.subheader("Judge Score Distribution")
                
                all_scores = []
                for trace in traces:
                    for span in trace.spans:
                        if span.judge_score is not None:
                            all_scores.append(span.judge_score)
                
                if all_scores:
                    st.metric("Min Score", f"{min(all_scores):.2f}")
                    st.metric("Max Score", f"{max(all_scores):.2f}")
                    st.metric("Avg Score", f"{sum(all_scores) / len(all_scores):.2f}")
            else:
                st.info("No traces available")
        
        # Evaluation Cases
        with tab2:
            st.subheader("📋 Evaluation Cases")
            
            cases = eval_repo.list_cases(limit=1000)
            
            if cases:
                st.metric("Total Cases", len(cases))
                
                st.divider()
                
                # Display cases
                for case in cases[:10]:  # Show first 10
                    with st.expander(f"Case {case.case_id[:8]}... - {case.failure_type}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Failing Step:** {case.failing_step}")
                            st.write(f"**Root Cause Step:** {case.root_cause_step}")
                        
                        with col2:
                            st.write(f"**Failure Type:** {case.failure_type}")
                        
                        if case.original_input:
                            st.write("**Original Input:**")
                            st.json(case.original_input)
                        
                        if case.incorrect_output:
                            st.write("**Incorrect Output:**")
                            st.json(case.incorrect_output)
                        
                        if case.corrected_output:
                            st.write("**Corrected Output:**")
                            st.json(case.corrected_output)
            else:
                st.info("No evaluation cases recorded")
        
        # Regression Results
        with tab3:
            st.subheader("🔄 Regression Results")
            
            st.info("Regression results tracking would be displayed here")
            st.markdown("""
            - Track pipeline performance over time
            - Identify regressions in model behavior
            - Monitor evaluation case success rates
            """)
    
    except Exception as e:
        st.error(f"Error: {e}")
