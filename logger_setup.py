"""
Logger Setup Module

This module provides a consistent logging configuration for the entire application.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Global logger instance
logger = logging.getLogger("star_generator")
logger.setLevel(logging.INFO)

# Add a default console handler to ensure logging works even before setup_logging is called
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(console_handler)

def setup_logging(log_level=None, log_dir="logs", log_to_console=True, log_to_file=True):
    """
    Configure logging with consistent formatting across the application.
    
    Args:
        log_level (str, optional): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            Defaults to INFO if None or invalid.
        log_dir (str, optional): Directory for log files. Defaults to "logs".
        log_to_console (bool, optional): Whether to log to console. Defaults to True.
        log_to_file (bool, optional): Whether to log to file. Defaults to True.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    global logger
    
    # Convert string log level to logging constant
    if isinstance(log_level, str):
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            print(f"Invalid log level: {log_level}. Defaulting to INFO.")
            numeric_level = logging.INFO
    else:
        numeric_level = logging.INFO
    
    logger.setLevel(numeric_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        try:
            # Create log directory if it doesn't exist
            os.makedirs(log_dir, exist_ok=True)
            
            # Create a timestamped log file name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"star_generator_{timestamp}.log")
            
            # Create rotating file handler (10 MB max size, keep 5 backup files)
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=10*1024*1024,  # 10 MB
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            print(f"Logging to file: {log_file}")
            logger.info(f"Logging to file: {log_file}")
        except Exception as e:
            print(f"Failed to set up file logging: {e}")
            logger.error(f"Failed to set up file logging: {e}")
    
    print(f"Logging configured with level: {logging.getLevelName(numeric_level)}")
    logger.info(f"Logging configured with level: {logging.getLevelName(numeric_level)}")
    return logger

if __name__ == "__main__":
    # Example usage
    test_logger = setup_logging(log_level="DEBUG")
    
    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    test_logger.critical("This is a critical message")
