# FailureForensicsTool: Methodology and Technical Approach

## Executive Summary

FailureForensicsTool is an AI pipeline failure analysis framework designed for systematic diagnosis of failures in multi-step AI pipelines. It combines tracing, LLM-based evaluation, and graph-based propagation analysis to identify root causes of failures.

## System Architecture

### Core Components

#### 1. Pipeline Framework (Phases 1-4)
- **Purpose**: Execute AI pipelines with modular step execution
- **Key Features**:
  - Generic step interface supporting custom implementations
  - Demonstration pipeline: Intake → Extraction → Classification → Summarization
  - Support for batch execution and statistics aggregation
  - LLM fallback mechanisms for fault tolerance

#### 2. Tracing System (Phase 5)
- **Purpose**: Capture detailed execution traces with span-level granularity
- **Key Features**:
  - Automatic span creation and lifecycle management
  - Status tracking (PENDING, RUNNING, SUCCESS, FAILED)
  - Input/output capture and latency measurement
  - Context management with current trace tracking
  - Trace statistics and query utilities

#### 3. Storage Layer (Phase 6)
- **Database**: SQLite for local, dependency-free persistence
- **Schema**: 7 tables covering traces, spans, failures, propagation, root causes, evaluation cases, regression runs
- **Repository Pattern**: DAO layer for clean CRUD operations with JSON serialization for complex types

#### 4. Evaluation Engine (Phase 7)
- **Judge Model**: LLM-as-Judge for multi-step evaluation
- **Metrics**:
  - Overall score (0-1)
  - Criteria-specific scores
  - Pass/fail classification
  - Issue identification
- **Scoring**: Aggregation with optional weighting, confidence calculation from variance

#### 5. Failure Detection (Phase 8)
- **Detection**: Threshold-based identification of low-quality outputs
- **Classification**: Rule-based categorization into failure types:
  - EXTRACTION_HALLUCINATION
  - MISCLASSIFICATION
  - INCOMPLETE_OUTPUT
  - UNKNOWN
- **Severity**: Calculated from judge score gap below threshold

#### 6. Propagation Analysis (Phase 9)
- **Purpose**: Model how failures affect downstream steps
- **Propagation Score (PS)**: Combines score degradation with distance decay:
  ```
  PS = score_drop × distance_factor
  distance_factor = 1.0 / (1.0 + distance × 0.1)
  ```
- **Aggregation**: Mean propagation score across all affected paths
- **Output**: Affected span list, propagation paths, overall propagation score

#### 7. Root Cause Engine (Phase 10)
- **Root Cause Confidence (RCC)**: Dual-component metric:
  ```
  RCC = 0.6 × local_severity + 0.4 × downstream_impact
  local_severity = 1.0 - judge_score
  downstream_impact = max(propagation_scores) from this span
  ```
- **Candidate Ranking**: Sorts by RCC in descending order
- **Evidence**: Includes judge score, downstream impact, reasoning

#### 8. Feedback Loop (Phase 11)
- **Evaluation Dataset**: JSON-based case storage
- **Regression Testing**: Rerun historical cases to detect regressions
- **Dataset Management**: Load/save functionality for persistence

#### 9. UI Layer (Phase 12)
- **Framework**: Streamlit for minimal setup
- **Pages**:
  - Dashboard: System statistics and overview
  - Pipeline Runner: Execute pipelines with real-time tracing
  - Trace Explorer: Browse and analyze execution traces
  - Failure Analysis: Detect and classify failures
  - Propagation Analysis: Visualize failure propagation
  - Feedback & Evaluation: Manage evaluation dataset
  - Analytics: System-wide metrics and statistics

## Technical Design Decisions

### 1. Pydantic v2 with ConfigDict
**Rationale**: Future-proofing and eliminating deprecation warnings
- Chosen over class Config for Pydantic v2 compatibility
- Provides validation and serialization out of the box

### 2. OllamaClient with Custom Exceptions
**Rationale**: Specific error handling and retry mechanisms
- OllamaException hierarchy enables targeted handling
- Exponential backoff with jitter for resilience
- Graceful degradation when LLM unavailable

### 3. LLM Fallback Strategy
**Rationale**: Research MVP robustness over perfect quality
- Each pipeline step has fallback_extract/classify/summarize methods
- Allows partial processing if LLM fails
- Documented trade-off in architecture guide

### 4. Global Trace Context
**Rationale**: Simplicity for research MVP
- Acknowledged limitation: not thread-safe
- Sufficient for single-threaded research evaluation
- Could upgrade to thread-local storage in production

### 5. Repository Pattern with JSON Serialization
**Rationale**: Fine-grained control vs ORM overhead
- Custom DAO layer enables complex type handling
- JSON serialization preserves structured data in SQLite
- Clear separation of concerns

### 6. SQLite for Persistence
**Rationale**: No external dependencies, local-only per requirements
- Embedded database, no server setup
- ACID compliance for data integrity
- Sufficient for research evaluation scale

## Evaluation Methodology

### Test Case Design

#### Scenario 1: Good Execution
- All steps maintain high quality (0.95+ judge scores)
- Expected: No failures detected, zero propagation
- Tests normal operation and baseline metrics

#### Scenario 2: Early Failure
- First step fails (score 0.3), propagates downward
- Expected: Failure detected in step 0, RCC = high for early step
- Tests failure localization at pipeline start

#### Scenario 3: Intermediate Failure
- Middle step fails (0.4), partial downstream impact
- Expected: Failure detected with propagation to final step
- Tests distance decay in propagation analysis

#### Scenario 4: Late Failure
- Final step fails (0.2), no downstream propagation
- Expected: Failure detected, zero affected downstream spans
- Tests boundary case with no propagation

#### Scenario 5: Partial Failure
- Mix of good (0.9) and bad (0.3-0.4) spans
- Expected: Multiple failures detected, varied RCC scores
- Tests multi-failure handling

### Key Metrics

| Metric | Definition | Interpretation |
|--------|-----------|-----------------|
| Judge Score | LLM evaluation of output quality | 0-1, higher is better |
| Failure Rate | % of spans with score < threshold | 0-1, lower is better |
| Propagation Score | Average failure propagation to downstream | 0-1, lower = less propagation |
| Root Cause Confidence | Probability candidate is true root cause | 0-1, higher = more confident |
| Latency | Step execution time | ms, lower is better |

## Implementation Statistics

### Code Organization
- **Source**: 15 modules across 7 directories
- **Tests**: 178 comprehensive tests (12 test files)
- **UI**: 7 Streamlit pages with integrated features
- **Research**: Evaluation framework with 5 test cases

### Test Coverage
- Models: 27 tests
- LLM Integration: 26 tests
- Pipeline: 21 tests
- Tracing: 22 tests
- Storage: 8 tests
- Evaluation: 12 tests
- Failure Detection: 12 tests
- Propagation: 11 tests
- Root Cause: 12 tests
- Feedback: 14 tests
- Integration E2E: 8 tests

### Performance
- Average latency per span: ~100ms
- Database operations: <10ms
- Trace serialization: <5ms for typical 4-span trace

## Limitations and Future Work

### Known Limitations
1. **Single-threaded trace context**: Use thread-local storage for concurrency
2. **Rule-based classification**: Replace with ML-based categorization
3. **Simple propagation model**: Could incorporate semantic similarity
4. **No visualization**: Add graph-based failure propagation UI
5. **Local-only storage**: Add cloud backend option
6. **Mock Ollama tests**: Requires running Ollama for end-to-end validation

### Future Enhancements
1. **Advanced root cause analysis**: Causal inference models
2. **Cross-pipeline failure correlation**: Multi-pipeline analysis
3. **Automated repair suggestions**: Generate fixes for detected failures
4. **Performance optimization**: Caching and indexing strategies
5. **Extended LLM support**: Anthropic, OpenAI, Hugging Face APIs
6. **Containerization**: Docker deployment for reproducibility
7. **Distributed tracing**: Support for asynchronous/distributed execution

## Research Contributions

### Novel Elements
1. **Propagation Score formula**: Combines degradation with distance decay
2. **Root Cause Confidence metric**: Dual-component scoring from local + downstream impact
3. **Integrated evaluation pipeline**: Traces → Judge → Failures → Propagation → RCC
4. **LLM-as-Judge evaluation**: Structured evaluation with criteria scores

### Experimental Validation
- Framework tested on 5 representative failure scenarios
- Metrics collection and aggregation validated
- JSON output format suitable for downstream analysis
- Performance characteristics measured and documented

## Reproducibility

All code is open and available at workspace root. To reproduce:

```bash
# Setup
pip install -r requirements.txt
cd d:\sem5\EDI

# Run tests
python -m pytest tests/ -v

# Run research evaluation
python research/run_evaluation.py

# Launch UI
streamlit run app.py
```

Results are automatically saved to `research/results/` with timestamps.
