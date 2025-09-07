"""
Logging configuration for Survey Generation API
"""

import logging
import logging.handlers
import os
from pathlib import Path


def setup_logging(log_level: str = None) -> logging.Logger:
    """
    Set up logging configuration with rotating file handler.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Get log level from environment or parameter
    level = log_level or os.getenv("LOG_LEVEL", "INFO")
    
    # Configure root logger
    logger = logging.getLogger("survey_api")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "api.log",
        maxBytes=10_485_760,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Log startup message
    logger.info("=" * 60)
    logger.info("Survey Generation API Logger Initialized")
    logger.info(f"Log Level: {level}")
    logger.info(f"Log File: {log_dir / 'api.log'}")
    logger.info("=" * 60)
    
    return logger