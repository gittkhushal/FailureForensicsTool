"""
Regression testing framework.

Provides:
- RegressionRunner: Re-executes evaluation cases
"""

import logging
import uuid
from typing import List
from datetime import datetime

from src.models.evaluation_models import (
    EvaluationCase, 
    RegressionResult, 
    AdaptiveRecommendation, 
    ImprovementReport
)
from src.feedback.adaptive_optimizer import AdaptiveOptimizer
from src.pipeline.runner import PipelineRunner
from src.pipeline.base import Pipeline
from src.pipeline.intake import IntakeStep
from src.pipeline.extraction import ExtractionStep
from src.pipeline.classification import ClassificationStep
from src.pipeline.summarization import SummarizationStep


logger = logging.getLogger(__name__)


class RegressionRunner:
    """Runs regression tests on evaluation cases and benchmarks self-improving adaptations."""
    
    def __init__(self):
        """Initialize runner."""
        self.logger = logging.getLogger(f"{__name__}")
        self.results: List[RegressionResult] = []
    
    def run(
        self, 
        cases: List[EvaluationCase],
        pipeline: Optional[Pipeline] = None,
    ) -> List[RegressionResult]:
        """
        Run regression on evaluation cases using specified or demo pipeline.
        
        Args:
            cases: Evaluation cases to run
            pipeline: Optional specific pipeline (defaults to standard demo pipeline)
            
        Returns:
            List of regression results
        """
        self.logger.info(f"Running regression on {len(cases)} cases")
        self.results = []
        
        # Use provided pipeline or create default demo pipeline
        active_pipeline = pipeline if pipeline is not None else self._create_pipeline()
        runner = PipelineRunner(pipeline=active_pipeline)
        
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
                    output=output,
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
                    output=None,
                    score=0.0,
                    passed=False,
                    executed_at=datetime.now(),
                    error=str(e),
                )
                self.results.append(result)
        
        return self.results
    
    def compare_runs(
        self,
        cases: List[EvaluationCase],
        adapted_pipeline: Optional[Pipeline] = None,
        recommendations: Optional[List[AdaptiveRecommendation]] = None,
    ) -> ImprovementReport:
        """
        Run baseline vs. adapted pipeline to quantify self-improving performance gain.
        
        Args:
            cases: Evaluation cases to evaluate
            adapted_pipeline: Optional pre-built adapted pipeline
            recommendations: Optional recommendations list
            
        Returns:
            ImprovementReport with comparative metrics
        """
        optimizer = AdaptiveOptimizer()
        
        if recommendations is None:
            recommendations = optimizer.generate_recommendations_from_cases(cases)
            
        if adapted_pipeline is None:
            adapted_pipeline = optimizer.build_adapted_pipeline(recommendations)
            
        # 1. Run baseline
        baseline_pipeline = self._create_pipeline()
        baseline_results = self.run(cases, pipeline=baseline_pipeline)
        
        # 2. Run adapted
        adapted_results = self.run(cases, pipeline=adapted_pipeline)
        
        total = len(cases)
        if total == 0:
            return ImprovementReport(
                report_id=str(uuid.uuid4()),
                recommendations_applied=recommendations,
            )
            
        base_passed = sum(1 for r in baseline_results if r.passed)
        adapt_passed = sum(1 for r in adapted_results if r.passed)
        base_avg_score = sum(r.score for r in baseline_results) / total
        adapt_avg_score = sum(r.score for r in adapted_results) / total
        
        cases_fixed = sum(
            1 for b, a in zip(baseline_results, adapted_results)
            if not b.passed and a.passed
        )
        
        detailed = []
        for i, (b, a) in enumerate(zip(baseline_results, adapted_results)):
            detailed.append({
                "case_id": cases[i].case_id,
                "failing_step": cases[i].failing_step,
                "failure_type": cases[i].failure_type,
                "baseline_score": b.score,
                "adapted_score": a.score,
                "score_delta": a.score - b.score,
                "baseline_passed": b.passed,
                "adapted_passed": a.passed,
                "fixed": not b.passed and a.passed,
            })
            
        report = ImprovementReport(
            report_id=str(uuid.uuid4()),
            total_cases_evaluated=total,
            baseline_pass_rate=base_passed / total,
            adapted_pass_rate=adapt_passed / total,
            pass_rate_gain=(adapt_passed - base_passed) / total,
            baseline_avg_score=base_avg_score,
            adapted_avg_score=adapt_avg_score,
            score_gain=adapt_avg_score - base_avg_score,
            cases_fixed=cases_fixed,
            recommendations_applied=recommendations,
            detailed_results=detailed,
        )
        
        self.logger.info(
            f"Comparison Complete: Pass Rate {report.baseline_pass_rate:.1%} -> "
            f"{report.adapted_pass_rate:.1%} (Gain: +{report.pass_rate_gain:.1%})"
        )
        return report
    
    def _create_pipeline(self) -> Pipeline:
        """Create standard demo pipeline."""
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
        
        # If both are dictionaries, calculate key + value overlap
        if isinstance(actual, dict) and isinstance(expected, dict):
            common_keys = set(actual.keys()) & set(expected.keys())
            if not expected:
                return 0.0
            key_score = len(common_keys) / len(expected)
            return min(1.0, max(0.0, key_score))
        
        # Convert to strings for comparison
        actual_str = str(actual).lower().strip()
        expected_str = str(expected).lower().strip()
        
        actual_words = set(actual_str.split())
        expected_words = set(expected_str.split())
        
        if not expected_words:
            return 0.0
        
        overlap = len(actual_words & expected_words)
        score = overlap / len(expected_words)
        
        return min(1.0, max(0.0, score))
    
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
