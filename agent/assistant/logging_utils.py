import logging
import os


def get_logger(name: str) -> logging.Logger:
    """Return a configured module-level logger with consistent formatting.

    Honors LOG_LEVEL env var; defaults to INFO.
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger(name)
    if logger.handlers:
        # Already configured
        return logger

    logger.setLevel(level)

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def set_global_log_level(level_name: str) -> None:
    """Set root logger level dynamically (optional helper)."""
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.getLogger().setLevel(level)
