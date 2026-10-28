"""
Adaptive pipeline optimizer for closed-loop self-improvement.

Provides:
- AdaptiveOptimizer: Derives tuning recommendations from root causes and builds adapted pipelines
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.models.failure_models import Failure, FailureType, RootCauseAnalysis
from src.models.evaluation_models import AdaptiveRecommendation, EvaluationCase
from src.pipeline.base import Pipeline, PipelineStep
from src.pipeline.intake import IntakeStep
from src.pipeline.extraction import ExtractionStep
from src.pipeline.classification import ClassificationStep
from src.pipeline.summarization import SummarizationStep


logger = logging.getLogger(__name__)


class AdaptiveOptimizer:
    """Derives self-healing adjustments and builds adapted pipelines based on failure diagnostics."""
    
    def __init__(self):
        """Initialize optimizer."""
        self.logger = logging.getLogger(f"{__name__}")
    
    def generate_recommendations(
        self,
        failures: List[Failure],
        root_causes: Optional[List[RootCauseAnalysis]] = None,
    ) -> List[AdaptiveRecommendation]:
        """
        Analyze failures and root cause evidence to generate targeted adaptations.
        
        Args:
            failures: Detected failures
            root_causes: Optional root cause analyses
            
        Returns:
            List of AdaptiveRecommendation instances
        """
        recommendations = []
        target_steps_seen = set()
        
        for failure in failures:
            step_name = failure.step_name.lower()
            if step_name in target_steps_seen:
                continue
            
            ftype = failure.failure_type
            rec_id = str(uuid.uuid4())
            
            if ftype == FailureType.EXTRACTION_HALLUCINATION:
                rec = AdaptiveRecommendation(
                    recommendation_id=rec_id,
                    target_step=failure.step_name,
                    failure_type=ftype.value,
                    suggested_temperature=0.1,
                    prompt_guideline_prefix=(
                        "[GROUNDING CONSTRAINT]: Extract ONLY entities and assertions explicitly mentioned. "
                        "Do not infer or fabricate any unstated facts."
                    ),
                    parameter_adjustments={"temperature": 0.1, "top_p": 0.8},
                    rationale="Hallucination detected; reduced sampling temperature and enforced strict verbatim grounding constraints."
                )
                recommendations.append(rec)
                target_steps_seen.add(step_name)
                
            elif ftype == FailureType.MISCLASSIFICATION:
                rec = AdaptiveRecommendation(
                    recommendation_id=rec_id,
                    target_step=failure.step_name,
                    failure_type=ftype.value,
                    suggested_temperature=0.2,
                    prompt_guideline_prefix=(
                        "[DISAMBIGUATION GUIDELINE]: Carefully distinguish between domain, intent, and content category. "
                        "Base categorization strictly on core assertions rather than incidental keywords."
                    ),
                    parameter_adjustments={"temperature": 0.2, "top_p": 0.85},
                    rationale="Misclassification detected; added domain disambiguation guidelines and constrained categorization variance."
                )
                recommendations.append(rec)
                target_steps_seen.add(step_name)
                
            elif ftype == FailureType.INCOMPLETE_OUTPUT:
                rec = AdaptiveRecommendation(
                    recommendation_id=rec_id,
                    target_step=failure.step_name,
                    failure_type=ftype.value,
                    suggested_temperature=0.3,
                    prompt_guideline_prefix=(
                        "[COMPLETENESS MANDATE]: Provide exhaustive coverage of all extracted findings. "
                        "Do not truncate or omit secondary conclusions."
                    ),
                    parameter_adjustments={"min_length_factor": 1.25, "temperature": 0.3},
                    rationale="Incomplete output detected; enforced exhaustive key findings coverage mandate."
                )
                recommendations.append(rec)
                target_steps_seen.add(step_name)
                
            elif ftype == FailureType.TIMEOUT:
                rec = AdaptiveRecommendation(
                    recommendation_id=rec_id,
                    target_step=failure.step_name,
                    failure_type=ftype.value,
                    suggested_temperature=0.3,
                    prompt_guideline_prefix="[LATENCY CONSTRAINT]: Be concise and direct to minimize token generation overhead.",
                    parameter_adjustments={"max_tokens": 512, "model_tier": "fast"},
                    rationale="Timeout detected; constrained token generation limits and recommended fast model tier."
                )
                recommendations.append(rec)
                target_steps_seen.add(step_name)
                
            elif ftype == FailureType.PROPAGATION_ERROR:
                rec = AdaptiveRecommendation(
                    recommendation_id=rec_id,
                    target_step=failure.step_name,
                    failure_type=ftype.value,
                    suggested_temperature=0.2,
                    prompt_guideline_prefix=(
                        "[INPUT RE-VALIDATION]: Validate upstream assertions for completeness before processing. "
                        "Filter out ungrounded assertions."
                    ),
                    parameter_adjustments={"input_validation": "strict"},
                    rationale="Propagated failure detected; added upstream input sanity validation check."
                )
                recommendations.append(rec)
                target_steps_seen.add(step_name)
        
        self.logger.info(f"Generated {len(recommendations)} adaptive recommendations")
        return recommendations
    
    def generate_recommendations_from_cases(
        self,
        cases: List[EvaluationCase],
    ) -> List[AdaptiveRecommendation]:
        """Derive adaptive recommendations directly from a set of stored evaluation cases."""
        synthetic_failures = []
        for case in cases:
            ftype = FailureType.UNKNOWN
            for member in FailureType:
                if member.value == case.failure_type:
                    ftype = member
                    break
            
            synth = Failure(
                failure_id=f"synth_{case.case_id}",
                trace_id=case.trace_id,
                span_id=f"span_{case.case_id}",
                step_name=case.failing_step or case.root_cause_step or "extraction",
                failure_type=ftype,
                severity=case.severity,
            )
            synthetic_failures.append(synth)
            
        return self.generate_recommendations(synthetic_failures)
    
    def build_adapted_pipeline(
        self,
        recommendations: List[AdaptiveRecommendation],
        pipeline_name: str = "adapted_pipeline",
    ) -> Pipeline:
        """
        Build an executable pipeline with adapted guidelines applied to target steps.
        
        Args:
            recommendations: Adaptations to apply
            pipeline_name: Name for adapted pipeline
            
        Returns:
            Pipeline configured with adaptations
        """
        pipeline = Pipeline(name=pipeline_name)
        rec_map = {r.target_step.lower(): r for r in recommendations}
        
        # 1. Intake step
        pipeline.add_step(IntakeStep())
        
        # 2. Extraction step with adaptation
        extraction = ExtractionStep()
        if "extraction" in rec_map:
            rec = rec_map["extraction"]
            orig_exec = extraction.execute
            prefix = rec.prompt_guideline_prefix
            
            def adapted_extraction(step_input, orig=orig_exec, p=prefix):
                if isinstance(step_input.data, dict) and "document" in step_input.data:
                    step_input.data["document"] = f"{p}\n\nDocument: {step_input.data['document']}"
                elif isinstance(step_input.data, str):
                    step_input.data = f"{p}\n\nDocument: {step_input.data}"
                return orig(step_input)
                
            extraction.execute = adapted_extraction
        pipeline.add_step(extraction)
        
        # 3. Classification step with adaptation
        classification = ClassificationStep()
        if "classification" in rec_map:
            rec = rec_map["classification"]
            orig_exec = classification.execute
            prefix = rec.prompt_guideline_prefix
            
            def adapted_classification(step_input, orig=orig_exec, p=prefix):
                if isinstance(step_input.data, dict) and "document" in step_input.data:
                    step_input.data["document"] = f"{p}\n\nDocument: {step_input.data['document']}"
                return orig(step_input)
                
            classification.execute = adapted_classification
        pipeline.add_step(classification)
        
        # 4. Summarization step with adaptation
        summarization = SummarizationStep()
        if "summarization" in rec_map:
            rec = rec_map["summarization"]
            orig_exec = summarization.execute
            prefix = rec.prompt_guideline_prefix
            
            def adapted_summarization(step_input, orig=orig_exec, p=prefix):
                if isinstance(step_input.data, dict) and "document" in step_input.data:
                    step_input.data["document"] = f"{p}\n\nDocument: {step_input.data['document']}"
                return orig(step_input)
                
            summarization.execute = adapted_summarization
        pipeline.add_step(summarization)
        
        return pipeline
