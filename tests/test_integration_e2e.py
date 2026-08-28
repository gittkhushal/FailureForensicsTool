"""End-to-end integration tests for complete workflows."""

import pytest
from unittest.mock import Mock, patch

from src.pipeline.runner import PipelineRunner
from src.tracing.instrumentation import TraceContext
from src.evaluation.judge import Judge
from src.evaluation.evaluator import Evaluator
from src.failure.detector import FailureDetector
from src.failure.classifier import FailureClassifier
from src.failure.propagation import PropagationAnalyzer
from src.failure.root_cause import RootCauseEngine
from src.storage.database import Database
from src.storage.repositories import TraceRepository, FailureRepository


class TestCompleteWorkflow:
    """Test complete end-to-end workflows."""
    
    def test_storage_workflow(self):
        """Test trace storage and retrieval workflow."""
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = Database(db_path)
            
            # Create and save trace
            from src.models.trace_models import Trace, Span
            
            trace = Trace(trace_id="t1", pipeline_name="test")
            span = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
            span.judge_score = 0.8
            trace.add_span(span)
            
            repo = TraceRepository(db)
            repo.save(trace)
            
            # Retrieve and verify
            retrieved = repo.get("t1")
            assert retrieved is not None
            assert retrieved.trace_id == "t1"
            assert len(retrieved.spans) == 1
            
            # Store failures
            from src.models.failure_models import Failure, FailureType
            
            failure = Failure(
                failure_id="f1",
                trace_id="t1",
                span_id="s1",
                step_name="step1",
                failure_type=FailureType.EXTRACTION_HALLUCINATION,
            )
            
            failure_repo = FailureRepository(db)
            failure_repo.save(failure)
            
            # Retrieve failures
            failures = failure_repo.list_by_trace("t1")
            assert len(failures) == 1
            assert failures[0].failure_type == FailureType.EXTRACTION_HALLUCINATION
    
    def test_multi_trace_analysis(self):
        """Test analyzing multiple traces."""
        import tempfile
        import os
        
        from src.models.trace_models import Trace, Span
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = Database(db_path)
            repo = TraceRepository(db)
            
            # Create and save multiple traces
            traces = []
            for i in range(3):
                trace = Trace(trace_id=f"t{i}", pipeline_name="test")
                for j in range(2):
                    span = Span(
                        span_id=f"s{i}_{j}",
                        trace_id=f"t{i}",
                        step_name=f"step{j}",
                        step_index=j
                    )
                    span.judge_score = 0.9 - (i * 0.1)
                    trace.add_span(span)
                
                repo.save(trace)
                traces.append(trace)
            
            # Retrieve all
            all_traces = repo.list_all(limit=10)
            assert len(all_traces) >= 3
            
            # Analyze each
            for trace in all_traces[:3]:
                assert len(trace.spans) == 2


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON responses."""
        from unittest.mock import Mock, patch
        
        with patch('src.evaluation.judge.get_ollama_client') as mock_client:
            mock_llm = Mock()
            mock_llm.generate_json.side_effect = ValueError("Invalid JSON")
            mock_client.return_value = mock_llm
            
            judge = Judge()
            result = judge.evaluate(
                step_name="test",
                step_type="test",
                input_data={},
                output_data={},
            )
            
            # Should return default result on error
            assert result.passed is False
            assert result.overall_score == 0.0
    
    def test_empty_trace_handling(self):
        """Test handling empty traces."""
        from src.models.trace_models import Trace
        
        trace = Trace(trace_id="t_empty", pipeline_name="test")
        
        # Should handle empty trace
        assert len(trace.spans) == 0
        
        # Get statistics
        stats = trace.get_statistics()
        assert stats is not None


class TestScalability:
    """Test system scalability."""
    
    def test_large_trace_handling(self):
        """Test handling large traces with many spans."""
        from src.models.trace_models import Trace, Span
        
        trace = Trace(trace_id="t_large", pipeline_name="test")
        
        # Create 100 spans
        for i in range(100):
            span = Span(
                span_id=f"s_{i}",
                trace_id="t_large",
                step_name=f"step_{i}",
                step_index=i
            )
            span.judge_score = 0.8
            trace.add_span(span)
        
        # Should handle without issues
        assert len(trace.spans) == 100
        
        # Get statistics
        stats = trace.get_statistics()
        assert stats is not None
    
    def test_failure_batch_processing(self):
        """Test processing many failures."""
        from src.models.trace_models import Trace, Span
        from src.models.failure_models import Failure, FailureType
        from src.failure.classifier import FailureClassifier
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        
        # Create spans
        for i in range(10):
            span = Span(
                span_id=f"s{i}",
                trace_id="t1",
                step_name=f"step{i}",
                step_index=i
            )
            trace.add_span(span)
        
        # Create failures
        failures = []
        for i in range(5):
            failure = Failure(
                failure_id=f"f{i}",
                trace_id="t1",
                span_id=f"s{i}",
                step_name=f"step{i}",
                failure_type=FailureType.UNKNOWN,
            )
            failures.append(failure)
        
        # Classify all
        classifier = FailureClassifier()
        classified = classifier.classify_batch(failures, trace)
        
        assert len(classified) == 5
        assert all(f.failure_type is not None for f in classified)


class TestDataIntegrity:
    """Test data integrity across operations."""
    
    def test_trace_serialization_roundtrip(self):
        """Test trace can be serialized and deserialized."""
        from src.models.trace_models import Trace, Span, TraceStatus
        
        # Create trace
        trace = Trace(
            trace_id="t1",
            pipeline_name="test",
            status=TraceStatus.SUCCESS,
            final_score=0.85,
            total_latency_ms=1000.0
        )
        
        span = Span(
            span_id="s1",
            trace_id="t1",
            step_name="step1",
            step_index=0,
            input_data={"key": "value"},
            output_data={"result": "output"},
            judge_score=0.9
        )
        trace.add_span(span)
        
        # Serialize
        data = trace.model_dump(mode='json')
        
        # Deserialize
        restored = Trace(**data)
        
        # Verify
        assert restored.trace_id == "t1"
        assert restored.final_score == 0.85
        assert len(restored.spans) == 1
    
    def test_failure_serialization(self):
        """Test failure serialization."""
        from src.models.failure_models import Failure, FailureType
        
        failure = Failure(
            failure_id="f1",
            trace_id="t1",
            span_id="s1",
            step_name="step1",
            failure_type=FailureType.EXTRACTION_HALLUCINATION,
            severity=0.7,
            description="Test failure",
            evidence={"key": "value"}
        )
        
        # Serialize
        data = failure.model_dump(mode='json')
        
        # Deserialize
        restored = Failure(**data)
        
        # Verify
        assert restored.failure_id == "f1"
        assert restored.failure_type == FailureType.EXTRACTION_HALLUCINATION
