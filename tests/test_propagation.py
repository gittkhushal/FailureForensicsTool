"""Tests for failure propagation analysis."""

import pytest
from src.failure.propagation import PropagationAnalyzer
from src.models.trace_models import Trace, Span
from src.models.failure_models import Failure, FailureType


class TestPropagationAnalyzer:
    """Test propagation analysis engine."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = PropagationAnalyzer()
        assert analyzer is not None
    
    def test_simple_propagation(self):
        """Test propagation from one span to next."""
        analyzer = PropagationAnalyzer()
        
        # Create trace
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        span1 = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
        span1.judge_score = 0.5  # Low score - failure
        trace.add_span(span1)
        
        span2 = Span(span_id="s2", trace_id="t1", step_name="step2", step_index=1)
        span2.judge_score = 0.3  # Even lower - propagated failure
        trace.add_span(span2)
        
        # Create failure
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s1",
            step_name="step1",
            failure_type=FailureType.EXTRACTION_HALLUCINATION,
        )
        
        # Analyze
        analysis = analyzer.analyze(failure, trace)
        
        assert len(analysis.paths) > 0
        assert analysis.overall_propagation_score > 0.0
    
    def test_no_downstream_propagation(self):
        """Test failure at end has no propagation."""
        analyzer = PropagationAnalyzer()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        span1 = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
        span1.judge_score = 0.9
        trace.add_span(span1)
        
        span2 = Span(span_id="s2", trace_id="t1", step_name="step2", step_index=1)
        span2.judge_score = 0.5  # Failure at end
        trace.add_span(span2)
        
        # Failure in last span
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s2",
            step_name="step2",
            failure_type=FailureType.UNKNOWN,
        )
        
        analysis = analyzer.analyze(failure, trace)
        
        # No downstream spans, so no propagation
        assert len(analysis.paths) == 0
    
    def test_propagation_score_calculation(self):
        """Test propagation score calculation."""
        analyzer = PropagationAnalyzer()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        span1 = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
        span1.judge_score = 1.0  # Perfect
        trace.add_span(span1)
        
        span2 = Span(span_id="s2", trace_id="t1", step_name="step2", step_index=1)
        span2.judge_score = 1.0  # Still perfect
        trace.add_span(span2)
        
        ps = analyzer._calculate_propagation_score(span1, span2, trace)
        
        # No score drop, so PS should be 0
        assert ps == 0.0
    
    def test_propagation_score_with_drop(self):
        """Test propagation score with score degradation."""
        analyzer = PropagationAnalyzer()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        span1 = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
        span1.judge_score = 1.0
        trace.add_span(span1)
        
        span2 = Span(span_id="s2", trace_id="t1", step_name="step2", step_index=1)
        span2.judge_score = 0.5  # Large drop
        trace.add_span(span2)
        
        ps = analyzer._calculate_propagation_score(span1, span2, trace)
        
        # Should have positive PS due to score drop
        assert ps > 0.0
        # Score drop of 0.5
        assert ps >= 0.45  # With distance factor applied
    
    def test_distance_decay(self):
        """Test that distance reduces propagation influence."""
        analyzer = PropagationAnalyzer()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        span1 = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
        span1.judge_score = 1.0
        trace.add_span(span1)
        
        span_adjacent = Span(span_id="s2", trace_id="t1", step_name="step2", step_index=1)
        span_adjacent.judge_score = 0.5
        trace.add_span(span_adjacent)
        
        span_distant = Span(span_id="s3", trace_id="t1", step_name="step3", step_index=10)
        span_distant.judge_score = 0.5
        trace.add_span(span_distant)
        
        ps_adjacent = analyzer._calculate_propagation_score(span1, span_adjacent, trace)
        ps_distant = analyzer._calculate_propagation_score(span1, span_distant, trace)
        
        # Adjacent should have higher propagation than distant
        assert ps_adjacent > ps_distant
    
    def test_aggregation(self):
        """Test propagation score aggregation."""
        from src.models.failure_models import PropagationPath
        
        analyzer = PropagationAnalyzer()
        
        paths = [
            PropagationPath(
                source_span_id="s1",
                target_span_id="s2",
                propagation_score=0.8,
            ),
            PropagationPath(
                source_span_id="s1",
                target_span_id="s3",
                propagation_score=0.6,
            ),
        ]
        
        agg = analyzer._aggregate_propagation(paths)
        
        # Should be mean of scores
        assert abs(agg - 0.7) < 0.01
    
    def test_aggregation_empty(self):
        """Test aggregation with no paths."""
        analyzer = PropagationAnalyzer()
        agg = analyzer._aggregate_propagation([])
        assert agg == 0.0
    
    def test_multiple_span_pipeline(self):
        """Test propagation in multi-span pipeline."""
        analyzer = PropagationAnalyzer()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        # Create 5-step pipeline
        for i in range(5):
            span = Span(span_id=f"s{i}", trace_id="t1", step_name=f"step{i}", step_index=i)
            # Degrading scores
            span.judge_score = 1.0 - (i * 0.15)
            trace.add_span(span)
        
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s0",
            step_name="step0",
            failure_type=FailureType.EXTRACTION_HALLUCINATION,
        )
        
        analysis = analyzer.analyze(failure, trace)
        
        # Should have propagation to downstream spans
        assert len(analysis.paths) > 0
        assert analysis.overall_propagation_score > 0.0
        # All downstream spans should be marked as affected
        assert len(analysis.affected_spans) == 4


class TestPropagationEdgeCases:
    """Test edge cases in propagation analysis."""
    
    def test_missing_source_span(self):
        """Test when source span doesn't exist."""
        analyzer = PropagationAnalyzer()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        trace.add_span(Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0))
        
        # Failure references non-existent span
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s99",  # Doesn't exist
            step_name="missing",
            failure_type=FailureType.UNKNOWN,
        )
        
        analysis = analyzer.analyze(failure, trace)
        
        # Should handle gracefully
        assert len(analysis.paths) == 0
    
    def test_spans_without_judge_scores(self):
        """Test propagation with spans missing judge scores."""
        analyzer = PropagationAnalyzer()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        span1 = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
        span1.judge_score = None  # No score
        trace.add_span(span1)
        
        span2 = Span(span_id="s2", trace_id="t1", step_name="step2", step_index=1)
        span2.judge_score = None  # No score
        trace.add_span(span2)
        
        ps = analyzer._calculate_propagation_score(span1, span2, trace)
        
        # Should use default score of 0.5
        assert 0.0 <= ps <= 1.0
