"""
SQLite database management.

Provides:
- Database schema initialization
- Connection management
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


class Database:
    """SQLite database management."""
    
    def __init__(self, db_path: str = "data/failure_forensics.db"):
        """
        Initialize database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(f"{__name__}")
        self.init_schema()
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get database connection.
        
        Returns:
            SQLite connection
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_schema(self) -> None:
        """Initialize database schema."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Traces table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS traces (
                    trace_id TEXT PRIMARY KEY,
                    created_at DATETIME,
                    status TEXT,
                    final_score REAL,
                    total_latency REAL,
                    pipeline_name TEXT,
                    metadata TEXT
                )
            """)
            
            # Spans table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spans (
                    span_id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    step_name TEXT,
                    step_index INTEGER,
                    input_data TEXT,
                    output_data TEXT,
                    prompt TEXT,
                    raw_response TEXT,
                    confidence REAL,
                    judge_score REAL,
                    latency REAL,
                    status TEXT,
                    error TEXT,
                    FOREIGN KEY (trace_id) REFERENCES traces(trace_id)
                )
            """)
            
            # Failures table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS failures (
                    failure_id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    span_id TEXT NOT NULL,
                    failure_type TEXT,
                    severity REAL,
                    description TEXT,
                    evidence TEXT,
                    confirmed BOOLEAN,
                    created_at DATETIME,
                    FOREIGN KEY (trace_id) REFERENCES traces(trace_id),
                    FOREIGN KEY (span_id) REFERENCES spans(span_id)
                )
            """)
            
            # Propagation table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS propagation (
                    propagation_id TEXT PRIMARY KEY,
                    failure_id TEXT NOT NULL,
                    source_span TEXT,
                    target_span TEXT,
                    propagation_score REAL,
                    evidence TEXT,
                    FOREIGN KEY (failure_id) REFERENCES failures(failure_id)
                )
            """)
            
            # Root causes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS root_causes (
                    analysis_id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    failure_id TEXT,
                    root_span_id TEXT,
                    root_cause_confidence REAL,
                    reasoning TEXT,
                    evidence TEXT,
                    created_at DATETIME,
                    FOREIGN KEY (trace_id) REFERENCES traces(trace_id),
                    FOREIGN KEY (root_span_id) REFERENCES spans(span_id)
                )
            """)
            
            # Evaluation cases table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evaluation_cases (
                    case_id TEXT PRIMARY KEY,
                    original_input TEXT,
                    failing_step TEXT,
                    incorrect_output TEXT,
                    corrected_output TEXT,
                    failure_type TEXT,
                    root_cause TEXT,
                    created_at DATETIME
                )
            """)
            
            # Regression runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regression_runs (
                    run_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    pipeline_version TEXT,
                    result TEXT,
                    score REAL,
                    executed_at DATETIME,
                    FOREIGN KEY (case_id) REFERENCES evaluation_cases(case_id)
                )
            """)
            
            conn.commit()
            self.logger.info("Database schema initialized")
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
