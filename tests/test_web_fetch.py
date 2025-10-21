"""
Tests for the fetch_pdf function in the web retrieval module.
"""

import os
import shutil
import tempfile
from unittest import mock

import pytest
import requests

from arrestx.model import WebRetrievalError
from arrestx.web import fetch_pdf


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


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