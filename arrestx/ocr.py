"""
OCR utilities for Texas Extract.
"""

import logging
import tempfile
from typing import Optional

from arrestx.log import get_logger

logger = get_logger(__name__)


def check_ocr_dependencies() -> bool:
    """
    Check if OCR dependencies are installed.
    
    Returns:
        True if dependencies are installed, False otherwise
    """
    try:
        import pdf2image
        import pytesseract
        return True
    except ImportError:
        logger.error("OCR dependencies not installed. Install with: pip install pdf2image pytesseract")
        return False


def apply_ocr_to_image(image, lang: str = "eng") -> str:
    """
    Apply OCR to an image.
    
    Args:
        image: Image object
        lang: OCR language
        
    Returns:
        Extracted text as a string
    """
    try:
        import pytesseract
        return pytesseract.image_to_string(image, lang=lang)
    except Exception as e:
        logger.error(f"Error applying OCR: {e}")
        return ""


def convert_pdf_to_images(pdf_path: str, dpi: int = 300) -> list:
    """
    Convert a PDF file to a list of images.
    
    Args:
        pdf_path: Path to the PDF file
        dpi: DPI for the images
        
    Returns:
        List of images
    """
    try:
        from pdf2image import convert_from_path
        return convert_from_path(pdf_path, dpi=dpi)
    except Exception as e:
        logger.error(f"Error converting PDF to images: {e}")
        return []


def ocr_pdf_file(pdf_path: str, lang: str = "eng", dpi: int = 300) -> str:
    """
    Apply OCR to a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        lang: OCR language
        dpi: DPI for the images
        
    Returns:
        Extracted text as a string
    """
    if not check_ocr_dependencies():
        return ""
    
    try:
        # Convert PDF to images
        images = convert_pdf_to_images(pdf_path, dpi)
        
        # Apply OCR to each image
        text = ""
        for i, image in enumerate(images):
            logger.debug(f"Applying OCR to page {i+1}")
            page_text = apply_ocr_to_image(image, lang)
            text += page_text + "\n\n"
            
        return text
    except Exception as e:
        logger.error(f"Error applying OCR to PDF: {e}")
        return ""


def ocr_pdf_page(page, lang: str = "eng", dpi: int = 300) -> str:
    """
    Apply OCR to a PDF page.
    
    Args:
        page: PDF page object
        lang: OCR language
        dpi: DPI for the image
        
    Returns:
        Extracted text as a string
    """
    if not check_ocr_dependencies():
        return ""
    
    try:
        # Import OCR dependencies
        from pdf2image import convert_from_bytes
        
        # Convert page to image
        images = convert_from_bytes(page.raw_page.data, dpi=dpi)
        
        # Apply OCR to the image
        text = ""
        for image in images:
            text += apply_ocr_to_image(image, lang) + "\n"
            
        return text
    except Exception as e:
        logger.error(f"Error applying OCR to page: {e}")
        return ""