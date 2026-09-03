"""Pipeline execution and management view."""

import streamlit as st
import json
from src.pipeline.runner import PipelineRunner
from src.pipeline.base import Pipeline
from src.pipeline.intake import IntakeStep
from src.pipeline.extraction import ExtractionStep
from src.pipeline.classification import ClassificationStep
from src.pipeline.summarization import SummarizationStep
from src.tracing.instrumentation import TraceContext
from src.storage.database import Database
from src.storage.repositories import TraceRepository


def create_demo_pipeline() -> Pipeline:
    """Create the demo pipeline with all steps."""
    pipeline = Pipeline(name="demo_pipeline")
    pipeline.add_step(IntakeStep())
    pipeline.add_step(ExtractionStep())
    pipeline.add_step(ClassificationStep())
    pipeline.add_step(SummarizationStep())
    return pipeline


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
        ["Text", "JSON"]
    )
    
    if input_format == "Text":
        input_data = st.text_area(
            "Input Text",
            placeholder="Enter text to process...",
            height=200,
            value="The quick brown fox jumps over the lazy dog. This is a sample text for pipeline testing."
        )
    else:
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
            input_data = None
    
    st.divider()
    
    # Execution
    if st.button("▶️ Execute Pipeline", type="primary"):
        if not input_data:
            st.error("Please provide input data")
        else:
            try:
                with st.spinner("Executing pipeline..."):
                    # Create demo pipeline
                    pipeline = create_demo_pipeline()
                    runner = PipelineRunner(pipeline=pipeline)
                    
                    # Execute with tracing
                    output, trace = runner.run(input_data)
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
                        st.metric("Status", trace.status.value)
                        st.metric("Total Latency", f"{trace.total_latency_ms:.0f}ms")
                    
                    st.divider()
                    
                    # Span details
                    st.subheader("Pipeline Steps")
                    
                    for i, span in enumerate(trace.spans):
                        with st.expander(f"Step {i}: {span.step_name}"):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.write(f"**Status:** {span.status.value}")
                            with col2:
                                st.write(f"**Latency:** {span.latency_ms:.0f}ms")
                            with col3:
                                score = f"{span.judge_score:.2f}" if span.judge_score else "N/A"
                                st.write(f"**Judge Score:** {score}")
                            
                            if span.input_data:
                                st.write("**Input:**")
                                st.text(str(span.input_data)[:200])
                            
                            if span.output_data:
                                st.write("**Output:**")
                                st.text(str(span.output_data)[:200])
                            
                            if span.error:
                                st.error(f"Error: {span.error}")
                    
                    # Store trace ID in session for other views
                    st.session_state.last_trace_id = trace_id
                    
            except Exception as e:
                st.error(f"❌ Pipeline execution failed: {e}")
                import traceback
                st.write(traceback.format_exc())
