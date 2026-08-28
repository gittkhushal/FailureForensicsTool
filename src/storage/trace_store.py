"""
JSON trace archival and serialization.

Provides:
- TraceStore: Stores traces as JSON
"""

import json
import logging
from pathlib import Path
from typing import Optional

from src.models.trace_models import Trace


logger = logging.getLogger(__name__)


class TraceStore:
    """Stores traces as JSON for human inspection."""
    
    def __init__(self, trace_dir: str = "data/traces"):
        """
        Initialize trace store.
        
        Args:
            trace_dir: Directory to store traces
        """
        self.trace_dir = Path(trace_dir)
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(f"{__name__}")
    
    def save(self, trace: Trace) -> Path:
        """
        Save trace as JSON.
        
        Args:
            trace: Trace to save
            
        Returns:
            Path to saved file
        """
        file_path = self.trace_dir / f"{trace.trace_id}.json"
        
        try:
            # Convert trace to dict
            trace_dict = trace.model_dump(mode='json')
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(trace_dict, f, indent=2)
            
            self.logger.info(f"Saved trace to {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to save trace: {e}")
            raise
    
    def load(self, trace_id: str) -> Optional[Trace]:
        """
        Load trace from JSON.
        
        Args:
            trace_id: Trace ID to load
            
        Returns:
            Trace or None
        """
        file_path = self.trace_dir / f"{trace_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                trace_dict = json.load(f)
            
            trace = Trace(**trace_dict)
            self.logger.info(f"Loaded trace from {file_path}")
            return trace
            
        except Exception as e:
            self.logger.error(f"Failed to load trace: {e}")
            return None
