"""
Logging configuration for Agnira Voice Assistant.
Provides centralized logging setup and utilities.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from config.settings import settings

# Create logs directory if it doesn't exist
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Log file paths
LOG_FILE = os.path.join(LOG_DIR, f"agnira_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "agnira_errors.log")


def setup_logging() -> logging.Logger:
    """
    Configure logging for the application.

    Sets up:
    - Console handler with INFO level
    - File handler with DEBUG level
    - Error file handler with ERROR level
    - Custom formatter with timestamp and level

    Returns:
        logging.Logger: Configured root logger.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (all levels)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5  # 10 MB per file, keep 5 backups
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Error file handler (errors only)
    error_handler = logging.FileHandler(ERROR_LOG_FILE)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    root_logger.info(
        f"Logging initialized - Level: {settings.LOG_LEVEL}, "
        f"Environment: {settings.ENVIRONMENT}"
    )

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name (str): Module name (usually __name__).

    Returns:
        logging.Logger: Logger instance.
    """
    return logging.getLogger(name)
