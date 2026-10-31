"""Logging configuration for Lucy & Yak Shopify Harvester."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Union

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import LOG_FILE_PATH


def setup_logger(
    name: str = "LucyAndYakHarvester",
    log_file: Union[Path, str] = LOG_FILE_PATH,
    level: int = logging.INFO,
) -> logging.Logger:
    """Configures and returns a thread-safe logger with console and rotating file output.

    Args:
        name: Name of the logger instance.
        log_file: Path to destination log file.
        level: Logging level threshold.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)-8s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Rotating file handler (up to 5 MB per file, max 3 backups)
        file_handler = RotatingFileHandler(
            filename=str(log_path),
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

        # Standard console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    return logger


# Shared default logger instance
logger = setup_logger()
