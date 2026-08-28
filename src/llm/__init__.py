"""
LLM integration layer for FailureForensicsTool

- ollama_client: Ollama API client
- prompts: Prompt templates for pipeline and evaluation
"""

from .ollama_client import *
from .prompts import *

__all__ = [
    "OllamaClient",
    "PROMPTS",
]
