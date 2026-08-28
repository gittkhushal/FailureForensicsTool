"""
Tests for LLM integration (Ollama client).

Note: These tests use mocking since we don't want to require 
a running Ollama instance for basic unit tests.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from src.llm.ollama_client import (
    OllamaClient,
    OllamaException,
    OllamaConnectionError,
    OllamaGenerationError,
    OllamaJSONParseError,
)


class TestOllamaClient:
    """Test OllamaClient basic functionality."""
    
    def test_client_initialization(self):
        """Test client can be initialized."""
        client = OllamaClient(
            base_url="http://localhost:11434",
            model="qwen2.5:7b-instruct"
        )
        
        assert client.base_url == "http://localhost:11434"
        assert client.model == "qwen2.5:7b-instruct"
        assert client.timeout == 300
        assert client.max_retries == 3
    
    def test_client_initialization_with_custom_params(self):
        """Test client initialization with custom parameters."""
        client = OllamaClient(
            base_url="http://localhost:11434",
            model="custom-model",
            timeout=60,
            max_retries=5,
        )
        
        assert client.timeout == 60
        assert client.max_retries == 5


class TestOllamaHealthCheck:
    """Test Ollama health check functionality."""
    
    @patch('src.llm.ollama_client.requests.get')
    def test_health_check_server_unavailable(self, mock_get):
        """Test health check when server is unavailable."""
        import requests
        mock_get.side_effect = requests.ConnectionError("Connection refused")
        
        client = OllamaClient()
        health = client.health_check()
        
        assert health["server_available"] is False
        assert health["model_available"] is False
        assert len(health["errors"]) > 0
    
    @patch('src.llm.ollama_client.requests.get')
    def test_health_check_server_available_model_missing(self, mock_get):
        """Test health check when server is up but model is missing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2"},
                {"name": "mistral"},
            ]
        }
        mock_get.return_value = mock_response
        
        client = OllamaClient(model="qwen2.5:7b-instruct")
        health = client.health_check()
        
        assert health["server_available"] is True
        assert health["model_available"] is False
        assert "qwen2.5" not in str(health["available_models"])


class TestOllamaGeneration:
    """Test text generation functionality."""
    
    @patch('src.llm.ollama_client.OllamaClient._is_available')
    @patch('src.llm.ollama_client.requests.post')
    def test_generate_success(self, mock_post, mock_available):
        """Test successful text generation."""
        mock_available.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "This is generated text."
        }
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        result = client.generate("Test prompt")
        
        assert result == "This is generated text."
        assert mock_post.called
    
    @patch('src.llm.ollama_client.OllamaClient._is_available')
    def test_generate_server_unavailable(self, mock_available):
        """Test generation when server is unavailable."""
        mock_available.return_value = False
        
        client = OllamaClient()
        
        with pytest.raises(OllamaConnectionError):
            client.generate("Test prompt")
    
    @patch('src.llm.ollama_client.OllamaClient._is_available')
    @patch('src.llm.ollama_client.requests.post')
    def test_generate_empty_response(self, mock_post, mock_available):
        """Test generation with empty response."""
        mock_available.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": ""}
        mock_post.return_value = mock_response
        
        client = OllamaClient(max_retries=1)
        
        with pytest.raises(OllamaGenerationError):
            client.generate("Test prompt")


class TestJSONGeneration:
    """Test JSON generation functionality."""
    
    def test_extract_json_pure_json(self):
        """Test extracting pure JSON."""
        response = '{"key": "value", "number": 42}'
        
        client = OllamaClient()
        result = client._extract_json(response)
        
        assert result["key"] == "value"
        assert result["number"] == 42
    
    def test_extract_json_markdown_wrapped(self):
        """Test extracting JSON from markdown code block."""
        response = '''Here is the JSON response:
```json
{
    "key": "value",
    "nested": {
        "item": "data"
    }
}
```
That's the response!'''
        
        client = OllamaClient()
        result = client._extract_json(response)
        
        assert result["key"] == "value"
        assert result["nested"]["item"] == "data"
    
    def test_extract_json_with_surrounding_text(self):
        """Test extracting JSON with surrounding text."""
        response = '''The analysis shows:
{
    "correctness": 0.9,
    "hallucination": 0.1,
    "completeness": 0.85
}
This is the evaluation result.'''
        
        client = OllamaClient()
        result = client._extract_json(response)
        
        assert result["correctness"] == 0.9
        assert result["hallucination"] == 0.1
    
    def test_extract_json_invalid(self):
        """Test extracting invalid JSON."""
        response = "This is just text with no JSON."
        
        client = OllamaClient()
        
        with pytest.raises(OllamaJSONParseError):
            client._extract_json(response)
    
    @patch('src.llm.ollama_client.OllamaClient.generate')
    def test_generate_json_success(self, mock_generate):
        """Test successful JSON generation."""
        json_response = '{"status": "success", "score": 0.95}'
        mock_generate.return_value = json_response
        
        client = OllamaClient()
        result = client.generate_json("Generate JSON")
        
        assert result["status"] == "success"
        assert result["score"] == 0.95
    
    @patch('src.llm.ollama_client.OllamaClient.generate')
    def test_generate_json_with_retries(self, mock_generate):
        """Test JSON generation with fallback to extraction."""
        # First attempt: markdown wrapped
        # Second attempt: pure JSON (if first fails)
        markdown_response = '''```json
{"status": "success"}
```'''
        mock_generate.return_value = markdown_response
        
        client = OllamaClient()
        result = client.generate_json("Generate JSON")
        
        assert result["status"] == "success"


class TestPrompts:
    """Test prompt templates."""
    
    def test_import_prompts(self):
        """Test prompt templates can be imported."""
        from src.llm.prompts import PROMPTS, get_prompt, format_prompt
        
        assert "extraction" in PROMPTS
        assert "classification" in PROMPTS
        assert "summarization" in PROMPTS
        assert "judge" in PROMPTS
    
    def test_get_prompt(self):
        """Test getting a prompt template."""
        from src.llm.prompts import get_prompt
        
        extraction_prompt = get_prompt("extraction")
        assert isinstance(extraction_prompt, str)
        assert len(extraction_prompt) > 0
    
    def test_get_invalid_prompt(self):
        """Test getting invalid prompt type."""
        from src.llm.prompts import get_prompt
        
        with pytest.raises(ValueError):
            get_prompt("nonexistent")
    
    def test_format_prompt(self):
        """Test formatting prompt with variables."""
        from src.llm.prompts import format_prompt
        
        formatted = format_prompt(
            "extraction",
            document="Sample document text"
        )
        
        assert isinstance(formatted, str)
        assert "Sample document text" in formatted
    
    def test_judge_prompt_content(self):
        """Test judge prompt has required evaluation criteria."""
        from src.llm.prompts import get_prompt
        
        judge_prompt = get_prompt("judge")
        
        # Check for evaluation criteria
        assert "correctness" in judge_prompt.lower()
        assert "hallucination" in judge_prompt.lower()
        assert "completeness" in judge_prompt.lower()
        assert "consistency" in judge_prompt.lower()


class TestOllamaExceptions:
    """Test custom exceptions."""
    
    def test_ollama_exception(self):
        """Test OllamaException."""
        exc = OllamaException("Test error")
        assert str(exc) == "Test error"
    
    def test_connection_error_is_ollama_exception(self):
        """Test OllamaConnectionError is an OllamaException."""
        exc = OllamaConnectionError("Connection failed")
        assert isinstance(exc, OllamaException)
    
    def test_generation_error_is_ollama_exception(self):
        """Test OllamaGenerationError is an OllamaException."""
        exc = OllamaGenerationError("Generation failed")
        assert isinstance(exc, OllamaException)
    
    def test_json_parse_error_is_ollama_exception(self):
        """Test OllamaJSONParseError is an OllamaException."""
        exc = OllamaJSONParseError("JSON parse failed")
        assert isinstance(exc, OllamaException)


class TestGlobalClient:
    """Test global client instance."""
    
    def test_get_global_client(self):
        """Test getting global Ollama client."""
        from src.llm.ollama_client import get_ollama_client
        
        client1 = get_ollama_client()
        client2 = get_ollama_client()
        
        # Should return same instance
        assert client1 is client2
    
    def test_get_global_client_with_params(self):
        """Test global client with custom parameters."""
        from src.llm.ollama_client import get_ollama_client
        
        # Reset global client
        import src.llm.ollama_client as ollama_module
        ollama_module._client = None
        
        client = get_ollama_client(
            base_url="http://custom:11434",
            model="custom-model"
        )
        
        assert client.base_url == "http://custom:11434"
        assert client.model == "custom-model"


class TestListModels:
    """Test model listing functionality."""
    
    @patch('src.llm.ollama_client.requests.get')
    def test_list_models_success(self, mock_get):
        """Test listing available models."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2"},
                {"name": "qwen2.5:7b-instruct"},
                {"name": "mistral"},
            ]
        }
        mock_get.return_value = mock_response
        
        client = OllamaClient()
        models = client.list_models()
        
        assert len(models) == 3
        assert "llama2" in models
        assert "qwen2.5:7b-instruct" in models
    
    @patch('src.llm.ollama_client.requests.get')
    def test_list_models_connection_error(self, mock_get):
        """Test listing models with connection error."""
        import requests
        mock_get.side_effect = requests.ConnectionError("Connection refused")
        
        client = OllamaClient()
        
        with pytest.raises(OllamaConnectionError):
            client.list_models()
