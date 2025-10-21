"""
PDF I/O utilities for Texas Extract.
"""

import concurrent.futures
import logging
import re
from typing import List, Optional

import pdfplumber

from arrestx.config import Config
from arrestx.log import get_logger
from arrestx.model import ParseError

logger = get_logger(__name__)


def extract_lines_from_pdf(path: str, cfg: Config) -> List[List[str]]:
    """
    Extract text lines from each page of a PDF.
    
    Args:
        path: Path to the PDF file
        cfg: Application configuration
        
    Returns:
        List of lists, where each inner list contains lines from one page
    """
    logger.info(f"Extracting text from {path}")
    
    try:
        # Use parallel processing if configured
        if cfg.performance.parallel_pages:
            return extract_lines_from_pdf_parallel(path, cfg)
        else:
            return extract_lines_from_pdf_sequential(path, cfg)
    except Exception as e:
        logger.error(f"Error extracting text from {path}: {e}")
        raise ParseError(f"Error extracting text from {path}: {e}")


def extract_lines_from_pdf_sequential(path: str, cfg: Config) -> List[List[str]]:
    """
    Extract text lines from each page of a PDF sequentially.
    
    Args:
        path: Path to the PDF file
        cfg: Application configuration
        
    Returns:
        List of lists, where each inner list contains lines from one page
    """
    lines_per_page = []
    
    # Use pdfplumber to extract text
    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            logger.debug(f"Processing page {page_num} of {len(pdf.pages)}")
            
            text = extract_text_from_page(page)
            
            # If text extraction failed and OCR fallback is enabled
            if (not text or text.isspace()) and cfg.input.ocr_fallback:
                logger.info(f"No text found on page {page_num}, using OCR fallback")
                text = apply_ocr_to_page(page, cfg.input.ocr_lang)
                ocr_used = True
            else:
                ocr_used = False
                
            # Split text into lines and clean
            page_lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Add OCR flag to metadata
            page_lines.append(f"__META_OCR_USED:{ocr_used}")
            
            lines_per_page.append(page_lines)
            
    return lines_per_page


def extract_lines_from_pdf_parallel(path: str, cfg: Config) -> List[List[str]]:
    """
    Extract text lines from each page of a PDF in parallel.
    
    Args:
        path: Path to the PDF file
        cfg: Application configuration
        
    Returns:
        List of lists, where each inner list contains lines from one page
    """
    # Use pdfplumber to extract text
    with pdfplumber.open(path) as pdf:
        pages = list(pdf.pages)
        
        # Process pages in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(
                lambda p: process_page(p, cfg),
                [(i+1, page) for i, page in enumerate(pages)]
            ))
            
    # Sort results by page number
    results.sort(key=lambda x: x[0])
    
    # Extract lines
    return [lines for _, lines in results]


def process_page(page_info: tuple, cfg: Config) -> tuple:
    """
    Process a single page.
    
    Args:
        page_info: Tuple of (page_num, page)
        cfg: Application configuration
        
    Returns:
        Tuple of (page_num, lines)
    """
    page_num, page = page_info
    logger.debug(f"Processing page {page_num}")
    
    text = extract_text_from_page(page)
    
    # If text extraction failed and OCR fallback is enabled
    if (not text or text.isspace()) and cfg.input.ocr_fallback:
        logger.info(f"No text found on page {page_num}, using OCR fallback")
        text = apply_ocr_to_page(page, cfg.input.ocr_lang)
        ocr_used = True
    else:
        ocr_used = False
        
    # Split text into lines and clean
    page_lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Add OCR flag to metadata
    page_lines.append(f"__META_OCR_USED:{ocr_used}")
    
    return (page_num, page_lines)


def extract_text_from_page(page) -> str:
    """
    Extract text from a PDF page.
    
    Args:
        page: PDF page object
        
    Returns:
        Extracted text as a string
    """
    try:
        # First try to extract text with position information
        return extract_text_with_layout(page) or page.extract_text() or ""
    except Exception as e:
        logger.warning(f"Error extracting text with layout, falling back to standard extraction: {e}")
        return page.extract_text() or ""


def extract_text_with_layout(page) -> str:
    """
    Extract text from a PDF page with layout awareness.
    
    This function extracts text while preserving the columnar layout of the PDF.
    It uses character position information to determine columns and reconstruct
    the text in a way that respects the visual layout.
    
    Args:
        page: PDF page object
        
    Returns:
        Extracted text as a string with layout preserved
    """
    # Extract character objects with position information
    chars = page.chars
    
    if not chars:
        return ""
    
    # Determine column boundaries by analyzing x-positions
    x_positions = [char['x0'] for char in chars]
    
    # Use clustering to identify column boundaries
    # This is a simple approach - we could use more sophisticated clustering algorithms
    x_positions.sort()
    
    # Calculate differences between consecutive x positions
    diffs = [x_positions[i+1] - x_positions[i] for i in range(len(x_positions)-1)]
    
    # Find large gaps that might indicate column boundaries
    # Use a threshold based on the average difference
    avg_diff = sum(diffs) / len(diffs) if diffs else 0
    threshold = avg_diff * 3  # Adjust this multiplier as needed
    
    column_boundaries = []
    for i, diff in enumerate(diffs):
        if diff > threshold:
            # This is a potential column boundary
            column_boundaries.append((x_positions[i] + x_positions[i+1]) / 2)
    
    # Add page boundaries
    page_width = page.width
    column_boundaries = [0] + column_boundaries + [page_width]
    
    # Group characters by line (y-position)
    line_groups = {}
    for char in chars:
        # Round y-position to group characters on the same line
        y_key = round(char['top'], 1)
        if y_key not in line_groups:
            line_groups[y_key] = []
        line_groups[y_key].append(char)
    
    # Sort lines by y-position
    sorted_lines = sorted(line_groups.items())
    
    # Process each line
    processed_text = []
    for y, line_chars in sorted_lines:
        # Sort characters by x-position
        line_chars.sort(key=lambda c: c['x0'])
        
        # Determine which column each character belongs to
        column_texts = [""] * (len(column_boundaries) - 1)
        
        for char in line_chars:
            x = char['x0']
            # Find which column this character belongs to
            for i in range(len(column_boundaries) - 1):
                if column_boundaries[i] <= x < column_boundaries[i+1]:
                    column_texts[i] += char['text']
                    break
        
        # Add non-empty column texts to the processed text
        line_text = " | ".join([text.strip() for text in column_texts if text.strip()])
        if line_text:
            processed_text.append(line_text)
    
    return "\n".join(processed_text)


def apply_ocr_to_page(page, lang: str) -> str:
    """
    Apply OCR to a PDF page.
    
    Args:
        page: PDF page object
        lang: OCR language
        
    Returns:
        Extracted text as a string
    """
    try:
        # Import OCR dependencies here to avoid requiring them if OCR is not used
        from pdf2image import convert_from_bytes
        import pytesseract
        
        # Convert page to image
        images = convert_from_bytes(page.raw_page.data)
        
        # Apply OCR to each image
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image, lang=lang) + "\n"
            
        return text
    except ImportError:
        logger.error("OCR dependencies not installed. Install with: pip install pdf2image pytesseract")
        return ""
    except Exception as e:
        logger.error(f"Error applying OCR: {e}")
        return ""


def preprocess_lines(lines_per_page: List[List[str]], cfg: Config) -> List[str]:
    """
    Preprocess text lines from all pages.
    
    Args:
        lines_per_page: List of lists, where each inner list contains lines from one page
        cfg: Application configuration
        
    Returns:
        Single list of processed lines
    """
    # Compile header/footer patterns
    header_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in cfg.parsing.header_patterns]
    
    # Flatten and process lines
    processed_lines = []
    ocr_used = False
    
    for page_lines in lines_per_page:
        # Extract metadata
        for i, line in enumerate(page_lines):
            if line.startswith("__META_OCR_USED:"):
                ocr_used = ocr_used or (line == "__META_OCR_USED:True")
                page_lines.pop(i)
                break
                
        for line in page_lines:
            # Skip headers and footers
            if any(pattern.search(line) for pattern in header_patterns):
                logger.debug(f"Skipping header/footer: {line}")
                continue
            
            # Process columnar data
            if " | " in line:
                processed_lines.extend(process_columnar_line(line))
            else:
                # Add line to processed lines
                processed_lines.append(line)
    
    # Add OCR metadata
    processed_lines.append(f"__META_OCR_USED:{ocr_used}")
            
    return processed_lines


def process_columnar_line(line: str) -> List[str]:
    """
    Process a line that contains columnar data.
    
    Args:
        line: Line with columnar data separated by " | "
        
    Returns:
        List of processed lines
    """
    # Split the line by the column separator
    columns = line.split(" | ")
    
    # Process each column
    processed_lines = []
    
    for column in columns:
        if not column.strip():
            continue
            
        # Check if this column contains a booking number
        booking_match = re.match(r"^(\d{2}-\d{6,7})\s+(.+)$", column)
        if booking_match:
            # This is a booking line
            booking_no = booking_match.group(1)
            description = booking_match.group(2)
            processed_lines.append(f"{booking_no} {description}")
        elif re.match(r"^\d{5,8}\s+\d{1,2}/\d{1,2}/\d{4}$", column):
            # This is an ID and date line
            processed_lines.append(column)
        elif re.match(r"^[A-Z][A-Z\-\.' ]+,\s+[A-Z][A-Z\-\.' ]+", column):
            # This is a name line
            processed_lines.append(column)
        elif re.match(r"^[A-Za-z\s]+\s+[A-Z]{2}\s+\d{5}(-\d{4})?$", column):
            # This is an address line
            processed_lines.append(column)
        else:
            # This is some other type of line
            processed_lines.append(column)
    
    return processed_lines