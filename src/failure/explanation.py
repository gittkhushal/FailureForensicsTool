"""
Explanation generation for failures.

Provides:
- ExplanationGenerator: Generates human-readable explanations
"""

import logging
from typing import Optional, Dict, Any

from src.models.failure_models import Failure, RootCauseAnalysis, PropagationAnalysis
from src.models.trace_models import Trace


logger = logging.getLogger(__name__)


class ExplanationGenerator:
    """Generates human-readable failure explanations."""
    
    def __init__(self):
        """Initialize generator."""
        self.logger = logging.getLogger(f"{__name__}")
    
    def generate(
        self,
        failure: Failure,
        trace: Trace,
        root_cause_analysis: RootCauseAnalysis,
        propagation_analysis: PropagationAnalysis,
    ) -> str:
        """
        Generate explanation for failure.
        
        Args:
            failure: Detected failure
            trace: Execution trace
            root_cause_analysis: Root cause analysis
            propagation_analysis: Propagation analysis
            
        Returns:
            Explanation string
        """
        explanation = []
        
        # Summary
        explanation.append("FAILURE ANALYSIS")
        explanation.append("=" * 50)
        
        # Failure detection
        explanation.append(f"\n1. FAILURE DETECTED")
        explanation.append(f"   Step: {failure.step_name}")
        explanation.append(f"   Severity: {failure.severity:.2%}")
        explanation.append(f"   Quality Score: {failure.judge_score:.2f}")
        explanation.append(f"   Type: {failure.failure_type.value}")
        
        # Root cause
        explanation.append(f"\n2. ROOT CAUSE IDENTIFIED")
        explanation.append(f"   Step: {root_cause_analysis.root_step_name}")
        explanation.append(f"   Confidence: {root_cause_analysis.root_cause_confidence:.2%}")
        explanation.append(f"   Reasoning: {root_cause_analysis.reasoning}")
        
        # Propagation
        explanation.append(f"\n3. PROPAGATION ANALYSIS")
        explanation.append(f"   Affected Steps: {len(propagation_analysis.affected_spans)}")
        explanation.append(f"   Overall Propagation Score: {propagation_analysis.overall_propagation_score:.2f}")
        explanation.append(f"   Paths:")
        
        for path in propagation_analysis.paths:
            explanation.append(
                f"   - Source → Target: "
                f"PS={path.propagation_score:.2f}"
            )
        
        # Evidence
        explanation.append(f"\n4. EVIDENCE")
        for key, value in failure.evidence.items():
            explanation.append(f"   {key}: {value}")
        
        return "\n".join(explanation)
    
    def generate_summary(
        self,
        failure: Failure,
        trace: Trace,
        root_cause_analysis: RootCauseAnalysis,
    ) -> str:
        """
        Generate brief summary explanation.
        
        Args:
            failure: Detected failure
            trace: Execution trace
            root_cause_analysis: Root cause analysis
            
        Returns:
            Summary explanation
        """
        return (
            f"{root_cause_analysis.root_step_name} is the likely root cause "
            f"(RCC={root_cause_analysis.root_cause_confidence:.2%}). "
            f"The error affected subsequent steps and contributed to the final failure "
            f"(severity={failure.severity:.2%}). "
        )
