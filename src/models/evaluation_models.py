"""
Evaluation and feedback data models.

Defines:
- JudgeResult: LLM evaluation output
- EvaluationCase: Failure case for regression testing
- FeedbackRecord: Human feedback on diagnosis
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, Optional, List
from datetime import datetime
from enum import Enum


class EvaluationCriteria(str, Enum):
    """Dimensions of evaluation."""
    CORRECTNESS = "correctness"
    HALLUCINATION = "hallucination"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    RELEVANCE = "relevance"


class JudgeResult(BaseModel):
    """Result of LLM-as-Judge evaluation."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    span_id: str = Field(..., description="Evaluated span")
    step_name: str = Field(..., description="Evaluated step")
    
    # Scores
    overall_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Overall quality score")
    criteria_scores: Dict[str, float] = Field(
        default_factory=dict, 
        description="Scores by evaluation criteria"
    )
    
    # Analysis
    passed: bool = Field(default=True, description="Meets quality threshold")
    issues: List[str] = Field(default_factory=list, description="Identified issues")
    reasoning: str = Field(default="", description="Judge reasoning")
    
    # Metadata
    model_used: str = Field(default="qwen2.5:7b-instruct", description="LLM model name")
    created_at: datetime = Field(default_factory=datetime.now, description="Evaluation timestamp")


class EvaluationCase(BaseModel):
    """Failure case for regression testing and evaluation."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    case_id: str = Field(..., description="Unique case identifier")
    trace_id: str = Field(..., description="Original trace ID")
    failure_id: Optional[str] = Field(default=None, description="Associated failure ID")
    
    # Input/Output
    original_input: Any = Field(..., description="Pipeline input that caused failure")
    failing_step: str = Field(..., description="Step where failure originated")
    incorrect_output: Any = Field(..., description="Incorrect output produced")
    corrected_output: Any = Field(..., description="Correct/expected output")
    
    # Classification
    failure_type: str = Field(..., description="Type of failure")
    root_cause_step: str = Field(..., description="Identified root cause step")
    severity: float = Field(default=0.5, ge=0.0, le=1.0, description="Failure severity")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Case creation timestamp")
    confirmed: bool = Field(default=False, description="Confirmed by human")


class FeedbackRecord(BaseModel):
    """Human feedback on diagnosis."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    feedback_id: str = Field(..., description="Unique feedback identifier")
    trace_id: str = Field(..., description="Associated trace ID")
    failure_id: Optional[str] = Field(default=None, description="Associated failure ID")
    
    # Feedback
    diagnosis_confirmed: bool = Field(..., description="Is diagnosis correct?")
    root_cause_confirmed: bool = Field(default=False, description="Is root cause correct?")
    corrected_output: Optional[Any] = Field(default=None, description="Corrected output if applicable")
    
    # Comments
    comments: str = Field(default="", description="User comments")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Feedback timestamp")


class RegressionResult(BaseModel):
    """Result of re-running evaluation case."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    run_id: str = Field(..., description="Unique run identifier")
    case_id: str = Field(..., description="Associated evaluation case")
    
    # Execution
    passed: bool = Field(..., description="Case still fails?")
    output: Any = Field(default=None, description="Current output")
    score: float = Field(default=0.5, ge=0.0, le=1.0, description="Current quality score")
    
    # Comparison
    improved: Optional[bool] = Field(default=None, description="Improved vs. original?")
    score_delta: float = Field(default=0.0, description="Score change from original")
    
    # Metadata
    executed_at: datetime = Field(default_factory=datetime.now, description="Execution timestamp")


class DatasetStatistics(BaseModel):
    """Statistics for evaluation dataset."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    total_cases: int = Field(default=0, description="Total number of cases")
    failure_types: Dict[str, int] = Field(default_factory=dict, description="Cases by failure type")
    root_causes: Dict[str, int] = Field(default_factory=dict, description="Cases by root cause")
    severity_distribution: Dict[str, int] = Field(default_factory=dict, description="Cases by severity level")
