"""Structured logging configuration with secret masking and standardized formatting."""
import logging
import re
import sys
from typing import Any, Dict

# Regex pattern to match potential API keys or tokens in logs
SECRET_PATTERNS = [
    re.compile(r'(?i)(key|token|secret|password|bearer|authorization)[:=\s]+(["\']?)([a-zA-Z0-9_\-\.]{8,})(["\']?)'),
]

class SecretMaskingFormatter(logging.Formatter):
    """Custom formatter that automatically obscures API tokens and sensitive credentials."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        masked = original
        for pattern in SECRET_PATTERNS:
            masked = pattern.sub(r'\1: \2***REDACTED***\4', masked)
        return masked

def setup_logger(name: str = "xauusd_agent", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a structured logger instance."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    # Ensure stdout handles UTF-8 emojis cleanly on Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    formatter = SecretMaskingFormatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s.%(funcName)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()
