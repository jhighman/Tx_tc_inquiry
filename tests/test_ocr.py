"""
Tests for the OCR module.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from arrestx.ocr import (
    apply_ocr_to_image,
    check_ocr_dependencies,
    convert_pdf_to_images,
    ocr_pdf_file,
    ocr_pdf_page,
)


@patch("arrestx.ocr.pytesseract", None)
@patch("arrestx.ocr.pdf2image", None)
def test_check_ocr_dependencies_not_installed():
    """Test checking OCR dependencies when they're not installed."""
    assert check_ocr_dependencies() is False


@patch("arrestx.ocr.pytesseract")
@patch("arrestx.ocr.pdf2image")
def test_check_ocr_dependencies_installed(mock_pdf2image, mock_pytesseract):
    """Test checking OCR dependencies when they're installed."""
    assert check_ocr_dependencies() is True


@patch("arrestx.ocr.pytesseract")
def test_apply_ocr_to_image(mock_pytesseract):
    """Test applying OCR to an image."""
    # Mock pytesseract
    mock_pytesseract.image_to_string.return_value = "OCR text"
    
    # Apply OCR
    text = apply_ocr_to_image("dummy_image", "eng")
    
    # Verify text
    assert text == "OCR text"
    mock_pytesseract.image_to_string.assert_called_once_with("dummy_image", lang="eng")


@patch("arrestx.ocr.pytesseract")
def test_apply_ocr_to_image_error(mock_pytesseract):
    """Test error handling when applying OCR to an image."""
    # Mock pytesseract to raise an exception
    mock_pytesseract.image_to_string.side_effect = Exception("Test error")
    
    # Apply OCR
    text = apply_ocr_to_image("dummy_image", "eng")
    
    # Verify text is empty
    assert text == ""
    mock_pytesseract.image_to_string.assert_called_once_with("dummy_image", lang="eng")


@patch("arrestx.ocr.convert_from_path")
def test_convert_pdf_to_images(mock_convert_from_path):
    """Test converting a PDF to images."""
    # Mock convert_from_path
    mock_images = [MagicMock(), MagicMock()]
    mock_convert_from_path.return_value = mock_images
    
    # Convert PDF to images
    images = convert_pdf_to_images("test.pdf", 300)
    
    # Verify images
    assert images == mock_images
    mock_convert_from_path.assert_called_once_with("test.pdf", dpi=300)


@patch("arrestx.ocr.convert_from_path")
def test_convert_pdf_to_images_error(mock_convert_from_path):
    """Test error handling when converting a PDF to images."""
    # Mock convert_from_path to raise an exception
    mock_convert_from_path.side_effect = Exception("Test error")
    
    # Convert PDF to images
    images = convert_pdf_to_images("test.pdf", 300)
    
    # Verify images is empty
    assert images == []
    mock_convert_from_path.assert_called_once_with("test.pdf", dpi=300)


@patch("arrestx.ocr.check_ocr_dependencies", return_value=False)
def test_ocr_pdf_file_dependencies_not_installed(mock_check_dependencies):
    """Test OCR PDF file when dependencies are not installed."""
    # OCR PDF file
    text = ocr_pdf_file("test.pdf")
    
    # Verify text is empty
    assert text == ""
    mock_check_dependencies.assert_called_once()


@patch("arrestx.ocr.check_ocr_dependencies", return_value=True)
@patch("arrestx.ocr.convert_pdf_to_images")
@patch("arrestx.ocr.apply_ocr_to_image")
def test_ocr_pdf_file(mock_apply_ocr, mock_convert_to_images, mock_check_dependencies):
    """Test OCR PDF file."""
    # Mock convert_pdf_to_images
    mock_images = [MagicMock(), MagicMock()]
    mock_convert_to_images.return_value = mock_images
    
    # Mock apply_ocr_to_image
    mock_apply_ocr.side_effect = ["Page 1 text", "Page 2 text"]
    
    # OCR PDF file
    text = ocr_pdf_file("test.pdf", "eng", 300)
    
    # Verify text
    assert text == "Page 1 text\n\nPage 2 text\n\n"
    mock_check_dependencies.assert_called_once()
    mock_convert_to_images.assert_called_once_with("test.pdf", 300)
    assert mock_apply_ocr.call_count == 2
    mock_apply_ocr.assert_any_call(mock_images[0], "eng")
    mock_apply_ocr.assert_any_call(mock_images[1], "eng")


@patch("arrestx.ocr.check_ocr_dependencies", return_value=True)
@patch("arrestx.ocr.convert_pdf_to_images", side_effect=Exception("Test error"))
def test_ocr_pdf_file_error(mock_convert_to_images, mock_check_dependencies):
    """Test error handling when OCR PDF file."""
    # OCR PDF file
    text = ocr_pdf_file("test.pdf")
    
    # Verify text is empty
    assert text == ""
    mock_check_dependencies.assert_called_once()
    mock_convert_to_images.assert_called_once_with("test.pdf", 300)


@patch("arrestx.ocr.check_ocr_dependencies", return_value=False)
def test_ocr_pdf_page_dependencies_not_installed(mock_check_dependencies):
    """Test OCR PDF page when dependencies are not installed."""
    # OCR PDF page
    text = ocr_pdf_page(MagicMock())
    
    # Verify text is empty
    assert text == ""
    mock_check_dependencies.assert_called_once()


@patch("arrestx.ocr.check_ocr_dependencies", return_value=True)
@patch("arrestx.ocr.convert_from_bytes")
@patch("arrestx.ocr.apply_ocr_to_image")
def test_ocr_pdf_page(mock_apply_ocr, mock_convert_from_bytes, mock_check_dependencies):
    """Test OCR PDF page."""
    # Mock page
    mock_page = MagicMock()
    mock_page.raw_page.data = b"test data"
    
    # Mock convert_from_bytes
    mock_images = [MagicMock(), MagicMock()]
    mock_convert_from_bytes.return_value = mock_images
    
    # Mock apply_ocr_to_image
    mock_apply_ocr.side_effect = ["Page 1 text", "Page 2 text"]
    
    # OCR PDF page
    text = ocr_pdf_page(mock_page, "eng", 300)
    
    # Verify text
    assert text == "Page 1 text\nPage 2 text\n"
    mock_check_dependencies.assert_called_once()
    mock_convert_from_bytes.assert_called_once_with(b"test data", dpi=300)
    assert mock_apply_ocr.call_count == 2
    mock_apply_ocr.assert_any_call(mock_images[0], "eng")
    mock_apply_ocr.assert_any_call(mock_images[1], "eng")


@patch("arrestx.ocr.check_ocr_dependencies", return_value=True)
@patch("arrestx.ocr.convert_from_bytes", side_effect=Exception("Test error"))
def test_ocr_pdf_page_error(mock_convert_from_bytes, mock_check_dependencies):
    """Test error handling when OCR PDF page."""
    # Mock page
    mock_page = MagicMock()
    mock_page.raw_page.data = b"test data"
    
    # OCR PDF page
    text = ocr_pdf_page(mock_page)
    
    # Verify text is empty
    assert text == ""
    mock_check_dependencies.assert_called_once()
    mock_convert_from_bytes.assert_called_once_with(b"test data", dpi=300)