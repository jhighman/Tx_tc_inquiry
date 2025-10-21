"""
HTML-based parser module for Texas Extract.

This module provides an alternative parsing approach by converting PDFs to HTML
and then parsing the structured HTML tables, which is more reliable than
parsing raw text.
"""

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from arrestx.config import Config
from arrestx.log import get_logger
from arrestx.model import Record

# Try to import enhanced parser
try:
    from arrestx.html_parser_enhanced import parse_pdf_via_enhanced_html
    ENHANCED_PARSER_AVAILABLE = True
except ImportError:
    ENHANCED_PARSER_AVAILABLE = False

logger = get_logger(__name__)


def parse_pdf_via_html(path: str, cfg: Config) -> List[Record]:
    """
    Parse a PDF file by first converting it to HTML and then parsing the HTML structure.
    
    Args:
        path: Path to the PDF file
        cfg: Configuration
        
    Returns:
        List of extracted records
        
    Raises:
        ImportError: If required dependencies are not available
        RuntimeError: If PDF to HTML conversion fails
    """
    if not BS4_AVAILABLE:
        raise ImportError("BeautifulSoup4 is required for HTML parsing. Install with: pip install beautifulsoup4")
    
    logger.info(f"Parsing PDF via HTML conversion: {path}")
    
    # Check if enhanced parser should be used
    use_enhanced_parser = getattr(cfg.parsing, 'use_enhanced_html_parser', True)
    
    if use_enhanced_parser and ENHANCED_PARSER_AVAILABLE:
        try:
            logger.info("Attempting enhanced HTML parsing with multiple extraction methods")
            records = parse_pdf_via_enhanced_html(path, cfg)
            
            if records and len(records) > 0:
                logger.info(f"Enhanced HTML parsing successful: extracted {len(records)} records")
                return records
            else:
                logger.warning("Enhanced HTML parsing returned no records, falling back to standard HTML parsing")
        except Exception as e:
            logger.warning(f"Enhanced HTML parsing failed: {e}, falling back to standard HTML parsing")
    
    # Fallback to standard HTML parsing
    logger.info("Using standard HTML parsing")
    
    # Convert PDF to HTML
    html_content = convert_pdf_to_html(path, cfg)
    
    if not html_content:
        raise RuntimeError("Failed to convert PDF to HTML")
    
    # Parse HTML content
    records = parse_html_content(html_content, path, cfg)
    
    logger.info(f"Extracted {len(records)} records from HTML")
    return records


def convert_pdf_to_html(pdf_path: str, cfg: Config) -> Optional[str]:
    """
    Convert PDF to HTML using various methods.
    
    Args:
        pdf_path: Path to the PDF file
        cfg: Configuration
        
    Returns:
        HTML content as string, or None if conversion fails
    """
    # Try multiple conversion methods in order of preference
    methods = [
        _convert_with_pdfplumber,
        _convert_with_pdftohtml,
        _convert_with_pymupdf,
    ]
    
    for method in methods:
        try:
            logger.debug(f"Trying conversion method: {method.__name__}")
            html_content = method(pdf_path, cfg)
            if html_content:
                logger.info(f"Successfully converted PDF to HTML using {method.__name__}")
                return html_content
        except Exception as e:
            logger.warning(f"Conversion method {method.__name__} failed: {e}")
            continue
    
    logger.error("All PDF to HTML conversion methods failed")
    return None


def _convert_with_pdfplumber(pdf_path: str, cfg: Config) -> Optional[str]:
    """
    Convert PDF to HTML using pdfplumber by extracting table data.
    
    Args:
        pdf_path: Path to the PDF file
        cfg: Configuration
        
    Returns:
        HTML content as string, or None if conversion fails
    """
    try:
        import pdfplumber
        
        html_parts = ['<html><body>']
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                logger.debug(f"Processing page {page_num}")
                
                # Try to extract tables first
                tables = page.extract_tables()
                
                if tables:
                    for table_num, table in enumerate(tables):
                        html_parts.append(f'<table id="page_{page_num}_table_{table_num}">')
                        
                        for row_num, row in enumerate(table):
                            if row and any(cell for cell in row if cell):  # Skip empty rows
                                html_parts.append('<tr>')
                                for cell in row:
                                    cell_content = (cell or "").strip()
                                    # Use th for header rows, td for data rows
                                    tag = 'th' if row_num == 0 else 'td'
                                    html_parts.append(f'<{tag}>{cell_content}</{tag}>')
                                html_parts.append('</tr>')
                        
                        html_parts.append('</table>')
                else:
                    # Fallback: extract text and try to structure it
                    text = page.extract_text()
                    if text:
                        # Try to detect tabular structure in text
                        html_table = _text_to_html_table(text, page_num)
                        if html_table:
                            html_parts.append(html_table)
        
        html_parts.append('</body></html>')
        return '\n'.join(html_parts)
        
    except Exception as e:
        logger.error(f"pdfplumber conversion failed: {e}")
        return None


def _convert_with_pdftohtml(pdf_path: str, cfg: Config) -> Optional[str]:
    """
    Convert PDF to HTML using pdftohtml command-line tool.
    
    Args:
        pdf_path: Path to the PDF file
        cfg: Configuration
        
    Returns:
        HTML content as string, or None if conversion fails
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output"
            
            # Run pdftohtml command
            cmd = [
                "pdftohtml",
                "-c",  # Generate complex output
                "-s",  # Generate single HTML file
                "-noframes",  # Don't use frames
                str(pdf_path),
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Read the generated HTML file
                html_file = output_path.with_suffix('.html')
                if html_file.exists():
                    return html_file.read_text(encoding='utf-8')
            else:
                logger.warning(f"pdftohtml failed: {result.stderr}")
                
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning(f"pdftohtml not available or failed: {e}")
    except Exception as e:
        logger.error(f"pdftohtml conversion failed: {e}")
    
    return None


def _convert_with_pymupdf(pdf_path: str, cfg: Config) -> Optional[str]:
    """
    Convert PDF to HTML using PyMuPDF (fitz).
    
    Args:
        pdf_path: Path to the PDF file
        cfg: Configuration
        
    Returns:
        HTML content as string, or None if conversion fails
    """
    try:
        import fitz  # PyMuPDF
        
        html_parts = ['<html><body>']
        
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Get HTML representation of the page
            html = page.get_text("html")
            
            # Wrap in a div with page identifier
            html_parts.append(f'<div id="page_{page_num + 1}">')
            html_parts.append(html)
            html_parts.append('</div>')
        
        doc.close()
        
        html_parts.append('</body></html>')
        return '\n'.join(html_parts)
        
    except ImportError:
        logger.warning("PyMuPDF not available")
    except Exception as e:
        logger.error(f"PyMuPDF conversion failed: {e}")
    
    return None


def _text_to_html_table(text: str, page_num: int) -> Optional[str]:
    """
    Convert structured text to HTML table format.
    
    Args:
        text: Text content from PDF page
        page_num: Page number
        
    Returns:
        HTML table string, or None if no table structure detected
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if not lines:
        return None
    
    # Look for table header pattern
    header_pattern = re.compile(r'Inmate\s+Name.*Identifier.*Book\s+In\s+Date.*Booking.*Description', re.IGNORECASE)
    
    table_start = None
    for i, line in enumerate(lines):
        if header_pattern.search(line):
            table_start = i
            break
    
    if table_start is None:
        return None
    
    # Build HTML table
    html_parts = [f'<table id="page_{page_num}_text_table">']
    
    # Add header row
    html_parts.append('<tr>')
    html_parts.append('<th>Inmate Name</th>')
    html_parts.append('<th>Identifier CID</th>')
    html_parts.append('<th>Book In Date</th>')
    html_parts.append('<th>Booking No.</th>')
    html_parts.append('<th>Description</th>')
    html_parts.append('</tr>')
    
    # Process data rows
    current_row = {}
    
    for line in lines[table_start + 1:]:
        # Skip header/footer patterns
        if _is_header_or_footer(line):
            continue
        
        # Try to parse the line as a data row
        row_data = _parse_text_line_to_row(line)
        if row_data:
            if row_data.get('name'):
                # Start of new record
                if current_row:
                    html_parts.append(_row_to_html(current_row))
                current_row = row_data
            else:
                # Continuation of current record
                _merge_row_data(current_row, row_data)
    
    # Add the last row
    if current_row:
        html_parts.append(_row_to_html(current_row))
    
    html_parts.append('</table>')
    
    return '\n'.join(html_parts)


def _is_header_or_footer(line: str) -> bool:
    """Check if a line is a header or footer."""
    patterns = [
        r'^Daily Booked In Report$',
        r'^Inmates Booked In During the Past 24 Hours',
        r'^Page:\s*\d+\s+of\s+\d+$',
        r'^[-\s]{5,}$',
        r'^Report Date:',
    ]
    
    for pattern in patterns:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    
    return False


def _parse_text_line_to_row(line: str) -> Dict[str, str]:
    """Parse a text line into row data."""
    row = {}
    
    # Name pattern
    name_match = re.match(r'^([A-Z][A-Z\-\.\' ]+,\s+[A-Z][A-Z\-\.\' ]+)', line)
    if name_match:
        row['name'] = name_match.group(1).strip()
        line = line[name_match.end():].strip()
    
    # Identifier pattern
    id_match = re.search(r'\b(\d{6,8})\b', line)
    if id_match:
        row['identifier'] = id_match.group(1)
    
    # Date pattern
    date_match = re.search(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', line)
    if date_match:
        row['date'] = date_match.group(1)
    
    # Booking number pattern
    booking_match = re.search(r'\b(\d{2}-\d{6,7})\b', line)
    if booking_match:
        row['booking'] = booking_match.group(1)
        # Everything after booking number is description
        desc_start = booking_match.end()
        if desc_start < len(line):
            row['description'] = line[desc_start:].strip()
    
    return row


def _merge_row_data(current_row: Dict[str, str], new_data: Dict[str, str]) -> None:
    """Merge new data into current row."""
    for key, value in new_data.items():
        if key == 'description' and key in current_row:
            current_row[key] += ' ' + value
        elif key not in current_row or not current_row[key]:
            current_row[key] = value


def _row_to_html(row: Dict[str, str]) -> str:
    """Convert row data to HTML table row."""
    return (
        '<tr>'
        f'<td>{row.get("name", "")}</td>'
        f'<td>{row.get("identifier", "")}</td>'
        f'<td>{row.get("date", "")}</td>'
        f'<td>{row.get("booking", "")}</td>'
        f'<td>{row.get("description", "")}</td>'
        '</tr>'
    )


def parse_html_content(html_content: str, source_file: str, cfg: Config) -> List[Record]:
    """
    Parse HTML content to extract structured records.
    
    Args:
        html_content: HTML content as string
        source_file: Source PDF filename
        cfg: Configuration
        
    Returns:
        List of parsed records
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    records = []
    
    # Find all tables
    tables = soup.find_all('table')
    
    for table in tables:
        table_records = _parse_html_table(table, source_file, cfg)
        records.extend(table_records)
    
    logger.info(f"Parsed {len(records)} records from HTML tables")
    return records


def _parse_html_table(table, source_file: str, cfg: Config) -> List[Record]:
    """
    Parse a single HTML table to extract records.
    
    Args:
        table: BeautifulSoup table element
        source_file: Source PDF filename
        cfg: Configuration
        
    Returns:
        List of parsed records
    """
    records = []
    rows = table.find_all('tr')
    
    if not rows:
        return records
    
    # Find header row and determine column indices
    header_indices = _find_column_indices(rows[0])
    
    if not header_indices:
        logger.warning("Could not identify table columns")
        return records
    
    # Process data rows
    current_record = None
    
    for row in rows[1:]:  # Skip header row
        cells = row.find_all(['td', 'th'])
        
        if len(cells) < len(header_indices):
            # This might be a continuation row
            if current_record and cells:
                # Add to description of last charge
                additional_text = ' '.join(cell.get_text(strip=True) for cell in cells)
                if additional_text and current_record['charges']:
                    current_record['charges'][-1]['description'] += ' ' + additional_text
            continue
        
        # Extract data from cells
        row_data = _extract_row_data(cells, header_indices)
        
        if row_data.get('name'):
            # Start of new record
            if current_record:
                records.append(current_record)
            
            current_record = _create_record_from_row(row_data, source_file)
        elif current_record and (row_data.get('booking') or row_data.get('description')):
            # Additional charge for current record
            _add_charge_to_record(current_record, row_data)
    
    # Add the last record
    if current_record:
        records.append(current_record)
    
    return records


def _find_column_indices(header_row) -> Dict[str, int]:
    """
    Find the column indices for each field type.
    
    Args:
        header_row: BeautifulSoup row element
        
    Returns:
        Dictionary mapping field names to column indices
    """
    cells = header_row.find_all(['th', 'td'])
    indices = {}
    
    for i, cell in enumerate(cells):
        text = cell.get_text(strip=True).lower()
        
        if 'name' in text:
            indices['name'] = i
        elif 'identifier' in text or 'cid' in text:
            indices['identifier'] = i
        elif 'date' in text:
            indices['date'] = i
        elif 'booking' in text:
            indices['booking'] = i
        elif 'description' in text:
            indices['description'] = i
    
    return indices


def _extract_row_data(cells, header_indices: Dict[str, int]) -> Dict[str, str]:
    """
    Extract data from table row cells.
    
    Args:
        cells: List of BeautifulSoup cell elements
        header_indices: Column indices mapping
        
    Returns:
        Dictionary of extracted data
    """
    data = {}
    
    for field, index in header_indices.items():
        if index < len(cells):
            text = cells[index].get_text(strip=True)
            if text:
                data[field] = text
    
    return data


def _create_record_from_row(row_data: Dict[str, str], source_file: str) -> Record:
    """
    Create a new record from row data.
    
    Args:
        row_data: Extracted row data
        source_file: Source PDF filename
        
    Returns:
        New record
    """
    record = {
        'name': row_data.get('name', ''),
        'name_normalized': _normalize_name(row_data.get('name', '')),
        'street': [],
        'identifier': row_data.get('identifier'),
        'book_in_date': _normalize_date(row_data.get('date')),
        'charges': [],
        'source_file': source_file,
        'source_page_span': [1, 1],  # Will be updated if needed
        'parse_warnings': [],
        'ocr_used': False
    }
    
    # Add charge if present
    if row_data.get('booking') or row_data.get('description'):
        _add_charge_to_record(record, row_data)
    
    return record


def _add_charge_to_record(record: Record, row_data: Dict[str, str]) -> None:
    """
    Add a charge to a record.
    
    Args:
        record: Record to add charge to
        row_data: Row data containing charge information
    """
    charge = {
        'booking_no': row_data.get('booking', ''),
        'description': row_data.get('description', '')
    }
    
    record['charges'].append(charge)


def _normalize_name(name: str) -> str:
    """
    Normalize a name from "LAST, FIRST MIDDLE" to "First Middle Last".
    
    Args:
        name: Name in "LAST, FIRST MIDDLE" format
        
    Returns:
        Normalized name
    """
    if not name or ',' not in name:
        return name
    
    try:
        last, first_middle = name.split(',', 1)
        last = last.strip().title()
        first_middle = first_middle.strip().title()
        return f"{first_middle} {last}"
    except Exception:
        return name


def _normalize_date(date_str: Optional[str]) -> Optional[str]:
    """
    Normalize a date from MM/DD/YYYY to YYYY-MM-DD.
    
    Args:
        date_str: Date string in MM/DD/YYYY format
        
    Returns:
        Normalized date in YYYY-MM-DD format
    """
    if not date_str:
        return None
    
    try:
        month, day, year = date_str.split("/")
        month_int = int(month)
        day_int = int(day)
        if month_int < 1 or month_int > 12 or day_int < 1 or day_int > 31:
            return date_str
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except (ValueError, IndexError):
        return date_str