"""
Simplified tests for the web retrieval module.
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
from arrestx.web import backup_file, extract_report_date


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