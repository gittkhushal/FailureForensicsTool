"""
Failure classification.

Provides:
- FailureClassifier: Categorizes failure types
"""

import logging
from typing import List, Tuple

from src.models.failure_models import Failure, FailureType
from src.models.trace_models import Trace, Span


logger = logging.getLogger(__name__)


class FailureClassifier:
    """Classifies failure types."""
    
    def __init__(self):
        """Initialize classifier."""
        self.logger = logging.getLogger(f"{__name__}")
    
    def classify(self, failure: Failure, trace: Trace) -> FailureType:
        """
        Classify failure type.
        
        Args:
            failure: Failure to classify
            trace: Associated trace for context
            
        Returns:
            Classified failure type
        """
        # Find the failed span
        span = next((s for s in trace.spans if s.span_id == failure.span_id), None)
        if not span:
            return FailureType.UNKNOWN
        
        # Simple heuristic classification based on step name and evidence
        step_name = span.step_name.lower()
        
        if "extract" in step_name:
            return FailureType.EXTRACTION_HALLUCINATION
        elif "classif" in step_name:
            return FailureType.MISCLASSIFICATION
        elif "summar" in step_name:
            return FailureType.INCOMPLETE_OUTPUT
        
        return FailureType.UNKNOWN
    
    def classify_batch(self, failures: List[Failure], trace: Trace) -> List[Failure]:
        """
        Classify multiple failures.
        
        Args:
            failures: Failures to classify
            trace: Associated trace
            
        Returns:
            Classified failures
        """
        for failure in failures:
            failure.failure_type = self.classify(failure, trace)
        
        return failures
