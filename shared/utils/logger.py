"""
Logging Configuration for SAFE-BMAD System
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from shared.config.settings import get_settings


def setup_logging():
    """
    Setup logging configuration for the application
    Creates structured logging with both file and console handlers
    """
    settings = get_settings()

    # Create logs directory if it doesn't exist
    log_file_path = Path(settings.log_file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatters
    if settings.log_format.lower() == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    try:
        # Parse log_max_size (e.g., "10MB")
        max_bytes = _parse_size(settings.log_max_size)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=settings.log_file,
            maxBytes=max_bytes,
            backupCount=settings.log_backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, settings.log_level))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        logging.warning(f"Failed to setup file logging: {e}")

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )
    logging.getLogger("redis").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    """
    return logging.getLogger(name)


def _parse_size(size_str: str) -> int:
    """
    Parse size string (e.g., "10MB") to bytes
    """
    size_str = size_str.upper().strip()

    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)


class JsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """

    def format(self, record):
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            }:
                log_entry[key] = value

        return self._json_serialize(log_entry)

    def _json_serialize(self, obj):
        """Serialize object to JSON string"""
        try:
            import json
            return json.dumps(obj, default=str, ensure_ascii=False)
        except ImportError:
            # Fallback if json is not available
            return str(obj)


class ContextFilter(logging.Filter):
    """
    Custom filter to add context information to log records
    """

    def __init__(self, request_id: Optional[str] = None, user_id: Optional[str] = None):
        super().__init__()
        self.request_id = request_id
        self.user_id = user_id

    def filter(self, record):
        """Add context information to log record"""
        if self.request_id:
            record.request_id = self.request_id
        if self.user_id:
            record.user_id = self.user_id
        return True


def setup_context_logging(request_id: str, user_id: Optional[str] = None):
    """
    Setup context logging for a specific request
    """
    context_filter = ContextFilter(request_id=request_id, user_id=user_id)

    # Add filter to all handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(context_filter)

    return context_filter


def remove_context_logging(context_filter: ContextFilter):
    """
    Remove context logging filter
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.removeFilter(context_filter)