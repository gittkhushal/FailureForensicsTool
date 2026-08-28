"""
Failure detection from evaluation scores.

Provides:
- FailureDetector: Identifies failed outputs
"""

import logging
from typing import Optional, List

from src.models.trace_models import Trace, Span
from src.models.failure_models import Failure, FailureType
import uuid
from datetime import datetime


logger = logging.getLogger(__name__)


class FailureDetector:
    """Detects failures in pipeline execution."""
    
    def __init__(self, threshold: float = 0.7):
        """
        Initialize detector.
        
        Args:
            threshold: Score threshold below which output is considered failed
        """
        self.threshold = threshold
        self.logger = logging.getLogger(f"{__name__}")
    
    def detect(self, trace: Trace) -> List[Failure]:
        """
        Detect failures in trace.
        
        Args:
            trace: Trace to analyze
            
        Returns:
            List of detected failures
        """
        failures = []
        
        for span in trace.spans:
            if span.judge_score is not None and span.judge_score < self.threshold:
                failure = Failure(
                    failure_id=str(uuid.uuid4()),
                    trace_id=trace.trace_id,
                    span_id=span.span_id,
                    step_name=span.step_name,
                    failure_type=FailureType.UNKNOWN,
                    severity=1.0 - span.judge_score,
                    judge_score=span.judge_score,
                    description=f"Low quality output: {span.judge_score:.2f} < {self.threshold}",
                    evidence={
                        "judge_score": span.judge_score,
                        "threshold": self.threshold,
                        "step_name": span.step_name,
                    }
                )
                failures.append(failure)
                self.logger.warning(
                    f"Failure detected in {span.step_name}: score={span.judge_score:.2f}"
                )
        
        return failures
