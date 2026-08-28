"""
Automatic instrumentation for tracing.

Provides:
- Decorators for automatic span generation
- Context managers for manual instrumentation
"""

import logging
from contextlib import contextmanager
from typing import Optional, Any, Generator
import uuid
from datetime import datetime

from src.tracing.trace import Trace, Span, TraceStatus, SpanStatus


logger = logging.getLogger(__name__)

# Thread-local storage for current trace
_current_trace: Optional[Trace] = None


def set_current_trace(trace: Optional[Trace]) -> None:
    """Set current trace context."""
    global _current_trace
    _current_trace = trace


def get_current_trace() -> Optional[Trace]:
    """Get current trace context."""
    return _current_trace


class TraceContext:
    """Context manager for trace execution."""
    
    def __init__(self, trace_id: str = "", pipeline_name: str = ""):
        """
        Initialize trace context.
        
        Args:
            trace_id: Trace ID (generated if empty)
            pipeline_name: Pipeline name
        """
        self.trace = Trace(
            trace_id=trace_id or str(uuid.uuid4()),
            pipeline_name=pipeline_name,
            status=TraceStatus.RUNNING,
            started_at=datetime.now(),
        )
    
    def __enter__(self) -> Trace:
        """Enter context."""
        set_current_trace(self.trace)
        return self.trace
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        if exc_type:
            self.trace.status = TraceStatus.FAILED
            self.trace.error = str(exc_val)
        else:
            self.trace.status = TraceStatus.SUCCESS
        
        self.trace.completed_at = datetime.now()
        set_current_trace(None)


@contextmanager
def trace_step(
    step_name: str,
    step_index: int = 0,
    input_data: Any = None,
) -> Generator[Span, None, None]:
    """
    Context manager for tracing a single step.
    
    Args:
        step_name: Name of step
        step_index: Index in pipeline
        input_data: Step input
        
    Yields:
        Span for this step
    """
    current_trace = get_current_trace()
    if current_trace is None:
        logger.warning("No active trace context")
        yield Span(
            span_id=str(uuid.uuid4()),
            trace_id="",
            step_name=step_name,
            step_index=step_index,
            input_data=input_data,
        )
        return
    
    span = Span(
        span_id=str(uuid.uuid4()),
        trace_id=current_trace.trace_id,
        step_name=step_name,
        step_index=step_index,
        input_data=input_data,
        status=SpanStatus.RUNNING,
        started_at=datetime.now(),
    )
    
    try:
        yield span
        span.status = SpanStatus.SUCCESS
    except Exception as e:
        span.status = SpanStatus.FAILED
        span.error = str(e)
        raise
    finally:
        span.completed_at = datetime.now()
        current_trace.add_span(span)
