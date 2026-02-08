"""
Pipeline module initialization.
"""
import logging
import os
from pathlib import Path

# Set up basic logging configuration for the pipeline system
def setup_logging():
    """Set up logging configuration for the pipeline system."""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Create logs directory if it doesn't exist
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.FileHandler(logs_dir / 'pipeline.log'),
            logging.StreamHandler()  # Also log to console
        ]
    )

# Set up logging when module is imported
setup_logging()