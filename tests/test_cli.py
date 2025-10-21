"""
Tests for the CLI module.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner

from arrestx.cli import app, main


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@patch("arrestx.cli.parse_pdf")
@patch("arrestx.cli.write_outputs")
def test_main_basic(mock_write_outputs, mock_parse_pdf, runner):
    """Test basic CLI functionality."""
    # Create a temporary file
    with open("test.pdf", "w") as f:
        f.write("test")
    
    try:
        # Mock parse_pdf to return a list of records
        mock_parse_pdf.return_value = [{"name": "Test"}]
        
        # Run the CLI
        result = runner.invoke(app, ["--in", "test.pdf", "--json", "out.json"])
        
        # Verify the result
        assert result.exit_code == 0
        
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


@patch("arrestx.cli.parse_pdf")
@patch("arrestx.cli.write_outputs")
@patch("arrestx.cli.redact_records")
def test_main_with_redaction(mock_redact_records, mock_write_outputs, mock_parse_pdf, runner):
    """Test CLI with redaction options."""
    # Create a temporary file
    with open("test.pdf", "w") as f:
        f.write("test")
    
    try:
        # Mock parse_pdf to return a list of records
        mock_parse_pdf.return_value = [{"name": "Test"}]
        
        # Mock redact_records to return a list of redacted records
        mock_redact_records.return_value = [{"name": "Test", "address": ["[REDACTED]"]}]
        
        # Run the CLI with redaction options
        result = runner.invoke(app, [
            "--in", "test.pdf",
            "--json", "out.json",
            "--redact-address",
            "--hash-id"
        ])
        
        # Verify the result
        assert result.exit_code == 0
        
        # Verify parse_pdf was called
        mock_parse_pdf.assert_called_once()
        
        # Verify redact_records was called with correct options
        mock_redact_records.assert_called_once()
        assert mock_redact_records.call_args[0][0] == [{"name": "Test"}]
        assert mock_redact_records.call_args[1]["redact_address"] is True
        assert mock_redact_records.call_args[1]["hash_id"] is True
        
        # Verify write_outputs was called with redacted records
        mock_write_outputs.assert_called_once()
        assert mock_write_outputs.call_args[0][0] == [{"name": "Test", "address": ["[REDACTED]"]}]
    finally:
        # Clean up
        if os.path.exists("test.pdf"):
            os.unlink("test.pdf")


@patch("arrestx.cli.parse_pdf", side_effect=Exception("Test error"))
def test_main_error(mock_parse_pdf, runner):
    """Test CLI error handling."""
    # Create a temporary file
    with open("test.pdf", "w") as f:
        f.write("test")
    
    try:
        # Run the CLI
        result = runner.invoke(app, ["--in", "test.pdf", "--json", "out.json"])
        
        # Verify the result
        assert result.exit_code == 2
        assert "Error: Test error" in result.stdout
    finally:
        # Clean up
        if os.path.exists("test.pdf"):
            os.unlink("test.pdf")


def test_main_no_output(runner):
    """Test CLI with no output specified."""
    # Create a temporary file
    with open("test.pdf", "w") as f:
        f.write("test")
    
    try:
        # Run the CLI without specifying output
        result = runner.invoke(app, ["--in", "test.pdf"])
        
        # Verify the result
        assert result.exit_code == 2
        assert "Error: At least one output format must be specified" in result.stdout
    finally:
        # Clean up
        if os.path.exists("test.pdf"):
            os.unlink("test.pdf")


def test_main_no_input_files(runner):
    """Test CLI with no input files."""
    # Run the CLI with a non-existent file
    result = runner.invoke(app, ["--in", "nonexistent.pdf", "--json", "out.json"])
    
    # Verify the result
    assert result.exit_code == 2
    assert "Error: No input files found" in result.stdout


def test_version(runner):
    """Test CLI version option."""
    # Run the CLI with --version
    with patch("arrestx.cli.__version__", "1.0.0"):
        result = runner.invoke(app, ["--version"])
        
        # Verify the result
        assert result.exit_code == 0
        assert "arrestx version 1.0.0" in result.stdout


@patch("arrestx.cli.process_daily_report")
def test_fetch_command(mock_process_daily_report, runner):
    """Test fetch command."""
    # Mock process_daily_report to return a result
    mock_process_daily_report.return_value = {
        "status": "new",
        "message": "New report processed",
        "record_count": 10,
        "inserted_count": 10
    }
    
    # Run the fetch command
    result = runner.invoke(app, ["fetch", "--url", "https://example.com/test.pdf"])
    
    # Verify the result
    assert result.exit_code == 0
    assert "Status: new" in result.stdout
    assert "Message: New report processed" in result.stdout
    assert "Records: 10" in result.stdout
    assert "Inserted: 10" in result.stdout
    
    # Verify process_daily_report was called
    mock_process_daily_report.assert_called_once()
    assert mock_process_daily_report.call_args[0][0] == "https://example.com/test.pdf"


@patch("arrestx.cli.process_daily_report", side_effect=Exception("Test error"))
def test_fetch_command_error(mock_process_daily_report, runner):
    """Test fetch command error handling."""
    # Run the fetch command
    result = runner.invoke(app, ["fetch", "--url", "https://example.com/test.pdf"])
    
    # Verify the result
    assert result.exit_code == 2
    assert "Error: Test error" in result.stdout