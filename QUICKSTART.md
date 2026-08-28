# FailureForensicsTool: Quick Start Guide

## Installation

### Prerequisites
- Python 3.10+
- pip or conda

### Setup

```bash
# Clone or navigate to workspace
cd d:\sem5\EDI

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import src; print('Installation successful!')"
```

## Running Tests

```bash
# Run all tests (178 tests, ~2 seconds)
python -m pytest tests/ -v

# Run specific test suite
python -m pytest tests/test_pipeline.py -v

# Run with coverage
python -m pytest tests/ --cov=src
```

## Research Evaluation

```bash
# Run research evaluation on 5 test scenarios
python research/run_evaluation.py

# Results saved to: research/results/evaluation_*.json
# Summary statistics: research/results/summary.json
```

## Launch UI

```bash
# Start Streamlit app
streamlit run app.py

# Opens at: http://localhost:8501
```

### UI Navigation
- **Dashboard**: System overview and statistics
- **Run Pipeline**: Execute pipelines with live tracing
- **Trace Explorer**: Browse saved execution traces
- **Failure Analysis**: Detect and classify failures
- **Propagation Analysis**: Analyze failure propagation
- **Feedback & Evaluation**: Create and manage evaluation cases
- **Analytics & Metrics**: System-wide performance metrics

## Basic Usage Example

### 1. Create a Trace
```python
from src.tracing.instrumentation import TraceContext
from src.models.trace_models import Trace, Span

# Trace execution
with TraceContext(pipeline_name="my_pipeline") as trace:
    # Your pipeline code here
    span = Span(
        span_id="s1",
        trace_id=trace.trace_id,
        step_name="extraction",
        step_index=0
    )
    span.judge_score = 0.85
    trace.add_span(span)
```

### 2. Evaluate for Failures
```python
from src.evaluation.evaluator import Evaluator
from src.failure.detector import FailureDetector
from src.failure.classifier import FailureClassifier

# Evaluate
evaluator = Evaluator()
evaluator.evaluate_trace(trace)

# Detect failures
detector = FailureDetector(threshold=0.7)
failures = detector.detect(trace)

# Classify
classifier = FailureClassifier()
failures = classifier.classify_batch(failures, trace)
```

### 3. Analyze Root Causes
```python
from src.failure.propagation import PropagationAnalyzer
from src.failure.root_cause import RootCauseEngine

# Propagation analysis
analyzer = PropagationAnalyzer()
prop_analysis = analyzer.analyze(failures[0], trace)

# Root cause
engine = RootCauseEngine()
root_analysis = engine.analyze(failures[0], trace, prop_analysis)

print(f"Root Cause: {root_analysis.root_step_name}")
print(f"RCC: {root_analysis.root_cause_confidence:.2f}")
```

### 4. Store Results
```python
from src.storage.database import Database
from src.storage.repositories import TraceRepository

# Save to database
db = Database()
repo = TraceRepository(db)
repo.save(trace)

# Retrieve later
retrieved = repo.get(trace.trace_id)
```

## Architecture Overview

```
Pipeline Execution
        ↓
   Tracing System (Spans, Traces)
        ↓
   LLM-as-Judge Evaluation
        ↓
   Failure Detection & Classification
        ↓
   Propagation Analysis (Propagation Score)
        ↓
   Root Cause Engine (Root Cause Confidence)
        ↓
   Storage & Persistence
        ↓
   Streamlit UI & Analytics
```

## Key Concepts

### Propagation Score (PS)
- Quantifies failure transmission from source to target step
- Formula: `PS = score_drop × distance_factor`
- Range: 0-1 (higher = more propagation)

### Root Cause Confidence (RCC)
- Combines local severity and downstream impact
- Formula: `RCC = 0.6 × local_severity + 0.4 × downstream_impact`
- Range: 0-1 (higher = more likely root cause)

### Judge Score
- LLM evaluation of step output quality
- Range: 0-1 (higher = better quality)

### Failure Detection
- Automatic when judge_score < threshold (default: 0.7)
- Severity calculated from score gap

## Configuration

### Failure Detection Threshold
```python
detector = FailureDetector(threshold=0.75)  # Default 0.7
```

### Database Location
```python
db = Database("path/to/database.db")  # Default: "failure_forensics.db"
```

### LLM Model
```python
from src.evaluation.judge import Judge
judge = Judge(model="qwen2.5:7b-instruct")  # Default
```

## Troubleshooting

### "Ollama server not available"
- The system works without Ollama using fallback methods
- To use LLM evaluation, install and run Ollama:
  ```bash
  ollama serve
  ollama pull qwen2.5:7b-instruct
  ```

### Database locked error
- Ensure only one process is accessing the database
- Delete `failure_forensics.db` to start fresh

### Tests fail with import errors
- Verify Python path includes workspace root
- Run from workspace root: `cd d:\sem5\EDI`

## Next Steps

1. **Understand the Framework**: Read `docs/METHODOLOGY.md`
2. **Run Research Evaluation**: Execute `python research/run_evaluation.py`
3. **Explore the Code**: Check `/src` directory structure
4. **Create Custom Steps**: Implement `PipelineStep` subclass
5. **Review Test Cases**: See `tests/` for usage examples

## Documentation

- **Architecture**: `docs/architecture.md`
- **Methodology**: `docs/METHODOLOGY.md`
- **Research Paper**: `docs/RESEARCH_PAPER_OUTLINE.md`
- **README**: `README.md` (project overview)

## Project Statistics

- **Code**: ~4000 lines across 15 modules
- **Tests**: 178 comprehensive tests
- **UI Pages**: 7 Streamlit views
- **Test Coverage**: All core components tested
- **Documentation**: 4 comprehensive guides

## Getting Help

1. Check documentation in `/docs`
2. Review test cases in `/tests` for examples
3. See `README.md` for additional context
4. Review `architecture.md` for design decisions

---

**Ready to get started!** 🚀

For detailed information, see the full README and documentation files.
