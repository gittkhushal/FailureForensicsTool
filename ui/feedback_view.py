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
    
    # Run regression & Self-Improving Adaptation
    with tab3:
        st.subheader("🔄 Closed-Loop Regression & Self-Improving Benchmark")
        
        st.markdown(
            "Execute stored evaluation cases against the baseline pipeline, or benchmark the "
            "**Self-Improving Adaptive Optimizer** to measure automated recovery gains."
        )
        
        try:
            db = Database()
            eval_repo = EvaluationRepository(db)
            cases = eval_repo.list_cases(limit=100)
            
            if not cases:
                st.info("No evaluation cases found in database. Create a case in 'Create Case' tab first.")
            else:
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.metric("Stored Evaluation Cases", len(cases))
                with col_info2:
                    unique_types = len(set(c.failure_type for c in cases))
                    st.metric("Unique Failure Types", unique_types)
                
                st.divider()
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    run_standard = st.button("🚀 Run Standard Regression", type="secondary")
                with col_btn2:
                    run_adaptive = st.button("⚡ Run Self-Improving Adaptation & Benchmark", type="primary")
                
                # Option 1: Standard Regression
                if run_standard:
                    with st.spinner("Running standard regression tests..."):
                        runner = RegressionRunner()
                        results = runner.run(cases)
                        
                        st.success(f"✅ Regression complete! Processed {len(results)} cases")
                        
                        passed = sum(1 for r in results if r.passed)
                        failed = len(results) - passed
                        pass_rate = (passed / len(results)) * 100 if results else 0
                        avg_score = sum(r.score for r in results) / len(results) if results else 0
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Runs", len(results))
                        with col2:
                            st.metric("Passed", passed)
                        with col3:
                            st.metric("Failed", failed)
                        with col4:
                            st.metric("Pass Rate", f"{pass_rate:.1f}%")
                            
                        st.divider()
                        st.subheader("Detailed Run Log")
                        for r in results:
                            st.write(
                                f"{'✅' if r.passed else '❌'} **{r.case_id}** | "
                                f"Score: `{r.score:.2f}` | Passed: `{r.passed}`"
                            )
                
                # Option 2: Self-Improving Closed-Loop Benchmark
                if run_adaptive:
                    with st.spinner("Analyzing root causes, synthesizing adaptive configurations, and benchmarking..."):
                        runner = RegressionRunner()
                        report = runner.compare_runs(cases)
                        
                        st.success("🎉 Self-Improving Adaptive Optimization Complete!")
                        st.divider()
                        
                        # Comparison Metric Cards
                        st.subheader("📈 Before vs. After Optimization Delta")
                        m1, m2, m3, m4 = st.columns(4)
                        with m1:
                            st.metric(
                                "Baseline Pass Rate", 
                                f"{report.baseline_pass_rate:.1%}"
                            )
                        with m2:
                            st.metric(
                                "Adapted Pass Rate", 
                                f"{report.adapted_pass_rate:.1%}",
                                delta=f"{report.pass_rate_gain:+.1%}"
                            )
                        with m3:
                            st.metric(
                                "Avg Quality Score", 
                                f"{report.adapted_avg_score:.2f}",
                                delta=f"{report.score_gain:+.2f}"
                            )
                        with m4:
                            st.metric(
                                "Healed / Fixed Cases", 
                                f"{report.cases_fixed} / {report.total_cases_evaluated}"
                            )
                            
                        st.divider()
                        
                        # Applied Adaptive Recommendations
                        st.subheader("💡 Applied Adaptive Recommendations")
                        for rec in report.recommendations_applied:
                            with st.expander(f"Step: {rec.target_step} (Targeting {rec.failure_type})", expanded=True):
                                st.write(f"**Rationale:** {rec.rationale}")
                                st.write(f"**Suggested LLM Temperature:** `{rec.suggested_temperature}`")
                                st.code(rec.prompt_guideline_prefix, language="markdown")
                                if rec.parameter_adjustments:
                                    st.json(rec.parameter_adjustments)
                        
                        st.divider()
                        
                        # Comparative Breakdown
                        st.subheader("📊 Case-by-Case Improvement Breakdown")
                        for detail in report.detailed_results:
                            status_icon = "🌟 Fixed" if detail["fixed"] else ("✅ Passed" if detail["adapted_passed"] else "❌ Needs Tuning")
                            col_a, col_b, col_c = st.columns([2, 1, 1])
                            with col_a:
                                st.write(f"**{detail['case_id']}** ({detail['failure_type']} @ {detail['failing_step']})")
                            with col_b:
                                st.write(f"Score: `{detail['baseline_score']:.2f}` ➔ `{detail['adapted_score']:.2f}`")
                            with col_c:
                                st.markdown(f"**{status_icon}**")
                                
        except Exception as e:
            st.error(f"Error executing regression view: {e}")
            import traceback
            st.code(traceback.format_exc())
