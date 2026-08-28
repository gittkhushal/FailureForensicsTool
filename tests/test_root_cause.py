"""Tests for root cause analysis engine."""

import pytest
from src.failure.root_cause import RootCauseEngine
from src.failure.propagation import PropagationAnalyzer
from src.models.trace_models import Trace, Span
from src.models.failure_models import Failure, FailureType, PropagationAnalysis, PropagationPath


class TestRootCauseEngine:
    """Test root cause analysis engine."""
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = RootCauseEngine()
        assert engine is not None
    
    def test_single_failure_root_cause(self):
        """Test identifying single failure as root cause."""
        engine = RootCauseEngine()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        span1 = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
        span1.judge_score = 0.3  # Very low
        trace.add_span(span1)
        
        span2 = Span(span_id="s2", trace_id="t1", step_name="step2", step_index=1)
        span2.judge_score = 0.2  # Also low
        trace.add_span(span2)
        
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s2",
            step_name="step2",
            failure_type=FailureType.UNKNOWN,
        )
        
        # Create empty propagation for now
        propagation_analysis = PropagationAnalysis(
            analysis_id="p1",
            failure_id="f1",
            trace_id="t1",
        )
        
        analysis = engine.analyze(failure, trace, propagation_analysis)
        
        assert analysis.root_cause_confidence > 0.0
        assert len(analysis.candidate_root_causes) > 0
    
    def test_multiple_candidates(self):
        """Test with multiple candidate root causes."""
        engine = RootCauseEngine()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        # Multiple failed spans
        span1 = Span(span_id="s1", trace_id="t1", step_name="extraction", step_index=0)
        span1.judge_score = 0.4
        trace.add_span(span1)
        
        span2 = Span(span_id="s2", trace_id="t1", step_name="classification", step_index=1)
        span2.judge_score = 0.5
        trace.add_span(span2)
        
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s2",
            step_name="classification",
            failure_type=FailureType.UNKNOWN,
        )
        
        propagation_analysis = PropagationAnalysis(
            analysis_id="p1",
            failure_id="f1",
            trace_id="t1",
        )
        
        analysis = engine.analyze(failure, trace, propagation_analysis)
        
        # Should have multiple candidates
        assert len(analysis.candidate_root_causes) >= 2
    
    def test_rcc_calculation(self):
        """Test RCC (Root Cause Confidence) calculation."""
        engine = RootCauseEngine()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        span = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
        span.judge_score = 0.2  # Very low
        trace.add_span(span)
        
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s1",
            step_name="step1",
            failure_type=FailureType.UNKNOWN,
        )
        
        propagation_analysis = PropagationAnalysis(
            analysis_id="p1",
            failure_id="f1",
            trace_id="t1",
        )
        
        rcc = engine._calculate_rcc(span, failure, trace, propagation_analysis)
        
        # Very low score = high RCC (0.6 * 0.8 = 0.48)
        assert rcc > 0.4
    
    def test_rcc_with_propagation(self):
        """Test RCC considers propagation impact."""
        engine = RootCauseEngine()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        span1 = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
        span1.judge_score = 0.3
        trace.add_span(span1)
        
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s1",
            step_name="step1",
            failure_type=FailureType.UNKNOWN,
        )
        
        # Propagation with impact from s1
        propagation_analysis = PropagationAnalysis(
            analysis_id="p1",
            failure_id="f1",
            trace_id="t1",
        )
        propagation_analysis.paths.append(
            PropagationPath(
                source_span_id="s1",
                target_span_id="s2",
                propagation_score=0.8,
            )
        )
        
        rcc = engine._calculate_rcc(span1, failure, trace, propagation_analysis)
        
        # With propagation impact, RCC should be higher
        assert rcc > 0.0
    
    def test_candidates_sorted_by_confidence(self):
        """Test candidates are ranked by confidence."""
        engine = RootCauseEngine()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        span1 = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
        span1.judge_score = 0.2  # Very bad
        trace.add_span(span1)
        
        span2 = Span(span_id="s2", trace_id="t1", step_name="step2", step_index=1)
        span2.judge_score = 0.6  # Less bad
        trace.add_span(span2)
        
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s2",
            step_name="step2",
            failure_type=FailureType.UNKNOWN,
        )
        
        propagation_analysis = PropagationAnalysis(
            analysis_id="p1",
            failure_id="f1",
            trace_id="t1",
        )
        
        analysis = engine.analyze(failure, trace, propagation_analysis)
        
        # Candidates should be sorted by confidence
        candidates = analysis.candidate_root_causes
        if len(candidates) > 1:
            assert candidates[0]["confidence"] >= candidates[1]["confidence"]
    
    def test_empty_trace(self):
        """Test with empty trace."""
        engine = RootCauseEngine()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s1",
            step_name="step1",
            failure_type=FailureType.UNKNOWN,
        )
        
        propagation_analysis = PropagationAnalysis(
            analysis_id="p1",
            failure_id="f1",
            trace_id="t1",
        )
        
        analysis = engine.analyze(failure, trace, propagation_analysis)
        
        # Should handle gracefully
        assert analysis.root_cause_confidence == 0.0
        assert len(analysis.candidate_root_causes) == 0
    
    def test_high_quality_trace(self):
        """Test trace with no failures."""
        engine = RootCauseEngine()
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        span1 = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
        span1.judge_score = 0.95  # Very good
        trace.add_span(span1)
        
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s1",
            step_name="step1",
            failure_type=FailureType.UNKNOWN,
        )
        
        propagation_analysis = PropagationAnalysis(
            analysis_id="p1",
            failure_id="f1",
            trace_id="t1",
        )
        
        analysis = engine.analyze(failure, trace, propagation_analysis)
        
        # No failed candidates, so RCC should be low
        assert analysis.root_cause_confidence < 0.7


class TestDownstreamImpact:
    """Test downstream impact calculation."""
    
    def test_downstream_impact_calculation(self):
        """Test calculating downstream impact."""
        engine = RootCauseEngine()
        
        span = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
        
        propagation_analysis = PropagationAnalysis(
            analysis_id="p1",
            failure_id="f1",
            trace_id="t1",
        )
        propagation_analysis.paths.append(
            PropagationPath(
                source_span_id="s1",
                target_span_id="s2",
                propagation_score=0.7,
            )
        )
        
        impact = engine._get_downstream_impact(span, propagation_analysis)
        
        # Should reflect the propagation score
        assert impact == 0.7
    
    def test_max_impact_multiple_paths(self):
        """Test max impact with multiple propagation paths."""
        engine = RootCauseEngine()
        
        span = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
        
        propagation_analysis = PropagationAnalysis(
            analysis_id="p1",
            failure_id="f1",
            trace_id="t1",
        )
        propagation_analysis.paths.append(
            PropagationPath(
                source_span_id="s1",
                target_span_id="s2",
                propagation_score=0.5,
            )
        )
        propagation_analysis.paths.append(
            PropagationPath(
                source_span_id="s1",
                target_span_id="s3",
                propagation_score=0.8,
            )
        )
        
        impact = engine._get_downstream_impact(span, propagation_analysis)
        
        # Should be max of all impacts
        assert impact == 0.8
    
    def test_no_propagation_impact(self):
        """Test when span has no propagation paths."""
        engine = RootCauseEngine()
        
        span = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
        
        propagation_analysis = PropagationAnalysis(
            analysis_id="p1",
            failure_id="f1",
            trace_id="t1",
        )
        propagation_analysis.paths.append(
            PropagationPath(
                source_span_id="s2",  # Different source
                target_span_id="s3",
                propagation_score=0.5,
            )
        )
        
        impact = engine._get_downstream_impact(span, propagation_analysis)
        
        # No paths from s1, so impact is 0
        assert impact == 0.0


class TestIntegration:
    """Integration tests for root cause analysis."""
    
    def test_full_root_cause_workflow(self):
        """Test complete root cause analysis workflow."""
        analyzer = PropagationAnalyzer()
        engine = RootCauseEngine()
        
        # Create trace
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        span1 = Span(span_id="s1", trace_id="t1", step_name="extraction", step_index=0)
        span1.judge_score = 0.3  # Failure here
        trace.add_span(span1)
        
        span2 = Span(span_id="s2", trace_id="t1", step_name="classification", step_index=1)
        span2.judge_score = 0.4  # Propagated failure
        trace.add_span(span2)
        
        # Create failure
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s2",
            step_name="classification",
            failure_type=FailureType.MISCLASSIFICATION,
        )
        
        # Analyze propagation
        propagation_analysis = analyzer.analyze(failure, trace)
        
        # Analyze root cause
        root_analysis = engine.analyze(failure, trace, propagation_analysis)
        
        # Should identify extraction as root cause
        assert root_analysis.root_cause_confidence > 0.0
        assert len(root_analysis.candidate_root_causes) > 0
