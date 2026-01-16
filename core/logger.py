"""
Logging Configuration

Centralized logging setup for HomeCentralMaid.
Logs to both file and console with structured formatting.
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logging(
    log_dir: str = "logs",
    log_level: str = "INFO",
    app_name: str = "HomeCentralMaid"
) -> logging.Logger:
    """
    Configure application logging

    Creates a logger that outputs to both:
    - Console (for real-time monitoring)
    - File (for persistent logs, with date-stamped filename)

    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        app_name: Application name for logger

    Returns:
        Configured logger instance
    """
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Create log filename with date
    log_filename = log_path / f"{app_name.lower()}_{datetime.now().strftime('%Y%m%d')}.log"

    # Configure logging level
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Setup file handler
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Create app logger
    logger = logging.getLogger(app_name)

    logger.info(f"Logging initialized: level={log_level}, log_file={log_filename}")

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance

    Args:
        name: Logger name (typically module or class name)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
