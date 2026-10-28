"""Pipeline execution, smart prompt ingestion, and multi-model management view."""

import streamlit as st
import json
import os
from src.pipeline.runner import PipelineRunner
from src.pipeline.base import Pipeline
from src.pipeline.intake import IntakeStep
from src.pipeline.extraction import ExtractionStep
from src.pipeline.classification import ClassificationStep
from src.pipeline.summarization import SummarizationStep
from src.pipeline.smart_input import SmartInputPreprocessor, PRESET_TEMPLATES
from src.llm.provider import get_llm_provider
from src.failure.report_exporter import ForensicsReportExporter
from src.storage.database import Database
from src.storage.repositories import TraceRepository, FailureRepository


def create_demo_pipeline() -> Pipeline:
    """Create the demo pipeline with all 4 steps."""
    pipeline = Pipeline(name="demo_pipeline")
    pipeline.add_step(IntakeStep())
    pipeline.add_step(ExtractionStep())
    pipeline.add_step(ClassificationStep())
    pipeline.add_step(SummarizationStep())
    return pipeline


def render():
    """Render pipeline execution view."""
    st.title("🚀 Pipeline Execution & Forensics Studio")
    st.caption("Execute AI pipelines with NVIDIA GPU acceleration, auto-structured big prompts, and instant failure diagnosis.")

    # =========================================================================
    # 1. LLM Runner & Hardware Configuration
    # =========================================================================
    with st.expander("⚡ LLM Runner & Hardware Engine Settings", expanded=True):
        col_r1, col_r2, col_r3 = st.columns(3)
        
        with col_r1:
            provider_choice = st.selectbox(
                "Execution Engine",
                ["Ollama (Local NVIDIA RTX 4050)", "Google Gemini (Cloud API)", "Groq LPU (Ultra-Fast Cloud)"],
                index=0,
                help="Select between local GPU acceleration or cloud inference."
            )
        
        with col_r2:
            if "Ollama" in provider_choice:
                model_raw = st.selectbox(
                    "Ollama Model (D:\\ollama_models)",
                    ["qwen2.5:1.5b (Fast & Cool - Recommended)", "qwen2.5:7b-instruct (Heavy Reasoning - High Heat)"],
                    index=0,
                    help="1.5B uses 1.1GB VRAM and stays at ~50°C. 7B uses 4.5GB VRAM and causes 86°C thermal throttling on laptops."
                )
                model_name = model_raw.split()[0]
                api_key = ""
            elif "Gemini" in provider_choice:
                model_name = "gemini-1.5-flash"
                api_key = st.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
            else:
                model_name = "llama-3.3-70b-versatile"
                api_key = st.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""))
                
        with col_r3:
            auto_evaluate = st.checkbox(
                "🔍 Auto-Evaluate & Diagnose Failures",
                value=True,
                help="Run LLM-as-Judge, detect semantic failures, and compute Root Cause Confidence in real-time."
            )
            auto_heal = st.checkbox(
                "🔄 Auto-Heal & Correct Failures",
                value=True,
                help="If failures are diagnosed, automatically synthesize prompt constraints and re-execute to produce corrected output."
            )
            st.caption("Hardware: **NVIDIA GeForce RTX 4050 (6GB VRAM)**")

    st.divider()

    # =========================================================================
    # 2. Preset Big Prompts & Document Ingestion
    # =========================================================================
    st.subheader("📝 Input Data & Big Prompt Ingestion")
    
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        st.markdown("**Load Real-World Preset Template:**")
        preset_names = ["-- Custom Input --"] + list(PRESET_TEMPLATES.keys())
        selected_preset = st.selectbox(
            "Choose a curated scenario",
            preset_names,
            index=1,
            label_visibility="collapsed"
        )
    
    with col_t2:
        st.markdown("**Upload Document File:**")
        uploaded_file = st.file_uploader(
            "Upload file",
            type=["txt", "json", "csv", "md"],
            label_visibility="collapsed",
            help="Upload raw logs, clinical notes, or financial statements."
        )

    # Determine initial text
    initial_text = ""
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        initial_text = SmartInputPreprocessor.parse_uploaded_file(file_bytes, uploaded_file.name)
        st.success(f"Loaded `{uploaded_file.name}` ({len(initial_text)} chars)")
    elif selected_preset != "-- Custom Input --":
        initial_text = PRESET_TEMPLATES[selected_preset]["text"]
        st.info(f"💡 **Scenario:** {PRESET_TEMPLATES[selected_preset]['description']}")
    else:
        initial_text = "The patient reported mild headache after taking medication A."

    input_text = st.text_area(
        "Prompt / Document Content",
        value=initial_text,
        height=220,
        help="Paste dense unstructured documents, conversation logs, or adversarial prompts."
    )

    # Smart Pre-processor Bar
    col_c1, col_c2, col_c3 = st.columns([2, 1, 1])
    with col_c1:
        words = len(input_text.split())
        chars = len(input_text)
        domain = SmartInputPreprocessor.detect_domain(input_text)
        st.caption(f"📊 Stats: **{chars} characters** | **{words} words** | Detected Domain: **`{domain.upper()}`**")

    with col_c2:
        use_smart_structure = st.checkbox("✨ Auto-Structure Input", value=True, help="Automatically cleans and formats input for optimal pipeline ingestion.")

    with col_c3:
        pass

    st.divider()

    # =========================================================================
    # 3. Pipeline Execution
    # =========================================================================
    if st.button("▶️ Execute Pipeline & Diagnose Forensics", type="primary", use_container_width=True):
        if not input_text.strip():
            st.error("Please provide prompt text or upload a document.")
            return

        # Prepare payload
        if use_smart_structure:
            payload = SmartInputPreprocessor.auto_structure(input_text)
        else:
            payload = {"raw_text": input_text}

        # Configure LLM Provider
        provider_type = "gemini" if "Gemini" in provider_choice else ("groq" if "Groq" in provider_choice else "ollama")
        try:
            get_llm_provider(provider_type=provider_type, model=model_name, api_key=api_key)
            if provider_type == "ollama":
                from src.llm.ollama_client import get_ollama_client
                get_ollama_client().set_model(model_name)
        except Exception as p_err:
            st.warning(f"Provider notice: {p_err}")

        # Execute
        try:
            with st.spinner(f"Executing 4-step pipeline using {model_name} on NVIDIA RTX 4050..."):
                pipeline = create_demo_pipeline()
                runner = PipelineRunner(pipeline=pipeline, auto_persist=True)
                
                output, trace = runner.run(payload)
                trace_id = trace.trace_id
                
                db = Database()
                trace_repo = TraceRepository(db)
                failure_repo = FailureRepository(db)
                
                failures = []
                if auto_evaluate:
                    try:
                        from src.evaluation.evaluator import Evaluator
                        from src.failure.detector import FailureDetector
                        from src.failure.classifier import FailureClassifier
                        
                        evaluator = Evaluator()
                        evaluator.evaluate_trace(trace)
                        
                        detector = FailureDetector(threshold=0.7)
                        detected_failures = detector.detect(trace)
                        
                        classifier = FailureClassifier()
                        failures = classifier.classify_batch(detected_failures, trace)
                        
                        for f in failures:
                            failure_repo.save(f)
                    except Exception as eval_e:
                        st.warning(f"Evaluation note: {eval_e}")
                
                # Re-save trace with updated scores
                trace_repo.save(trace)
                
                # Perform propagation & root cause if failures exist
                propagation_analysis = None
                root_cause = None
                if failures:
                    from src.failure.propagation import PropagationAnalyzer
                    from src.failure.root_cause import RootCauseEngine
                    
                    pa = PropagationAnalyzer()
                    propagation_analysis = pa.analyze(failures[0], trace)
                    
                    rce = RootCauseEngine()
                    root_cause = rce.analyze(failures[0], trace, propagation_analysis)

                # Real-time self-healing auto-correction pass
                healed_trace = None
                healed_recs = []
                if auto_heal and failures:
                    with st.spinner("🔄 Failure diagnosed! Synthesizing adaptive constraints and self-healing pipeline..."):
                        try:
                            from src.feedback.adaptive_optimizer import AdaptiveOptimizer
                            optimizer = AdaptiveOptimizer()
                            healed_recs = optimizer.generate_recommendations(failures)
                            adapted_pipeline = optimizer.build_adapted_pipeline(healed_recs)
                            adapted_runner = PipelineRunner(pipeline=adapted_pipeline, auto_persist=True)
                            healed_output, healed_trace = adapted_runner.run(payload)
                            
                            evaluator = Evaluator()
                            evaluator.evaluate_trace(healed_trace)
                            trace_repo.save(healed_trace)
                        except Exception as heal_err:
                            st.warning(f"Auto-heal note: {heal_err}")

            # Store last trace
            st.session_state.last_trace_id = trace_id
            
            # =========================================================================
            # 4. Results & Forensics Summary
            # =========================================================================
            st.success("🎉 Pipeline executed, traced, and persisted successfully!")
            
            # Metric Cards
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Trace ID", trace_id[:12] + "...")
            with col2:
                st.metric("Spans Captured", len(trace.spans))
            with col3:
                st.metric("Total Latency", f"{trace.total_latency_ms:.0f}ms")
            with col4:
                if failures:
                    st.metric("Failures Detected", len(failures), delta=f"-{len(failures)}", delta_color="inverse")
                else:
                    st.metric("Failures Detected", 0, delta="Healthy")

            # Failure Notice & Quick DAG Button
            if failures:
                st.error(
                    f"⚠️ **{len(failures)} Failure(s) Identified!** "
                    f"Root Cause: `{root_cause.root_step_name if root_cause else failures[0].step_name}` | "
                    f"Confidence: `{root_cause.root_cause_confidence:.1% if root_cause else 'N/A'}`"
                )
                
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    report_md = ForensicsReportExporter.generate_markdown(
                        trace=trace,
                        failure=failures[0] if failures else None,
                        propagation=propagation_analysis,
                        root_cause=root_cause,
                    )
                    st.download_button(
                        label="📥 Download Forensics Report (.md)",
                        data=report_md,
                        file_name=f"forensics_report_{trace_id[:8]}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                with col_d2:
                    st.info("👉 Switch to **Propagation Analysis** in the sidebar to inspect the interactive Plotly DAG!")

            # Display Self-Healing Auto-Correction Comparison if available
            if healed_trace:
                st.success("🌟 **Closed-Loop Self-Healing Succeeded:** Corrected failure by synthesizing adaptive constraints!")
                with st.expander("✨ View Before vs. After Correction (Self-Healing Comparison)", expanded=True):
                    col_h1, col_h2 = st.columns(2)
                    with col_h1:
                        st.markdown("#### 🔴 Original Output (With Failure)")
                        orig_score = f"{trace.final_score:.2f}" if trace.final_score is not None else "Failed"
                        st.caption(f"Trace ID: `{trace_id[:8]}` | Score: `{orig_score}`")
                        st.json(trace.spans[-1].output_data)
                    with col_h2:
                        st.markdown("#### 🟢 Self-Healed Output (Corrected)")
                        healed_score = f"{healed_trace.final_score:.2f}" if healed_trace.final_score is not None else "Healthy"
                        st.caption(f"Trace ID: `{healed_trace.trace_id[:8]}` | Score: `{healed_score}`")
                        st.json(healed_trace.spans[-1].output_data)
                    
                    if healed_recs:
                        st.info(f"**Applied Grounding Constraint:** `{healed_recs[0].prompt_guideline_prefix}`")

            st.divider()

            # Sequential Steps Audit
            st.subheader("Pipeline Steps & Intermediate Data Audit")
            for i, span in enumerate(trace.spans):
                judge_score_val = span.judge_score
                score_badge = f"{judge_score_val:.2f}" if judge_score_val is not None else "N/A"
                status_emoji = "🔴" if (judge_score_val is not None and judge_score_val < 0.7) else "🟢"
                
                with st.expander(f"{status_emoji} Step {i}: {span.step_name} | Score: {score_badge} | Latency: {span.latency_ms:.0f}ms", expanded=(i == 1)):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.write(f"**Step Status:** `{span.status.value}`")
                    with c2:
                        st.write(f"**Latency:** `{span.latency_ms:.1f}ms`")
                    with c3:
                        st.write(f"**Judge Score:** `{score_badge}`")
                    
                    span_err = getattr(span, "error", None) or getattr(span, "error_message", None)
                    if span_err:
                        st.error(f"**Error / Diagnostic Signal:** {span_err}")
                        
                    st.write("**Step Output:**")
                    st.json(span.output_data)

        except Exception as e:
            st.error(f"❌ Execution error: {e}")
            import traceback
            st.code(traceback.format_exc())
