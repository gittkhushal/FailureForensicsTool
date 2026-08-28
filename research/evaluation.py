"""Research evaluation framework for FailureForensicsTool."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from src.models.trace_models import Trace
from src.evaluation.evaluator import Evaluator
from src.failure.detector import FailureDetector
from src.failure.classifier import FailureClassifier
from src.failure.propagation import PropagationAnalyzer
from src.failure.root_cause import RootCauseEngine


logger = logging.getLogger(__name__)


class ResearchEvaluator:
    """Conducts research evaluation of FailureForensicsTool."""
    
    def __init__(self, output_dir: str = "research/results"):
        """Initialize evaluator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = {}
        self.logger = logging.getLogger(f"{__name__}")
    
    def evaluate_trace(self, trace: Trace) -> Dict[str, Any]:
        """
        Evaluate a trace and collect metrics.
        
        Args:
            trace: Trace to evaluate
            
        Returns:
            Metrics dictionary
        """
        metrics = {
            "trace_id": trace.trace_id,
            "pipeline_name": trace.pipeline_name,
            "timestamp": datetime.now().isoformat(),
            "evaluation": {},
            "failure_detection": {},
            "propagation": {},
            "root_cause": {},
        }
        
        # Evaluation metrics
        evaluator = Evaluator()
        eval_results = evaluator.evaluate_trace(trace)
        
        metrics["evaluation"]["judge_results"] = len(eval_results)
        metrics["evaluation"]["avg_score"] = (
            sum(r.overall_score for r in eval_results) / len(eval_results)
            if eval_results else 0.0
        )
        metrics["evaluation"]["passed_count"] = sum(1 for r in eval_results if r.passed)
        
        # Failure detection metrics
        detector = FailureDetector(threshold=0.7)
        failures = detector.detect(trace)
        
        metrics["failure_detection"]["failures_detected"] = len(failures)
        metrics["failure_detection"]["failure_rate"] = (
            len(failures) / len(trace.spans) if trace.spans else 0.0
        )
        
        if failures:
            # Classify failures
            classifier = FailureClassifier()
            failures = classifier.classify_batch(failures, trace)
            
            failure_types = {}
            for failure in failures:
                ft = failure.failure_type.value
                failure_types[ft] = failure_types.get(ft, 0) + 1
            
            metrics["failure_detection"]["failure_types"] = failure_types
            
            # Propagation analysis for first failure
            analyzer = PropagationAnalyzer()
            prop_analysis = analyzer.analyze(failures[0], trace)
            
            metrics["propagation"]["propagation_score"] = prop_analysis.overall_propagation_score
            metrics["propagation"]["affected_spans"] = len(prop_analysis.affected_spans)
            metrics["propagation"]["propagation_paths"] = len(prop_analysis.paths)
            
            # Root cause analysis
            engine = RootCauseEngine()
            root_analysis = engine.analyze(failures[0], trace, prop_analysis)
            
            metrics["root_cause"]["confidence"] = root_analysis.root_cause_confidence
            metrics["root_cause"]["candidates_found"] = len(root_analysis.candidate_root_causes)
        
        # Performance metrics
        metrics["performance"] = {
            "total_latency_ms": trace.total_latency_ms,
            "span_count": len(trace.spans),
            "avg_span_latency_ms": (
                trace.total_latency_ms / len(trace.spans)
                if trace.spans else 0.0
            ),
        }
        
        return metrics
    
    def save_results(self, results: List[Dict[str, Any]]) -> Path:
        """
        Save evaluation results to file.
        
        Args:
            results: List of evaluation results
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"evaluation_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"Saved {len(results)} evaluation results to {output_file}")
        return output_file
    
    def generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics from results.
        
        Args:
            results: List of evaluation results
            
        Returns:
            Summary statistics
        """
        if not results:
            return {}
        
        summary = {
            "total_traces": len(results),
            "evaluation": {
                "avg_judge_score": (
                    sum(r["evaluation"]["avg_score"] for r in results) / len(results)
                ),
                "total_passed": sum(r["evaluation"]["passed_count"] for r in results),
            },
            "failure_detection": {
                "total_failures": sum(r["failure_detection"]["failures_detected"] for r in results),
                "avg_failure_rate": (
                    sum(r["failure_detection"]["failure_rate"] for r in results) / len(results)
                ),
            },
            "propagation": {
                "avg_propagation_score": (
                    sum(r["propagation"].get("propagation_score", 0.0) for r in results if r["propagation"]) 
                    / len([r for r in results if r["propagation"]]) 
                    if any(r["propagation"] for r in results) else 0.0
                ),
            },
            "root_cause": {
                "avg_confidence": (
                    sum(r["root_cause"].get("confidence", 0.0) for r in results if r["root_cause"]) 
                    / len([r for r in results if r["root_cause"]]) 
                    if any(r["root_cause"] for r in results) else 0.0
                ),
            },
            "performance": {
                "avg_total_latency_ms": (
                    sum(r["performance"]["total_latency_ms"] for r in results) / len(results)
                ),
                "avg_span_latency_ms": (
                    sum(r["performance"]["avg_span_latency_ms"] for r in results) / len(results)
                ),
            },
        }
        
        return summary
