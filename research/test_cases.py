"""Research test cases for FailureForensicsTool evaluation."""

from src.models.trace_models import Trace, Span, SpanStatus


def create_test_case_good_execution() -> Trace:
    """Create test case: good execution with high quality outputs."""
    trace = Trace(trace_id="tc_good", pipeline_name="demo_pipeline")
    
    # All steps execute successfully with high scores
    for i in range(4):
        span = Span(
            span_id=f"good_{i}",
            trace_id="tc_good",
            step_name=f"step{i}",
            step_index=i
        )
        span.judge_score = 0.95
        span.status = SpanStatus.SUCCESS
        span.latency_ms = 100.0
        span.input_data = {"input": f"data_{i}"}
        span.output_data = {"output": f"result_{i}"}
        trace.add_span(span)
    
    trace.final_score = 0.95
    trace.total_latency_ms = 400.0
    return trace


def create_test_case_early_failure() -> Trace:
    """Create test case: early failure that propagates."""
    trace = Trace(trace_id="tc_early_fail", pipeline_name="demo_pipeline")
    
    # First step has low quality
    span0 = Span(
        span_id="early_0",
        trace_id="tc_early_fail",
        step_name="step0",
        step_index=0
    )
    span0.judge_score = 0.3  # Failure in first step
    span0.status = SpanStatus.SUCCESS
    span0.latency_ms = 100.0
    trace.add_span(span0)
    
    # Subsequent steps show degradation
    for i in range(1, 4):
        span = Span(
            span_id=f"early_{i}",
            trace_id="tc_early_fail",
            step_name=f"step{i}",
            step_index=i
        )
        span.judge_score = 0.3 - (i * 0.05)  # Degrading
        span.status = SpanStatus.SUCCESS
        span.latency_ms = 100.0
        trace.add_span(span)
    
    trace.final_score = 0.25
    trace.total_latency_ms = 400.0
    return trace


def create_test_case_intermediate_failure() -> Trace:
    """Create test case: failure in middle step."""
    trace = Trace(trace_id="tc_mid_fail", pipeline_name="demo_pipeline")
    
    # First steps are good
    for i in range(2):
        span = Span(
            span_id=f"mid_{i}",
            trace_id="tc_mid_fail",
            step_name=f"step{i}",
            step_index=i
        )
        span.judge_score = 0.9
        span.status = SpanStatus.SUCCESS
        span.latency_ms = 100.0
        trace.add_span(span)
    
    # Middle step fails
    span2 = Span(
        span_id="mid_2",
        trace_id="tc_mid_fail",
        step_name="step2",
        step_index=2
    )
    span2.judge_score = 0.4
    span2.status = SpanStatus.SUCCESS
    span2.latency_ms = 150.0
    trace.add_span(span2)
    
    # Last step affected
    span3 = Span(
        span_id="mid_3",
        trace_id="tc_mid_fail",
        step_name="step3",
        step_index=3
    )
    span3.judge_score = 0.5
    span3.status = SpanStatus.SUCCESS
    span3.latency_ms = 100.0
    trace.add_span(span3)
    
    trace.final_score = 0.68
    trace.total_latency_ms = 450.0
    return trace


def create_test_case_late_failure() -> Trace:
    """Create test case: failure in final step."""
    trace = Trace(trace_id="tc_late_fail", pipeline_name="demo_pipeline")
    
    # Most steps are good
    for i in range(3):
        span = Span(
            span_id=f"late_{i}",
            trace_id="tc_late_fail",
            step_name=f"step{i}",
            step_index=i
        )
        span.judge_score = 0.92
        span.status = SpanStatus.SUCCESS
        span.latency_ms = 100.0
        trace.add_span(span)
    
    # Last step fails
    span3 = Span(
        span_id="late_3",
        trace_id="tc_late_fail",
        step_name="step3",
        step_index=3
    )
    span3.judge_score = 0.2
    span3.status = SpanStatus.SUCCESS
    span3.latency_ms = 100.0
    trace.add_span(span3)
    
    trace.final_score = 0.64
    trace.total_latency_ms = 400.0
    return trace


def create_test_case_partial_failure() -> Trace:
    """Create test case: multiple independent failures."""
    trace = Trace(trace_id="tc_partial", pipeline_name="demo_pipeline")
    
    # Mix of good and bad spans
    scores = [0.9, 0.4, 0.85, 0.3]
    for i in range(4):
        span = Span(
            span_id=f"partial_{i}",
            trace_id="tc_partial",
            step_name=f"step{i}",
            step_index=i
        )
        span.judge_score = scores[i]
        span.status = SpanStatus.SUCCESS
        span.latency_ms = 100.0
        trace.add_span(span)
    
    trace.final_score = sum(scores) / len(scores)
    trace.total_latency_ms = 400.0
    return trace


def get_test_cases() -> list:
    """Get all test cases for research evaluation."""
    return [
        create_test_case_good_execution(),
        create_test_case_early_failure(),
        create_test_case_intermediate_failure(),
        create_test_case_late_failure(),
        create_test_case_partial_failure(),
    ]


def get_test_case_descriptions() -> dict:
    """Get descriptions for test cases."""
    return {
        "tc_good": "Good execution - all steps high quality (0.95+)",
        "tc_early_fail": "Early failure - first step low (0.3), propagates downward",
        "tc_mid_fail": "Intermediate failure - middle step fails (0.4), partial propagation",
        "tc_late_fail": "Late failure - final step fails (0.2), limited propagation",
        "tc_partial": "Partial failure - mix of good (0.9) and bad (0.3-0.4) spans",
    }
