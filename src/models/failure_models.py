"""
Failure analysis data models.

Defines:
- FailureType: Categories of failures
- Failure: Individual failure record
- PropagationPath: How failure propagates
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, Optional, List
from datetime import datetime
from enum import Enum


class FailureType(str, Enum):
    """Categories of detected failures."""
    EXTRACTION_HALLUCINATION = "extraction_hallucination"
    MISCLASSIFICATION = "misclassification"
    PROPAGATION_ERROR = "propagation_error"
    PROMPT_FAILURE = "prompt_failure"
    CONTEXT_LOSS = "context_loss"
    INCOMPLETE_OUTPUT = "incomplete_output"
    INCORRECT_OUTPUT = "incorrect_output"
    INCONSISTENCY = "inconsistency"
    TIMEOUT = "timeout"
    LLM_ERROR = "llm_error"
    UNKNOWN = "unknown"


class Failure(BaseModel):
    """Detected failure in pipeline execution."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    failure_id: str = Field(..., description="Unique failure identifier")
    trace_id: str = Field(..., description="Associated trace ID")
    span_id: str = Field(..., description="Failed span ID")
    step_name: str = Field(..., description="Name of failed step")
    
    # Failure characteristics
    failure_type: FailureType = Field(..., description="Type of failure")
    severity: float = Field(default=0.5, ge=0.0, le=1.0, description="Severity score")
    judge_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Judge evaluation score")
    
    # Details
    description: str = Field(default="", description="Human-readable description")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Supporting evidence")
    
    # Status
    confirmed: bool = Field(default=False, description="Human-confirmed failure")
    created_at: datetime = Field(default_factory=datetime.now, description="Detection timestamp")


class PropagationPath(BaseModel):
    """Path of failure propagation through pipeline."""
    source_span_id: str = Field(..., description="Originating span")
    target_span_id: str = Field(..., description="Affected span")
    propagation_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Propagation strength")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Propagation evidence")


class PropagationAnalysis(BaseModel):
    """Complete failure propagation analysis."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    analysis_id: str = Field(..., description="Unique analysis ID")
    failure_id: str = Field(..., description="Associated failure ID")
    trace_id: str = Field(..., description="Associated trace ID")
    
    # Propagation graph
    paths: List[PropagationPath] = Field(default_factory=list, description="Propagation paths")
    affected_spans: List[str] = Field(default_factory=list, description="IDs of affected spans")
    
    # Metrics
    overall_propagation_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Aggregate PS")
    amplification: float = Field(default=1.0, ge=0.0, description="Error amplification factor")
    
    created_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")


class RootCauseCandidate(BaseModel):
    """Candidate root cause."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    span_id: str = Field(..., description="Span ID")
    step_name: str = Field(..., description="Step name")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    local_severity: float = Field(ge=0.0, le=1.0, description="Local severity")
    downstream_impact: float = Field(ge=0.0, le=1.0, description="Downstream impact")
    reasoning: str = Field(default="", description="Why this is a candidate")


class RootCauseAnalysis(BaseModel):
    """Root cause identification and confidence."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    analysis_id: str = Field(..., description="Unique analysis ID")
    trace_id: str = Field(..., description="Associated trace ID")
    failure_id: str = Field(..., description="Associated failure ID")
    
    # Root cause
    root_span_id: str = Field(..., description="Identified root cause span")
    root_step_name: str = Field(..., description="Identified root cause step name")
    root_cause_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="RCC score")
    
    # Evidence
    reasoning: str = Field(default="", description="Explanation of analysis")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Supporting evidence")
    
    # Candidates
    candidate_root_causes: List[RootCauseCandidate] = Field(
        default_factory=list, 
        description="Alternative root cause candidates with scores"
    )
    
    created_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")


class FailureAnalysisSummary(BaseModel):
    """Complete failure analysis summary."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    trace_id: str = Field(..., description="Associated trace ID")
    failure_detected: bool = Field(..., description="Was failure detected?")
    failure_count: int = Field(default=0, description="Number of failures")
    primary_failure: Optional[Failure] = Field(default=None, description="Most severe failure")
    root_cause: Optional[RootCauseAnalysis] = Field(default=None, description="Root cause analysis")
    propagation_impact: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall propagation impact")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
