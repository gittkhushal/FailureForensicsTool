"""
Classification step: Document classification.

Uses LLM to classify document type, category, and other attributes.
"""

import logging
import json
from typing import Any, Dict

from src.models import StepInput, StepOutput
from src.pipeline.base import PipelineStep
from src.llm.ollama_client import get_ollama_client, OllamaGenerationError, OllamaJSONParseError
from src.llm.prompts import format_prompt


logger = logging.getLogger(__name__)


class ClassificationStep(PipelineStep):
    """Document classification step."""
    
    def __init__(self):
        """Initialize classification step."""
        super().__init__(
            name="classification",
            description="Document classification using LLM"
        )
        self.llm = get_ollama_client()
    
    def execute(self, step_input: StepInput) -> StepOutput:
        """
        Classify document.
        
        Args:
            step_input: Extracted data from previous step
            
        Returns:
            Classification results
        """
        try:
            # Get document content from input
            document = ""
            
            if isinstance(step_input.data, dict):
                # Check for document first
                if "document" in step_input.data:
                    document = step_input.data["document"]
                # Fall back to assertions if they exist
                elif "assertions" in step_input.data:
                    assertions = step_input.data.get("assertions", [])
                    if assertions:
                        document = ". ".join(str(a) for a in assertions)
            
            # If still empty, use string representation
            if not document:
                document = str(step_input.data)[:1000]
            
            if not document or document.strip() == "":
                raise ValueError("No document content for classification")
            
            # Format prompt with context
            prompt = format_prompt(
                "classification",
                document=document,
                context="general document analysis"
            )
            
            # Call LLM
            try:
                result = self.llm.generate_json(prompt, temperature=0.3, max_attempts=2)
            except (OllamaGenerationError, OllamaJSONParseError) as e:
                self.logger.warning(f"LLM classification failed: {e}, using fallback")
                result = self._fallback_classification()
            
            # Extract and structure
            classification_result = {
                "type": result.get("type", "document"),
                "category": result.get("category", "general"),
                "subcategories": result.get("subcategories", []),
                "sentiment": result.get("sentiment", "neutral"),
                "relevance_score": result.get("relevance_score", 0.5),
                "confidence": result.get("confidence", 0.7),
            }
            
            output = StepOutput(
                data=classification_result,
                confidence=classification_result["confidence"],
                metadata={"classification_method": "llm"}
            )
            
            self.logger.info(
                f"Classification: {classification_result['type']} / "
                f"{classification_result['category']}, "
                f"confidence={classification_result['confidence']:.2f}"
            )
            return output
            
        except Exception as e:
            self.logger.error(f"Classification failed: {e}")
            raise
    
    def _fallback_classification(self) -> Dict[str, Any]:
        """
        Fallback classification using simple heuristics.
        
        Returns:
            Basic classification result
        """
        return {
            "type": "document",
            "category": "general",
            "subcategories": [],
            "sentiment": "neutral",
            "relevance_score": 0.5,
            "confidence": 0.4,
        }
