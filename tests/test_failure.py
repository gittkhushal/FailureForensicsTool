"""Tests for failure detection and classification."""

import pytest
from unittest.mock import Mock, patch

from src.failure.detector import FailureDetector
from src.failure.classifier import FailureClassifier
from src.models.trace_models import Trace, Span, SpanStatus
from src.models.failure_models import Failure, FailureType


class TestFailureDetector:
    """Test failure detection engine."""
    
    def test_detector_initialization(self):
        """Test detector initialization."""
        detector = FailureDetector(threshold=0.7)
        assert detector.threshold == 0.7
    
    def test_detector_detects_low_score(self):
        """Test detection of low judge scores."""
        detector = FailureDetector(threshold=0.8)
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        span = Span(
            span_id="s1",
            trace_id="t1",
            step_name="extraction",
            step_index=0,
        )
        span.judge_score = 0.5  # Below threshold
        trace.add_span(span)
        
        failures = detector.detect(trace)
        
        assert len(failures) == 1
        assert failures[0].span_id == "s1"
        assert failures[0].trace_id == "t1"
    
    def test_detector_ignores_high_score(self):
        """Test that high scores don't trigger failures."""
        detector = FailureDetector(threshold=0.8)
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        span = Span(
            span_id="s1",
            trace_id="t1",
            step_name="extraction",
            step_index=0,
        )
        span.judge_score = 0.9  # Above threshold
        trace.add_span(span)
        
        failures = detector.detect(trace)
        
        assert len(failures) == 0
    
    def test_detector_handles_multiple_spans(self):
        """Test detection with multiple spans."""
        detector = FailureDetector(threshold=0.7)
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        # Good span
        span1 = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
        span1.judge_score = 0.9
        trace.add_span(span1)
        
        # Bad span
        span2 = Span(span_id="s2", trace_id="t1", step_name="step2", step_index=1)
        span2.judge_score = 0.5
        trace.add_span(span2)
        
        failures = detector.detect(trace)
        
        assert len(failures) == 1
        assert failures[0].span_id == "s2"
    
    def test_detector_severity_calculation(self):
        """Test severity calculation from judge score."""
        detector = FailureDetector(threshold=0.7)
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        span = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
        span.judge_score = 0.3
        trace.add_span(span)
        
        failures = detector.detect(trace)
        
        assert len(failures) == 1
        # Severity = 1.0 - 0.3 = 0.7
        assert abs(failures[0].severity - 0.7) < 0.01


class TestFailureClassifier:
    """Test failure classification engine."""
    
    def test_classifier_initialization(self):
        """Test classifier initialization."""
        classifier = FailureClassifier()
        assert classifier is not None
    
    def test_classifier_extraction_failure(self):
        """Test classification of extraction failures."""
        classifier = FailureClassifier()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        span = Span(span_id="s1", trace_id="t1", step_name="extraction", step_index=0)
        trace.add_span(span)
        
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s1",
            step_name="extraction",
            failure_type=FailureType.UNKNOWN,
        )
        
        classified = classifier.classify(failure, trace)
        
        assert classified == FailureType.EXTRACTION_HALLUCINATION
    
    def test_classifier_classification_failure(self):
        """Test classification of classification failures."""
        classifier = FailureClassifier()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        span = Span(span_id="s1", trace_id="t1", step_name="classification", step_index=0)
        trace.add_span(span)
        
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s1",
            step_name="classification",
            failure_type=FailureType.UNKNOWN,
        )
        
        classified = classifier.classify(failure, trace)
        
        assert classified == FailureType.MISCLASSIFICATION
    
    def test_classifier_summarization_failure(self):
        """Test classification of summarization failures."""
        classifier = FailureClassifier()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        span = Span(span_id="s1", trace_id="t1", step_name="summarization", step_index=0)
        trace.add_span(span)
        
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s1",
            step_name="summarization",
            failure_type=FailureType.UNKNOWN,
        )
        
        classified = classifier.classify(failure, trace)
        
        assert classified == FailureType.INCOMPLETE_OUTPUT
    
    def test_classifier_unknown_failure(self):
        """Test classification of unknown failures."""
        classifier = FailureClassifier()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        span = Span(span_id="s1", trace_id="t1", step_name="unknown_step", step_index=0)
        trace.add_span(span)
        
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s1",
            step_name="unknown_step",
            failure_type=FailureType.UNKNOWN,
        )
        
        classified = classifier.classify(failure, trace)
        
        assert classified == FailureType.UNKNOWN
    
    def test_classifier_batch_classify(self):
        """Test batch classification."""
        classifier = FailureClassifier()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        trace.add_span(Span(span_id="s1", trace_id="t1", step_name="extraction", step_index=0))
        trace.add_span(Span(span_id="s2", trace_id="t1", step_name="classification", step_index=1))
        
        failures = [
            Failure(
                failure_id="f1",
                trace_id="t1",
                span_id="s1",
                step_name="extraction",
                failure_type=FailureType.UNKNOWN,
            ),
            Failure(
                failure_id="f2",
                trace_id="t1",
                span_id="s2",
                step_name="classification",
                failure_type=FailureType.UNKNOWN,
            ),
        ]
        
        classified = classifier.classify_batch(failures, trace)
        
        assert classified[0].failure_type == FailureType.EXTRACTION_HALLUCINATION
        assert classified[1].failure_type == FailureType.MISCLASSIFICATION


class TestIntegration:
    """Integration tests for failure detection and classification."""
    
    def test_detect_and_classify_workflow(self):
        """Test complete detect and classify workflow."""
        # Create trace with mixed quality spans
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        span1 = Span(span_id="s1", trace_id="t1", step_name="extraction", step_index=0)
        span1.judge_score = 0.5
        trace.add_span(span1)
        
        span2 = Span(span_id="s2", trace_id="t1", step_name="classification", step_index=1)
        span2.judge_score = 0.9
        trace.add_span(span2)
        
        # Detect failures
        detector = FailureDetector(threshold=0.7)
        failures = detector.detect(trace)
        
        assert len(failures) == 1
        
        # Classify failures
        classifier = FailureClassifier()
        classified = classifier.classify_batch(failures, trace)
        
        assert classified[0].failure_type == FailureType.EXTRACTION_HALLUCINATION
