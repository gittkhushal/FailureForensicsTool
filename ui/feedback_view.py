"""Feedback and evaluation management view."""

import streamlit as st
import json
from src.storage.database import Database
from src.storage.repositories import TraceRepository, EvaluationRepository
from src.models.evaluation_models import EvaluationCase
from src.feedback.dataset import EvaluationDataset
from src.feedback.regression import RegressionRunner


def render():
    """Render feedback and evaluation view."""
    st.title("📝 Feedback & Evaluation")
    
    st.markdown("Create evaluation cases for regression testing and feedback loops.")
    
    # Tab selection
    tab1, tab2, tab3 = st.tabs(["Create Case", "Manage Dataset", "Run Regression"])
    
    # Create evaluation case
    with tab1:
        st.subheader("Create Evaluation Case")
        
        st.markdown("Create a new evaluation case from a failed trace.")
        
        try:
            db = Database()
            trace_repo = TraceRepository(db)
            eval_repo = EvaluationRepository(db)
            
            traces = trace_repo.list_all(limit=100)
            
            if traces:
                trace_options = {f"{t.trace_id[:12]}... ({t.pipeline_name})" : t.trace_id for t in traces}
                selected = st.selectbox("Select trace", list(trace_options.keys()), key="case_trace")
                selected_trace_id = trace_options[selected]
                
                trace = trace_repo.get(selected_trace_id)
                
                st.divider()
                
                # Case details form
                col1, col2 = st.columns(2)
                
                with col1:
                    case_id = st.text_input("Case ID", value=f"case_{trace.trace_id[:8]}")
                    failing_step = st.text_input("Failing Step", value=trace.spans[0].step_name if trace.spans else "")
                
                with col2:
                    root_cause_step = st.text_input("Root Cause Step", value=trace.spans[0].step_name if trace.spans else "")
                    failure_type = st.selectbox(
                        "Failure Type",
                        ["hallucination", "misclassification", "incomplete_output", "other"]
                    )
                
                st.divider()
                
                # Input/Output mapping
                st.subheader("Input/Output Mapping")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    original_input = st.text_area(
                        "Original Input",
                        value=json.dumps(trace.spans[0].input_data) if trace.spans and trace.spans[0].input_data else "{}",
                        height=150
                    )
                
                with col2:
                    incorrect_output = st.text_area(
                        "Incorrect Output",
                        value=json.dumps(trace.spans[-1].output_data) if trace.spans and trace.spans[-1].output_data else "{}",
                        height=150
                    )
                
                corrected_output = st.text_area(
                    "Corrected Output",
                    placeholder="What should the output be?",
                    height=150
                )
                
                st.divider()
                
                # Save case
                if st.button("💾 Save Evaluation Case", type="primary"):
                    try:
                        case = EvaluationCase(
                            case_id=case_id,
                            trace_id=selected_trace_id,
                            original_input=json.loads(original_input),
                            failing_step=failing_step,
                            incorrect_output=json.loads(incorrect_output),
                            corrected_output=json.loads(corrected_output),
                            failure_type=failure_type,
                            root_cause_step=root_cause_step,
                        )
                        
                        eval_repo.save_case(case)
                        st.success(f"✅ Evaluation case saved: {case_id}")
                    except json.JSONDecodeError as e:
                        st.error(f"Invalid JSON: {e}")
                    except Exception as e:
                        st.error(f"Error saving case: {e}")
            else:
                st.info("No traces available")
        
        except Exception as e:
            st.error(f"Error: {e}")
    
    # Manage dataset
    with tab2:
        st.subheader("Manage Dataset")
        
        st.markdown("View and manage evaluation dataset.")
        
        try:
            db = Database()
            eval_repo = EvaluationRepository(db)
            
            cases = eval_repo.list_cases(limit=1000)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Cases", len(cases))
            
            with col2:
                if st.button("📥 Export Dataset"):
                    dataset = EvaluationDataset()
                    for case in cases:
                        dataset.add_case(case)
                    saved_path = dataset.save()
                    st.success(f"Dataset exported to {saved_path}")
            
            st.divider()
            
            # Display cases
            if cases:
                st.subheader("Evaluation Cases")
                
                for case in cases:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**{case.case_id}** - {case.failure_type}")
                    with col2:
                        st.write(f"Step: {case.failing_step}")
                    with col3:
                        if st.button("🗑️", key=f"del_{case.case_id}"):
                            st.info("Delete functionality would be implemented")
            else:
                st.info("No evaluation cases in dataset")
        
        except Exception as e:
            st.error(f"Error: {e}")
    
    # Run regression
    with tab3:
        st.subheader("Run Regression Tests")
        
        st.markdown("Re-execute evaluation cases and track results.")
        
        try:
            db = Database()
            eval_repo = EvaluationRepository(db)
            
            cases = eval_repo.list_cases(limit=100)
            
            if cases:
                st.metric("Available Cases", len(cases))
                
                st.divider()
                
                if st.button("🚀 Run Regression", type="primary"):
                    with st.spinner("Running regression tests..."):
                        runner = RegressionRunner()
                        results = runner.run(cases)
                        
                        st.success(f"✅ Regression complete! {len(results)} results")
                        
                        if results:
                            st.subheader("Regression Results")
                            
                            passed = sum(1 for r in results if r.passed)
                            failed = len(results) - passed
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Passed", passed)
                            with col2:
                                st.metric("Failed", failed)
                            with col3:
                                pass_rate = passed / len(results) * 100 if results else 0
                                st.metric("Pass Rate", f"{pass_rate:.1f}%")
            else:
                st.info("No evaluation cases available for regression testing")
        
        except Exception as e:
            st.error(f"Error: {e}")
