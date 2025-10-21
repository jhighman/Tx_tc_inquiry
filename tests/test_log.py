"""
Tests for the logging module.
"""

import logging
from unittest.mock import patch

import pytest

from arrestx.config import Config, LoggingConfig
from arrestx.log import configure_logging, get_logger


def test_get_logger():
    """Test getting a logger."""
    logger = get_logger("test")
    
    # Verify logger
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test"


@patch("arrestx.log.logging.basicConfig")
def test_configure_logging_default(mock_basicConfig):
    """Test configuring logging with default settings."""
    # Configure logging
    configure_logging()
    
    # Verify basicConfig was called with correct arguments
    mock_basicConfig.assert_called_once()
    args = mock_basicConfig.call_args[1]
    assert args["level"] == logging.INFO
    assert "format" in args
    assert "datefmt" in args


@patch("arrestx.log.logging.basicConfig")
def test_configure_logging_with_config(mock_basicConfig):
    """Test configuring logging with custom config."""
    # Create config
    cfg = Config(logging=LoggingConfig(level="DEBUG"))
    
    # Configure logging
    configure_logging(cfg)
    
    # Verify basicConfig was called with correct arguments
    mock_basicConfig.assert_called_once()
    args = mock_basicConfig.call_args[1]
    assert args["level"] == logging.DEBUG
    assert "format" in args
    assert "datefmt" in args


@patch("arrestx.log.logging.basicConfig")
def test_configure_logging_invalid_level(mock_basicConfig):
    """Test configuring logging with invalid level."""
    # Create config
    cfg = Config(logging=LoggingConfig(level="INVALID"))
    
    # Configure logging
    with pytest.raises(ValueError) as excinfo:
        configure_logging(cfg)
    
    # Verify error message
    assert "Invalid log level" in str(excinfo.value)
    
    # Verify basicConfig was not called
    mock_basicConfig.assert_not_called()


@patch("arrestx.log.logging.basicConfig")
def test_configure_logging_warn_level(mock_basicConfig):
    """Test configuring logging with WARN level."""
    # Create config
    cfg = Config(logging=LoggingConfig(level="WARN"))
    
    # Configure logging
    configure_logging(cfg)
    
    # Verify basicConfig was called with correct arguments
    mock_basicConfig.assert_called_once()
    args = mock_basicConfig.call_args[1]
    assert args["level"] == logging.WARNING  # WARN maps to WARNING
    assert "format" in args
    assert "datefmt" in args


@patch("arrestx.log.logging.basicConfig")
def test_configure_logging_error_level(mock_basicConfig):
    """Test configuring logging with ERROR level."""
    # Create config
    cfg = Config(logging=LoggingConfig(level="ERROR"))
    
    # Configure logging
    configure_logging(cfg)
    
    # Verify basicConfig was called with correct arguments
    mock_basicConfig.assert_called_once()
    args = mock_basicConfig.call_args[1]
    assert args["level"] == logging.ERROR
    assert "format" in args
    assert "datefmt" in args