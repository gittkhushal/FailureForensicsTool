"""
Ollama LLM client for local inference.

Provides:
- OllamaClient: Interface to Ollama API
- Retry and fallback logic
- JSON parsing with validation
- Error handling and recovery
"""

import requests
import json
import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime


logger = logging.getLogger(__name__)

# Custom exceptions
class OllamaException(Exception):
    """Base exception for Ollama operations."""
    pass


class OllamaConnectionError(OllamaException):
    """Connection to Ollama failed."""
    pass


class OllamaGenerationError(OllamaException):
    """Text generation failed."""
    pass


class OllamaJSONParseError(OllamaException):
    """JSON parsing failed."""
    pass


class OllamaClient:
    """Client for Ollama API."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:7b-instruct",
        timeout: int = 300,
        max_retries: int = 3,
    ):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama server URL
            model: Model name to use
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def _is_available(self) -> bool:
        """Check if Ollama server is available."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Returns:
            Dictionary with health status information
        """
        result = {
            "server_available": False,
            "model_available": False,
            "timestamp": datetime.now().isoformat(),
            "errors": [],
        }
        
        # Check server
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                result["server_available"] = True
                models = response.json().get("models", [])
                model_names = [m.get("name") for m in models]
                result["available_models"] = model_names
                
                # Check if our model is available
                if any(self.model in name for name in model_names):
                    result["model_available"] = True
                else:
                    result["errors"].append(
                        f"Model {self.model} not found. Available: {model_names}"
                    )
            else:
                result["errors"].append(f"Server returned status {response.status_code}")
        except requests.RequestException as e:
            result["errors"].append(f"Server unavailable: {str(e)}")
        
        return result
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stream: bool = False,
        retry_count: int = 0,
    ) -> str:
        """
        Generate text using Ollama with exponential backoff retry.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0-1)
            top_p: Top-p sampling parameter
            stream: Whether to stream response
            retry_count: Internal retry counter (for recursion)
            
        Returns:
            Generated text
            
        Raises:
            OllamaConnectionError: If Ollama is unavailable
            OllamaGenerationError: If generation fails
        """
        if not self._is_available():
            error_msg = (
                f"Ollama server not available at {self.base_url}. "
                "Ensure Ollama is running: ollama serve"
            )
            self.logger.error(error_msg)
            raise OllamaConnectionError(error_msg)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "top_p": top_p,
                    "stream": stream,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get("response", "").strip()
            
            if not generated_text:
                self.logger.warning("Generated empty response")
                if retry_count < self.max_retries:
                    backoff = 2 ** retry_count
                    self.logger.info(f"Retrying after {backoff}s backoff")
                    time.sleep(backoff)
                    return self.generate(
                        prompt, temperature, top_p, stream, retry_count + 1
                    )
                raise OllamaGenerationError("Generated empty response after retries")
            
            self.logger.debug(f"Generated text: {len(generated_text)} chars")
            return generated_text
                
        except requests.Timeout:
            if retry_count < self.max_retries:
                backoff = 2 ** retry_count
                self.logger.warning(f"Timeout, retrying after {backoff}s")
                time.sleep(backoff)
                return self.generate(
                    prompt, temperature, top_p, stream, retry_count + 1
                )
            raise OllamaGenerationError(f"Timeout after {self.max_retries} retries")
        except requests.RequestException as e:
            if retry_count < self.max_retries:
                backoff = 2 ** retry_count
                self.logger.warning(f"Request failed: {e}, retrying after {backoff}s")
                time.sleep(backoff)
                return self.generate(
                    prompt, temperature, top_p, stream, retry_count + 1
                )
            error_msg = f"Failed to generate after {self.max_retries} attempts: {e}"
            self.logger.error(error_msg)
            raise OllamaGenerationError(error_msg)
    
    def generate_json(
        self,
        prompt: str,
        temperature: float = 0.3,
        top_p: float = 0.9,
        max_attempts: int = 3,
    ) -> Dict[str, Any]:
        """
        Generate JSON response using Ollama with robust parsing.
        
        Args:
            prompt: Input prompt (should request JSON)
            temperature: Sampling temperature (lower for more consistent JSON)
            top_p: Top-p sampling
            max_attempts: Max attempts to get valid JSON
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            OllamaGenerationError: If generation fails
            OllamaJSONParseError: If unable to parse JSON
        """
        json_prompt = (
            prompt + 
            "\n\nIMPORTANT: Return ONLY valid JSON, no other text, no markdown, "
            "no explanation."
        )
        
        for attempt in range(max_attempts):
            try:
                response = self.generate(
                    json_prompt,
                    temperature=temperature,
                    top_p=top_p,
                )
                
                # Try to extract JSON from response
                parsed = self._extract_json(response)
                self.logger.debug(f"Parsed JSON: {list(parsed.keys())}")
                return parsed
                    
            except OllamaJSONParseError as e:
                self.logger.warning(
                    f"JSON parse attempt {attempt + 1}/{max_attempts} failed: {e}"
                )
                if attempt == max_attempts - 1:
                    error_msg = (
                        f"Failed to parse JSON after {max_attempts} attempts. "
                        f"Last response: {response[:200]}..."
                    )
                    self.logger.error(error_msg)
                    raise OllamaJSONParseError(error_msg)
            except OllamaGenerationError:
                raise
    
    def _extract_json(self, response: str) -> Dict[str, Any]:
        """
        Extract and parse JSON from response text.
        
        Handles various formats:
        - Pure JSON
        - JSON wrapped in markdown code blocks
        - JSON with surrounding text
        
        Args:
            response: Response text
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            OllamaJSONParseError: If JSON cannot be extracted
        """
        # Try parsing as-is first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try extracting from markdown code blocks
        lines = response.split("\n")
        json_start = -1
        json_end = -1
        in_code_block = False
        
        for i, line in enumerate(lines):
            if "```" in line:
                if in_code_block:
                    # End of code block
                    in_code_block = False
                    if json_start != -1:
                        json_end = i
                        break
                else:
                    # Start of code block
                    in_code_block = True
                    json_start = i + 1  # Start from next line after ```
            elif in_code_block and "{" in line and json_start == i + 1:
                # First line of code block with {
                json_start = i
        
        if json_start != -1 and json_end != -1:
            try:
                json_text = "\n".join(lines[json_start:json_end])
                return json.loads(json_text)
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse extracted JSON: {e}")
        
        # Try finding { } pairs outside code blocks
        for i in range(len(lines)):
            line = lines[i]
            if "{" in line:
                json_start = i
                for j in range(i, len(lines)):
                    if "}" in lines[j]:
                        json_end = j + 1
                        try:
                            json_text = "\n".join(lines[json_start:json_end])
                            return json.loads(json_text)
                        except json.JSONDecodeError:
                            pass
        
        raise OllamaJSONParseError(
            f"Unable to extract valid JSON from response. "
            f"Response: {response[:200]}..."
        )
    
    def embedding(self, text: str) -> list[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
            
        Raises:
            OllamaGenerationError: If embedding fails
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("embedding", [])
        except requests.RequestException as e:
            error_msg = f"Embedding generation failed: {e}"
            self.logger.error(error_msg)
            raise OllamaGenerationError(error_msg)
    
    def list_models(self) -> list[str]:
        """
        List available models on Ollama server.
        
        Returns:
            List of model names
            
        Raises:
            OllamaConnectionError: If server unavailable
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            response.raise_for_status()
            models = response.json().get("models", [])
            return [m.get("name") for m in models]
        except requests.RequestException as e:
            error_msg = f"Failed to list models: {e}"
            self.logger.error(error_msg)
            raise OllamaConnectionError(error_msg)


# Global client instance
_client: Optional[OllamaClient] = None


def get_ollama_client(
    base_url: str = "http://localhost:11434",
    model: str = "qwen2.5:7b-instruct",
) -> OllamaClient:
    """Get or create global Ollama client."""
    global _client
    if _client is None:
        _client = OllamaClient(base_url=base_url, model=model)
    return _client
