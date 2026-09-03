"""
Root cause analysis and identification.

Provides:
- RootCauseEngine: Identifies root causes
- Root Cause Confidence calculation
"""

import logging
from typing import Optional, List
import uuid
from datetime import datetime

from src.models.failure_models import (
    Failure, 
    RootCauseAnalysis, 
    PropagationAnalysis,
    RootCauseCandidate
)
from src.models.trace_models import Trace, Span


logger = logging.getLogger(__name__)


class RootCauseEngine:
    """Identifies root causes and calculates Root Cause Confidence."""
    
    def __init__(self):
        """Initialize engine."""
        self.logger = logging.getLogger(f"{__name__}")
    
    def analyze(
        self,
        failure: Failure,
        trace: Trace,
        propagation_analysis: PropagationAnalysis,
    ) -> RootCauseAnalysis:
        """
        Perform root cause analysis.
        
        Args:
            failure: Detected failure
            trace: Execution trace
            propagation_analysis: Propagation analysis for same failure
            
        Returns:
            Root cause analysis
        """
        analysis = RootCauseAnalysis(
            analysis_id=str(uuid.uuid4()),
            trace_id=trace.trace_id,
            failure_id=failure.failure_id,
            root_span_id=failure.span_id,
            root_step_name=failure.step_name,
        )
        
        # Collect candidate root causes
        candidates = self._find_candidates(failure, trace, propagation_analysis)
        analysis.candidate_root_causes = candidates
        
        if not candidates:
            analysis.root_cause_confidence = 0.0
            analysis.reasoning = "No candidates found"
            return analysis
        
        # Select best candidate
        best = candidates[0]
        analysis.root_span_id = best.span_id
        analysis.root_step_name = best.step_name
        analysis.root_cause_confidence = best.confidence
        analysis.reasoning = best.reasoning
        analysis.evidence = {
            "local_severity": best.local_severity,
            "downstream_impact": best.downstream_impact,
        }
        
        self.logger.info(
            f"Root cause identified: {analysis.root_step_name}, "
            f"RCC={analysis.root_cause_confidence:.2f}"
        )
        return analysis
    
    def _find_candidates(
        self,
        failure: Failure,
        trace: Trace,
        propagation_analysis: PropagationAnalysis,
    ) -> List[RootCauseCandidate]:
        """
        Find candidate root causes.
        
        Args:
            failure: Detected failure
            trace: Execution trace
            propagation_analysis: Propagation analysis
            
        Returns:
            Ranked list of candidates with confidence
        """
        candidates = []
        
        # Consider all failed spans before final output
        for span in trace.spans:
            if span.judge_score is not None and span.judge_score < 0.7:
                # Calculate local severity and downstream impact
                local_severity = 1.0 - span.judge_score
                downstream_impact = self._get_downstream_impact(span, propagation_analysis)
                
                # Calculate root cause confidence for this candidate
                rcc = self._calculate_rcc(local_severity, downstream_impact)
                
                candidate = RootCauseCandidate(
                    span_id=span.span_id,
                    step_name=span.step_name,
                    confidence=rcc,
                    local_severity=local_severity,
                    downstream_impact=downstream_impact,
                    reasoning=f"Candidate: {span.step_name} (score={span.judge_score:.2f}, RCC={rcc:.2f})"
                )
                candidates.append(candidate)
        
        # Sort by confidence (descending)
        candidates.sort(key=lambda x: x.confidence, reverse=True)
        return candidates
    
    def _calculate_rcc(
        self,
        local_severity: float,
        downstream_impact: float,
    ) -> float:
        """
        Calculate Root Cause Confidence.
        
        Args:
            local_severity: Local severity (1.0 - judge_score)
            downstream_impact: Downstream propagation impact
            
        Returns:
            RCC score (0-1)
        """
        # RCC = weighted combination
        # 60% local signals, 40% propagation effects
        rcc = 0.6 * local_severity + 0.4 * downstream_impact
        return min(1.0, max(0.0, rcc))
    
    def _get_downstream_impact(
        self,
        span: Span,
        propagation_analysis: PropagationAnalysis,
    ) -> float:
        """
        Get downstream impact score for a span.
        
        Args:
            span: Span to analyze
            propagation_analysis: Propagation analysis
            
        Returns:
            Impact score (0-1)
        """
        # Maximum propagation score from this span
        impact = 0.0
        for path in propagation_analysis.paths:
            if path.source_span_id == span.span_id:
                impact = max(impact, path.propagation_score)
        
        return impact
