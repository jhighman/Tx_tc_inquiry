"""
Tests for the CLI module.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from arrestx.cli import main


@patch("arrestx.cli.parse_pdf")
@patch("arrestx.cli.write_outputs")
@patch("sys.argv", ["arrestx", "--in", "test.pdf", "--json", "out.json"])
def test_main_basic(mock_write_outputs, mock_parse_pdf):
    """Test basic CLI functionality."""
    # Create a temporary file
    with open("test.pdf", "w") as f:
        f.write("test")
    
    try:
        # Mock parse_pdf to return a list of records
        mock_parse_pdf.return_value = [{"name": "Test"}]
        
        # Run the CLI
        result = main()
        
        # Verify the result
        assert result == 0
        
        # Verify parse_pdf was called
        mock_parse_pdf.assert_called_once()
        assert mock_parse_pdf.call_args[0][0] == "test.pdf"
        
        # Verify write_outputs was called
        mock_write_outputs.assert_called_once()
        assert mock_write_outputs.call_args[0][0] == [{"name": "Test"}]
    finally:
        # Clean up
        if os.path.exists("test.pdf"):
            os.unlink("test.pdf")


@patch("arrestx.cli.parse_pdf", side_effect=Exception("Test error"))
@patch("sys.argv", ["arrestx", "--in", "test.pdf", "--json", "out.json"])
def test_main_error(mock_parse_pdf):
    """Test CLI error handling."""
    # Create a temporary file
    with open("test.pdf", "w") as f:
        f.write("test")
    
    try:
        # Run the CLI
        result = main()
        
        # Verify the result
        assert result == 1
    finally:
        # Clean up
        if os.path.exists("test.pdf"):
            os.unlink("test.pdf")


@patch("sys.argv", ["arrestx", "--in", "nonexistent.pdf", "--json", "out.json"])
def test_main_no_input_files():
    """Test CLI with no input files."""
    # Run the CLI with a non-existent file
    result = main()
    
    # Verify the result
    assert result == 1


@patch("arrestx.cli.process_daily_report")
@patch("sys.argv", ["arrestx", "fetch", "--url", "https://example.com/test.pdf"])
def test_fetch_command(mock_process_daily_report):
    """Test fetch command."""
    # Mock process_daily_report to return a result
    mock_process_daily_report.return_value = {
        "status": "success",
        "record_count": 10
    }
    
    # Run the fetch command
    result = main()
    
    # Verify the result
    assert result == 0
    
    # Verify process_daily_report was called
    mock_process_daily_report.assert_called_once()
    assert mock_process_daily_report.call_args[0][0] == "https://example.com/test.pdf"


@patch("arrestx.cli.process_daily_report")
@patch("sys.argv", ["arrestx", "fetch", "--url", "https://example.com/test.pdf"])
def test_fetch_command_error(mock_process_daily_report):
    """Test fetch command error handling."""
    # Mock process_daily_report to return an error
    mock_process_daily_report.return_value = {
        "status": "error",
        "error": "Test error"
    }
    
    # Run the fetch command
    result = main()
    
    # Verify the result
    assert result == 1