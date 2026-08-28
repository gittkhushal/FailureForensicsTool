"""
Base classes for pipeline steps and pipelines.

Defines:
- PipelineStep: Abstract base class for steps
- Pipeline: Pipeline orchestrator with automatic tracing
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
from datetime import datetime
import uuid

from src.models import StepInput, StepOutput, TraceStatus
from src.tracing import Span, Trace, SpanStatus, TraceContext, trace_step


logger = logging.getLogger(__name__)


class PipelineStep(ABC):
    """Abstract base class for pipeline steps."""
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize pipeline step.
        
        Args:
            name: Step name (must be unique in pipeline)
            description: Step description
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def execute(self, step_input: StepInput) -> StepOutput:
        """
        Execute the step.
        
        Args:
            step_input: Input to the step
            
        Returns:
            Output from the step
        """
        pass
    
    def validate_input(self, step_input: StepInput) -> bool:
        """
        Validate input before execution.
        
        Args:
            step_input: Input to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If invalid
        """
        if step_input.data is None:
            raise ValueError(f"{self.name}: Input data cannot be None")
        return True
    
    def validate_output(self, step_output: StepOutput) -> bool:
        """
        Validate output after execution.
        
        Args:
            step_output: Output to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If invalid
        """
        if step_output.data is None:
            raise ValueError(f"{self.name}: Output data cannot be None")
        return True


class Pipeline:
    """Orchestrator for multi-step pipeline execution."""
    
    def __init__(self, name: str = "pipeline"):
        """
        Initialize pipeline.
        
        Args:
            name: Pipeline name
        """
        self.name = name
        self.steps: Dict[str, PipelineStep] = {}
        self.step_order: list[str] = []
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    def add_step(self, step: PipelineStep, position: Optional[int] = None) -> None:
        """
        Add step to pipeline.
        
        Args:
            step: Step to add
            position: Position in pipeline (None = end)
        """
        if step.name in self.steps:
            raise ValueError(f"Step {step.name} already exists")
        
        self.steps[step.name] = step
        
        if position is None:
            self.step_order.append(step.name)
        else:
            self.step_order.insert(position, step.name)
        
        self.logger.info(f"Added step: {step.name}")
    
    def execute(self, input_data: Any) -> tuple[Any, Trace]:
        """
        Execute pipeline on input.
        
        Args:
            input_data: Input to pipeline
            
        Returns:
            Tuple of (output_data, trace)
        """
        trace_id = str(uuid.uuid4())
        trace = Trace(
            trace_id=trace_id,
            pipeline_name=self.name,
            input_data=input_data,
            status=TraceStatus.RUNNING,
            started_at=datetime.now(),
        )
        
        current_data = input_data
        start_time = datetime.now()
        
        try:
            for step_index, step_name in enumerate(self.step_order):
                step = self.steps[step_name]
                
                # Create span
                span_id = str(uuid.uuid4())
                span = Span(
                    span_id=span_id,
                    trace_id=trace_id,
                    step_name=step_name,
                    step_index=step_index,
                    input_data=current_data,
                    status=SpanStatus.RUNNING,
                    started_at=datetime.now(),
                )
                
                try:
                    # Validate input
                    step_input = StepInput(data=current_data)
                    step.validate_input(step_input)
                    
                    # Execute step
                    step_start = datetime.now()
                    step_output = step.execute(step_input)
                    step_duration = (datetime.now() - step_start).total_seconds() * 1000
                    
                    # Validate output
                    step.validate_output(step_output)
                    
                    # Update span
                    span.output_data = step_output.data
                    span.confidence = step_output.confidence
                    span.latency_ms = step_duration
                    span.status = SpanStatus.SUCCESS
                    span.completed_at = datetime.now()
                    
                    current_data = step_output.data
                    
                    self.logger.info(
                        f"Step {step_name} completed in {step_duration:.2f}ms "
                        f"(confidence: {step_output.confidence:.2f})"
                    )
                    
                except Exception as e:
                    span.status = SpanStatus.FAILED
                    span.error = str(e)
                    span.completed_at = datetime.now()
                    self.logger.error(f"Step {step_name} failed: {e}")
                    trace.add_span(span)
                    raise
                
                trace.add_span(span)
            
            # Pipeline succeeded
            total_duration = (datetime.now() - start_time).total_seconds() * 1000
            trace.output_data = current_data
            trace.total_latency_ms = total_duration
            trace.status = TraceStatus.SUCCESS
            trace.completed_at = datetime.now()
            
            self.logger.info(f"Pipeline completed successfully in {total_duration:.2f}ms")
            return current_data, trace
            
        except Exception as e:
            total_duration = (datetime.now() - start_time).total_seconds() * 1000
            trace.error = str(e)
            trace.total_latency_ms = total_duration
            trace.status = TraceStatus.FAILED
            trace.completed_at = datetime.now()
            
            self.logger.error(f"Pipeline failed: {e}")
            raise
