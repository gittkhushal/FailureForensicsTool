"""
Regression testing framework.

Provides:
- RegressionRunner: Re-executes evaluation cases
"""

import logging
import uuid
from typing import List
from datetime import datetime

from src.models.evaluation_models import EvaluationCase, RegressionResult
from src.pipeline.runner import PipelineRunner
from src.pipeline.base import Pipeline
from src.pipeline.intake import IntakeStep
from src.pipeline.extraction import ExtractionStep
from src.pipeline.classification import ClassificationStep
from src.pipeline.summarization import SummarizationStep


logger = logging.getLogger(__name__)


class RegressionRunner:
    """Runs regression tests on evaluation cases."""
    
    def __init__(self):
        """Initialize runner."""
        self.logger = logging.getLogger(f"{__name__}")
        self.results: List[RegressionResult] = []
    
    def run(self, cases: List[EvaluationCase]) -> List[RegressionResult]:
        """
        Run regression on evaluation cases.
        
        Args:
            cases: Evaluation cases to run
            
        Returns:
            List of regression results
        """
        self.logger.info(f"Running regression on {len(cases)} cases")
        self.results = []
        
        # Create demo pipeline
        pipeline = self._create_pipeline()
        runner = PipelineRunner(pipeline=pipeline)
        
        for i, case in enumerate(cases):
            try:
                self.logger.debug(f"Running case {i+1}/{len(cases)}: {case.case_id}")
                
                # Execute pipeline on case input
                output, trace = runner.run(case.original_input)
                
                # Compare with expected output
                score = self._calculate_score(output, case.corrected_output)
                passed = score >= 0.7  # Pass if score >= threshold
                
                # Create result
                result = RegressionResult(
                    run_id=str(uuid.uuid4()),
                    case_id=case.case_id,
                    expected_output=case.corrected_output,
                    actual_output=output,
                    score=score,
                    passed=passed,
                    executed_at=datetime.now(),
                )
                
                self.results.append(result)
                self.logger.info(
                    f"Case {i+1}: {'PASS' if passed else 'FAIL'} "
                    f"(score={score:.2f})"
                )
                
            except Exception as e:
                self.logger.error(f"Case {case.case_id} failed: {e}")
                result = RegressionResult(
                    run_id=str(uuid.uuid4()),
                    case_id=case.case_id,
                    expected_output=case.corrected_output,
                    actual_output=None,
                    score=0.0,
                    passed=False,
                    executed_at=datetime.now(),
                    error=str(e),
                )
                self.results.append(result)
        
        return self.results
    
    def _create_pipeline(self) -> Pipeline:
        """Create demo pipeline."""
        pipeline = Pipeline(name="regression_pipeline")
        pipeline.add_step(IntakeStep())
        pipeline.add_step(ExtractionStep())
        pipeline.add_step(ClassificationStep())
        pipeline.add_step(SummarizationStep())
        return pipeline
    
    def _calculate_score(self, actual: any, expected: any) -> float:
        """
        Calculate similarity score between actual and expected output.
        
        Args:
            actual: Actual output
            expected: Expected output
            
        Returns:
            Score (0-1)
        """
        if not actual or not expected:
            return 0.0
        
        # Convert to strings for comparison
        actual_str = str(actual).lower().strip()
        expected_str = str(expected).lower().strip()
        
        # Simple string similarity (word overlap)
        actual_words = set(actual_str.split())
        expected_words = set(expected_str.split())
        
        if not expected_words:
            return 0.0
        
        overlap = len(actual_words & expected_words)
        score = overlap / len(expected_words)
        
        return min(1.0, score)
    
    def get_summary(self) -> dict:
        """
        Get regression summary statistics.
        
        Returns:
            Summary dict
        """
        if not self.results:
            return {
                "total_runs": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0.0,
                "average_score": 0.0,
            }
        
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        avg_score = sum(r.score for r in self.results) / len(self.results)
        
        return {
            "total_runs": len(self.results),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(self.results),
            "average_score": avg_score,
        }
