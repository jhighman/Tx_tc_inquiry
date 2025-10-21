"""
Tests for the process_daily_report function in the web retrieval module.
"""

import os
import shutil
import tempfile
from unittest import mock

import pytest

from arrestx.config import Config
from arrestx.web import process_daily_report


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = Config()
    config.output.json_path = "test_output/arrests.json"
    config.output.csv_path = "test_output/arrests.csv"
    config.input.ocr_fallback = False
    return config


@mock.patch("arrestx.web.fetch_pdf")
@mock.patch("arrestx.web.extract_report_date")
@mock.patch("arrestx.web.backup_file")
@mock.patch("arrestx.web.parse_pdf")
@mock.patch("arrestx.writers.write_outputs")
def test_process_daily_report_success(
    mock_write_outputs, mock_parse_pdf, mock_backup_file, 
    mock_extract_report_date, mock_fetch_pdf, mock_config, temp_dir
):
    """Test processing a daily report successfully."""
    # Set up mocks
    mock_fetch_pdf.return_value = {
        "status": "success",
        "message": "File downloaded successfully",
        "modified": True
    }
    mock_extract_report_date.return_value = "2025-10-15"
    mock_backup_file.return_value = os.path.join(temp_dir, "archive", "01_2025-10-15.PDF")
    mock_parse_pdf.return_value = [{"name": "Test Person"}]
    
    # Create a test file to simulate an existing file
    output_dir = os.path.dirname(mock_config.output.json_path)
    os.makedirs(output_dir, exist_ok=True)
    test_file = os.path.join(output_dir, "01.PDF")
    with open(test_file, "wb") as f:
        f.write(b"Test content")
    
    try:
        # Call function
        result = process_daily_report("http://example.com/01.PDF", mock_config)
        
        # Verify results
        assert result["status"] == "success"
        assert result["record_count"] == 1
        
        # Verify backup was created
        assert mock_backup_file.called
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)


@mock.patch("arrestx.web.fetch_pdf")
def test_process_daily_report_not_modified(mock_fetch_pdf, mock_config):
    """Test processing a daily report that hasn't been modified."""
    # Set up mock
    mock_fetch_pdf.return_value = {
        "status": "not_modified",
        "message": "File not modified since last fetch",
        "modified": False
    }
    
    # Call function
    result = process_daily_report("http://example.com/01.PDF", mock_config)
    
    # Verify results
    assert result["status"] == "not_modified"