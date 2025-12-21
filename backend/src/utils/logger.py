"""
Logging infrastructure for the backend pipeline
"""
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "rag_pipeline",
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> logging.Logger:
    """
    Set up a logger with both file and console handlers

    Args:
        name: Name of the logger
        log_file: Path to the log file (optional, defaults to logs/pipeline.log)
        level: Logging level (default: INFO)
        log_format: Format string for log messages

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file is None:
        # Default to logs/pipeline.log
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "pipeline.log"

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Global logger instance
logger = setup_logger()