"""Run research evaluation of FailureForensicsTool."""

import sys
import json
import logging
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from research.evaluation import ResearchEvaluator
from research.test_cases import get_test_cases, get_test_case_descriptions


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run research evaluation."""
    logger.info("Starting FailureForensicsTool Research Evaluation")
    logger.info("=" * 60)
    
    # Initialize evaluator
    evaluator = ResearchEvaluator()
    
    # Get test cases
    test_cases = get_test_cases()
    descriptions = get_test_case_descriptions()
    
    logger.info(f"Evaluating {len(test_cases)} test cases...")
    logger.info("-" * 60)
    
    # Evaluate each test case
    results = []
    for trace in test_cases:
        logger.info(f"\nEvaluating: {descriptions[trace.trace_id]}")
        
        try:
            metrics = evaluator.evaluate_trace(trace)
            results.append(metrics)
            
            # Print metrics
            logger.info(f"  Judge Score: {metrics['evaluation']['avg_score']:.2f}")
            logger.info(f"  Failures Detected: {metrics['failure_detection']['failures_detected']}")
            logger.info(f"  Failure Rate: {metrics['failure_detection']['failure_rate']:.2%}")
            
            if metrics['propagation']:
                logger.info(f"  Propagation Score: {metrics['propagation']['propagation_score']:.2f}")
            
            if metrics['root_cause']:
                logger.info(f"  Root Cause Confidence: {metrics['root_cause']['confidence']:.2f}")
            
        except Exception as e:
            logger.error(f"Error evaluating {trace.trace_id}: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Generating Summary Statistics...")
    logger.info("-" * 60)
    
    # Generate summary
    summary = evaluator.generate_summary(results)
    
    logger.info("\nSummary Statistics:")
    logger.info(f"  Total Traces: {summary['total_traces']}")
    logger.info(f"  Avg Judge Score: {summary['evaluation']['avg_judge_score']:.2f}")
    logger.info(f"  Total Failures Detected: {summary['failure_detection']['total_failures']}")
    logger.info(f"  Avg Failure Rate: {summary['failure_detection']['avg_failure_rate']:.2%}")
    logger.info(f"  Avg Propagation Score: {summary['propagation']['avg_propagation_score']:.2f}")
    logger.info(f"  Avg Root Cause Confidence: {summary['root_cause']['avg_confidence']:.2f}")
    logger.info(f"  Avg Total Latency: {summary['performance']['avg_total_latency_ms']:.0f}ms")
    
    # Save results
    output_file = evaluator.save_results(results)
    logger.info(f"\nResults saved to: {output_file}")
    
    # Save summary
    summary_file = Path(output_file).parent / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Summary saved to: {summary_file}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Research Evaluation Complete!")
    logger.info("=" * 60)
    
    return results, summary


if __name__ == "__main__":
    results, summary = main()
