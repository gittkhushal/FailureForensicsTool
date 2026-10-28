"""
Unified multi-provider LLM abstraction layer.

Supports:
- Local Ollama with NVIDIA GPU acceleration
- Google Gemini API (gemini-1.5-flash / gemini-2.0-flash)
- Groq Cloud API (llama-3.3-70b / mixtral-8x7b)
- OpenAI-compatible local/remote servers (vLLM, LMStudio, llama.cpp)
"""

import os
import json
import logging
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from src.llm.ollama_client import OllamaClient, get_ollama_client, OllamaGenerationError, OllamaJSONParseError


logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base provider for LLM inference."""

    @abstractmethod
    def generate(self, prompt: str, temperature: float = 0.7, **kwargs) -> str:
        """Generate text from prompt."""
        pass

    @abstractmethod
    def generate_json(self, prompt: str, temperature: float = 0.3, **kwargs) -> Dict[str, Any]:
        """Generate structured JSON from prompt."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is reachable."""
        pass

    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """Return provider metadata and active model."""
        pass


class OllamaProvider(BaseLLMProvider):
    """Local Ollama provider with GPU acceleration."""

    def __init__(self, model: str = "qwen2.5:7b-instruct", base_url: str = "http://localhost:11434"):
        self.client = get_ollama_client(base_url=base_url, model=model)
        self.model = model

    def set_model(self, model: str) -> None:
        self.model = model
        self.client.set_model(model)

    def generate(self, prompt: str, temperature: float = 0.7, **kwargs) -> str:
        return self.client.generate(prompt, temperature=temperature)

    def generate_json(self, prompt: str, temperature: float = 0.3, **kwargs) -> Dict[str, Any]:
        return self.client.generate_json(prompt, temperature=temperature)

    def is_available(self) -> bool:
        return self.client.is_available()

    def get_provider_info(self) -> Dict[str, Any]:
        health = self.client.health_check()
        return {
            "provider": "Ollama (Local NVIDIA GPU)",
            "model": self.client.model,
            "available": health.get("server_available", False),
            "models_path": health.get("models_path", "D:\\ollama_models"),
            "models": health.get("available_models", []),
        }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API Provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def is_available(self) -> bool:
        return bool(self.api_key.strip())

    def generate(self, prompt: str, temperature: float = 0.7, **kwargs) -> str:
        if not self.api_key:
            raise OllamaGenerationError("Gemini API key is not configured.")
        
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        try:
            res = requests.post(url, json=payload, timeout=30)
            res.raise_for_status()
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            raise OllamaGenerationError(f"Gemini generation error: {e}")

    def generate_json(self, prompt: str, temperature: float = 0.2, **kwargs) -> Dict[str, Any]:
        json_prompt = f"{prompt}\n\nIMPORTANT: Return ONLY valid JSON, no markdown formatting."
        raw = self.generate(json_prompt, temperature=temperature)
        cleaned = raw.strip()
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise OllamaJSONParseError(f"Failed to parse Gemini response as JSON: {e}")

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "provider": "Google Gemini (Cloud API)",
            "model": self.model,
            "available": bool(self.api_key),
        }


class GroqProvider(BaseLLMProvider):
    """Groq LPU High-Speed Cloud Provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model = model
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def is_available(self) -> bool:
        return bool(self.api_key.strip())

    def generate(self, prompt: str, temperature: float = 0.7, **kwargs) -> str:
        if not self.api_key:
            raise OllamaGenerationError("Groq API key is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        try:
            res = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise OllamaGenerationError(f"Groq generation error: {e}")

    def generate_json(self, prompt: str, temperature: float = 0.2, **kwargs) -> Dict[str, Any]:
        if not self.api_key:
            raise OllamaGenerationError("Groq API key is not configured.")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        try:
            res = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
            res.raise_for_status()
            data = res.json()
            return json.loads(data["choices"][0]["message"]["content"])
        except Exception as e:
            raise OllamaJSONParseError(f"Groq JSON parse error: {e}")

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "provider": "Groq LPU (Ultra-Fast Cloud)",
            "model": self.model,
            "available": bool(self.api_key),
        }


# Global active provider cache
_ACTIVE_PROVIDER: Optional[BaseLLMProvider] = None


def get_llm_provider(
    provider_type: str = "ollama",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> BaseLLMProvider:
    """
    Get or create active LLM provider.
    
    Args:
        provider_type: 'ollama', 'gemini', or 'groq'
        model: Optional model name
        api_key: Optional API key for cloud providers
    """
    global _ACTIVE_PROVIDER

    p_type = provider_type.lower()
    if p_type == "gemini":
        _ACTIVE_PROVIDER = GeminiProvider(api_key=api_key, model=model or "gemini-1.5-flash")
    elif p_type == "groq":
        _ACTIVE_PROVIDER = GroqProvider(api_key=api_key, model=model or "llama-3.3-70b-versatile")
    else:
        _ACTIVE_PROVIDER = OllamaProvider(model=model or "qwen2.5:7b-instruct")

    return _ACTIVE_PROVIDER
