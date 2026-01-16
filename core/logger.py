"""
Logging Configuration

Centralized logging setup for HomeCentralMaid.
Logs to both file and console with structured formatting.
Supports colorized console output for better readability.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Try to import colorama for Windows color support
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    # Fallback: define empty color codes
    class Fore:
        RED = ''
        YELLOW = ''
        GREEN = ''
        CYAN = ''
        WHITE = ''
        LIGHTBLACK_EX = ''

    class Style:
        BRIGHT = ''
        RESET_ALL = ''


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to log levels

    Color scheme:
    - DEBUG: Gray (Cyan dimmed)
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Bright Red
    """

    # Define color codes for each log level
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        # Save original levelname
        original_levelname = record.levelname

        # Add color to levelname if available
        if COLORAMA_AVAILABLE:
            color = self.COLORS.get(record.levelname, '')
            record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"

        # Format the message
        result = super().format(record)

        # Restore original levelname
        record.levelname = original_levelname

        return result


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

    # Create formatters
    # File formatter: plain text without colors
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console formatter: colorized for better readability
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Setup file handler
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)

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
