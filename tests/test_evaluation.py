"""Tests for LLM-as-Judge evaluation engine."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.evaluation.judge import Judge
from src.evaluation.evaluator import Evaluator
from src.evaluation.scoring import aggregate_scores, confidence_from_agreement
from src.models.evaluation_models import JudgeResult
from src.models.trace_models import Trace, Span, SpanStatus


class TestJudge:
    """Test Judge evaluation engine."""
    
    @patch('src.evaluation.judge.get_ollama_client')
    def test_judge_initialization(self, mock_client):
        """Test judge initialization."""
        judge = Judge(model="test-model")
        assert judge.model == "test-model"
    
    @patch('src.evaluation.judge.get_ollama_client')
    def test_judge_evaluate(self, mock_client):
        """Test evaluation of step output."""
        mock_llm = Mock()
        mock_llm.generate_json.return_value = {
            "overall_score": 0.85,
            "criteria_scores": {"accuracy": 0.9, "completeness": 0.8},
            "pass": True,
            "critical_issues": [],
            "reasoning": "Good output"
        }
        mock_client.return_value = mock_llm
        
        judge = Judge()
        result = judge.evaluate(
            step_name="extraction",
            step_type="extraction",
            input_data={"text": "input"},
            output_data={"entities": ["A", "B"]},
        )
        
        assert isinstance(result, JudgeResult)
        assert result.overall_score == 0.85
        assert result.passed is True
    
    @patch('src.evaluation.judge.get_ollama_client')
    def test_judge_evaluate_failure(self, mock_client):
        """Test evaluation returns default on LLM error."""
        mock_llm = Mock()
        mock_llm.generate_json.side_effect = Exception("LLM error")
        mock_client.return_value = mock_llm
        
        judge = Judge()
        result = judge.evaluate(
            step_name="extraction",
            step_type="extraction",
            input_data={},
            output_data={},
        )
        
        assert result.passed is False
        assert result.overall_score == 0.0


class TestEvaluator:
    """Test Evaluator orchestrator."""
    
    def test_evaluator_initialization(self):
        """Test evaluator initialization."""
        judge = Mock()
        evaluator = Evaluator(judge=judge)
        assert evaluator.judge == judge
    
    def test_evaluator_evaluate_trace(self):
        """Test evaluating a complete trace."""
        # Create mock judge
        judge = Mock()
        judge.evaluate.return_value = JudgeResult(
            span_id="",
            step_name="test",
            overall_score=0.8,
            passed=True,
            reasoning="Good",
        )
        
        evaluator = Evaluator(judge=judge)
        
        # Create trace
        trace = Trace(trace_id="t1", pipeline_name="test")
        trace.add_span(Span(
            span_id="s1",
            trace_id="t1",
            step_name="step1",
            step_index=0,
            output_data={"result": "output"}
        ))
        
        # Evaluate
        results = evaluator.evaluate_trace(trace)
        
        assert len(results) == 1
        assert results[0].overall_score == 0.8
        assert judge.evaluate.called
    
    def test_evaluator_overall_score(self):
        """Test calculating overall trace score."""
        judge = Mock()
        evaluator = Evaluator(judge=judge)
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        span1 = Span(span_id="s1", trace_id="t1", step_name="step1", step_index=0)
        span1.judge_score = 0.8
        span2 = Span(span_id="s2", trace_id="t1", step_name="step2", step_index=1)
        span2.judge_score = 0.9
        
        trace.add_span(span1)
        trace.add_span(span2)
        
        score = evaluator.get_overall_score(trace)
        assert abs(score - 0.85) < 0.01
    
    def test_evaluator_empty_trace(self):
        """Test handling empty trace."""
        judge = Mock()
        evaluator = Evaluator(judge=judge)
        
        trace = Trace(trace_id="t1", pipeline_name="test")
        score = evaluator.get_overall_score(trace)
        
        assert score == 1.0


class TestScoring:
    """Test scoring utilities."""
    
    def test_aggregate_scores_simple(self):
        """Test simple score aggregation."""
        scores = [0.8, 0.9, 0.7]
        result = aggregate_scores(scores)
        assert abs(result - 0.8) < 0.01
    
    def test_aggregate_scores_weighted(self):
        """Test weighted score aggregation."""
        scores = [0.8, 0.6]
        weights = [0.7, 0.3]
        result = aggregate_scores(scores, weights=weights)
        expected = 0.8 * 0.7 + 0.6 * 0.3
        assert abs(result - expected) < 0.01
    
    def test_confidence_from_agreement(self):
        """Test confidence calculation."""
        # High score, low variance = high confidence
        conf1 = confidence_from_agreement(0.9, variance=0.1)
        
        # High score, high variance = lower confidence
        conf2 = confidence_from_agreement(0.9, variance=0.5)
        
        assert conf1 > conf2
    
    def test_confidence_bounds(self):
        """Test confidence stays in bounds."""
        for score in [0.0, 0.5, 1.0]:
            for var in [0.0, 0.5, 1.0]:
                conf = confidence_from_agreement(score, variance=var)
                assert 0.0 <= conf <= 1.0


class TestIntegration:
    """Integration tests for evaluation system."""
    
    @patch('src.evaluation.judge.get_ollama_client')
    def test_full_evaluation_pipeline(self, mock_client):
        """Test complete evaluation workflow."""
        # Setup mock
        mock_llm = Mock()
        mock_llm.generate_json.side_effect = [
            {
                "overall_score": 0.85,
                "criteria_scores": {},
                "pass": True,
                "critical_issues": [],
                "reasoning": "Good"
            },
            {
                "overall_score": 0.75,
                "criteria_scores": {},
                "pass": True,
                "critical_issues": [],
                "reasoning": "OK"
            }
        ]
        mock_client.return_value = mock_llm
        
        # Create evaluator
        judge = Judge()
        evaluator = Evaluator(judge=judge)
        
        # Create trace
        trace = Trace(trace_id="t1", pipeline_name="test")
        trace.add_span(Span(
            span_id="s1",
            trace_id="t1",
            step_name="step1",
            step_index=0,
        ))
        trace.add_span(Span(
            span_id="s2",
            trace_id="t1",
            step_name="step2",
            step_index=1,
        ))
        
        # Evaluate
        results = evaluator.evaluate_trace(trace)
        
        assert len(results) == 2
        assert results[0].overall_score == 0.85
        assert results[1].overall_score == 0.75
        
        overall = evaluator.get_overall_score(trace)
        assert abs(overall - 0.8) < 0.01
