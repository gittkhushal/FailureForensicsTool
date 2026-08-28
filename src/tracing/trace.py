"""
Trace representation and management.

Provides:
- Core Trace class (imported from models)
- Trace utilities
"""

from src.models.trace_models import Trace, Span, TraceStatus, SpanStatus

__all__ = ["Trace", "Span", "TraceStatus", "SpanStatus"]
