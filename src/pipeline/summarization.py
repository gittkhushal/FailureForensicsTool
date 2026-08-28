"""
Summarization step: Content summarization.

Uses LLM to generate structured summaries of documents.
"""

import logging
import json
from typing import Any, Dict

from src.models import StepInput, StepOutput
from src.pipeline.base import PipelineStep
from src.llm.ollama_client import get_ollama_client, OllamaGenerationError, OllamaJSONParseError
from src.llm.prompts import format_prompt


logger = logging.getLogger(__name__)


class SummarizationStep(PipelineStep):
    """Document summarization step."""
    
    def __init__(self):
        """Initialize summarization step."""
        super().__init__(
            name="summarization",
            description="Content summarization using LLM"
        )
        self.llm = get_ollama_client()
    
    def execute(self, step_input: StepInput) -> StepOutput:
        """
        Summarize document content.
        
        Args:
            step_input: Classified data from previous step
            
        Returns:
            Summary results
        """
        try:
            # Get document content - reconstruct from input chain
            document = ""
            if isinstance(step_input.data, dict):
                # Try to get original document
                if "document" in step_input.data:
                    document = step_input.data["document"]
                elif "assertions" in step_input.data:
                    assertions = step_input.data["assertions"]
                    if assertions:
                        document = ". ".join(str(a) for a in assertions)
            
            if not document:
                # Fallback: use string representation
                document = str(step_input.data)[:500]
            
            if not document or document.strip() == "":
                raise ValueError("No document content for summarization")
            
            # Format prompt
            prompt = format_prompt("summarization", document=document)
            
            # Call LLM
            try:
                result = self.llm.generate_json(prompt, temperature=0.5, max_attempts=2)
            except (OllamaGenerationError, OllamaJSONParseError) as e:
                self.logger.warning(f"LLM summarization failed: {e}, using fallback")
                result = self._fallback_summarization(document)
            
            # Extract and structure
            summary_result = {
                "executive_summary": result.get("executive_summary", ""),
                "key_findings": result.get("key_findings", []),
                "conclusions": result.get("conclusions", []),
                "action_items": result.get("action_items", []),
                "completeness": result.get("completeness", 0.7),
            }
            
            output = StepOutput(
                data=summary_result,
                confidence=summary_result["completeness"],
                metadata={"summarization_method": "llm"}
            )
            
            self.logger.info(
                f"Summarization: {len(summary_result['key_findings'])} findings, "
                f"completeness={summary_result['completeness']:.2f}"
            )
            return output
            
        except Exception as e:
            self.logger.error(f"Summarization failed: {e}")
            raise
    
    def _fallback_summarization(self, document: str) -> Dict[str, Any]:
        """
        Fallback summarization using simple heuristics.
        
        Args:
            document: Document text
            
        Returns:
            Basic summary result
        """
        sentences = [s.strip() for s in document.split(".") if s.strip()]
        
        return {
            "executive_summary": sentences[0] if sentences else "",
            "key_findings": sentences[1:4],  # First 3 sentences as findings
            "conclusions": sentences[4:6],  # Next 2 sentences as conclusions
            "action_items": [],
            "completeness": 0.5,
        }
