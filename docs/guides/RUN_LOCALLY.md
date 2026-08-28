# 🚀 How to Run FailureForensicsTool Locally

**Location**: `d:\sem5\EDI`

---

## Step 1: Verify Dependencies Are Installed

```bash
cd d:\sem5\EDI
pip list | grep -E "pydantic|streamlit|pytest"
```

**Expected Output**:
- pydantic >= 2.0
- streamlit >= latest
- pytest >= latest

If missing, install:
```bash
pip install -r requirements.txt
```

---

## Step 2: Run Tests (Verify Everything Works)

### Run All 178 Tests

```bash
cd d:\sem5\EDI
python -m pytest tests/ -v
```

**Expected Output**:
```
===== 178 passed in 1.69s =====
```

### Run Specific Test File

```bash
python -m pytest tests/test_pipeline.py -v
python -m pytest tests/test_evaluation.py -v
python -m pytest tests/test_failure.py -v
```

### Run Quick Test

```bash
python -m pytest tests/ -q
```

---

## Step 3: Run Research Evaluation

Analyze 5 failure scenarios with metrics collection:

```bash
cd d:\sem5\EDI
python research/run_evaluation.py
```

**What it does**:
- Runs 5 test scenarios (good execution, early/intermediate/late failures, partial failure)
- Collects metrics for each scenario
- Generates JSON results

**Output**:
```
research/results/
├── evaluation_20260828_193509.json    (Detailed metrics)
└── summary.json                       (Aggregated statistics)
```

**View Results**:
```bash
type research/results/summary.json
```

---

## Step 4: Launch Streamlit UI (Main Application)

This is the main interactive interface:

```bash
cd d:\sem5\EDI
streamlit run app.py
```

**What happens**:
1. Streamlit server starts
2. Browser opens at: `http://localhost:8501`
3. You see the FailureForensicsTool UI with 7 pages

**UI Pages Available**:
1. 📊 **Dashboard** - System overview
2. 🚀 **Run Pipeline** - Execute pipelines with tracing
3. 🔍 **Trace Explorer** - Browse execution traces
4. 🔴 **Failure Analysis** - Detect and classify failures
5. 🌊 **Propagation Analysis** - Analyze failure propagation
6. 📝 **Feedback & Evaluation** - Manage evaluation cases
7. 📈 **Analytics & Metrics** - System statistics

**Stop the UI**:
- Press `Ctrl+C` in terminal

---

## Step 5: Run Individual Components

### Execute a Single Pipeline

```bash
cd d:\sem5\EDI
python
```

Then in Python:
```python
from src.pipeline.runner import PipelineRunner
from src.tracing.instrumentation import TraceContext

runner = PipelineRunner()

with TraceContext(pipeline_name="test_pipeline") as trace:
    result = runner.execute_demo("Hello, World!")
    print(f"Trace ID: {trace.trace_id}")
    print(f"Spans: {len(trace.spans)}")
    for span in trace.spans:
        print(f"  - {span.step_name}: {span.status}")
```

Press `Ctrl+D` to exit Python.

### Run Failure Detection

```python
from src.failure.detector import FailureDetector
from src.failure.classifier import FailureClassifier

detector = FailureDetector(threshold=0.7)
failures = detector.detect(trace)

classifier = FailureClassifier()
failures = classifier.classify_batch(failures, trace)

for f in failures:
    print(f"Type: {f.failure_type.value}, Severity: {f.severity:.2f}")
```

### Analyze Propagation

```python
from src.failure.propagation import PropagationAnalyzer

analyzer = PropagationAnalyzer()
prop = analyzer.analyze(failures[0], trace)
print(f"Propagation Score: {prop.overall_propagation_score:.2f}")
```

### Identify Root Cause

```python
from src.failure.root_cause import RootCauseEngine

engine = RootCauseEngine()
root = engine.analyze(failures[0], trace, prop)
print(f"Root Cause: {root.root_step_name}")
print(f"RCC: {root.root_cause_confidence:.2f}")
```

---

## Step 6: Use the Database

### Save Trace to Database

```python
from src.storage.database import Database
from src.storage.repositories import TraceRepository

db = Database()
repo = TraceRepository(db)
repo.save(trace)
print("Trace saved!")
```

### Retrieve Trace

```python
retrieved = repo.get(trace.trace_id)
print(f"Retrieved trace with {len(retrieved.spans)} spans")
```

### List All Traces

```python
all_traces = repo.list_all(limit=10)
print(f"Total traces: {len(all_traces)}")
```

---

## Complete Workflow Example

Here's a complete end-to-end example:

```bash
cd d:\sem5\EDI
python
```

```python
from src.pipeline.runner import PipelineRunner
from src.tracing.instrumentation import TraceContext
from src.evaluation.evaluator import Evaluator
from src.failure.detector import FailureDetector
from src.failure.classifier import FailureClassifier
from src.failure.propagation import PropagationAnalyzer
from src.failure.root_cause import RootCauseEngine
from src.storage.database import Database
from src.storage.repositories import TraceRepository

# 1. Execute pipeline with tracing
runner = PipelineRunner()
with TraceContext(pipeline_name="demo") as trace:
    result = runner.execute_demo("Test input")

# 2. Evaluate
evaluator = Evaluator()
evaluator.evaluate_trace(trace)

# 3. Detect failures
detector = FailureDetector(threshold=0.7)
failures = detector.detect(trace)
print(f"Failures detected: {len(failures)}")

# 4. Classify
classifier = FailureClassifier()
failures = classifier.classify_batch(failures, trace)

# 5. Propagation analysis
if failures:
    analyzer = PropagationAnalyzer()
    prop = analyzer.analyze(failures[0], trace)
    print(f"Propagation Score: {prop.overall_propagation_score:.2f}")
    
    # 6. Root cause
    engine = RootCauseEngine()
    root = engine.analyze(failures[0], trace, prop)
    print(f"Root Cause: {root.root_step_name}")
    print(f"RCC: {root.root_cause_confidence:.2f}")

# 7. Save to database
db = Database()
repo = TraceRepository(db)
repo.save(trace)
print("Trace saved to database!")
```

---

## Quick Commands Reference

```bash
# Navigate to project
cd d:\sem5\EDI

# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_pipeline.py -v

# Run research evaluation
python research/run_evaluation.py

# Launch UI
streamlit run app.py

# Run Python interactive
python

# Check requirements
pip list | grep pydantic

# Install dependencies
pip install -r requirements.txt
```

---

## Troubleshooting

### Issue: "No module named 'src'"
**Solution**: Make sure you're running from `d:\sem5\EDI` directory
```bash
cd d:\sem5\EDI
```

### Issue: "Ollama server not available"
**Solution**: This is normal - the system has fallback methods. To use LLM:
```bash
ollama serve          # In one terminal
ollama pull qwen2.5:7b-instruct
```

### Issue: Database locked
**Solution**: Delete the database and start fresh
```bash
del failure_forensics.db
```

### Issue: Tests failing
**Solution**: Verify dependencies and Python version
```bash
python --version      # Should be 3.10+
pip install -r requirements.txt --upgrade
python -m pytest tests/ -v
```

---

## What Each Component Does

| Component | What It Does | How to Run |
|-----------|------------|-----------|
| **Pipeline** | Executes multi-step AI pipeline | `python` → run code |
| **Tracing** | Captures execution details | Automatic with TraceContext |
| **Evaluation** | Assesses step quality with LLM | `evaluator.evaluate_trace()` |
| **Failure Detection** | Identifies low-quality outputs | `detector.detect(trace)` |
| **Classification** | Categorizes failure types | `classifier.classify_batch()` |
| **Propagation** | Measures failure transmission | `analyzer.analyze()` |
| **Root Cause** | Identifies root causes | `engine.analyze()` |
| **Storage** | Persists to SQLite | `repo.save(trace)` |
| **UI** | Interactive Streamlit app | `streamlit run app.py` |
| **Research** | Runs 5 test scenarios | `python research/run_evaluation.py` |

---

## Performance

**Typical execution times**:
- Single span: ~10-20ms
- Single trace (4 spans): ~100-200ms
- Failure detection: ~50ms per trace
- Full analysis (all components): ~300-400ms
- Research evaluation (5 scenarios): ~2-5 seconds

---

## File Structure for Reference

```
d:\sem5\EDI/
├── src/                    # Source code
├── tests/                  # Test files
├── ui/                     # Streamlit pages
├── research/              # Research framework
├── docs/                  # Documentation
├── app.py                 # UI entry point
├── requirements.txt       # Dependencies
└── failure_forensics.db   # Database (created on first run)
```

---

## Next Steps

1. **Run tests first**: `python -m pytest tests/ -v`
2. **Try research eval**: `python research/run_evaluation.py`
3. **Launch UI**: `streamlit run app.py`
4. **Explore components**: Try Python examples above
5. **Check database**: Traces are saved in `failure_forensics.db`

---

## Support

- **Documentation**: See `/docs` folder
- **Code examples**: Check `/tests` folder
- **UI usage**: Use the Streamlit pages at localhost:8501
- **Questions**: Refer to README.md and QUICKSTART.md

---

**Ready to start!** 🚀

Begin with: `cd d:\sem5\EDI && streamlit run app.py`
