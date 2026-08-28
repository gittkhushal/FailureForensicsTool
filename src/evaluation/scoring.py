"""
Scoring and aggregation utilities.

Provides:
- Score aggregation
- Confidence calculations
"""

from typing import List, Dict, Any
import statistics


def aggregate_scores(scores: List[float], weights: List[float] = None) -> float:
    """
    Aggregate multiple scores.
    
    Args:
        scores: List of scores
        weights: Optional weights
        
    Returns:
        Aggregated score
    """
    if not scores:
        return 0.0
    
    if weights:
        if len(weights) != len(scores):
            raise ValueError("Weights must match scores length")
        total_weight = sum(weights)
        return sum(s * w for s, w in zip(scores, weights)) / total_weight
    
    return statistics.mean(scores)


def confidence_from_agreement(
    score: float,
    variance: float = 0.0,
) -> float:
    """
    Calculate confidence from score and variance.
    
    Args:
        score: Primary score
        variance: Variance in scores
        
    Returns:
        Confidence score
    """
    # Lower variance increases confidence
    confidence = score * (1.0 - min(variance, 1.0))
    return max(0.0, min(1.0, confidence))
