"""
Tests for the web retrieval module.
"""

import os
import shutil
import tempfile
from datetime import datetime
from unittest import mock

import pytest
import requests

from arrestx.config import Config
from arrestx.model import WebRetrievalError
from arrestx.web import backup_file, extract_report_date, fetch_pdf, process_daily_report
from tests.test_helpers import MockWebRetrievalError


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_pdf(temp_dir):
    """Create a sample PDF file for testing."""
    # Create a mock PDF file
    pdf_path = os.path.join(temp_dir, "sample.pdf")
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.5\n")  # PDF header
        f.write(b"Mock PDF content")
    return pdf_path


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = Config()
    config.output.json_path = "test_output/arrests.json"
    config.output.csv_path = "test_output/arrests.csv"
    config.input.ocr_fallback = False
    
    # Add db configuration as a dictionary attribute
    # This is a workaround since we can't directly set attributes on Pydantic models
    setattr(config, '_db_enabled', False)
    
    return config


def test_backup_file(temp_dir, sample_pdf):
    """Test backing up a file with a report date."""
    # Set up test
    report_date = "2025-10-15"
    
    # Call function
    backup_path = backup_file(sample_pdf, report_date)
    
    # Verify results
    assert backup_path is not None
    assert os.path.exists(backup_path)
    assert "archive" in backup_path
    assert f"sample_{report_date}.pdf" in backup_path
    
    # Verify file content is the same
    with open(sample_pdf, "rb") as f1, open(backup_path, "rb") as f2:
        assert f1.read() == f2.read()


def test_backup_file_nonexistent(temp_dir):
    """Test backing up a nonexistent file."""
    # Set up test
    nonexistent_path = os.path.join(temp_dir, "nonexistent.pdf")
    report_date = "2025-10-15"
    
    # Call function
    backup_path = backup_file(nonexistent_path, report_date)
    
    # Verify results
    assert backup_path is None


def test_backup_file_existing_backup(temp_dir, sample_pdf):
    """Test backing up a file when backup already exists."""
    # Set up test
    report_date = "2025-10-15"
    
    # Create archive directory
    archive_dir = os.path.join(temp_dir, "archive")
    os.makedirs(archive_dir, exist_ok=True)
    
    # Create existing backup
    existing_backup = os.path.join(archive_dir, f"sample_{report_date}.pdf")
    with open(existing_backup, "wb") as f:
        f.write(b"Existing backup content")
    
    # Call function
    backup_path = backup_file(sample_pdf, report_date)
    
    # Verify results
    assert backup_path == existing_backup
    
    # Verify existing backup was not overwritten
    with open(existing_backup, "rb") as f:
        assert f.read() == b"Existing backup content"


@mock.patch("arrestx.web.pdf_open")
def test_extract_report_date(mock_pdf_open, temp_dir):
    """Test extracting report date from a PDF."""
    # Set up mock
    mock_pdf = mock.MagicMock()
    mock_page = mock.MagicMock()
    mock_page.extract_text.return_value = "Inmates Booked In\nReport Date: 10/15/2025\nPage 1"
    mock_pdf.pages = [mock_page]
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf
    
    # Call function
    report_date = extract_report_date("mock.pdf")
    
    # Verify results
    assert report_date == "2025-10-15"


@mock.patch("arrestx.web.pdf_open")
def test_extract_report_date_alternative_format(mock_pdf_open, temp_dir):
    """Test extracting report date from a PDF with alternative format."""
    # Set up mock
    mock_pdf = mock.MagicMock()
    mock_page = mock.MagicMock()
    mock_page.extract_text.return_value = "Inmates Booked In\nDate: 10/15/2025\nPage 1"
    mock_pdf.pages = [mock_page]
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf
    
    # Call function
    report_date = extract_report_date("mock.pdf")
    
    # Verify results
    assert report_date == "2025-10-15"


@mock.patch("arrestx.web.pdf_open")
def test_extract_report_date_not_found(mock_pdf_open, temp_dir):
    """Test extracting report date when not found in PDF."""
    # Set up mock
    mock_pdf = mock.MagicMock()
    mock_page = mock.MagicMock()
    mock_page.extract_text.return_value = "Inmates Booked In\nNo date here\nPage 1"
    mock_pdf.pages = [mock_page]
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf
    
    # Call function
    report_date = extract_report_date("mock.pdf")
    
    # Verify results
    assert report_date is None


@mock.patch("arrestx.web.requests.get")
def test_fetch_pdf_success(mock_get, temp_dir):
    """Test fetching a PDF successfully."""
    # Set up mock
    mock_response = mock.MagicMock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = [b"PDF content"]
    mock_response.headers = {"ETag": "123", "Last-Modified": "Wed, 15 Oct 2025 12:00:00 GMT"}
    mock_get.return_value = mock_response
    
    # Set up test
    output_path = os.path.join(temp_dir, "output.pdf")
    
    # Call function
    result = fetch_pdf("http://example.com/test.pdf", output_path)
    
    # Verify results
    assert result["status"] == "success"
    assert result["modified"] is True
    assert result["etag"] == "123"
    assert os.path.exists(output_path)
    
    # Verify file content
    with open(output_path, "rb") as f:
        assert f.read() == b"PDF content"


@mock.patch("arrestx.web.requests.get")
def test_fetch_pdf_not_modified(mock_get, temp_dir):
    """Test fetching a PDF that hasn't been modified."""
    # Set up mock
    mock_response = mock.MagicMock()
    mock_response.status_code = 304  # Not Modified
    mock_get.return_value = mock_response
    
    # Set up test
    output_path = os.path.join(temp_dir, "output.pdf")
    with open(output_path, "wb") as f:
        f.write(b"Existing content")
    
    # Call function
    result = fetch_pdf("http://example.com/test.pdf", output_path)
    
    # Verify results
    assert result["status"] == "not_modified"
    assert result["modified"] is False
    
    # Verify file content was not changed
    with open(output_path, "rb") as f:
        assert f.read() == b"Existing content"


@mock.patch("arrestx.web.requests.get")
def test_fetch_pdf_error(mock_get, temp_dir):
    """Test fetching a PDF with an error."""
    # Set up mock to raise a custom exception that we can catch
    mock_get.side_effect = mock.Mock(side_effect=requests.exceptions.RequestException("Connection error"))
    
    # Set up test
    output_path = os.path.join(temp_dir, "output.pdf")
    
    # Call function and verify exception
    with pytest.raises(WebRetrievalError):
        fetch_pdf("http://example.com/test.pdf", output_path)


@mock.patch("arrestx.web.fetch_pdf")
@mock.patch("arrestx.web.extract_report_date")
@mock.patch("arrestx.web.backup_file")
@mock.patch("arrestx.web.parse_pdf")
@mock.patch("arrestx.writers.write_outputs")  # Fix: mock the correct module
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


@mock.patch("arrestx.web.fetch_pdf")
def test_process_daily_report_error(mock_fetch_pdf, mock_config):
    """Test processing a daily report with an error."""
    # Set up mock to raise our custom exception
    mock_fetch_pdf.side_effect = MockWebRetrievalError("Failed to fetch PDF")
    
    # Call function and verify exception
    with pytest.raises(WebRetrievalError):
        process_daily_report("http://example.com/01.PDF", mock_config)