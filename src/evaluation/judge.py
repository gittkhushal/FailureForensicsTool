"""
LLM-as-Judge evaluation module.

Provides:
- Judge: Evaluation engine
- Result parsing and validation
"""

import logging
from typing import Any, Dict, Optional
import json

from src.models.evaluation_models import JudgeResult, EvaluationCriteria
from src.llm.ollama_client import get_ollama_client
from src.llm.prompts import format_prompt


logger = logging.getLogger(__name__)


class Judge:
    """LLM-based evaluator of pipeline outputs."""
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize judge.
        
        Args:
            model: Optional LLM model to use (defaults to currently active client model)
        """
        if model:
            self.llm = get_ollama_client(model=model)
            self.model = str(model)
        else:
            self.llm = get_ollama_client()
            raw_model = getattr(self.llm, "model", "qwen2.5:7b-instruct")
            self.model = str(raw_model) if isinstance(raw_model, str) else "qwen2.5:7b-instruct"
        self.logger = logging.getLogger(f"{__name__}")
    
    def evaluate(
        self,
        step_name: str,
        step_type: str,
        input_data: Any,
        output_data: Any,
        context: str = "",
    ) -> JudgeResult:
        """
        Evaluate step output.
        
        Args:
            step_name: Name of step
            step_type: Type of step (extraction, classification, etc.)
            input_data: Step input
            output_data: Step output
            context: Additional context
            
        Returns:
            Evaluation result
        """
        try:
            # Format prompt
            prompt = format_prompt(
                "judge",
                step_name=step_name,
                step_type=step_type,
                input=str(input_data)[:500],
                output=str(output_data)[:500],
            )
            
            # Get evaluation from LLM
            response = self.llm.generate_json(prompt)
            
            # Parse result
            result = JudgeResult(
                span_id="",  # Will be set by caller
                step_name=step_name,
                overall_score=response.get("overall_score", 0.5),
                criteria_scores=response.get("criteria_scores", {}),
                passed=response.get("pass", True),
                issues=response.get("critical_issues", []),
                reasoning=response.get("reasoning", ""),
                model_used=self.model,
            )
            
            self.logger.info(
                f"Evaluated {step_name}: score={result.overall_score:.2f}, "
                f"passed={result.passed}"
            )
            return result
            
        except Exception as e:
            self.logger.error(f"Evaluation failed for {step_name}: {e}")
            # Return default result on error
            return JudgeResult(
                span_id="",
                step_name=step_name,
                overall_score=0.0,
                passed=False,
                issues=[str(e)],
                reasoning=f"Evaluation error: {e}",
            )
