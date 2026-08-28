"""
Setup script for FailureForensicsTool.

Initializes:
- Project structure
- Database
- Configuration
"""

import os
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup():
    """Initialize project."""
    logger.info("Setting up FailureForensicsTool...")
    
    # Create directories
    dirs = [
        "data/traces",
        "data/datasets",
        "logs",
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")
    
    # Initialize database
    from src.storage.database import Database
    db = Database()
    logger.info("Database initialized")
    
    logger.info("Setup complete!")


if __name__ == "__main__":
    setup()
