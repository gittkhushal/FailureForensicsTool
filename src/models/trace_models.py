"""
Trace and Span data models for observability.

Defines:
- Span: Individual step execution record
- Trace: Complete pipeline execution history
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, Optional, List
from datetime import datetime
from enum import Enum


class SpanStatus(str, Enum):
    """Status of span execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Span(BaseModel):
    """Record of a single pipeline step execution."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    span_id: str = Field(..., description="Unique span identifier")
    trace_id: str = Field(..., description="Parent trace identifier")
    step_name: str = Field(..., description="Name of the step")
    step_index: int = Field(..., ge=0, description="Position in pipeline")
    
    # Execution data
    input_data: Any = Field(default=None, description="Step input")
    output_data: Any = Field(default=None, description="Step output")
    prompt: Optional[str] = Field(default=None, description="LLM prompt if applicable")
    raw_response: Optional[str] = Field(default=None, description="Raw LLM response if applicable")
    
    # Metrics
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Output confidence")
    judge_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Evaluation score")
    latency_ms: float = Field(default=0.0, ge=0.0, description="Execution time in ms")
    
    # Status
    status: SpanStatus = Field(default=SpanStatus.PENDING, description="Execution status")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")


class TraceStatus(str, Enum):
    """Status of trace execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Trace(BaseModel):
    """Complete record of a pipeline execution."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    trace_id: str = Field(..., description="Unique trace identifier")
    pipeline_name: str = Field(default="default", description="Pipeline name")
    
    # Input/Output
    input_data: Any = Field(default=None, description="Pipeline input")
    output_data: Any = Field(default=None, description="Pipeline output")
    
    # Spans
    spans: List[Span] = Field(default_factory=list, description="Execution spans")
    
    # Metrics
    final_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Final quality score")
    total_latency_ms: float = Field(default=0.0, ge=0.0, description="Total execution time")
    
    # Status
    status: TraceStatus = Field(default=TraceStatus.PENDING, description="Execution status")
    error: Optional[str] = Field(default=None, description="Final error if failed")
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def add_span(self, span: Span) -> None:
        """Add a span to the trace."""
        self.spans.append(span)
    
    def get_span_by_index(self, index: int) -> Optional[Span]:
        """Get span by step index."""
        for span in self.spans:
            if span.step_index == index:
                return span
        return None
    
    def get_span_by_name(self, name: str) -> Optional[Span]:
        """Get span by step name."""
        for span in self.spans:
            if span.step_name == name:
                return span
        return None
    
    def get_span_by_id(self, span_id: str) -> Optional[Span]:
        """Get span by ID."""
        for span in self.spans:
            if span.span_id == span_id:
                return span
        return None
    
    def get_failed_spans(self, threshold: float = 0.7) -> list['Span']:
        """Get spans with score below threshold."""
        return [
            span for span in self.spans
            if span.judge_score is not None and span.judge_score < threshold
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get trace execution statistics."""
        return {
            "trace_id": self.trace_id,
            "pipeline_name": self.pipeline_name,
            "status": self.status.value,
            "total_spans": len(self.spans),
            "total_latency_ms": self.total_latency_ms,
            "final_score": self.final_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
