"""
Evaluation dataset management.

Provides:
- EvaluationDataset: Manages evaluation cases
"""

import logging
import json
from pathlib import Path
from typing import List, Optional

from src.models.evaluation_models import EvaluationCase


logger = logging.getLogger(__name__)


class EvaluationDataset:
    """Manages evaluation cases for regression testing."""
    
    def __init__(self, dataset_dir: str = "data/datasets"):
        """
        Initialize dataset.
        
        Args:
            dataset_dir: Directory for dataset files
        """
        self.dataset_dir = Path(dataset_dir)
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(f"{__name__}")
        self.cases: List[EvaluationCase] = []
    
    def add_case(self, case: EvaluationCase) -> None:
        """
        Add evaluation case to dataset.
        
        Args:
            case: Case to add
        """
        self.cases.append(case)
        self.logger.info(f"Added evaluation case {case.case_id}")
    
    def save(self) -> Path:
        """
        Save dataset to file.
        
        Returns:
            Path to saved file
        """
        file_path = self.dataset_dir / "evaluation_cases.json"
        
        try:
            cases_dict = [case.model_dump(mode='json') for case in self.cases]
            
            with open(file_path, 'w') as f:
                json.dump(cases_dict, f, indent=2)
            
            self.logger.info(f"Saved {len(self.cases)} cases to {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to save dataset: {e}")
            raise
    
    def load(self) -> None:
        """Load dataset from file."""
        file_path = self.dataset_dir / "evaluation_cases.json"
        
        if not file_path.exists():
            return
        
        try:
            with open(file_path, 'r') as f:
                cases_dict = json.load(f)
            
            self.cases = [EvaluationCase(**case) for case in cases_dict]
            self.logger.info(f"Loaded {len(self.cases)} cases from {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load dataset: {e}")
