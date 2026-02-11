"""Logging configuration for the stock-dashboard backend."""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with stdout handler and standard format.

    Args:
        level: Logging level string (e.g. "DEBUG", "INFO", "WARNING").
    """
    fmt = "%(asctime)s %(name)s %(levelname)s %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    # Avoid duplicate handlers on repeated calls
    if not root.handlers:
        root.addHandler(handler)
