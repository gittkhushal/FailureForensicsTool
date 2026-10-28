"""
Intake step: Input normalization and validation.

Normalizes and validates raw input for pipeline processing.
"""

import logging
from typing import Any, Dict

from src.models import StepInput, StepOutput
from src.pipeline.base import PipelineStep


logger = logging.getLogger(__name__)


class IntakeStep(PipelineStep):
    """Intake step for input normalization."""
    
    def __init__(self):
        """Initialize intake step."""
        super().__init__(
            name="intake",
            description="Input normalization and validation"
        )
    
    def execute(self, step_input: StepInput) -> StepOutput:
        """
        Normalize and validate input.
        
        Args:
            step_input: Raw input data
            
        Returns:
            Normalized output
        """
        try:
            # Validate and normalize input
            if not isinstance(step_input.data, str):
                if isinstance(step_input.data, dict):
                    data = (
                        step_input.data.get("document") or
                        step_input.data.get("text") or
                        step_input.data.get("raw_text") or
                        step_input.data.get("input") or
                        step_input.data.get("content") or
                        next((v for v in step_input.data.values() if isinstance(v, str) and v.strip()), "")
                    )
                else:
                    data = str(step_input.data)
            else:
                data = step_input.data
            
            # Strip and clean
            data = data.strip()
            
            if not data:
                raise ValueError("Input document cannot be empty")
            
            if len(data) > 100000:  # 100K char limit
                self.logger.warning(f"Input truncated from {len(data)} to 100000 chars")
                data = data[:100000]
            
            # Create normalized output
            normalized_data = {
                "document": data,
                "length": len(data),
                "word_count": len(data.split()),
            }
            
            output = StepOutput(
                data=normalized_data,
                confidence=0.95,
                metadata={"normalized": True}
            )
            
            self.logger.info(f"Intake: normalized {len(data)} chars")
            return output
            
        except Exception as e:
            self.logger.error(f"Intake failed: {e}")
            raise
