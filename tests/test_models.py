"""
Tests for data models.
"""

import pytest
from src.models import (
    StepInput, StepOutput,
    Span, Trace,
    Failure, FailureType,
)


def test_step_input_creation():
    """Test StepInput model."""
    input_data = {"text": "sample"}
    step_input = StepInput(data=input_data)
    assert step_input.data == input_data


def test_step_output_creation():
    """Test StepOutput model."""
    output_data = {"extracted": "entities"}
    step_output = StepOutput(data=output_data, confidence=0.9)
    assert step_output.data == output_data
    assert step_output.confidence == 0.9


def test_trace_creation():
    """Test Trace model."""
    trace = Trace(trace_id="test123")
    assert trace.trace_id == "test123"
    assert len(trace.spans) == 0


def test_span_creation():
    """Test Span model."""
    span = Span(
        span_id="span1",
        trace_id="trace1",
        step_name="extraction",
        step_index=0,
    )
    assert span.span_id == "span1"
    assert span.step_name == "extraction"


def test_failure_creation():
    """Test Failure model."""
    failure = Failure(
        failure_id="fail1",
        trace_id="trace1",
        span_id="span1",
        step_name="extraction",
        failure_type=FailureType.EXTRACTION_HALLUCINATION,
    )
    assert failure.failure_id == "fail1"
    assert failure.failure_type == FailureType.EXTRACTION_HALLUCINATION
