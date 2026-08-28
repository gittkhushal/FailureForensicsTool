"""
Tests for pipeline framework and steps.

Tests pipeline creation, step execution, and end-to-end pipeline execution.
"""

import pytest
from unittest.mock import Mock, patch

from src.models import StepInput, StepOutput, TraceStatus
from src.pipeline import (
    Pipeline, PipelineStep, PipelineRunner,
    IntakeStep, ExtractionStep, ClassificationStep, SummarizationStep
)


class TestPipelineStep:
    """Test base PipelineStep class."""
    
    def test_step_creation(self):
        """Test creating a pipeline step."""
        step = IntakeStep()
        
        assert step.name == "intake"
        assert step.description != ""
    
    def test_step_input_validation(self):
        """Test step input validation."""
        step = IntakeStep()
        
        # Valid input
        assert step.validate_input(StepInput(data="test")) is True
    
    def test_step_output_validation(self):
        """Test step output validation."""
        step = IntakeStep()
        
        # Valid output
        output = StepOutput(data={"key": "value"})
        assert step.validate_output(output) is True


class TestPipeline:
    """Test Pipeline class."""
    
    def test_pipeline_creation(self):
        """Test creating a pipeline."""
        pipeline = Pipeline(name="test_pipeline")
        
        assert pipeline.name == "test_pipeline"
        assert len(pipeline.steps) == 0
    
    def test_add_step(self):
        """Test adding steps to pipeline."""
        pipeline = Pipeline()
        step = IntakeStep()
        
        pipeline.add_step(step)
        
        assert len(pipeline.steps) == 1
        assert pipeline.steps["intake"] == step
    
    def test_add_multiple_steps(self):
        """Test adding multiple steps."""
        pipeline = Pipeline()
        
        pipeline.add_step(IntakeStep())
        pipeline.add_step(ExtractionStep())
        pipeline.add_step(ClassificationStep())
        
        assert len(pipeline.steps) == 3
        assert "intake" in pipeline.steps
        assert "extraction" in pipeline.steps
        assert "classification" in pipeline.steps
    
    def test_duplicate_step_fails(self):
        """Test that duplicate steps are rejected."""
        pipeline = Pipeline()
        
        pipeline.add_step(IntakeStep())
        
        with pytest.raises(ValueError):
            pipeline.add_step(IntakeStep())  # Same step name


class TestIntakeStep:
    """Test Intake step."""
    
    def test_intake_with_string_input(self):
        """Test intake with string input."""
        step = IntakeStep()
        step_input = StepInput(data="Test document content")
        
        output = step.execute(step_input)
        
        assert output.confidence > 0
        assert isinstance(output.data, dict)
        assert "document" in output.data
        assert output.data["document"] == "Test document content"
    
    def test_intake_with_dict_input(self):
        """Test intake with dict input."""
        step = IntakeStep()
        step_input = StepInput(data={"document": "Test document", "source": "test"})
        
        output = step.execute(step_input)
        
        assert output.data["document"] == "Test document"
    
    def test_intake_empty_input_fails(self):
        """Test intake fails with empty input."""
        step = IntakeStep()
        step_input = StepInput(data="")
        
        with pytest.raises(ValueError):
            step.execute(step_input)
    
    def test_intake_truncates_long_input(self):
        """Test intake truncates very long input."""
        step = IntakeStep()
        long_text = "x" * 200000  # 200K chars
        step_input = StepInput(data=long_text)
        
        output = step.execute(step_input)
        
        assert len(output.data["document"]) <= 100000


class TestExtractionStep:
    """Test Extraction step."""
    
    def test_extraction_initialization(self):
        """Test extraction step can be created."""
        step = ExtractionStep()
        
        assert step.name == "extraction"
        assert step.llm is not None
    
    @patch('src.llm.ollama_client.OllamaClient.generate_json')
    def test_extraction_with_llm(self, mock_generate_json):
        """Test extraction with mocked LLM."""
        mock_generate_json.return_value = {
            "entities": [{"name": "Entity1", "type": "PERSON"}],
            "facts": ["Fact1", "Fact2"],
            "relationships": [],
            "assertions": ["Assertion1"],
            "confidence": 0.85,
        }
        
        step = ExtractionStep()
        intake_output = StepOutput(
            data={"document": "Test document"}
        )
        
        output = step.execute(StepInput(data=intake_output.data))
        
        assert "entities" in output.data
        assert "facts" in output.data
        assert output.confidence > 0


class TestClassificationStep:
    """Test Classification step."""
    
    def test_classification_initialization(self):
        """Test classification step can be created."""
        step = ClassificationStep()
        
        assert step.name == "classification"
        assert step.llm is not None
    
    @patch('src.llm.ollama_client.OllamaClient.generate_json')
    def test_classification_with_llm(self, mock_generate_json):
        """Test classification with mocked LLM."""
        mock_generate_json.return_value = {
            "type": "article",
            "category": "technology",
            "subcategories": ["AI", "ML"],
            "sentiment": "positive",
            "relevance_score": 0.9,
            "confidence": 0.88,
        }
        
        step = ClassificationStep()
        step_input = StepInput(data={"document": "AI article", "assertions": []})
        
        output = step.execute(step_input)
        
        assert output.data["type"] == "article"
        assert output.data["category"] == "technology"


class TestSummarizationStep:
    """Test Summarization step."""
    
    def test_summarization_initialization(self):
        """Test summarization step can be created."""
        step = SummarizationStep()
        
        assert step.name == "summarization"
        assert step.llm is not None
    
    @patch('src.llm.ollama_client.OllamaClient.generate_json')
    def test_summarization_with_llm(self, mock_generate_json):
        """Test summarization with mocked LLM."""
        mock_generate_json.return_value = {
            "executive_summary": "This is a summary",
            "key_findings": ["Finding1", "Finding2"],
            "conclusions": ["Conclusion1"],
            "action_items": ["Action1"],
            "completeness": 0.9,
        }
        
        step = SummarizationStep()
        step_input = StepInput(data={"document": "Long document text"})
        
        output = step.execute(step_input)
        
        assert "executive_summary" in output.data
        assert len(output.data["key_findings"]) > 0


class TestPipelineExecution:
    """Test end-to-end pipeline execution."""
    
    @patch('src.llm.ollama_client.OllamaClient.generate_json')
    def test_execute_full_pipeline(self, mock_generate_json):
        """Test executing complete pipeline."""
        # Mock LLM responses for extraction and classification
        mock_generate_json.side_effect = [
            # Extraction response
            {
                "entities": [{"name": "Test", "type": "ORG"}],
                "facts": ["Fact"],
                "relationships": [],
                "assertions": ["Test assertion"],
                "confidence": 0.8,
            },
            # Classification response
            {
                "type": "document",
                "category": "general",
                "subcategories": [],
                "sentiment": "neutral",
                "relevance_score": 0.7,
                "confidence": 0.8,
            },
            # Summarization response
            {
                "executive_summary": "Summary",
                "key_findings": ["Finding"],
                "conclusions": ["Conclusion"],
                "action_items": [],
                "completeness": 0.8,
            },
        ]
        
        # Create pipeline
        pipeline = Pipeline(name="demo_pipeline")
        pipeline.add_step(IntakeStep())
        pipeline.add_step(ExtractionStep())
        pipeline.add_step(ClassificationStep())
        pipeline.add_step(SummarizationStep())
        
        # Execute
        output, trace = pipeline.execute("Test document for processing")
        
        # Verify
        assert trace.status == TraceStatus.SUCCESS
        assert len(trace.spans) == 4
        assert trace.output_data is not None
        assert trace.total_latency_ms > 0


class TestPipelineRunner:
    """Test PipelineRunner."""
    
    @patch('src.llm.ollama_client.OllamaClient.generate_json')
    def test_runner_single_execution(self, mock_generate_json):
        """Test runner executing single input."""
        mock_generate_json.side_effect = [
            {"entities": [], "facts": [], "relationships": [], "assertions": [], "confidence": 0.8},
            {"type": "document", "category": "general", "subcategories": [], "sentiment": "neutral", "relevance_score": 0.7, "confidence": 0.8},
            {"executive_summary": "Summary", "key_findings": [], "conclusions": [], "action_items": [], "completeness": 0.8},
        ]
        
        pipeline = Pipeline()
        pipeline.add_step(IntakeStep())
        pipeline.add_step(ExtractionStep())
        pipeline.add_step(ClassificationStep())
        pipeline.add_step(SummarizationStep())
        
        runner = PipelineRunner(pipeline)
        output, trace = runner.run("Test input")
        
        assert trace is not None
        assert len(runner.execution_history) == 1
    
    @patch('src.llm.ollama_client.OllamaClient.generate_json')
    def test_runner_batch_execution(self, mock_generate_json):
        """Test runner executing batch of inputs."""
        # Mock responses for 2 documents * 3 steps = 6 calls
        mock_generate_json.side_effect = [
            {"entities": [], "facts": [], "relationships": [], "assertions": [], "confidence": 0.8},
            {"type": "document", "category": "general", "subcategories": [], "sentiment": "neutral", "relevance_score": 0.7, "confidence": 0.8},
            {"executive_summary": "Summary", "key_findings": [], "conclusions": [], "action_items": [], "completeness": 0.8},
        ] * 2
        
        pipeline = Pipeline()
        pipeline.add_step(IntakeStep())
        pipeline.add_step(ExtractionStep())
        pipeline.add_step(ClassificationStep())
        pipeline.add_step(SummarizationStep())
        
        runner = PipelineRunner(pipeline)
        results = runner.run_batch(["Input 1", "Input 2"])
        
        assert len(results) == 2
    
    def test_runner_statistics(self):
        """Test runner statistics calculation."""
        pipeline = Pipeline()
        pipeline.add_step(IntakeStep())
        
        runner = PipelineRunner(pipeline)
        
        # No executions yet
        stats = runner.get_statistics()
        assert stats == {}
