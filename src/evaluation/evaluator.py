"""
Evaluation orchestrator for pipeline execution.

Provides:
- Evaluator: Manages evaluation of traces
"""

import logging
from typing import List, Any

from src.models.trace_models import Trace, Span
from src.models.evaluation_models import JudgeResult
from src.evaluation.judge import Judge


logger = logging.getLogger(__name__)


class Evaluator:
    """Orchestrates evaluation of pipeline traces."""
    
    def __init__(self, judge: Judge = None):
        """
        Initialize evaluator.
        
        Args:
            judge: Judge instance (creates new if None)
        """
        self.judge = judge or Judge()
        self.logger = logging.getLogger(f"{__name__}")
    
    def evaluate_trace(self, trace: Trace) -> List[JudgeResult]:
        """
        Evaluate all steps in a trace.
        
        Args:
            trace: Trace to evaluate
            
        Returns:
            List of evaluation results
        """
        results = []
        
        for span in trace.spans:
            try:
                result = self.judge.evaluate(
                    step_name=span.step_name,
                    step_type="unknown",  # Would be derived from step
                    input_data=span.input_data,
                    output_data=span.output_data,
                )
                result.span_id = span.span_id
                results.append(result)
                
                # Update span with judge score
                span.judge_score = result.overall_score
                
            except Exception as e:
                self.logger.error(f"Failed to evaluate span {span.span_id}: {e}")
                continue
        
        self.logger.info(f"Evaluated {len(results)} spans in trace {trace.trace_id}")
        return results
    
    def get_overall_score(self, trace: Trace) -> float:
        """
        Get overall trace quality score.
        
        Args:
            trace: Trace to score
            
        Returns:
            Overall quality score (0-1)
        """
        if not trace.spans:
            return 1.0
        
        scores = [
            span.judge_score for span in trace.spans 
            if span.judge_score is not None
        ]
        
        if not scores:
            return 1.0
        
        return sum(scores) / len(scores)
