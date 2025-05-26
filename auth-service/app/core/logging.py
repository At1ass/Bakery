"""
Logging configuration for the auth service
"""

import logging
import sys
from typing import Dict, Any

from .config import settings


def setup_logging() -> None:
    """
    Configure logging for the application.
    """
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    configure_loggers()


def configure_loggers() -> None:
    """
    Configure specific loggers with appropriate levels.
    """
    # Set uvicorn loggers to appropriate levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    
    # Set motor (MongoDB) logger to warning to reduce noise
    logging.getLogger("motor").setLevel(logging.WARNING)
    
    # Set our application logger
    logging.getLogger("app").setLevel(logging.DEBUG if settings.debug else logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: The logger name
        
    Returns:
        logging.Logger: The logger instance
    """
    return logging.getLogger(name)


# Application logger
logger = get_logger("app.auth") 