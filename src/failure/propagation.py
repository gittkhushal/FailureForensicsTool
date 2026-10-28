"""
Failure propagation analysis.

Provides:
- PropagationAnalyzer: Analyzes failure propagation
- Propagation Score calculation
"""

import logging
from typing import List, Dict, Any
import uuid
from datetime import datetime

from src.models.failure_models import Failure, PropagationPath, PropagationAnalysis
from src.models.trace_models import Trace, Span


logger = logging.getLogger(__name__)


class PropagationAnalyzer:
    """Analyzes how failures propagate through pipeline."""
    
    def __init__(self):
        """Initialize analyzer."""
        self.logger = logging.getLogger(f"{__name__}")
    
    def analyze(self, failure: Failure, trace: Trace) -> PropagationAnalysis:
        """
        Analyze failure propagation.
        
        Args:
            failure: Original failure
            trace: Execution trace
            
        Returns:
            Propagation analysis
        """
        analysis = PropagationAnalysis(
            analysis_id=str(uuid.uuid4()),
            failure_id=failure.failure_id,
            trace_id=trace.trace_id,
        )
        
        # Find source span
        source_span = next((s for s in trace.spans if s.span_id == failure.span_id), None)
        if not source_span:
            return analysis
        
        source_index = source_span.step_index
        
        # Analyze downstream spans
        affected_spans = []
        for span in trace.spans:
            if span.step_index > source_index:
                affected_spans.append(span.span_id)
                
                # Calculate propagation score
                ps = self._calculate_propagation_score(
                    source_span=source_span,
                    target_span=span,
                    trace=trace,
                )
                
                if ps > 0.0:
                    path = PropagationPath(
                        source_span_id=source_span.span_id,
                        target_span_id=span.span_id,
                        propagation_score=ps,
                        evidence={
                            "source_score": source_span.judge_score or 0.0,
                            "target_score": span.judge_score or 0.0,
                            "distance": span.step_index - source_index,
                        }
                    )
                    analysis.paths.append(path)
        
        analysis.affected_spans = affected_spans
        analysis.overall_propagation_score = self._aggregate_propagation(analysis.paths)
        
        self.logger.info(
            f"Propagation analysis: {len(analysis.paths)} paths, "
            f"PS={analysis.overall_propagation_score:.2f}"
        )
        return analysis
    
    def _calculate_propagation_score(
        self,
        source_span: Span,
        target_span: Span,
        trace: Trace,
    ) -> float:
        """
        Calculate propagation score between spans.
        
        Args:
            source_span: Source of failure
            target_span: Potentially affected span
            trace: Execution trace
            
        Returns:
            Propagation score (0-1)
        """
        source_score = source_span.judge_score if source_span.judge_score is not None else 0.5
        target_score = target_span.judge_score if target_span.judge_score is not None else 0.5
        
        # Simple heuristic: how much did score drop
        score_drop = max(0.0, source_score - target_score)
        
        # If both source and target explicitly failed below threshold (< 0.7),
        # capture cascading degradation even when the root step scored lower than downstream
        if (
            score_drop == 0.0
            and source_span.judge_score is not None
            and target_span.judge_score is not None
            and source_score < 0.7
            and target_score < 0.7
        ):
            score_drop = (1.0 - target_score) * (1.0 - source_score)
        
        # Distance decay: closer = more influence
        distance = target_span.step_index - source_span.step_index
        distance_factor = 1.0 / (1.0 + distance * 0.1)
        
        ps = score_drop * distance_factor
        return min(1.0, max(0.0, ps))
    
    def _aggregate_propagation(self, paths: List[PropagationPath]) -> float:
        """
        Aggregate propagation scores across paths.
        
        Args:
            paths: Propagation paths
            
        Returns:
            Overall propagation score
        """
        if not paths:
            return 0.0
        
        scores = [p.propagation_score for p in paths]
        return sum(scores) / len(scores)
