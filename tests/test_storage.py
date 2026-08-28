"""Tests for SQLite storage layer."""

import pytest
import tempfile
import os
from pathlib import Path

from src.storage.database import Database
from src.storage.repositories import TraceRepository, FailureRepository, EvaluationRepository
from src.models.trace_models import Trace, Span, TraceStatus, SpanStatus
from src.models.failure_models import Failure, FailureType
from src.models.evaluation_models import EvaluationCase, RegressionResult


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)
        yield db


class TestTraceRepository:
    """Test trace repository operations."""
    
    def test_save_and_get_trace(self, temp_db):
        """Test saving and retrieving trace."""
        repo = TraceRepository(temp_db)
        
        # Create trace
        trace = Trace(trace_id="t1", pipeline_name="test")
        trace.add_span(Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0))
        
        # Save
        repo.save(trace)
        
        # Retrieve
        retrieved = repo.get("t1")
        assert retrieved is not None
        assert retrieved.trace_id == "t1"
        assert len(retrieved.spans) == 1
    
    def test_list_traces(self, temp_db):
        """Test listing traces."""
        repo = TraceRepository(temp_db)
        
        for i in range(3):
            trace = Trace(trace_id=f"t{i}", pipeline_name="test")
            repo.save(trace)
        
        traces = repo.list_all(limit=10)
        assert len(traces) >= 3
    
    def test_delete_trace(self, temp_db):
        """Test deleting trace."""
        repo = TraceRepository(temp_db)
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        repo.save(trace)
        assert repo.get("t1") is not None
        
        repo.delete("t1")
        assert repo.get("t1") is None


class TestFailureRepository:
    """Test failure repository operations."""
    
    def test_save_and_get_failure(self, temp_db):
        """Test saving and retrieving failure."""
        repo = FailureRepository(temp_db)
        
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s1",
            step_name="step1",
            failure_type=FailureType.EXTRACTION_HALLUCINATION,
            description="Test failure"
        )
        
        repo.save(failure)
        retrieved = repo.get("f1")
        assert retrieved is not None
        assert retrieved.failure_id == "f1"
    
    def test_list_failures_by_trace(self, temp_db):
        """Test listing failures by trace."""
        repo = FailureRepository(temp_db)
        
        for i in range(2):
            failure = Failure(
                failure_id=f"f{i}",
                trace_id="t1",
                span_id=f"s{i}",
                step_name="step",
                failure_type=FailureType.UNKNOWN,
            )
            repo.save(failure)
        
        failures = repo.list_by_trace("t1")
        assert len(failures) >= 2


class TestEvaluationRepository:
    """Test evaluation repository operations."""
    
    def test_save_and_get_case(self, temp_db):
        """Test saving and retrieving evaluation case."""
        repo = EvaluationRepository(temp_db)
        
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
        
        repo.save_case(case)
        retrieved = repo.get_case("c1")
        assert retrieved is not None
        assert retrieved.case_id == "c1"
    
    def test_save_regression_result(self, temp_db):
        """Test saving regression result."""
        repo = EvaluationRepository(temp_db)
        
        result = RegressionResult(
            run_id="r1",
            case_id="c1",
            passed=True,
            score=0.95,
        )
        
        repo.save_regression_result(result)
        # Verify it saved without error


class TestDatabaseSchema:
    """Test database schema initialization."""
    
    def test_database_initialization(self, temp_db):
        """Test database is properly initialized."""
        # Database is initialized in fixture
        # Verify tables exist by attempting operations
        repo = TraceRepository(temp_db)
        traces = repo.list_all()
        assert isinstance(traces, list)
