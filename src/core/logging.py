"""
Logging configuration using Loguru.
Redirects standard logging messages to Loguru for consistent formatting.
"""

import logging
import sys
from types import FrameType
from typing import cast

from loguru import logger

from src.core.config import settings


class InterceptHandler(logging.Handler):
    """
    Default handler from examples in loguru documentation.
    Intercepts standard logging messages and redirects them to Loguru.
    This allows us to see logs from Uvicorn and SQLAlchemy in Loguru format.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record.
        """
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = cast(FrameType, frame.f_back)
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    """
    Configures the logging system.
    Sets up Loguru to handle all log output.
    """
    # Define log names to intercept (Uvicorn, SQLAlchemy, etc.)
    logging_names = ["uvicorn", "uvicorn.access", "uvicorn.error"]

    # Intercept standard logging messages
    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    # Remove standard handlers from Uvicorn to avoid duplicate logs
    for name in logging_names:
        _logger = logging.getLogger(name)
        _logger.handlers = []
        _logger.propagate = False  # Prevent propagation to root logger

    logger.remove()  # Remove default handler

    log_level = "DEBUG" if settings.DEBUG else "INFO"

    logger.add(
        sys.stderr,
        level=log_level,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
        backtrace=True,
        diagnose=True,
    )

    logger.info(f"Logging configured via Loguru. Level: {log_level}")
