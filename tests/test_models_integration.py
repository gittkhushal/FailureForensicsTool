"""
Integration tests for all data models.

Tests model creation, validation, serialization, and utilities.
"""

import pytest
import json
from datetime import datetime

from src.models import (
    StepType, StepInput, StepOutput, PipelineConfig,
    SpanStatus, Span, TraceStatus, Trace,
    FailureType, Failure, PropagationPath, PropagationAnalysis,
    RootCauseCandidate, RootCauseAnalysis, FailureAnalysisSummary,
    EvaluationCriteria, JudgeResult, EvaluationCase,
    FeedbackRecord, RegressionResult, DatasetStatistics,
)


class TestPipelineModels:
    """Test pipeline data models."""
    
    def test_step_input_creation(self):
        """Test StepInput creation and validation."""
        data = {"document": "test", "metadata": {"source": "test"}}
        step_input = StepInput(data=data, metadata={"version": "1"})
        
        assert step_input.data == data
        assert step_input.metadata["version"] == "1"
    
    def test_step_input_invalid(self):
        """Test StepInput requires data."""
        # data is required, so it must be provided
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            StepInput()  # Missing required 'data' field
    
    def test_step_output_creation(self):
        """Test StepOutput creation."""
        output_data = {"extracted": ["entity1", "entity2"]}
        step_output = StepOutput(
            data=output_data,
            confidence=0.95,
            metadata={"model": "qwen"}
        )
        
        assert step_output.data == output_data
        assert step_output.confidence == 0.95
    
    def test_step_output_confidence_validation(self):
        """Test confidence score bounds."""
        with pytest.raises(Exception):
            StepOutput(data={"test": 1}, confidence=1.5)  # > 1.0
        
        with pytest.raises(Exception):
            StepOutput(data={"test": 1}, confidence=-0.1)  # < 0.0
    
    def test_pipeline_config_creation(self):
        """Test PipelineConfig creation."""
        config = PipelineConfig(
            name="test_pipeline",
            steps=["intake", "extraction", "classification"],
            timeout_per_step=60,
            fail_fast=True
        )
        
        assert config.name == "test_pipeline"
        assert len(config.steps) == 3


class TestTraceModels:
    """Test trace and span models."""
    
    def test_span_creation(self):
        """Test Span creation."""
        span = Span(
            span_id="span1",
            trace_id="trace1",
            step_name="extraction",
            step_index=1,
            input_data={"text": "document"},
            output_data={"entities": []},
            confidence=0.8,
            judge_score=0.85,
            status=SpanStatus.SUCCESS,
        )
        
        assert span.span_id == "span1"
        assert span.step_name == "extraction"
        assert span.status == SpanStatus.SUCCESS
    
    def test_span_latency_tracking(self):
        """Test span latency recording."""
        span = Span(
            span_id="span1",
            trace_id="trace1",
            step_name="test",
            step_index=0,
            latency_ms=123.45,
        )
        
        assert span.latency_ms == 123.45
    
    def test_trace_creation(self):
        """Test Trace creation."""
        trace = Trace(
            trace_id="trace1",
            pipeline_name="document_pipeline",
            input_data={"document": "test"},
            status=TraceStatus.RUNNING,
        )
        
        assert trace.trace_id == "trace1"
        assert len(trace.spans) == 0
    
    def test_trace_span_operations(self):
        """Test trace span operations."""
        trace = Trace(trace_id="trace1")
        
        # Create and add spans
        span1 = Span(
            span_id="s1", trace_id="trace1", step_name="step1",
            step_index=0, output_data="output1", judge_score=0.9
        )
        span2 = Span(
            span_id="s2", trace_id="trace1", step_name="step2",
            step_index=1, output_data="output2", judge_score=0.5
        )
        
        trace.add_span(span1)
        trace.add_span(span2)
        
        assert len(trace.spans) == 2
        assert trace.get_span_by_name("step1") == span1
        assert trace.get_span_by_name("step2") == span2
        assert trace.get_span_by_id("s1") == span1
    
    def test_trace_failed_spans(self):
        """Test getting failed spans."""
        trace = Trace(trace_id="trace1")
        
        trace.add_span(Span(
            span_id="s1", trace_id="trace1", step_name="s1",
            step_index=0, judge_score=0.9  # Pass
        ))
        trace.add_span(Span(
            span_id="s2", trace_id="trace1", step_name="s2",
            step_index=1, judge_score=0.5  # Fail
        ))
        trace.add_span(Span(
            span_id="s3", trace_id="trace1", step_name="s3",
            step_index=2, judge_score=0.6  # Fail
        ))
        
        failed = trace.get_failed_spans(threshold=0.7)
        assert len(failed) == 2
    
    def test_trace_statistics(self):
        """Test trace statistics."""
        trace = Trace(
            trace_id="trace1",
            pipeline_name="test",
            total_latency_ms=150.0,
            final_score=0.85,
            status=TraceStatus.SUCCESS,
        )
        
        stats = trace.get_statistics()
        assert stats["trace_id"] == "trace1"
        assert stats["total_latency_ms"] == 150.0
        assert stats["final_score"] == 0.85


class TestFailureModels:
    """Test failure analysis models."""
    
    def test_failure_creation(self):
        """Test Failure creation."""
        failure = Failure(
            failure_id="fail1",
            trace_id="trace1",
            span_id="span1",
            step_name="extraction",
            failure_type=FailureType.EXTRACTION_HALLUCINATION,
            severity=0.8,
            judge_score=0.3,
            description="Extracted unsupported entities",
        )
        
        assert failure.failure_id == "fail1"
        assert failure.failure_type == FailureType.EXTRACTION_HALLUCINATION
    
    def test_failure_type_enum(self):
        """Test FailureType enum."""
        types = [
            FailureType.EXTRACTION_HALLUCINATION,
            FailureType.MISCLASSIFICATION,
            FailureType.INCOMPLETE_OUTPUT,
        ]
        
        assert len(types) == 3
        assert FailureType.EXTRACTION_HALLUCINATION.value == "extraction_hallucination"
    
    def test_propagation_path_creation(self):
        """Test PropagationPath creation."""
        path = PropagationPath(
            source_span_id="span1",
            target_span_id="span2",
            propagation_score=0.75,
            evidence={"reason": "error propagated"},
        )
        
        assert path.source_span_id == "span1"
        assert path.propagation_score == 0.75
    
    def test_propagation_analysis_creation(self):
        """Test PropagationAnalysis creation."""
        analysis = PropagationAnalysis(
            analysis_id="prop1",
            failure_id="fail1",
            trace_id="trace1",
        )
        
        # Add paths
        path1 = PropagationPath(
            source_span_id="s1", target_span_id="s2",
            propagation_score=0.8
        )
        path2 = PropagationPath(
            source_span_id="s1", target_span_id="s3",
            propagation_score=0.6
        )
        
        analysis.paths = [path1, path2]
        analysis.affected_spans = ["s2", "s3"]
        analysis.overall_propagation_score = 0.7
        
        assert len(analysis.paths) == 2
        assert analysis.overall_propagation_score == 0.7
    
    def test_root_cause_candidate_creation(self):
        """Test RootCauseCandidate creation."""
        candidate = RootCauseCandidate(
            span_id="span1",
            step_name="extraction",
            confidence=0.85,
            local_severity=0.9,
            downstream_impact=0.7,
            reasoning="Early failure with high propagation",
        )
        
        assert candidate.confidence == 0.85
        assert candidate.span_id == "span1"
    
    def test_root_cause_analysis_creation(self):
        """Test RootCauseAnalysis creation."""
        analysis = RootCauseAnalysis(
            analysis_id="rca1",
            trace_id="trace1",
            failure_id="fail1",
            root_span_id="span1",
            root_step_name="extraction",
            root_cause_confidence=0.88,
        )
        
        assert analysis.root_cause_confidence == 0.88
        assert analysis.root_step_name == "extraction"
    
    def test_failure_analysis_summary_creation(self):
        """Test FailureAnalysisSummary creation."""
        failure = Failure(
            failure_id="fail1",
            trace_id="trace1",
            span_id="s1",
            step_name="extraction",
            failure_type=FailureType.EXTRACTION_HALLUCINATION,
        )
        
        summary = FailureAnalysisSummary(
            trace_id="trace1",
            failure_detected=True,
            failure_count=1,
            primary_failure=failure,
            propagation_impact=0.75,
        )
        
        assert summary.failure_detected is True
        assert summary.failure_count == 1


class TestEvaluationModels:
    """Test evaluation models."""
    
    def test_judge_result_creation(self):
        """Test JudgeResult creation."""
        result = JudgeResult(
            span_id="span1",
            step_name="extraction",
            overall_score=0.85,
            criteria_scores={
                "correctness": 0.9,
                "hallucination": 0.8,
                "completeness": 0.85,
            },
            passed=True,
            reasoning="Good quality extraction",
        )
        
        assert result.overall_score == 0.85
        assert result.passed is True
    
    def test_evaluation_case_creation(self):
        """Test EvaluationCase creation."""
        case = EvaluationCase(
            case_id="case1",
            trace_id="trace1",
            original_input={"document": "test"},
            failing_step="extraction",
            incorrect_output={"entities": ["wrong"]},
            corrected_output={"entities": ["correct"]},
            failure_type="extraction_hallucination",
            root_cause_step="extraction",
        )
        
        assert case.case_id == "case1"
        assert case.failure_type == "extraction_hallucination"
    
    def test_feedback_record_creation(self):
        """Test FeedbackRecord creation."""
        feedback = FeedbackRecord(
            feedback_id="fb1",
            trace_id="trace1",
            diagnosis_confirmed=True,
            root_cause_confirmed=True,
            comments="Diagnosis was accurate",
        )
        
        assert feedback.diagnosis_confirmed is True
    
    def test_regression_result_creation(self):
        """Test RegressionResult creation."""
        result = RegressionResult(
            run_id="run1",
            case_id="case1",
            passed=False,
            score=0.85,
            improved=True,
            score_delta=0.1,
        )
        
        assert result.improved is True
        assert result.score_delta == 0.1
    
    def test_dataset_statistics_creation(self):
        """Test DatasetStatistics creation."""
        stats = DatasetStatistics(
            total_cases=10,
            failure_types={
                "extraction_hallucination": 5,
                "misclassification": 3,
                "incomplete_output": 2,
            },
            root_causes={
                "extraction": 6,
                "classification": 4,
            },
        )
        
        assert stats.total_cases == 10
        assert stats.failure_types["extraction_hallucination"] == 5


class TestModelSerialization:
    """Test model serialization and deserialization."""
    
    def test_trace_serialization(self):
        """Test Trace JSON serialization."""
        trace = Trace(
            trace_id="trace1",
            pipeline_name="test",
            input_data={"text": "test"},
            output_data={"result": "success"},
            status=TraceStatus.SUCCESS,
        )
        
        # Serialize
        json_str = trace.model_dump_json()
        assert "trace1" in json_str
        
        # Deserialize
        restored = Trace.model_validate_json(json_str)
        assert restored.trace_id == "trace1"
    
    def test_failure_serialization(self):
        """Test Failure serialization."""
        failure = Failure(
            failure_id="fail1",
            trace_id="trace1",
            span_id="s1",
            step_name="extraction",
            failure_type=FailureType.EXTRACTION_HALLUCINATION,
            evidence={"detail": "unsupported entity"},
        )
        
        # Serialize
        json_str = failure.model_dump_json()
        
        # Deserialize
        restored = Failure.model_validate_json(json_str)
        assert restored.failure_type == FailureType.EXTRACTION_HALLUCINATION


class TestModelValidation:
    """Test model validation."""
    
    def test_confidence_bounds_validation(self):
        """Test confidence score validation."""
        # Valid
        result = JudgeResult(
            span_id="s1", step_name="test",
            overall_score=0.5
        )
        assert result.overall_score == 0.5
        
        # Invalid high
        with pytest.raises(Exception):
            JudgeResult(span_id="s1", step_name="test", overall_score=1.5)
        
        # Invalid low
        with pytest.raises(Exception):
            JudgeResult(span_id="s1", step_name="test", overall_score=-0.1)
    
    def test_required_fields_validation(self):
        """Test required field validation."""
        # Missing required field
        with pytest.raises(Exception):
            Failure(
                failure_id="f1",
                trace_id="t1",
                # missing span_id
                step_name="test",
                failure_type=FailureType.UNKNOWN,
            )
