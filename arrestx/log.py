"""
Logging utilities for Texas Extract.
"""

import logging
from typing import Optional

from arrestx.config import Config


def configure_logging(config: Optional[Config] = None) -> None:
    """
    Configure logging based on configuration.
    
    Args:
        config: Configuration object
    """
    if config is None:
        level = "INFO"
    else:
        level = config.logging.level

    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)