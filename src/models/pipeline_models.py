"""
Pipeline data models using Pydantic for type safety and validation.

Defines:
- Input/output schemas for pipeline steps
- Pipeline configuration
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, Optional
from enum import Enum


class StepType(str, Enum):
    """Types of pipeline steps."""
    INTAKE = "intake"
    EXTRACTION = "extraction"
    CLASSIFICATION = "classification"
    SUMMARIZATION = "summarization"
    CUSTOM = "custom"


class StepInput(BaseModel):
    """Input to a pipeline step."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    data: Any = Field(..., description="Step input data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Input metadata")


class StepOutput(BaseModel):
    """Output from a pipeline step."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    data: Any = Field(..., description="Step output data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Output metadata")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Output confidence score")


class PipelineConfig(BaseModel):
    """Configuration for pipeline execution."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str = Field(default="default_pipeline", description="Pipeline name")
    steps: list[str] = Field(default_factory=list, description="Ordered list of step names")
    timeout_per_step: int = Field(default=300, ge=1, description="Timeout per step in seconds")
    max_retries: int = Field(default=2, ge=0, description="Max retries on failure")
    fail_fast: bool = Field(default=False, description="Stop on first failure")
