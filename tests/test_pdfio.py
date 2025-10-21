"""
Tests for the PDF I/O module.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from arrestx.config import Config
from arrestx.model import ParseError
from arrestx.pdfio import (
    extract_lines_from_pdf,
    extract_lines_from_pdf_parallel,
    extract_lines_from_pdf_sequential,
    extract_text_from_page,
    preprocess_lines,
    process_page,
)


@patch("arrestx.pdfio.pdfplumber")
def test_extract_text_from_page(mock_pdfplumber):
    """Test extracting text from a page."""
    # Mock page
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Test text"
    
    # Extract text
    text = extract_text_from_page(mock_page)
    
    # Verify text
    assert text == "Test text"
    mock_page.extract_text.assert_called_once()


@patch("arrestx.pdfio.apply_ocr_to_page")
def test_extract_text_from_page_empty(mock_apply_ocr):
    """Test extracting text from a page that returns empty text."""
    # Mock page
    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""
    
    # Extract text
    text = extract_text_from_page(mock_page)
    
    # Verify text
    assert text == ""
    mock_page.extract_text.assert_called_once()
    mock_apply_ocr.assert_not_called()


@patch("arrestx.pdfio.pdfplumber")
@patch("arrestx.pdfio.extract_text_from_page")
@patch("arrestx.pdfio.apply_ocr_to_page")
def test_extract_lines_from_pdf_sequential(mock_apply_ocr, mock_extract_text, mock_pdfplumber):
    """Test extracting lines from a PDF sequentially."""
    # Mock PDF
    mock_page1 = MagicMock()
    mock_page2 = MagicMock()
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page1, mock_page2]
    mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
    
    # Mock text extraction
    mock_extract_text.side_effect = ["Page 1 text", "Page 2 text"]
    
    # Extract lines
    cfg = Config()
    lines = extract_lines_from_pdf_sequential("test.pdf", cfg)
    
    # Verify lines
    assert len(lines) == 2
    assert lines[0] == ["Page 1 text", "__META_OCR_USED:False"]
    assert lines[1] == ["Page 2 text", "__META_OCR_USED:False"]
    
    # Verify text extraction was called for each page
    assert mock_extract_text.call_count == 2
    mock_extract_text.assert_any_call(mock_page1)
    mock_extract_text.assert_any_call(mock_page2)
    
    # Verify OCR was not called
    mock_apply_ocr.assert_not_called()


@patch("arrestx.pdfio.pdfplumber")
@patch("arrestx.pdfio.extract_text_from_page")
@patch("arrestx.pdfio.apply_ocr_to_page")
def test_extract_lines_from_pdf_sequential_with_ocr(mock_apply_ocr, mock_extract_text, mock_pdfplumber):
    """Test extracting lines from a PDF sequentially with OCR fallback."""
    # Mock PDF
    mock_page1 = MagicMock()
    mock_page2 = MagicMock()
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page1, mock_page2]
    mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
    
    # Mock text extraction (empty for page 1, text for page 2)
    mock_extract_text.side_effect = ["", "Page 2 text"]
    
    # Mock OCR
    mock_apply_ocr.return_value = "OCR text"
    
    # Extract lines
    cfg = Config()
    cfg.input.ocr_fallback = True
    lines = extract_lines_from_pdf_sequential("test.pdf", cfg)
    
    # Verify lines
    assert len(lines) == 2
    assert lines[0] == ["OCR text", "__META_OCR_USED:True"]
    assert lines[1] == ["Page 2 text", "__META_OCR_USED:False"]
    
    # Verify text extraction was called for each page
    assert mock_extract_text.call_count == 2
    mock_extract_text.assert_any_call(mock_page1)
    mock_extract_text.assert_any_call(mock_page2)
    
    # Verify OCR was called for page 1
    mock_apply_ocr.assert_called_once_with(mock_page1, "eng")


@patch("arrestx.pdfio.concurrent.futures.ThreadPoolExecutor")
@patch("arrestx.pdfio.pdfplumber")
def test_extract_lines_from_pdf_parallel(mock_pdfplumber, mock_executor):
    """Test extracting lines from a PDF in parallel."""
    # Mock PDF
    mock_page1 = MagicMock()
    mock_page2 = MagicMock()
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page1, mock_page2]
    mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
    
    # Mock executor
    mock_executor_instance = MagicMock()
    mock_executor.return_value.__enter__.return_value = mock_executor_instance
    mock_executor_instance.map.return_value = [
        (1, ["Page 1 text", "__META_OCR_USED:False"]),
        (2, ["Page 2 text", "__META_OCR_USED:False"])
    ]
    
    # Extract lines
    cfg = Config()
    lines = extract_lines_from_pdf_parallel("test.pdf", cfg)
    
    # Verify lines
    assert len(lines) == 2
    assert lines[0] == ["Page 1 text", "__META_OCR_USED:False"]
    assert lines[1] == ["Page 2 text", "__META_OCR_USED:False"]
    
    # Verify executor was used
    mock_executor_instance.map.assert_called_once()


@patch("arrestx.pdfio.extract_text_from_page")
@patch("arrestx.pdfio.apply_ocr_to_page")
def test_process_page(mock_apply_ocr, mock_extract_text):
    """Test processing a single page."""
    # Mock text extraction
    mock_extract_text.return_value = "Page text"
    
    # Process page
    cfg = Config()
    result = process_page((1, MagicMock()), cfg)
    
    # Verify result
    assert result == (1, ["Page text", "__META_OCR_USED:False"])
    mock_extract_text.assert_called_once()
    mock_apply_ocr.assert_not_called()


@patch("arrestx.pdfio.extract_text_from_page")
@patch("arrestx.pdfio.apply_ocr_to_page")
def test_process_page_with_ocr(mock_apply_ocr, mock_extract_text):
    """Test processing a single page with OCR fallback."""
    # Mock text extraction (empty)
    mock_extract_text.return_value = ""
    
    # Mock OCR
    mock_apply_ocr.return_value = "OCR text"
    
    # Process page
    cfg = Config()
    cfg.input.ocr_fallback = True
    result = process_page((1, MagicMock()), cfg)
    
    # Verify result
    assert result == (1, ["OCR text", "__META_OCR_USED:True"])
    mock_extract_text.assert_called_once()
    mock_apply_ocr.assert_called_once()


@patch("arrestx.pdfio.extract_lines_from_pdf_parallel")
@patch("arrestx.pdfio.extract_lines_from_pdf_sequential")
def test_extract_lines_from_pdf_parallel_enabled(mock_sequential, mock_parallel):
    """Test extracting lines from a PDF with parallel processing enabled."""
    # Mock extraction functions
    mock_parallel.return_value = [["Line 1"], ["Line 2"]]
    
    # Extract lines
    cfg = Config()
    cfg.performance.parallel_pages = True
    lines = extract_lines_from_pdf("test.pdf", cfg)
    
    # Verify parallel extraction was used
    mock_parallel.assert_called_once_with("test.pdf", cfg)
    mock_sequential.assert_not_called()
    assert lines == [["Line 1"], ["Line 2"]]


@patch("arrestx.pdfio.extract_lines_from_pdf_parallel")
@patch("arrestx.pdfio.extract_lines_from_pdf_sequential")
def test_extract_lines_from_pdf_parallel_disabled(mock_sequential, mock_parallel):
    """Test extracting lines from a PDF with parallel processing disabled."""
    # Mock extraction functions
    mock_sequential.return_value = [["Line 1"], ["Line 2"]]
    
    # Extract lines
    cfg = Config()
    cfg.performance.parallel_pages = False
    lines = extract_lines_from_pdf("test.pdf", cfg)
    
    # Verify sequential extraction was used
    mock_sequential.assert_called_once_with("test.pdf", cfg)
    mock_parallel.assert_not_called()
    assert lines == [["Line 1"], ["Line 2"]]


@patch("arrestx.pdfio.extract_lines_from_pdf_sequential", side_effect=Exception("Test error"))
def test_extract_lines_from_pdf_error(mock_sequential):
    """Test error handling when extracting lines from a PDF."""
    # Extract lines
    cfg = Config()
    cfg.performance.parallel_pages = False
    
    # Verify error is raised
    with pytest.raises(ParseError) as excinfo:
        extract_lines_from_pdf("test.pdf", cfg)
    
    assert "Test error" in str(excinfo.value)


def test_preprocess_lines():
    """Test preprocessing lines."""
    # Create lines
    lines_per_page = [
        ["Inmates Booked In", "SMITH, JOHN", "123 MAIN ST", "__META_OCR_USED:False"],
        ["Page 2", "JOHNSON, MARY", "456 OAK AVE", "__META_OCR_USED:False"]
    ]
    
    # Preprocess lines
    cfg = Config()
    processed_lines = preprocess_lines(lines_per_page, cfg)
    
    # Verify processed lines
    assert processed_lines == [
        "SMITH, JOHN",
        "123 MAIN ST",
        "JOHNSON, MARY",
        "456 OAK AVE",
        "__META_OCR_USED:False"
    ]


def test_preprocess_lines_with_ocr():
    """Test preprocessing lines with OCR metadata."""
    # Create lines
    lines_per_page = [
        ["Inmates Booked In", "SMITH, JOHN", "123 MAIN ST", "__META_OCR_USED:True"],
        ["Page 2", "JOHNSON, MARY", "456 OAK AVE", "__META_OCR_USED:False"]
    ]
    
    # Preprocess lines
    cfg = Config()
    processed_lines = preprocess_lines(lines_per_page, cfg)
    
    # Verify processed lines
    assert processed_lines == [
        "SMITH, JOHN",
        "123 MAIN ST",
        "JOHNSON, MARY",
        "456 OAK AVE",
        "__META_OCR_USED:True"
    ]