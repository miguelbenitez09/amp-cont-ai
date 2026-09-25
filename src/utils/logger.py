"""
Centralized Logging Module for MLOps Pipeline.
Adheres to MLOps Masterclass Section 2.5: Professional structured logging.
"""

import logging
import os
import sys
from pathlib import Path

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

def setup_logger(name: str = "amp_mlops", log_file: str = "pipeline.log", level: int = logging.INFO) -> logging.Logger:
    """
    Configures and returns a logger instance with both console and file handlers.
    
    Args:
        name: Name of the logger.
        log_file: Name of the log file inside logs/.
        level: Logging level.
        
    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers if logger was already created
    if logger.handlers:
        return logger
        
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    file_path = LOGS_DIR / log_file
    file_handler = logging.FileHandler(file_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()
