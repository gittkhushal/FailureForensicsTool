"""
Seed script to populate realistic multi-step traces, failures, and evaluation cases.

Generates:
1. Pristine Healthy Trace (High Judge Scores, 0 Failures)
2. Cascading Failure Trace (Extraction Hallucination -> Misclassification -> Incomplete Output with active DAG propagation)
3. Direct Classification Failure Trace
4. Pre-packaged evaluation cases in database & JSON store for instant closed-loop benchmarking
"""

import sys
import uuid
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from src.storage.database import Database
from src.storage.repositories import TraceRepository, FailureRepository, EvaluationRepository
from src.models.trace_models import Trace, Span, TraceStatus, SpanStatus
from src.models.failure_models import Failure, FailureType
from src.models.evaluation_models import EvaluationCase
from src.feedback.dataset import EvaluationDataset


def seed_database():
    """Seed sample forensics data."""
    db = Database()
    trace_repo = TraceRepository(db)
    failure_repo = FailureRepository(db)
    eval_repo = EvaluationRepository(db)
    dataset = EvaluationDataset()

    print("🌱 Seeding realistic demo data for FailureForensicsTool...")

    # =========================================================================
    # 1. Healthy Baseline Trace
    # =========================================================================
    healthy_trace_id = str(uuid.uuid4())
    healthy_spans = [
        Span(
            span_id=str(uuid.uuid4()),
            trace_id=healthy_trace_id,
            step_name="intake",
            step_index=0,
            status=SpanStatus.SUCCESS,
            latency_ms=12.4,
            judge_score=0.96,
            input_data={"raw_text": "TechCorp announced Q3 earnings of $4.2B, exceeding estimates."},
            output_data={"normalized_text": "TechCorp announced Q3 earnings of $4.2B, exceeding estimates.", "length": 59},
        ),
        Span(
            span_id=str(uuid.uuid4()),
            trace_id=healthy_trace_id,
            step_name="extraction",
            step_index=1,
            status=SpanStatus.SUCCESS,
            latency_ms=184.2,
            judge_score=0.94,
            input_data={"normalized_text": "TechCorp announced Q3 earnings of $4.2B, exceeding estimates."},
            output_data={"company": "TechCorp", "metric": "earnings", "value": "$4.2B", "period": "Q3"},
        ),
        Span(
            span_id=str(uuid.uuid4()),
            trace_id=healthy_trace_id,
            step_name="classification",
            step_index=2,
            status=SpanStatus.SUCCESS,
            latency_ms=142.1,
            judge_score=0.95,
            input_data={"company": "TechCorp", "value": "$4.2B"},
            output_data={"category": "Financial Performance", "sentiment": "Positive", "confidence": 0.95},
        ),
        Span(
            span_id=str(uuid.uuid4()),
            trace_id=healthy_trace_id,
            step_name="summarization",
            step_index=3,
            status=SpanStatus.SUCCESS,
            latency_ms=210.5,
            judge_score=0.93,
            input_data={"category": "Financial Performance", "value": "$4.2B"},
            output_data={"summary": "TechCorp reported a strong Q3 with $4.2B earnings beating consensus."},
        ),
    ]
    healthy_trace = Trace(
        trace_id=healthy_trace_id,
        pipeline_name="financial_intake_pipeline",
        status=TraceStatus.SUCCESS,
        total_latency_ms=sum(s.latency_ms for s in healthy_spans),
        final_score=0.95,
        spans=healthy_spans,
    )
    trace_repo.save(healthy_trace)
    print(f"  ✅ Saved Healthy Trace: {healthy_trace_id[:12]}... (Score: 0.95)")

    # =========================================================================
    # 2. Cascading Failure Trace (Root Cause: Extraction Hallucination)
    # =========================================================================
    fail_trace_id = str(uuid.uuid4())
    s0_id = str(uuid.uuid4())
    s1_id = str(uuid.uuid4())
    s2_id = str(uuid.uuid4())
    s3_id = str(uuid.uuid4())

    fail_spans = [
        Span(
            span_id=s0_id,
            trace_id=fail_trace_id,
            step_name="intake",
            step_index=0,
            status=SpanStatus.SUCCESS,
            latency_ms=15.1,
            judge_score=0.92,
            input_data={"raw_text": "The patient reported mild headache after taking medication A."},
            output_data={"normalized_text": "The patient reported mild headache after taking medication A.", "length": 60},
        ),
        Span(
            span_id=s1_id,
            trace_id=fail_trace_id,
            step_name="extraction",
            step_index=1,
            status=SpanStatus.FAILED,
            latency_ms=340.8,
            judge_score=0.32,  # Severe failure!
            input_data={"normalized_text": "The patient reported mild headache after taking medication A."},
            output_data={
                "symptoms": ["severe migraine", "loss of consciousness", "cardiac arrest"],  # Hallucinated!
                "dosage": "500mg daily",
            },
            error="Entity hallucination: Extracted severe symptoms not mentioned in source text.",
        ),
        Span(
            span_id=s2_id,
            trace_id=fail_trace_id,
            step_name="classification",
            step_index=2,
            status=SpanStatus.FAILED,
            latency_ms=290.4,
            judge_score=0.41,  # Downstream degraded
            input_data={"symptoms": ["severe migraine", "loss of consciousness", "cardiac arrest"]},
            output_data={"triage_level": "CRITICAL EMERGENCY - ICU ADMISSION", "confidence": 0.88},
            error="Propagated misclassification due to hallucinated upstream inputs.",
        ),
        Span(
            span_id=s3_id,
            trace_id=fail_trace_id,
            step_name="summarization",
            step_index=3,
            status=SpanStatus.FAILED,
            latency_ms=315.6,
            judge_score=0.48,  # Final outcome corrupted
            input_data={"triage_level": "CRITICAL EMERGENCY - ICU ADMISSION"},
            output_data={"dispatch_summary": "Immediate ambulance dispatch required for acute cardiac emergency."},
            error="Corrupted clinical dispatch generated from false triage.",
        ),
    ]
    fail_trace = Trace(
        trace_id=fail_trace_id,
        pipeline_name="clinical_triage_pipeline",
        status=TraceStatus.FAILED,
        total_latency_ms=sum(s.latency_ms for s in fail_spans),
        final_score=0.41,
        spans=fail_spans,
    )
    trace_repo.save(fail_trace)

    # Attach detected failures
    f1 = Failure(
        failure_id=str(uuid.uuid4()),
        trace_id=fail_trace_id,
        span_id=s1_id,
        step_name="extraction",
        failure_type=FailureType.EXTRACTION_HALLUCINATION,
        severity=0.88,
        judge_score=0.32,
        description="Extracted critical ungrounded symptoms not present in patient report.",
        evidence={
            "judge_score": 0.32,
            "hallucinated_tokens": ["loss of consciousness", "cardiac arrest"],
            "classification_rationale": "Hallucinated symptoms triggered severe diagnostic distortion.",
        },
    )
    f2 = Failure(
        failure_id=str(uuid.uuid4()),
        trace_id=fail_trace_id,
        span_id=s2_id,
        step_name="classification",
        failure_type=FailureType.MISCLASSIFICATION,
        severity=0.75,
        judge_score=0.41,
        description="Triage category escalated to ICU emergency due to upstream hallucination.",
        evidence={"judge_score": 0.41, "classification_rationale": "Downstream misclassification."},
    )
    failure_repo.save(f1)
    failure_repo.save(f2)
    print(f"  ✅ Saved Cascading Failure Trace: {fail_trace_id[:12]}... (Origin: Extraction Hallucination)")

    # =========================================================================
    # 3. Pre-populate Evaluation Cases for Closed-Loop Optimization
    # =========================================================================
    cases = [
        EvaluationCase(
            case_id="case_med_hallucination_01",
            trace_id=fail_trace_id,
            original_input={"text": "The patient reported mild headache after taking medication A."},
            failing_step="extraction",
            incorrect_output={"symptoms": ["severe migraine", "loss of consciousness", "cardiac arrest"]},
            corrected_output={"symptoms": ["mild headache"], "medication": "medication A"},
            failure_type="hallucination",
            root_cause_step="extraction",
        ),
        EvaluationCase(
            case_id="case_triage_escalation_02",
            trace_id=fail_trace_id,
            original_input={"symptoms": ["mild headache"]},
            failing_step="classification",
            incorrect_output={"triage_level": "CRITICAL EMERGENCY"},
            corrected_output={"triage_level": "Routine Outpatient", "confidence": 0.95},
            failure_type="misclassification",
            root_cause_step="extraction",
        ),
        EvaluationCase(
            case_id="case_truncation_summary_03",
            trace_id=fail_trace_id,
            original_input={"patient": "John Doe", "history": "Hypertension, stable on lisinopril"},
            failing_step="summarization",
            incorrect_output={"summary": "Patient has"},
            corrected_output={"summary": "Patient John Doe with history of hypertension, clinically stable on lisinopril."},
            failure_type="incomplete_output",
            root_cause_step="summarization",
        ),
    ]

    for c in cases:
        eval_repo.save_case(c)
        dataset.add_case(c)
    dataset.save()
    print(f"  ✅ Saved {len(cases)} Evaluation Cases to database & evaluation_cases.json")

    print("\n🎉 Demo dataset seeded successfully!")
    print("Open http://localhost:8501 to explore:")
    print("  1. Dashboard -> Recent traces & metrics")
    print("  2. Propagation Analysis -> Visual Interactive DAG showing failure flow")
    print("  3. Feedback & Evaluation -> Click 'Run Self-Improving Adaptation & Benchmark'")


if __name__ == "__main__":
    seed_database()
