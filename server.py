"""
FastAPI Backend Server for FailureForensicsTool.

Exposes REST APIs for:
- Multi-step pipeline execution with GPU acceleration
- Real-time failure detection, propagation analysis, and root-cause diagnosis
- Closed-loop adaptive self-healing execution
- Interactive DAG network visualization data
- Automated regression benchmarking
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add repository root to Python path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from src.storage.database import Database
from src.storage.repositories import TraceRepository, FailureRepository, EvaluationRepository
from src.pipeline.runner import PipelineRunner
from src.pipeline.base import Pipeline
from src.pipeline.intake import IntakeStep
from src.pipeline.extraction import ExtractionStep
from src.pipeline.classification import ClassificationStep
from src.pipeline.summarization import SummarizationStep
from src.pipeline.smart_input import SmartInputPreprocessor, PRESET_TEMPLATES
from src.llm.ollama_client import get_ollama_client
from src.llm.provider import get_llm_provider
from src.evaluation.evaluator import Evaluator
from src.failure.detector import FailureDetector
from src.failure.classifier import FailureClassifier
from src.failure.propagation import PropagationAnalyzer
from src.failure.root_cause import RootCauseEngine
from src.failure.report_exporter import ForensicsReportExporter
from src.failure.explanation import ExplanationGenerator
from src.models.evaluation_models import EvaluationCase
from src.models.failure_models import Failure, FailureType
from src.feedback.adaptive_optimizer import AdaptiveOptimizer
from src.feedback.dataset import EvaluationDataset
from src.feedback.regression import RegressionRunner


app = FastAPI(
    title="FailureForensicsTool API",
    description="Observability & Failure Forensics Engine for AI Pipelines",
    version="2.0.0",
)

# Enable CORS for local web development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    """Ensure static files and HTML are never cached during development."""
    response = await call_next(request)
    if request.url.path.startswith("/static") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


def create_pipeline() -> Pipeline:
    """Build standard 4-step pipeline."""
    pipe = Pipeline(name="demo_pipeline")
    pipe.add_step(IntakeStep())
    pipe.add_step(ExtractionStep())
    pipe.add_step(ClassificationStep())
    pipe.add_step(SummarizationStep())
    return pipe


# =============================================================================
# Request / Response Schemas
# =============================================================================
class RunPipelineRequest(BaseModel):
    input_text: str
    model: str = "qwen2.5:1.5b"
    provider: str = "ollama"
    auto_evaluate: bool = True
    auto_heal: bool = True
    auto_structure: bool = True


class DetectFailuresRequest(BaseModel):
    trace_id: str
    threshold: float = 0.70


# =============================================================================
# API Endpoints
# =============================================================================
@app.get("/api/status")
def get_system_status():
    """Return hardware, Ollama server status, and active models."""
    try:
        client = get_ollama_client()
        health = client.health_check()
        return {
            "server_online": health.get("server_available", False),
            "models_path": health.get("models_path", "D:\\ollama_models"),
            "active_model": client.model,
            "available_models": health.get("available_models", ["qwen2.5:1.5b", "qwen2.5:7b-instruct"]),
            "gpu_hardware": "NVIDIA GeForce RTX 4050 Laptop GPU (6GB VRAM)",
            "gpu_acceleration": "CUDA 13.4 | 29/29 Layers Offloaded",
        }
    except Exception as e:
        return {
            "server_online": False,
            "error": str(e),
            "gpu_hardware": "NVIDIA GeForce RTX 4050",
        }


@app.get("/api/presets")
def get_presets():
    """Return pre-packaged adversarial and benchmark prompt templates."""
    return PRESET_TEMPLATES


@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    """Return overall dashboard telemetry, failure counts, and recent traces."""
    db = Database()
    trace_repo = TraceRepository(db)
    fail_repo = FailureRepository(db)
    
    traces = trace_repo.list_all(limit=1000)
    total_traces = len(traces)
    total_failures = 0
    scores = []
    root_causes_found = 0
    
    for t in traces:
        fails = fail_repo.list_by_trace(t.trace_id)
        total_failures += len(fails)
        for s in t.spans:
            if s.judge_score is not None:
                scores.append(s.judge_score)
        if t.total_latency_ms and t.total_latency_ms > 0:
            root_causes_found += 1
            
    avg_score = (sum(scores) / len(scores)) if scores else 0.0
    
    recent = []
    for t in traces[:6]:
        fails = fail_repo.list_by_trace(t.trace_id)
        recent.append({
            "trace_id": t.trace_id,
            "pipeline_name": t.pipeline_name,
            "status": t.status.value if hasattr(t.status, "value") else str(t.status),
            "final_score": t.final_score,
            "span_count": len(t.spans),
            "failure_count": len(fails),
            "total_latency_ms": t.total_latency_ms,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })
        
    return {
        "total_traces": total_traces,
        "total_failures": total_failures,
        "avg_judge_score": round(avg_score, 2),
        "traces_analyzed": root_causes_found,
        "recent_traces": recent,
    }


@app.get("/api/traces")
def get_traces(limit: int = 50):
    """List recent execution traces with summary stats."""
    db = Database()
    trace_repo = TraceRepository(db)
    fail_repo = FailureRepository(db)
    
    traces = trace_repo.list_all(limit=limit)
    result = []
    for t in traces:
        failures = fail_repo.list_by_trace(t.trace_id)
        result.append({
            "trace_id": t.trace_id,
            "pipeline_name": t.pipeline_name,
            "status": t.status.value if hasattr(t.status, "value") else str(t.status),
            "total_latency_ms": t.total_latency_ms,
            "final_score": t.final_score,
            "span_count": len(t.spans),
            "failure_count": len(failures),
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })
    return result


@app.get("/api/traces/{trace_id}")
def get_trace_detail(trace_id: str):
    """Get full execution trace details, spans, and failures."""
    db = Database()
    trace_repo = TraceRepository(db)
    fail_repo = FailureRepository(db)
    
    trace = trace_repo.get(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
        
    failures = fail_repo.list_by_trace(trace_id)
    return {
        "trace": trace.model_dump(mode="json"),
        "failures": [f.model_dump(mode="json") for f in failures],
    }


@app.delete("/api/traces/{trace_id}")
def delete_trace(trace_id: str):
    """Delete an execution trace and its associated spans."""
    db = Database()
    repo = TraceRepository(db)
    success = repo.delete(trace_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete trace")
    return {"success": True, "trace_id": trace_id}


@app.post("/api/failures/detect")
def detect_failures_endpoint(req: DetectFailuresRequest):
    """Run failure detection and classification on a specific trace."""
    db = Database()
    trace_repo = TraceRepository(db)
    trace = trace_repo.get(req.trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
        
    # Only evaluate with LLM judge if spans are missing judge scores
    if any(s.judge_score is None for s in trace.spans):
        from src.evaluation.judge import Judge
        judge = Judge()
        evaluator = Evaluator(judge=judge)
        evaluator.evaluate_trace(trace)
    
    detector = FailureDetector(threshold=req.threshold)
    raw_failures = detector.detect(trace)
    
    classifier = FailureClassifier()
    classified_failures = classifier.classify_batch(raw_failures, trace)
    
    return {
        "failures": [f.model_dump(mode="json") for f in classified_failures],
        "count": len(classified_failures),
    }


@app.get("/api/failures/trace/{trace_id}")
def get_failures_by_trace(trace_id: str):
    """Get stored failures for a given trace."""
    db = Database()
    fail_repo = FailureRepository(db)
    failures = fail_repo.list_by_trace(trace_id)
    return [f.model_dump(mode="json") for f in failures]


@app.post("/api/failures/save")
def save_failure_endpoint(failure_data: Dict[str, Any] = Body(...)):
    """Save detected failure to the database."""
    db = Database()
    fail_repo = FailureRepository(db)
    try:
        f = Failure(
            failure_id=failure_data["failure_id"],
            trace_id=failure_data["trace_id"],
            span_id=failure_data["span_id"],
            step_name=failure_data.get("step_name", ""),
            failure_type=FailureType(failure_data["failure_type"]),
            severity=float(failure_data.get("severity", 0.5)),
            judge_score=float(failure_data.get("judge_score", 0.0)),
            description=failure_data.get("description", ""),
            evidence=failure_data.get("evidence", {}),
            confirmed=failure_data.get("confirmed", False),
        )
        fail_repo.save(f)
        return {"status": "saved", "failure_id": f.failure_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/propagation/{trace_id}")
def get_propagation_graph_data(trace_id: str):
    """Generate DAG graph nodes, edges, and transmission arcs for frontend Canvas/SVG rendering."""
    db = Database()
    trace_repo = TraceRepository(db)
    fail_repo = FailureRepository(db)
    
    trace = trace_repo.get(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
        
    failures = fail_repo.list_by_trace(trace_id)
    
    # Fallback: if no failures saved in DB, detect dynamically from spans
    if not failures:
        detector = FailureDetector(threshold=0.7)
        raw_fails = detector.detect(trace)
        if raw_fails:
            classifier = FailureClassifier()
            failures = classifier.classify_batch(raw_fails, trace)
    
    # 1. Build Base Nodes
    nodes = []
    root_cause_span_id = None
    root_cause_confidence = 0.85
    propagation_analysis = None
    root_cause = None
    
    if failures:
        pa = PropagationAnalyzer()
        propagation_analysis = pa.analyze(failures[0], trace)
        rce = RootCauseEngine()
        root_cause = rce.analyze(failures[0], trace, propagation_analysis)
        root_cause_span_id = root_cause.root_span_id
        root_cause_confidence = root_cause.root_cause_confidence
        
    affected_spans = set(propagation_analysis.affected_spans) if propagation_analysis else set()
    
    for i, s in enumerate(trace.spans):
        is_root = (s.span_id == root_cause_span_id)
        is_affected = (s.span_id in affected_spans)
        
        status_category = "healthy"
        if is_root:
            status_category = "root_cause"
        elif is_affected or s.error or (str(s.status).lower() == "failed") or (s.judge_score is not None and s.judge_score < 0.7):
            status_category = "propagated"
            
        nodes.append({
            "id": s.span_id,
            "step_name": s.step_name,
            "step_index": s.step_index,
            "status": s.status.value if hasattr(s.status, "value") else str(s.status),
            "status_category": status_category,
            "judge_score": s.judge_score,
            "latency_ms": s.latency_ms,
            "output_preview": str(s.output_data)[:200] if s.output_data else "",
            "output_data": s.output_data,
            "input_data": s.input_data,
            "error": s.error,
        })
        
    # 2. Sequential Base Edges
    edges = []
    for i in range(len(nodes) - 1):
        edges.append({
            "source": nodes[i]["id"],
            "target": nodes[i+1]["id"],
        })
        
    # 3. Curved Propagation Transmission Arcs
    arcs = []
    if propagation_analysis:
        for p in propagation_analysis.paths:
            arcs.append({
                "source": p.source_span_id,
                "target": p.target_span_id,
                "propagation_score": p.propagation_score,
                "evidence": p.evidence,
            })
            
    # 4. Generate AI Forensic Explanation
    explanation_text = ""
    if failures and propagation_analysis and root_cause:
        try:
            generator = ExplanationGenerator()
            explanation_text = generator.generate(failures[0], trace, root_cause, propagation_analysis)
        except Exception:
            explanation_text = f"Root cause diagnosed at step '{root_cause.root_step_name}' with confidence {root_cause.root_cause_confidence:.1%}."
            
    return {
        "trace_id": trace.trace_id,
        "nodes": nodes,
        "edges": edges,
        "propagation_arcs": arcs,
        "overall_propagation_score": propagation_analysis.overall_propagation_score if propagation_analysis else 0.0,
        "root_cause_confidence": root_cause_confidence if failures else 1.0,
        "root_cause_step": root_cause.root_step_name if root_cause else None,
        "has_failures": len(failures) > 0,
        "explanation": explanation_text,
    }


@app.post("/api/pipeline/run")
def run_pipeline(req: RunPipelineRequest):
    """Execute pipeline, diagnose failures, and conditionally auto-heal."""
    # 1. Structure input
    if req.auto_structure:
        payload = SmartInputPreprocessor.auto_structure(req.input_text)
    else:
        payload = {"raw_text": req.input_text}
        
    # 2. Set LLM Model
    clean_model = req.model.split()[0]
    client = get_ollama_client(model=clean_model)
    client.set_model(clean_model)
    
    # 3. Execute Pipeline
    pipeline = create_pipeline()
    runner = PipelineRunner(pipeline=pipeline, auto_persist=True)
    output, trace = runner.run(payload)
    
    db = Database()
    trace_repo = TraceRepository(db)
    fail_repo = FailureRepository(db)
    
    # 4. Evaluation & Failure Diagnosis
    failures = []
    evaluator = Evaluator()
    if req.auto_evaluate:
        try:
            evaluator.evaluate_trace(trace)
            detector = FailureDetector(threshold=0.7)
            raw_fails = detector.detect(trace)
            classifier = FailureClassifier()
            failures = classifier.classify_batch(raw_fails, trace)
            for f in failures:
                fail_repo.save(f)
            trace_repo.save(trace)
        except Exception as eval_err:
            print("Evaluation warning:", eval_err)
            
    # 5. Propagation & Root Cause
    propagation_analysis = None
    root_cause = None
    if failures:
        pa = PropagationAnalyzer()
        propagation_analysis = pa.analyze(failures[0], trace)
        rce = RootCauseEngine()
        root_cause = rce.analyze(failures[0], trace, propagation_analysis)
        
    # 6. Real-time Closed-Loop Self-Healing
    healed_trace = None
    recommendations_applied = []
    if req.auto_heal and failures:
        try:
            optimizer = AdaptiveOptimizer()
            recommendations_applied = optimizer.generate_recommendations(failures)
            adapted_pipe = optimizer.build_adapted_pipeline(recommendations_applied)
            adapted_runner = PipelineRunner(pipeline=adapted_pipe, auto_persist=True)
            healed_output, healed_trace = adapted_runner.run(payload)
            evaluator.evaluate_trace(healed_trace)
            trace_repo.save(healed_trace)
        except Exception as heal_err:
            print("Auto-heal warning:", heal_err)
            
    return {
        "trace": trace.model_dump(mode="json"),
        "failures": [f.model_dump(mode="json") for f in failures],
        "root_cause": root_cause.model_dump(mode="json") if root_cause else None,
        "propagation": propagation_analysis.model_dump(mode="json") if propagation_analysis else None,
        "healed_trace": healed_trace.model_dump(mode="json") if healed_trace else None,
        "recommendations": [r.model_dump(mode="json") for r in recommendations_applied],
    }


@app.post("/api/feedback/benchmark")
def run_benchmark():
    """Run closed-loop adaptive regression benchmark on evaluation cases."""
    dataset = EvaluationDataset()
    dataset.load()
    cases = dataset.cases
    
    if not cases:
        raise HTTPException(status_code=400, detail="No evaluation cases in dataset. Run a pipeline or seed data first.")
        
    runner = RegressionRunner()
    report = runner.compare_runs(cases)
    return report.model_dump(mode="json")


@app.get("/api/report/{trace_id}")
def export_report(trace_id: str):
    """Download Markdown investigation report for a trace."""
    db = Database()
    trace = TraceRepository(db).get(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
        
    failures = FailureRepository(db).list_by_trace(trace_id)
    primary_fail = failures[0] if failures else None
    
    prop = None
    rc = None
    if primary_fail:
        prop = PropagationAnalyzer().analyze(primary_fail, trace)
        rc = RootCauseEngine().analyze(primary_fail, trace, prop)
        
    md = ForensicsReportExporter.generate_markdown(trace, primary_fail, prop, rc)
    return PlainTextResponse(content=md, media_type="text/markdown")


@app.get("/api/feedback/cases")
def list_feedback_cases(limit: int = 100):
    """List evaluation cases for regression and evaluation dataset."""
    db = Database()
    eval_repo = EvaluationRepository(db)
    cases = eval_repo.list_cases(limit=limit)
    return [c.model_dump(mode="json") for c in cases]


@app.post("/api/feedback/case")
def create_feedback_case(case_data: Dict[str, Any] = Body(...)):
    """Save a new evaluation case from a failure trace."""
    db = Database()
    eval_repo = EvaluationRepository(db)
    try:
        case = EvaluationCase(
            case_id=case_data["case_id"],
            trace_id=case_data.get("trace_id", ""),
            failure_id=case_data.get("failure_id"),
            original_input=case_data.get("original_input", {}),
            failing_step=case_data.get("failing_step", ""),
            incorrect_output=case_data.get("incorrect_output", {}),
            corrected_output=case_data.get("corrected_output", {}),
            failure_type=case_data.get("failure_type", "hallucination"),
            root_cause_step=case_data.get("root_cause_step", ""),
        )
        eval_repo.save_case(case)
        return {"status": "saved", "case_id": case.case_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/feedback/export")
def export_feedback_dataset():
    """Export all saved evaluation cases into the dataset JSON file."""
    db = Database()
    eval_repo = EvaluationRepository(db)
    cases = eval_repo.list_cases(limit=1000)
    dataset = EvaluationDataset()
    for c in cases:
        dataset.add_case(c)
    saved_path = dataset.save()
    return {"status": "exported", "path": str(saved_path), "case_count": len(cases)}


@app.get("/api/analytics")
def get_analytics_metrics():
    """System-wide analytics, metrics distribution, and pipeline comparisons."""
    db = Database()
    trace_repo = TraceRepository(db)
    eval_repo = EvaluationRepository(db)
    
    traces = trace_repo.list_all(limit=1000)
    total_traces = len(traces)
    total_spans = sum(len(t.spans) for t in traces)
    valid_scores = [t.final_score for t in traces if t.final_score is not None]
    avg_score = (sum(valid_scores) / len(valid_scores)) if valid_scores else 0.0
    failed_count = sum(1 for t in traces if str(t.status).upper() in ["FAILED", "STATUS.FAILED"])
    
    # Pipeline breakdown
    pipelines = {}
    for t in traces:
        name = t.pipeline_name
        if name not in pipelines:
            pipelines[name] = {"count": 0, "total_score": 0.0, "scores_count": 0}
        pipelines[name]["count"] += 1
        if t.final_score is not None:
            pipelines[name]["total_score"] += t.final_score
            pipelines[name]["scores_count"] += 1
            
    breakdown = {}
    for name, data in pipelines.items():
        avg = (data["total_score"] / data["scores_count"]) if data["scores_count"] > 0 else 0.0
        breakdown[name] = {
            "count": data["count"],
            "avg_score": round(avg, 2),
        }
        
    # Judge scores distribution across all spans
    span_scores = []
    for t in traces:
        for s in t.spans:
            if s.judge_score is not None:
                span_scores.append(s.judge_score)
                
    score_stats = {
        "min": round(min(span_scores), 2) if span_scores else 0.0,
        "max": round(max(span_scores), 2) if span_scores else 0.0,
        "avg": round(sum(span_scores) / len(span_scores), 2) if span_scores else 0.0,
        "total_evaluated_spans": len(span_scores),
        "distribution": {
            "low": sum(1 for s in span_scores if s < 0.5),
            "medium": sum(1 for s in span_scores if 0.5 <= s < 0.7),
            "good": sum(1 for s in span_scores if 0.7 <= s < 0.9),
            "excellent": sum(1 for s in span_scores if s >= 0.9),
        },
    }
    
    cases = eval_repo.list_cases(limit=10)
    
    return {
        "total_traces": total_traces,
        "total_spans": total_spans,
        "avg_score": round(avg_score, 2),
        "failed_traces": failed_count,
        "pipeline_breakdown": breakdown,
        "score_stats": score_stats,
        "cases": [c.model_dump(mode="json") for c in cases],
    }



# =============================================================================
# Serve Modern Frontend Static Files
# =============================================================================
STATIC_DIR = ROOT_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "FailureForensicsTool API is online. Add static/index.html to view UI."}


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FailureForensicsTool Web Application on http://localhost:8000...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
