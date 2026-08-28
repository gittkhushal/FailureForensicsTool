# FailureForensicsTool Architecture

## System Overview

FailureForensicsTool is a general framework for failure analysis and root-cause diagnosis in multi-step AI pipelines. The system observes pipeline execution, evaluates intermediate outputs, detects failures, and determines the most influential root cause through propagation analysis.

## High-Level Architecture

```
                  USER
                   │
                   ▼
          ┌─────────────────┐
          │ Streamlit UI    │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ Pipeline Runner │
          └────────┬────────┘
                   │
        ┌──────────▼──────────┐
        │   Multi-Step AI     │
        │      Pipeline       │
        └──────────┬──────────┘
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
    Step 1       Step 2      Step N
       │           │           │
       └───────────┼───────────┘
                   ▼
          ┌─────────────────┐
          │ Trace/Span      │
          │ Instrumentation │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ LLM-as-Judge    │
          └────────┬────────┘
                   │
             Failure?
              /      \
            No        Yes
            │          │
            │          ▼
            │   ┌───────────────┐
            │   │ Propagation   │
            │   │ Analyzer      │
            │   └───────┬───────┘
            │           ▼
            │   ┌───────────────┐
            │   │ Root Cause    │
            │   │ Engine        │
            │   └───────┬───────┘
            │           ▼
            │   ┌───────────────┐
            │   │ Explanation   │
            │   └───────┬───────┘
            │           ▼
            └─────► Feedback/Eval
                        │
                        ▼
                  Regression Tests
```

## Core Components

### 1. Pipeline Framework (`src/pipeline/`)

**Purpose**: Execute multi-step AI workflows with modular step design.

- `base.py`: Abstract base classes for `PipelineStep` and `Pipeline`
- `runner.py`: Pipeline execution orchestrator
- `intake.py`: Input normalization and validation
- `extraction.py`: Entity/information extraction
- `classification.py`: Document/content classification
- `summarization.py`: Output summarization

### 2. Data Models (`src/models/`)

**Purpose**: Type-safe intermediate representations using Pydantic.

- `pipeline_models.py`: Step input/output schemas
- `trace_models.py`: Trace and span structures
- `failure_models.py`: Failure representation
- `evaluation_models.py`: Evaluation results and feedback

### 3. LLM Integration (`src/llm/`)

**Purpose**: Unified interface to local LLM (Ollama).

- `ollama_client.py`: Ollama API wrapper with retry/fallback logic
- `prompts.py`: Prompt templates for extraction, classification, summarization, and evaluation

### 4. Tracing System (`src/tracing/`)

**Purpose**: Observability layer capturing execution history.

- `trace.py`: Trace model (unique trace_id, creation time, status)
- `span.py`: Span model (step execution record with input/output/latency/confidence)
- `instrumentation.py`: Decorators/context managers for automatic span generation

### 5. Evaluation Module (`src/evaluation/`)

**Purpose**: LLM-as-Judge for output quality assessment.

- `judge.py`: Judge implementation with evaluation criteria
- `evaluator.py`: Evaluation orchestration and result aggregation
- `scoring.py`: Score computation and aggregation logic

### 6. Failure Analysis (`src/failure/`)

**Purpose**: Multi-stage failure analysis pipeline (the research core).

- `detector.py`: Identifies outputs below quality threshold
- `classifier.py`: Categorizes failure types (hallucination, misclassification, etc.)
- `propagation.py`: Builds propagation graph and calculates Propagation Score (PS)
- `root_cause.py`: Identifies influential root cause and calculates Root Cause Confidence (RCC)
- `explanation.py`: Generates human-readable explanations with evidence

### 7. Storage Layer (`src/storage/`)

**Purpose**: Persistent data management with SQLite.

- `database.py`: Schema definition and initialization
- `repositories.py`: Data access objects for traces, failures, evaluations
- `trace_store.py`: JSON archival of complete trace history

### 8. Feedback System (`src/feedback/`)

**Purpose**: Closed-loop improvement via human feedback and regression testing.

- `dataset.py`: Evaluation case collection and management
- `regression.py`: Re-execution of known failures and tracking

### 9. UI Layer (`ui/`)

**Purpose**: Streamlit-based interactive dashboard.

- `dashboard.py`: Overview, statistics, key metrics
- `pipeline_view.py`: Pipeline execution interface
- `trace_view.py`: Trace and span exploration
- `failure_view.py`: Failure details and analysis
- `propagation_view.py`: Propagation graph visualization
- `analytics_view.py`: Failure trends and statistics

## Data Flow

### Execution Flow

```
1. User Input
   ↓
2. Pipeline Execution
   ├─ Step 1 (Intake)
   ├─ Step 2 (Extraction)
   ├─ Step 3 (Classification)
   └─ Step 4 (Summarization)
   ↓
3. Trace Generation (span per step)
   ↓
4. Storage (SQLite + JSON)
   ↓
5. LLM-as-Judge Evaluation
   ├─ Correctness score
   ├─ Hallucination score
   ├─ Completeness score
   └─ Consistency score
   ↓
6. Failure Detection
   ├─ Threshold comparison
   ├─ Classification
   └─ Severity assessment
   ↓
7. If Failure Detected:
   ├─ Propagation Analysis
   ├─ Root Cause Analysis
   └─ Explanation Generation
   ↓
8. User Feedback
   └─ Evaluation Dataset Update
   └─ Regression Runs
```

## Database Schema

```
traces
├── trace_id (PK)
├── created_at
├── status
├── final_score
└── total_latency

spans
├── span_id (PK)
├── trace_id (FK → traces)
├── step_name
├── step_index
├── input_data
├── output_data
├── prompt
├── raw_response
├── confidence
├── judge_score
├── latency
├── status
└── error

failures
├── failure_id (PK)
├── trace_id (FK)
├── span_id (FK)
├── failure_type
├── severity
├── description
├── evidence
└── confirmed

propagation
├── propagation_id (PK)
├── failure_id (FK)
├── source_span
├── target_span
├── propagation_score
└── evidence

root_causes
├── analysis_id (PK)
├── trace_id (FK)
├── root_span_id
├── root_cause_confidence
├── reasoning
└── created_at

evaluation_cases
├── case_id (PK)
├── original_input
├── failing_step
├── incorrect_output
├── corrected_output
├── failure_type
├── root_cause
└── created_at

regression_runs
├── run_id (PK)
├── case_id (FK)
├── pipeline_version
├── result
├── score
└── executed_at
```

## Key Research Metrics

### Propagation Score (PS)

Measures how strongly a failure at step `i` affects downstream steps `i+1`, `i+2`, ..., `n`.

```
PS = f(degradation_i+1, degradation_i+2, ..., degradation_n)
    where degradation_j = judge_score_j_healthy - judge_score_j_with_failure
```

**Finalized during Phase 9 and experimentally validated in Phase 11.**

### Root Cause Confidence (RCC)

Measures confidence that a particular failed step is the most influential root cause.

```
RCC = g(local_severity, propagation_impact, judge_agreement, evidence_strength)
```

**Finalized during Phase 10 and experimentally validated in Phase 11.**

## Modular Design

The framework is intentionally **step-agnostic**:

- The demonstration uses: Intake → Extraction → Classification → Summarization
- The framework can support any multi-step pipeline
- Future extensions can add new pipeline types without framework modification

## Extension Points

1. **New Pipeline**: Implement concrete `PipelineStep` subclasses
2. **New Judge Criteria**: Add evaluation dimensions to judge prompts
3. **New Failure Types**: Extend `FailureType` enum in classifier
4. **New LLM**: Swap `OllamaClient` with alternative LLM interface
5. **New Storage**: Replace `Database` with alternative backend
6. **New UI Pages**: Add Streamlit pages to `ui/`

## Non-Goals (MVP Scope)

- Automatic LLM fine-tuning (tracked as future work)
- Production-scale distribution (research MVP on laptop)
- Multiple concurrent pipelines (sequential execution for clarity)
- Cloud deployment (local-only for MVP)
- REST API (Streamlit direct Python calls)
