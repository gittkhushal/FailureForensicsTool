"""
Extraction step: Entity and information extraction.

Uses LLM to extract key entities and information from documents.
"""

import logging
import json
from typing import Any, Dict

from src.models import StepInput, StepOutput
from src.pipeline.base import PipelineStep
from src.llm.ollama_client import get_ollama_client, OllamaGenerationError, OllamaJSONParseError
from src.llm.prompts import format_prompt


logger = logging.getLogger(__name__)


class ExtractionStep(PipelineStep):
    """Entity and information extraction step."""
    
    def __init__(self):
        """Initialize extraction step."""
        super().__init__(
            name="extraction",
            description="Entity and information extraction using LLM"
        )
        self.llm = get_ollama_client()
    
    def execute(self, step_input: StepInput) -> StepOutput:
        """
        Extract entities and information from document.
        
        Args:
            step_input: Normalized document data
            
        Returns:
            Extracted entities and information
        """
        try:
            # Get document from input
            if isinstance(step_input.data, dict):
                document = step_input.data.get("document", "")
            else:
                document = str(step_input.data)
            
            if not document:
                raise ValueError("No document provided to extraction")
            
            # Format prompt
            prompt = format_prompt("extraction", document=document)
            
            # Call LLM
            try:
                result = self.llm.generate_json(prompt, temperature=0.3, max_attempts=2)
            except (OllamaGenerationError, OllamaJSONParseError) as e:
                self.logger.warning(f"LLM extraction failed: {e}, using fallback")
                result = self._fallback_extraction(document)
            
            # Extract and structure
            extraction_result = {
                "entities": result.get("entities", []),
                "facts": result.get("facts", []),
                "relationships": result.get("relationships", []),
                "assertions": result.get("assertions", []),
                "confidence": result.get("confidence", 0.7),
            }
            
            output = StepOutput(
                data=extraction_result,
                confidence=extraction_result["confidence"],
                metadata={"extraction_method": "llm"}
            )
            
            self.logger.info(
                f"Extraction: {len(extraction_result['entities'])} entities, "
                f"confidence={extraction_result['confidence']:.2f}"
            )
            return output
            
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            raise
    
    def _fallback_extraction(self, document: str) -> Dict[str, Any]:
        """
        Fallback extraction using simple heuristics.
        
        Args:
            document: Document text
            
        Returns:
            Basic extraction result
        """
        # Simple fallback: just return the document structure
        sentences = [s.strip() for s in document.split(".") if s.strip()]
        
        return {
            "entities": [],
            "facts": sentences[:5],  # First 5 sentences as facts
            "relationships": [],
            "assertions": sentences,
            "confidence": 0.5,
        }
