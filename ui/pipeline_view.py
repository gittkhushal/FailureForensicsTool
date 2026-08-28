"""Pipeline execution and management view."""

import streamlit as st
import json
from src.pipeline.runner import PipelineRunner
from src.tracing.trace import TraceContext
from src.storage.database import Database
from src.storage.repositories import TraceRepository


def render():
    """Render pipeline execution view."""
    st.title("🚀 Run Pipeline")
    
    st.markdown("Execute a pipeline and track its execution with detailed tracing.")
    
    # Pipeline selection
    st.subheader("Pipeline Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pipeline_name = st.text_input(
            "Pipeline Name",
            value="demo_pipeline",
            help="Name for this pipeline execution"
        )
    
    with col2:
        pipeline_type = st.selectbox(
            "Pipeline Type",
            ["Demo (Intake→Extract→Classify→Summarize)", "Custom"]
        )
    
    st.divider()
    
    # Input configuration
    st.subheader("Input Data")
    
    input_format = st.radio(
        "Input Format",
        ["Text", "JSON", "Upload File"]
    )
    
    if input_format == "Text":
        input_data = st.text_area(
            "Input Text",
            placeholder="Enter text to process...",
            height=200
        )
    elif input_format == "JSON":
        input_data = st.text_area(
            "Input JSON",
            placeholder='{"key": "value"}',
            height=200
        )
        try:
            if input_data:
                input_data = json.loads(input_data)
        except json.JSONDecodeError:
            st.error("Invalid JSON format")
    else:
        uploaded_file = st.file_uploader("Upload file", type=["txt", "json"])
        input_data = None
        if uploaded_file:
            if uploaded_file.type == "application/json":
                input_data = json.load(uploaded_file)
            else:
                input_data = uploaded_file.read().decode()
    
    st.divider()
    
    # Execution
    if st.button("▶️ Execute Pipeline", type="primary"):
        if not input_data:
            st.error("Please provide input data")
        else:
            try:
                with st.spinner("Executing pipeline..."):
                    # Create pipeline runner
                    runner = PipelineRunner()
                    
                    # Execute with tracing
                    with TraceContext(pipeline_name=pipeline_name) as trace:
                        result = runner.execute_demo(input_data)
                        trace_id = trace.trace_id
                    
                    # Save trace
                    db = Database()
                    repo = TraceRepository(db)
                    repo.save(trace)
                    
                    st.success(f"✅ Pipeline executed successfully!")
                    
                    # Display results
                    st.subheader("Execution Results")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Trace ID", trace_id[:12] + "...")
                        st.metric("Spans", len(trace.spans))
                    
                    with col2:
                        st.metric("Status", trace.status)
                        st.metric("Final Score", f"{trace.final_score:.2f}" if trace.final_score else "N/A")
                    
                    st.divider()
                    
                    # Span details
                    st.subheader("Pipeline Steps")
                    
                    for i, span in enumerate(trace.spans):
                        with st.expander(f"Step {i}: {span.step_name}"):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.write(f"**Status:** {span.status}")
                            with col2:
                                st.write(f"**Latency:** {span.latency_ms:.0f}ms")
                            with col3:
                                score = span.judge_score if span.judge_score else "N/A"
                                st.write(f"**Judge Score:** {score}")
                            
                            if span.input_data:
                                st.write("**Input:**")
                                st.json(span.input_data)
                            
                            if span.output_data:
                                st.write("**Output:**")
                                st.json(span.output_data)
                            
                            if span.error:
                                st.error(f"Error: {span.error}")
                    
                    # Store trace ID in session for other views
                    st.session_state.last_trace_id = trace_id
                    
            except Exception as e:
                st.error(f"❌ Pipeline execution failed: {e}")
                st.write(str(e))
