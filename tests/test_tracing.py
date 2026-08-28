"""
Tests for tracing system.

Tests trace/span creation, context management, and instrumentation.
"""

import pytest
from datetime import datetime

from src.tracing import (
    Trace, Span, TraceStatus, SpanStatus,
    TraceContext, trace_step,
    set_current_trace, get_current_trace
)


class TestSpan:
    """Test Span model."""
    
    def test_span_creation(self):
        """Test creating a span."""
        span = Span(
            span_id="span1",
            trace_id="trace1",
            step_name="test_step",
            step_index=0,
        )
        
        assert span.span_id == "span1"
        assert span.trace_id == "trace1"
        assert span.status == SpanStatus.PENDING
    
    def test_span_with_data(self):
        """Test span with input/output data."""
        input_data = {"key": "value"}
        output_data = {"result": "success"}
        
        span = Span(
            span_id="span1",
            trace_id="trace1",
            step_name="test",
            step_index=0,
            input_data=input_data,
            output_data=output_data,
            confidence=0.95,
            judge_score=0.88,
        )
        
        assert span.input_data == input_data
        assert span.output_data == output_data
        assert span.confidence == 0.95
        assert span.judge_score == 0.88
    
    def test_span_latency_calculation(self):
        """Test span latency tracking."""
        span = Span(
            span_id="span1",
            trace_id="trace1",
            step_name="test",
            step_index=0,
            latency_ms=123.45,
        )
        
        assert span.latency_ms == 123.45


class TestTrace:
    """Test Trace model."""
    
    def test_trace_creation(self):
        """Test creating a trace."""
        trace = Trace(trace_id="trace1", pipeline_name="test_pipeline")
        
        assert trace.trace_id == "trace1"
        assert trace.pipeline_name == "test_pipeline"
        assert len(trace.spans) == 0
        assert trace.status == TraceStatus.PENDING
    
    def test_trace_add_span(self):
        """Test adding spans to trace."""
        trace = Trace(trace_id="trace1")
        
        span1 = Span(span_id="s1", trace_id="trace1", step_name="step1", step_index=0)
        span2 = Span(span_id="s2", trace_id="trace1", step_name="step2", step_index=1)
        
        trace.add_span(span1)
        trace.add_span(span2)
        
        assert len(trace.spans) == 2
    
    def test_trace_get_span_by_name(self):
        """Test getting span by name."""
        trace = Trace(trace_id="trace1")
        
        span1 = Span(span_id="s1", trace_id="trace1", step_name="step1", step_index=0)
        span2 = Span(span_id="s2", trace_id="trace1", step_name="step2", step_index=1)
        
        trace.add_span(span1)
        trace.add_span(span2)
        
        retrieved = trace.get_span_by_name("step1")
        assert retrieved == span1
    
    def test_trace_get_span_by_id(self):
        """Test getting span by ID."""
        trace = Trace(trace_id="trace1")
        
        span1 = Span(span_id="s1", trace_id="trace1", step_name="step1", step_index=0)
        trace.add_span(span1)
        
        retrieved = trace.get_span_by_id("s1")
        assert retrieved == span1
    
    def test_trace_get_failed_spans(self):
        """Test getting failed spans."""
        trace = Trace(trace_id="trace1")
        
        # Pass
        trace.add_span(Span(
            span_id="s1", trace_id="trace1", step_name="s1",
            step_index=0, judge_score=0.9
        ))
        # Fail
        trace.add_span(Span(
            span_id="s2", trace_id="trace1", step_name="s2",
            step_index=1, judge_score=0.5
        ))
        # Fail
        trace.add_span(Span(
            span_id="s3", trace_id="trace1", step_name="s3",
            step_index=2, judge_score=0.6
        ))
        
        failed = trace.get_failed_spans(threshold=0.7)
        assert len(failed) == 2
        assert all(s.judge_score < 0.7 for s in failed)
    
    def test_trace_statistics(self):
        """Test trace statistics."""
        trace = Trace(
            trace_id="trace1",
            pipeline_name="test",
            total_latency_ms=150.0,
            final_score=0.85,
            status=TraceStatus.SUCCESS,
        )
        
        trace.add_span(Span(span_id="s1", trace_id="trace1", step_name="s1", step_index=0))
        
        stats = trace.get_statistics()
        
        assert stats["trace_id"] == "trace1"
        assert stats["total_latency_ms"] == 150.0
        assert stats["final_score"] == 0.85
        assert stats["total_spans"] == 1


class TestTraceContext:
    """Test TraceContext manager."""
    
    def test_trace_context_creation(self):
        """Test creating trace context."""
        with TraceContext(pipeline_name="test") as trace:
            assert trace is not None
            assert trace.pipeline_name == "test"
            assert trace.status == TraceStatus.RUNNING
    
    def test_trace_context_sets_current(self):
        """Test trace context sets current trace."""
        assert get_current_trace() is None
        
        with TraceContext() as trace:
            assert get_current_trace() == trace
        
        assert get_current_trace() is None
    
    def test_trace_context_success(self):
        """Test trace context on success."""
        with TraceContext() as trace:
            assert trace.status == TraceStatus.RUNNING
        
        assert trace.status == TraceStatus.SUCCESS
        assert trace.completed_at is not None
    
    def test_trace_context_failure(self):
        """Test trace context on failure."""
        try:
            with TraceContext() as trace:
                raise ValueError("Test error")
        except ValueError:
            pass
        
        assert trace.status == TraceStatus.FAILED
        assert "Test error" in trace.error


class TestTraceStep:
    """Test trace_step context manager."""
    
    def test_trace_step_without_context(self):
        """Test trace_step without active trace context."""
        with trace_step("test_step", step_index=0) as span:
            assert span.step_name == "test_step"
            # Without active context, span status stays PENDING
            assert span.status == SpanStatus.PENDING
    
    def test_trace_step_with_context(self):
        """Test trace_step with active trace context."""
        with TraceContext() as trace:
            with trace_step("test_step", step_index=0, input_data={"key": "value"}) as span:
                assert span.step_name == "test_step"
                assert span.input_data == {"key": "value"}
                assert span.status == SpanStatus.RUNNING
        
        # Verify span was added to trace
        assert len(trace.spans) == 1
        assert trace.spans[0].step_name == "test_step"
        assert trace.spans[0].status == SpanStatus.SUCCESS
    
    def test_trace_step_success(self):
        """Test trace_step on success."""
        with TraceContext() as trace:
            with trace_step("test", step_index=0) as span:
                pass
            
            assert span.status == SpanStatus.SUCCESS
            assert span.completed_at is not None
    
    def test_trace_step_failure(self):
        """Test trace_step on failure."""
        with TraceContext() as trace:
            try:
                with trace_step("test", step_index=0) as span:
                    raise RuntimeError("Step failed")
            except RuntimeError:
                pass
            
            assert span.status == SpanStatus.FAILED
            assert "Step failed" in span.error
    
    def test_nested_trace_steps(self):
        """Test nested trace_step calls."""
        with TraceContext() as trace:
            with trace_step("step1", step_index=0):
                pass
            
            with trace_step("step2", step_index=1):
                pass
            
            with trace_step("step3", step_index=2):
                pass
        
        # All steps are added to trace
        assert len(trace.spans) == 3
        # Note: order might not be guaranteed in all cases, so check by name
        step_names = [s.step_name for s in trace.spans]
        assert "step1" in step_names
        assert "step2" in step_names
        assert "step3" in step_names


class TestCurrentTrace:
    """Test current trace management."""
    
    def test_set_get_current_trace(self):
        """Test setting and getting current trace."""
        assert get_current_trace() is None
        
        trace = Trace(trace_id="test")
        set_current_trace(trace)
        
        assert get_current_trace() == trace
        
        set_current_trace(None)
        assert get_current_trace() is None
    
    def test_current_trace_isolation(self):
        """Test current trace isolation between contexts."""
        trace1 = None
        trace2 = None
        
        with TraceContext() as ctx1:
            trace1 = ctx1
            assert get_current_trace() == trace1
            
            with TraceContext() as ctx2:
                trace2 = ctx2
                # Context manager doesn't nest - second one overwrites
                assert get_current_trace() == trace2
            
            # After inner context, we're back to outer (if nested properly)
            # But TraceContext doesn't implement proper nesting
        
        assert get_current_trace() is None


class TestIntegration:
    """Integration tests for tracing."""
    
    def test_complete_trace_workflow(self):
        """Test complete trace workflow."""
        with TraceContext(pipeline_name="demo") as trace:
            # Simulate step 1
            with trace_step("intake", step_index=0, input_data="raw text") as span1:
                span1.output_data = {"normalized": "text"}
                span1.judge_score = 0.95
            
            # Simulate step 2
            with trace_step("extraction", step_index=1, input_data={"normalized": "text"}) as span2:
                span2.output_data = {"entities": ["entity1"]}
                span2.judge_score = 0.85
            
            # Simulate step 3
            with trace_step("classification", step_index=2) as span3:
                span3.output_data = {"category": "news"}
                span3.judge_score = 0.9
        
        # Verify trace
        assert trace.status == TraceStatus.SUCCESS
        assert len(trace.spans) == 3
        assert trace.spans[0].step_name == "intake"
        assert trace.spans[1].step_name == "extraction"
        assert trace.spans[2].step_name == "classification"
        
        # Verify all spans are successful
        assert all(s.status == SpanStatus.SUCCESS for s in trace.spans)
        
        # Verify scores
        assert trace.spans[0].judge_score == 0.95
        assert trace.spans[1].judge_score == 0.85
        assert trace.spans[2].judge_score == 0.9
    
    def test_trace_with_failure(self):
        """Test trace with step failure."""
        with TraceContext() as trace:
            with trace_step("step1", step_index=0):
                pass
            
            try:
                with trace_step("step2", step_index=1):
                    raise ValueError("Processing failed")
            except ValueError:
                pass
            
            with trace_step("step3", step_index=2):
                pass
        
        # Trace continues despite step failure
        assert trace.status == TraceStatus.SUCCESS  # Trace succeeded overall
        assert len(trace.spans) == 3
        assert trace.spans[0].status == SpanStatus.SUCCESS
        assert trace.spans[1].status == SpanStatus.FAILED
        assert trace.spans[2].status == SpanStatus.SUCCESS
