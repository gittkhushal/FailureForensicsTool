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
    """
    Semantic failure classifier.
    
    Categorizes failures using multi-signal analysis of span errors,
    LLM judge criteria, output completeness, latency, and pipeline context.
    """
    
    def __init__(self):
        """Initialize classifier."""
        self.logger = logging.getLogger(f"{__name__}")
    
    def classify(self, failure: Failure, trace: Trace) -> FailureType:
        """
        Classify failure type using multi-signal semantic heuristics.
        
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
        
        step_name = span.step_name.lower()
        error_text = (span.error or "").lower()
        desc_text = (failure.description or "").lower()
        evidence = failure.evidence or {}
        output_str = str(span.output_data or "").strip().lower()
        latency_ms = span.latency_ms or 0.0
        
        # Collect judge issues if present
        issues = evidence.get("issues", []) or evidence.get("critical_issues", [])
        issues_text = " ".join(str(i) for i in issues).lower()
        all_signals = f"{error_text} {desc_text} {issues_text}"
        
        detected_type = None
        rationale = ""
        
        # 1. Timeout failure
        if "timeout" in all_signals or "timed out" in all_signals or (latency_ms >= 30000 and "time" in all_signals):
            detected_type = FailureType.TIMEOUT
            rationale = f"Execution exceeded latency limit ({latency_ms:.0f}ms) or timed out"
            
        # 2. LLM engine / hardware failure
        elif any(t in all_signals for t in ["connection error", "ollama", "cuda", "out of memory", "oom", "server unavailable", "generation error"]):
            detected_type = FailureType.LLM_ERROR
            rationale = "Underlying LLM runtime or connectivity error encountered"
            
        # 3. Prompting / token limit failure
        elif any(t in all_signals for t in ["prompt template", "token limit", "context length exceeded", "prompt formatting"]):
            detected_type = FailureType.PROMPT_FAILURE
            rationale = "Prompt structure or context length limits exceeded"
            
        # 4. Context loss across spans
        elif any(t in all_signals for t in ["context loss", "missing context", "dropped input", "lost input"]):
            detected_type = FailureType.CONTEXT_LOSS
            rationale = "Intermediate context was lost or unreferenced from prior step"
            
        # 5. Semantic extraction hallucination
        elif any(t in all_signals for t in ["hallucin", "fabricated", "unsupported entity", "unsupported fact", "grounding failure"]):
            detected_type = FailureType.EXTRACTION_HALLUCINATION
            rationale = "Generated output contains entities or assertions not grounded in the source input"
            
        # 6. Misclassification
        elif any(t in all_signals for t in ["misclassif", "wrong class", "wrong category", "incorrect label"]):
            detected_type = FailureType.MISCLASSIFICATION
            rationale = "Output assigned to an incorrect domain or category"
            
        # 7. Inconsistency / Contradiction
        elif any(t in all_signals for t in ["inconsist", "contradict", "conflicting statement"]):
            detected_type = FailureType.INCONSISTENCY
            rationale = "Output contains internal contradictions or conflicts with input assertions"
            
        # 8. Incomplete / empty output
        elif any(t in all_signals for t in ["incomplete", "truncated", "missing findings", "empty output"]):
            detected_type = FailureType.INCOMPLETE_OUTPUT
            rationale = "Step produced empty, truncated, or incomplete results"
            
        # 9. Propagation error (caused by prior failed step with propagation indication)
        elif self._is_propagated_failure(span, trace) and ("propagat" in all_signals or "cascade" in all_signals or "downstream" in all_signals):
            detected_type = FailureType.PROPAGATION_ERROR
            rationale = "Step degraded as a direct consequence of an upstream failure"
            
        # 10. Step-name fallback heuristics (backward compatibility)
        elif "extract" in step_name:
            detected_type = FailureType.EXTRACTION_HALLUCINATION
            rationale = "Extraction step quality score below threshold"
        elif "classif" in step_name:
            detected_type = FailureType.MISCLASSIFICATION
            rationale = "Classification step quality score below threshold"
        elif "summar" in step_name:
            detected_type = FailureType.INCOMPLETE_OUTPUT
            rationale = "Summarization step quality score below threshold"
        else:
            detected_type = FailureType.UNKNOWN
            rationale = "Generic step failure without specific semantic signature"
        
        # Attach classification rationale to failure evidence
        failure.evidence["classification_rationale"] = rationale
        failure.evidence["semantic_classification"] = True
        
        self.logger.info(
            f"Classified failure in {span.step_name} as {detected_type.value}: {rationale}"
        )
        return detected_type
    
    def _is_propagated_failure(self, span: Span, trace: Trace) -> bool:
        """Check if this span's degradation is likely caused by an upstream failure."""
        for prior_span in trace.spans:
            if prior_span.step_index < span.step_index:
                # Upstream span had a severe failure
                if prior_span.judge_score is not None and prior_span.judge_score < 0.6:
                    return True
                if prior_span.status.value == "failed":
                    return True
        return False
    
    def classify_batch(self, failures: List[Failure], trace: Trace) -> List[Failure]:
        """
        Classify multiple failures and enrich failure objects.
        
        Args:
            failures: Failures to classify
            trace: Associated trace
            
        Returns:
            Classified failures
        """
        for failure in failures:
            failure.failure_type = self.classify(failure, trace)
        
        return failures
