"""
Pipeline runner and execution management.

Provides:
- PipelineRunner: High-level pipeline execution interface
- Batch execution support
"""

import logging
from typing import List, Any, Dict
from datetime import datetime

from src.models import StepInput, StepOutput
from src.tracing import Trace
from src.pipeline.base import Pipeline


logger = logging.getLogger(__name__)


class PipelineRunner:
    """High-level interface for running pipelines."""
    
    def __init__(self, pipeline: Pipeline):
        """
        Initialize runner.
        
        Args:
            pipeline: Pipeline instance
        """
        self.pipeline = pipeline
        self.logger = logging.getLogger(f"{__name__}.{pipeline.name}")
        self.execution_history: List[Trace] = []
    
    def run(self, input_data: Any) -> tuple[Any, Trace]:
        """
        Run pipeline on single input.
        
        Args:
            input_data: Input to process
            
        Returns:
            Tuple of (output, trace)
        """
        self.logger.info(f"Starting pipeline execution with input type: {type(input_data)}")
        
        try:
            output, trace = self.pipeline.execute(input_data)
            self.execution_history.append(trace)
            return output, trace
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")
            raise
    
    def run_batch(self, inputs: List[Any]) -> List[tuple[Any, Trace]]:
        """
        Run pipeline on batch of inputs.
        
        Args:
            inputs: List of inputs
            
        Returns:
            List of (output, trace) tuples
        """
        self.logger.info(f"Starting batch execution with {len(inputs)} inputs")
        
        results = []
        for i, input_data in enumerate(inputs):
            try:
                self.logger.info(f"Processing {i+1}/{len(inputs)}")
                output, trace = self.run(input_data)
                results.append((output, trace))
            except Exception as e:
                self.logger.error(f"Batch item {i} failed: {e}")
                # Continue with next item
                results.append((None, None))
        
        self.logger.info(f"Batch execution complete: {len(results)} items processed")
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get execution statistics.
        
        Returns:
            Dictionary of statistics
        """
        if not self.execution_history:
            return {}
        
        total_runs = len(self.execution_history)
        successful_runs = sum(1 for t in self.execution_history if t.status.value == "success")
        failed_runs = total_runs - successful_runs
        
        latencies = [t.total_latency_ms for t in self.execution_history if t.total_latency_ms > 0]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "success_rate": successful_runs / total_runs if total_runs > 0 else 0,
            "average_latency_ms": avg_latency,
            "min_latency_ms": min(latencies) if latencies else 0,
            "max_latency_ms": max(latencies) if latencies else 0,
        }
