"""
Data access objects (DAO pattern) for storage.

Provides:
- TraceRepository: CRUD for traces and spans
- FailureRepository: CRUD for failures
- EvaluationRepository: CRUD for evaluation cases and results
"""

import json
import logging
from typing import List, Optional, Any

from src.models.trace_models import Trace, Span
from src.models.failure_models import Failure, FailureType
from src.models.evaluation_models import EvaluationCase, RegressionResult
from src.storage.database import Database


logger = logging.getLogger(__name__)


class TraceRepository:
    """Data access for traces and spans."""
    
    def __init__(self, db: Database):
        """Initialize repository."""
        self.db = db
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def save(self, trace: Trace) -> None:
        """Save trace to database."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Save trace
            cursor.execute("""
                INSERT OR REPLACE INTO traces
                (trace_id, created_at, status, final_score, total_latency, pipeline_name)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                trace.trace_id,
                trace.created_at,
                trace.status.value,
                trace.final_score,
                trace.total_latency_ms,
                trace.pipeline_name,
            ))
            
            # Save spans
            for span in trace.spans:
                cursor.execute("""
                    INSERT OR REPLACE INTO spans
                    (span_id, trace_id, step_name, step_index, input_data, output_data,
                     prompt, raw_response, confidence, judge_score, latency, status, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    span.span_id,
                    span.trace_id,
                    span.step_name,
                    span.step_index,
                    json.dumps(span.input_data) if span.input_data else None,
                    json.dumps(span.output_data) if span.output_data else None,
                    span.prompt,
                    span.raw_response,
                    span.confidence,
                    span.judge_score,
                    span.latency_ms,
                    span.status.value,
                    span.error,
                ))
            
            conn.commit()
            self.logger.debug(f"Saved trace {trace.trace_id} with {len(trace.spans)} spans")
            
        except Exception as e:
            self.logger.error(f"Failed to save trace: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get(self, trace_id: str) -> Optional[Trace]:
        """Get trace by ID."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM traces WHERE trace_id = ?", (trace_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            trace = Trace(
                trace_id=row["trace_id"],
                pipeline_name=row["pipeline_name"],
                final_score=row["final_score"],
                total_latency_ms=row["total_latency"],
                status=row["status"],
            )
            
            # Get spans
            cursor.execute("SELECT * FROM spans WHERE trace_id = ?", (trace_id,))
            for span_row in cursor.fetchall():
                span = Span(
                    span_id=span_row["span_id"],
                    trace_id=span_row["trace_id"],
                    step_name=span_row["step_name"],
                    step_index=span_row["step_index"],
                    input_data=json.loads(span_row["input_data"]) if span_row["input_data"] else None,
                    output_data=json.loads(span_row["output_data"]) if span_row["output_data"] else None,
                    confidence=span_row["confidence"],
                    judge_score=span_row["judge_score"],
                    latency_ms=span_row["latency"],
                    status=span_row["status"],
                    error=span_row["error"],
                )
                trace.add_span(span)
            
            return trace
            
        except Exception as e:
            self.logger.error(f"Failed to get trace: {e}")
            return None
        finally:
            conn.close()
    
    def list_all(self, limit: int = 100) -> List[Trace]:
        """List all traces."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT trace_id FROM traces ORDER BY created_at DESC LIMIT ?", (limit,))
            traces = []
            for row in cursor.fetchall():
                trace = self.get(row["trace_id"])
                if trace:
                    traces.append(trace)
            return traces
        finally:
            conn.close()
    
    def delete(self, trace_id: str) -> bool:
        """Delete trace and associated spans."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM spans WHERE trace_id = ?", (trace_id,))
            cursor.execute("DELETE FROM traces WHERE trace_id = ?", (trace_id,))
            conn.commit()
            self.logger.debug(f"Deleted trace {trace_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete trace: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()


class FailureRepository:
    """Data access for failures."""
    
    def __init__(self, db: Database):
        """Initialize repository."""
        self.db = db
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def save(self, failure: Failure) -> None:
        """Save failure to database."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO failures
                (failure_id, trace_id, span_id, failure_type, severity,
                 description, evidence, confirmed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                failure.failure_id,
                failure.trace_id,
                failure.span_id,
                failure.failure_type.value,
                failure.severity,
                failure.description,
                json.dumps(failure.evidence),
                failure.confirmed,
                failure.created_at,
            ))
            
            conn.commit()
            self.logger.debug(f"Saved failure {failure.failure_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to save failure: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get(self, failure_id: str) -> Optional[Failure]:
        """Get failure by ID."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM failures WHERE failure_id = ?", (failure_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Get step_name and judge_score from spans table
            cursor.execute(
                "SELECT step_name, judge_score FROM spans WHERE span_id = ?",
                (row["span_id"],)
            )
            span_row = cursor.fetchone()
            step_name = span_row["step_name"] if span_row else ""
            judge_score = span_row["judge_score"] if span_row else 0.0
            
            failure = Failure(
                failure_id=row["failure_id"],
                trace_id=row["trace_id"],
                span_id=row["span_id"],
                step_name=step_name,
                failure_type=FailureType(row["failure_type"]),
                severity=row["severity"],
                judge_score=judge_score,
                description=row["description"],
                evidence=json.loads(row["evidence"]) if row["evidence"] else {},
                confirmed=row["confirmed"],
            )
            return failure
            
        except Exception as e:
            self.logger.error(f"Failed to get failure: {e}")
            return None
        finally:
            conn.close()
    
    def list_by_trace(self, trace_id: str) -> List[Failure]:
        """List failures for a trace."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT failure_id FROM failures WHERE trace_id = ?", (trace_id,))
            failures = []
            for row in cursor.fetchall():
                failure = self.get(row["failure_id"])
                if failure:
                    failures.append(failure)
            return failures
        finally:
            conn.close()


class EvaluationRepository:
    """Data access for evaluation cases and results."""
    
    def __init__(self, db: Database):
        """Initialize repository."""
        self.db = db
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def save_case(self, case: EvaluationCase) -> None:
        """Save evaluation case."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO evaluation_cases
                (case_id, original_input, failing_step, incorrect_output,
                 corrected_output, failure_type, root_cause, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case.case_id,
                json.dumps(case.original_input),
                case.failing_step,
                json.dumps(case.incorrect_output),
                json.dumps(case.corrected_output),
                case.failure_type,
                case.root_cause_step,
                case.created_at,
            ))
            
            conn.commit()
            self.logger.debug(f"Saved evaluation case {case.case_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to save case: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_case(self, case_id: str) -> Optional[EvaluationCase]:
        """Get evaluation case by ID."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM evaluation_cases WHERE case_id = ?", (case_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            case = EvaluationCase(
                case_id=row["case_id"],
                trace_id="",
                original_input=json.loads(row["original_input"]),
                failing_step=row["failing_step"],
                incorrect_output=json.loads(row["incorrect_output"]),
                corrected_output=json.loads(row["corrected_output"]),
                failure_type=row["failure_type"],
                root_cause_step=row["root_cause"],
            )
            return case
            
        except Exception as e:
            self.logger.error(f"Failed to get case: {e}")
            return None
        finally:
            conn.close()
    
    def list_cases(self, limit: int = 100) -> List[EvaluationCase]:
        """List evaluation cases."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT case_id FROM evaluation_cases ORDER BY created_at DESC LIMIT ?", (limit,))
            cases = []
            for row in cursor.fetchall():
                case = self.get_case(row["case_id"])
                if case:
                    cases.append(case)
            return cases
        finally:
            conn.close()
    
    def save_regression_result(self, result: RegressionResult) -> None:
        """Save regression test result."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO regression_runs
                (run_id, case_id, pipeline_version, result, score, executed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                result.run_id,
                result.case_id,
                "1.0",
                "pass" if result.passed else "fail",
                result.score,
                result.executed_at,
            ))
            
            conn.commit()
            self.logger.debug(f"Saved regression result {result.run_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to save regression result: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
