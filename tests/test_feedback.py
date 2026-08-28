"""Tests for feedback loop and regression testing."""

import pytest
import tempfile
import json
from pathlib import Path

from src.feedback.dataset import EvaluationDataset
from src.feedback.regression import RegressionRunner
from src.models.evaluation_models import EvaluationCase, RegressionResult


class TestEvaluationDataset:
    """Test evaluation dataset management."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for datasets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_dataset_initialization(self, temp_dir):
        """Test dataset initialization."""
        dataset = EvaluationDataset(dataset_dir=temp_dir)
        assert dataset.dataset_dir.exists()
        assert len(dataset.cases) == 0
    
    def test_add_case(self, temp_dir):
        """Test adding evaluation case."""
        dataset = EvaluationDataset(dataset_dir=temp_dir)
        
        case = EvaluationCase(
            case_id="c1",
            trace_id="t1",
            original_input={"text": "input"},
            failing_step="extraction",
            incorrect_output={"result": "wrong"},
            corrected_output={"result": "correct"},
            failure_type="hallucination",
            root_cause_step="extraction",
        )
        
        dataset.add_case(case)
        assert len(dataset.cases) == 1
        assert dataset.cases[0].case_id == "c1"
    
    def test_add_multiple_cases(self, temp_dir):
        """Test adding multiple cases."""
        dataset = EvaluationDataset(dataset_dir=temp_dir)
        
        for i in range(3):
            case = EvaluationCase(
                case_id=f"c{i}",
                trace_id=f"t{i}",
                original_input={"text": f"input{i}"},
                failing_step="extraction",
                incorrect_output={"result": f"wrong{i}"},
                corrected_output={"result": f"correct{i}"},
                failure_type="hallucination",
                root_cause_step="extraction",
            )
            dataset.add_case(case)
        
        assert len(dataset.cases) == 3
    
    def test_save_dataset(self, temp_dir):
        """Test saving dataset to file."""
        dataset = EvaluationDataset(dataset_dir=temp_dir)
        
        case = EvaluationCase(
            case_id="c1",
            trace_id="t1",
            original_input={"text": "input"},
            failing_step="extraction",
            incorrect_output={"result": "wrong"},
            corrected_output={"result": "correct"},
            failure_type="hallucination",
            root_cause_step="extraction",
        )
        dataset.add_case(case)
        
        file_path = dataset.save()
        
        assert file_path.exists()
        assert file_path.name == "evaluation_cases.json"
    
    def test_save_and_load(self, temp_dir):
        """Test saving and loading dataset."""
        dataset1 = EvaluationDataset(dataset_dir=temp_dir)
        
        for i in range(2):
            case = EvaluationCase(
                case_id=f"c{i}",
                trace_id=f"t{i}",
                original_input={"text": f"input{i}"},
                failing_step="extraction",
                incorrect_output={"result": f"wrong{i}"},
                corrected_output={"result": f"correct{i}"},
                failure_type="hallucination",
                root_cause_step="extraction",
            )
            dataset1.add_case(case)
        
        dataset1.save()
        
        # Load into new dataset
        dataset2 = EvaluationDataset(dataset_dir=temp_dir)
        dataset2.load()
        
        assert len(dataset2.cases) == 2
        assert dataset2.cases[0].case_id == "c0"
    
    def test_load_nonexistent_file(self, temp_dir):
        """Test loading when no file exists."""
        dataset = EvaluationDataset(dataset_dir=temp_dir)
        
        # Should not raise error
        dataset.load()
        assert len(dataset.cases) == 0
    
    def test_save_preserves_data(self, temp_dir):
        """Test that saved data can be reloaded correctly."""
        dataset1 = EvaluationDataset(dataset_dir=temp_dir)
        
        original_case = EvaluationCase(
            case_id="c1",
            trace_id="t1",
            original_input={"text": "test input", "tokens": 100},
            failing_step="classification",
            incorrect_output={"class": "A", "confidence": 0.3},
            corrected_output={"class": "B", "confidence": 0.9},
            failure_type="misclassification",
            root_cause_step="extraction",
        )
        dataset1.add_case(original_case)
        dataset1.save()
        
        # Reload
        dataset2 = EvaluationDataset(dataset_dir=temp_dir)
        dataset2.load()
        
        loaded_case = dataset2.cases[0]
        assert loaded_case.case_id == "c1"
        assert loaded_case.original_input["text"] == "test input"
        assert loaded_case.failure_type == "misclassification"


class TestRegressionRunner:
    """Test regression testing framework."""
    
    def test_runner_initialization(self):
        """Test regression runner initialization."""
        runner = RegressionRunner()
        assert len(runner.results) == 0
    
    def test_run_empty_cases(self):
        """Test running with no cases."""
        runner = RegressionRunner()
        results = runner.run([])
        
        assert len(results) == 0
    
    def test_run_single_case(self):
        """Test running single regression case."""
        runner = RegressionRunner()
        
        case = EvaluationCase(
            case_id="c1",
            trace_id="t1",
            original_input={"text": "input"},
            failing_step="extraction",
            incorrect_output={"result": "wrong"},
            corrected_output={"result": "correct"},
            failure_type="hallucination",
            root_cause_step="extraction",
        )
        
        results = runner.run([case])
        
        # Should handle gracefully (framework extensible)
        assert isinstance(results, list)
    
    def test_run_multiple_cases(self):
        """Test running multiple regression cases."""
        runner = RegressionRunner()
        
        cases = []
        for i in range(3):
            case = EvaluationCase(
                case_id=f"c{i}",
                trace_id=f"t{i}",
                original_input={"text": f"input{i}"},
                failing_step="extraction",
                incorrect_output={"result": f"wrong{i}"},
                corrected_output={"result": f"correct{i}"},
                failure_type="hallucination",
                root_cause_step="extraction",
            )
            cases.append(case)
        
        results = runner.run(cases)
        
        assert isinstance(results, list)


class TestIntegration:
    """Integration tests for feedback loop."""
    
    def test_full_feedback_workflow(self):
        """Test complete feedback workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and populate dataset
            dataset = EvaluationDataset(dataset_dir=tmpdir)
            
            cases = []
            for i in range(2):
                case = EvaluationCase(
                    case_id=f"c{i}",
                    trace_id=f"t{i}",
                    original_input={"text": f"input{i}"},
                    failing_step="extraction",
                    incorrect_output={"result": f"wrong{i}"},
                    corrected_output={"result": f"correct{i}"},
                    failure_type="hallucination",
                    root_cause_step="extraction",
                )
                cases.append(case)
                dataset.add_case(case)
            
            # Save dataset
            saved_path = dataset.save()
            assert saved_path.exists()
            
            # Run regression tests
            runner = RegressionRunner()
            results = runner.run(cases)
            
            # Results should be list
            assert isinstance(results, list)
            
            # Verify dataset persistence
            dataset2 = EvaluationDataset(dataset_dir=tmpdir)
            dataset2.load()
            assert len(dataset2.cases) == 2


class TestRegressionResult:
    """Test regression result creation and tracking."""
    
    def test_result_creation(self):
        """Test creating regression result."""
        result = RegressionResult(
            run_id="r1",
            case_id="c1",
            passed=True,
            score=0.95,
        )
        
        assert result.run_id == "r1"
        assert result.passed is True
        assert result.score == 0.95
    
    def test_result_failed(self):
        """Test failed regression result."""
        result = RegressionResult(
            run_id="r1",
            case_id="c1",
            passed=False,
            score=0.3,
        )
        
        assert result.passed is False
        assert result.score == 0.3
