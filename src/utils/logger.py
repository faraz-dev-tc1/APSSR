"""
Logging utility
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


class Logger:
    """Custom logger for the system"""

    def __init__(self, name: str, log_dir: str = "logs"):
        """Initialize logger"""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Create logs directory
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        simple_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)

        # File handler
        log_file = log_path / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)

        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, **kwargs)


def get_logger(name: str) -> Logger:
    """Get or create logger instance"""
    return Logger(name)
