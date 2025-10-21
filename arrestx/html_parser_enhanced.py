"""
Enhanced HTML-based parser module for Texas Extract.

This module provides improved PDF to HTML conversion and parsing approaches
that can handle various HTML structures including positioned text elements.
"""

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import logging

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import tabula
    TABULA_AVAILABLE = True
except ImportError:
    TABULA_AVAILABLE = False

try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False

from arrestx.config import Config
from arrestx.log import get_logger
from arrestx.model import Record

logger = get_logger(__name__)


class EnhancedHTMLParser:
    """Enhanced HTML parser with multiple extraction strategies."""
    
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.extraction_methods = [
            self._extract_with_tabula,
            self._extract_with_camelot,
            self._extract_with_pymupdf_positioned,
            self._extract_with_pdfplumber_enhanced,
            self._extract_with_pdftohtml,
        ]
    
    def parse_pdf(self, path: str) -> List[Record]:
        """
        Parse a PDF file using enhanced HTML extraction methods.
        
        Args:
            path: Path to the PDF file
            
        Returns:
            List of extracted records
        """
        logger.info(f"Starting enhanced HTML parsing for: {path}")
        
        for method in self.extraction_methods:
            try:
                logger.debug(f"Trying extraction method: {method.__name__}")
                records = method(path)
                
                if records and len(records) > 0:
                    logger.info(f"Successfully extracted {len(records)} records using {method.__name__}")
                    return records
                else:
                    logger.debug(f"Method {method.__name__} returned no records")
                    
            except Exception as e:
                logger.warning(f"Method {method.__name__} failed: {e}")
                continue
        
        logger.error("All enhanced HTML extraction methods failed")
        return []
    
    def _extract_with_tabula(self, path: str) -> List[Record]:
        """Extract tables using tabula-py."""
        if not TABULA_AVAILABLE:
            raise ImportError("tabula-py not available")
        
        logger.debug("Extracting tables with tabula-py")
        
        # Try different tabula extraction strategies
        strategies = [
            {"lattice": True},  # For tables with clear borders
            {"stream": True},   # For tables without borders
            {"multiple_tables": True, "pages": "all"},
        ]
        
        for strategy in strategies:
            try:
                dfs = tabula.read_pdf(path, **strategy)
                
                if dfs and len(dfs) > 0:
                    records = self._convert_dataframes_to_records(dfs, path)
                    if records:
                        return records
                        
            except Exception as e:
                logger.debug(f"Tabula strategy {strategy} failed: {e}")
                continue
        
        return []
    
    def _extract_with_camelot(self, path: str) -> List[Record]:
        """Extract tables using camelot-py."""
        if not CAMELOT_AVAILABLE:
            raise ImportError("camelot-py not available")
        
        logger.debug("Extracting tables with camelot-py")
        
        # Try different camelot extraction strategies
        strategies = [
            {"flavor": "lattice"},  # For tables with clear borders
            {"flavor": "stream"},   # For tables without borders
        ]
        
        for strategy in strategies:
            try:
                tables = camelot.read_pdf(path, **strategy)
                
                if tables and len(tables) > 0:
                    # Convert camelot tables to dataframes
                    dfs = [table.df for table in tables]
                    records = self._convert_dataframes_to_records(dfs, path)
                    if records:
                        return records
                        
            except Exception as e:
                logger.debug(f"Camelot strategy {strategy} failed: {e}")
                continue
        
        return []
    
    def _extract_with_pymupdf_positioned(self, path: str) -> List[Record]:
        """Extract data from PyMuPDF positioned text elements."""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("PyMuPDF not available")
        
        logger.debug("Extracting positioned text with PyMuPDF")
        
        doc = fitz.open(path)
        all_records = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Get text blocks with position information
            blocks = page.get_text("dict")
            
            # Convert positioned blocks to structured data
            records = self._parse_positioned_blocks(blocks, path, page_num + 1)
            all_records.extend(records)
        
        doc.close()
        return all_records
    
    def _extract_with_pdfplumber_enhanced(self, path: str) -> List[Record]:
        """Enhanced pdfplumber extraction with better table detection."""
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("pdfplumber not available")
        
        logger.debug("Enhanced extraction with pdfplumber")
        
        all_records = []
        
        with pdfplumber.open(path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Try multiple table extraction strategies
                strategies = [
                    {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
                    {"vertical_strategy": "text", "horizontal_strategy": "text"},
                    {"vertical_strategy": "explicit", "horizontal_strategy": "explicit"},
                ]
                
                for strategy in strategies:
                    try:
                        tables = page.extract_tables(table_settings=strategy)
                        
                        if tables:
                            for table in tables:
                                if table and len(table) > 1:  # Has header + data
                                    records = self._convert_table_to_records(table, path, page_num)
                                    all_records.extend(records)
                                    break  # Found valid tables, stop trying strategies
                    except Exception as e:
                        logger.debug(f"pdfplumber strategy {strategy} failed: {e}")
                        continue
                
                # If no tables found, try text-based extraction
                if not all_records:
                    text = page.extract_text()
                    if text:
                        records = self._parse_text_to_records(text, path, page_num)
                        all_records.extend(records)
        
        return all_records
    
    def _extract_with_pdftohtml(self, path: str) -> List[Record]:
        """Extract using pdftohtml command-line tool."""
        logger.debug("Extracting with pdftohtml")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / "output"
                
                # Run pdftohtml command with table-friendly options
                cmd = [
                    "pdftohtml",
                    "-c",  # Generate complex output
                    "-s",  # Generate single HTML file
                    "-noframes",  # Don't use frames
                    "-xml",  # Generate XML output for better structure
                    str(path),
                    str(output_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    # Read the generated HTML/XML file
                    html_file = output_path.with_suffix('.xml')
                    if not html_file.exists():
                        html_file = output_path.with_suffix('.html')
                    
                    if html_file.exists():
                        content = html_file.read_text(encoding='utf-8')
                        return self._parse_pdftohtml_content(content, path)
                        
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.debug(f"pdftohtml not available or failed: {e}")
        
        return []
    
    def _convert_dataframes_to_records(self, dfs: List, path: str) -> List[Record]:
        """Convert pandas DataFrames to Record objects."""
        records = []
        
        for df in dfs:
            if df.empty:
                continue
            
            # Try to identify column structure
            columns = df.columns.tolist()
            
            # Look for expected column patterns
            name_col = self._find_column_index(columns, ["name", "inmate"])
            id_col = self._find_column_index(columns, ["identifier", "id", "cid"])
            date_col = self._find_column_index(columns, ["date", "book"])
            booking_col = self._find_column_index(columns, ["booking", "no"])
            desc_col = self._find_column_index(columns, ["description", "charge"])
            
            if name_col is None:
                # Try using positional columns if headers aren't clear
                if len(columns) >= 5:
                    name_col, id_col, date_col, booking_col, desc_col = 0, 1, 2, 3, 4
                else:
                    continue
            
            # Convert rows to records
            for _, row in df.iterrows():
                try:
                    record = self._create_record_from_row(
                        row, path, name_col, id_col, date_col, booking_col, desc_col
                    )
                    if record:
                        records.append(record)
                except Exception as e:
                    logger.debug(f"Failed to convert row to record: {e}")
                    continue
        
        return records
    
    def _find_column_index(self, columns: List[str], patterns: List[str]) -> Optional[int]:
        """Find column index by matching patterns."""
        for i, col in enumerate(columns):
            col_lower = str(col).lower()
            for pattern in patterns:
                if pattern in col_lower:
                    return i
        return None
    
    def _create_record_from_row(self, row, path: str, name_col: int, id_col: int, 
                               date_col: int, booking_col: int, desc_col: int) -> Optional[Record]:
        """Create a Record from a table row."""
        try:
            name = str(row.iloc[name_col]) if name_col is not None else ""
            identifier = str(row.iloc[id_col]) if id_col is not None else ""
            date = str(row.iloc[date_col]) if date_col is not None else ""
            booking = str(row.iloc[booking_col]) if booking_col is not None else ""
            description = str(row.iloc[desc_col]) if desc_col is not None else ""
            
            # Clean up the data
            name = name.strip() if name != "nan" else ""
            identifier = identifier.strip() if identifier != "nan" else ""
            date = date.strip() if date != "nan" else ""
            booking = booking.strip() if booking != "nan" else ""
            description = description.strip() if description != "nan" else ""
            
            # Skip empty rows
            if not name and not identifier:
                return None
            
            # Parse address from name field if it contains line breaks
            street = []
            if "\n" in name:
                parts = name.split("\n")
                name = parts[0].strip()
                street = [part.strip() for part in parts[1:] if part.strip()]
            
            # Normalize name
            name_normalized = self._normalize_name(name)
            
            # Normalize date
            book_in_date = self._normalize_date(date)
            
            # Create charges
            charges = []
            if booking or description:
                charges.append({
                    "booking_no": booking,
                    "description": description
                })
            
            record = {
                "name": name,
                "name_normalized": name_normalized,
                "street": street,
                "identifier": identifier if identifier else None,
                "book_in_date": book_in_date,
                "charges": charges,
                "source_file": path,
                "source_page_span": [1, 1],
                "parse_warnings": [],
                "ocr_used": False
            }
            
            return record
            
        except Exception as e:
            logger.debug(f"Error creating record from row: {e}")
            return None
    
    def _parse_positioned_blocks(self, blocks: Dict, path: str, page_num: int) -> List[Record]:
        """Parse positioned text blocks from PyMuPDF."""
        # Extract text elements with their positions
        text_elements = []
        
        for block in blocks.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text:
                            bbox = span.get("bbox", [0, 0, 0, 0])
                            text_elements.append({
                                "text": text,
                                "x": bbox[0],
                                "y": bbox[1],
                                "width": bbox[2] - bbox[0],
                                "height": bbox[3] - bbox[1]
                            })
        
        # Sort by Y position (top to bottom), then X position (left to right)
        text_elements.sort(key=lambda x: (x["y"], x["x"]))
        
        # Group elements into logical rows based on Y position
        rows = self._group_elements_into_rows(text_elements)
        
        # Parse rows into records
        return self._parse_rows_to_records(rows, path, page_num)
    
    def _group_elements_into_rows(self, elements: List[Dict]) -> List[List[Dict]]:
        """Group text elements into rows based on Y position."""
        if not elements:
            return []
        
        rows = []
        current_row = [elements[0]]
        current_y = elements[0]["y"]
        
        for element in elements[1:]:
            # If Y position is close to current row, add to current row
            if abs(element["y"] - current_y) < 5:  # Reduced tolerance for better grouping
                current_row.append(element)
            else:
                # Start new row
                if current_row:
                    rows.append(sorted(current_row, key=lambda x: x["x"]))
                current_row = [element]
                current_y = element["y"]
        
        # Add the last row
        if current_row:
            rows.append(sorted(current_row, key=lambda x: x["x"]))
        
        return rows
    
    def _parse_rows_to_records(self, rows: List[List[Dict]], path: str, page_num: int) -> List[Record]:
        """Parse grouped rows into records."""
        records = []
        current_record = None
        
        for row in rows:
            row_text = " ".join([elem["text"] for elem in row])
            
            # Skip header/footer rows
            if self._is_header_or_footer(row_text):
                continue
            
            # Try to identify if this is a new record (contains a name)
            name_match = re.match(r'^([A-Z][A-Z\-\.\' ]+,\s+[A-Z][A-Z\-\.\' ]+)', row_text)
            
            if name_match:
                # Finalize previous record
                if current_record:
                    records.append(current_record)
                
                # Start new record
                current_record = self._create_new_record(path, page_num)
                current_record["name"] = name_match.group(1)
                current_record["name_normalized"] = self._normalize_name(name_match.group(1))
                
                # Extract other data from the same row
                remaining_text = row_text[name_match.end():].strip()
                self._extract_record_data(current_record, remaining_text)
            
            elif current_record:
                # This might be continuation data for the current record
                self._extract_record_data(current_record, row_text)
        
        # Add the last record
        if current_record:
            records.append(current_record)
        
        return records
    
    def _extract_record_data(self, record: Record, text: str) -> None:
        """Extract identifier, date, booking, and charges from text."""
        # Extract identifier
        if not record.get("identifier"):
            id_match = re.search(r'\b(\d{6,8})\b', text)
            if id_match:
                record["identifier"] = id_match.group(1)
        
        # Extract date
        if not record.get("book_in_date"):
            date_match = re.search(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', text)
            if date_match:
                record["book_in_date"] = self._normalize_date(date_match.group(1))
        
        # Extract booking number and description
        booking_match = re.search(r'\b(\d{2}-\d{6,7})\b\s*(.*)', text)
        if booking_match:
            booking_no = booking_match.group(1)
            description = booking_match.group(2).strip()
            
            record["charges"].append({
                "booking_no": booking_no,
                "description": description
            })
        
        # Enhanced address detection
        elif self._is_address_line(text):
            record["street"].append(text)
    
    def _is_address_line(self, text: str) -> bool:
        """Enhanced address line detection."""
        text = text.strip()
        if not text:
            return False
        
        # Skip if it contains booking numbers or identifiers
        if re.search(r'\b\d{2}-\d{6,7}\b', text) or re.search(r'\b\d{6,8}\b', text):
            return False
        
        # Skip if it contains dates
        if re.search(r'\b\d{1,2}/\d{1,2}/\d{4}\b', text):
            return False
        
        # Skip if it looks like a charge description
        charge_keywords = ['ASSAULT', 'THEFT', 'BURGLARY', 'DRIVING', 'POSS', 'CS', 'PG', 'DWI', 'WARRANT']
        if any(keyword in text.upper() for keyword in charge_keywords):
            return False
        
        # Positive indicators for address lines
        address_indicators = [
            r'\b\d+\s+[A-Za-z]',  # Street number + street name
            r'\b[A-Z]{2}\s+\d{5}',  # State + ZIP
            r'\b(ST|AVE|BLVD|DR|LN|RD|CT|WAY|CIR|TRL|PKWY|HWY|FWY)\b',  # Street suffixes
            r'\b(STREET|AVENUE|BOULEVARD|DRIVE|LANE|ROAD|COURT|WAY|CIRCLE|TRAIL|PARKWAY|HIGHWAY|FREEWAY)\b',
            r'\b(APT|UNIT|#|SUITE)\s*[A-Z0-9]',  # Apartment indicators
            r'\b(NORTH|SOUTH|EAST|WEST|N|S|E|W)\s+[A-Z]',  # Directional indicators
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in address_indicators)
    
    def _create_new_record(self, path: str, page_num: int) -> Record:
        """Create a new record with default values."""
        return {
            "name": "",
            "name_normalized": "",
            "street": [],
            "identifier": None,
            "book_in_date": None,
            "charges": [],
            "source_file": path,
            "source_page_span": [page_num, page_num],
            "parse_warnings": [],
            "ocr_used": False
        }
    
    def _normalize_name(self, name: str) -> str:
        """Normalize a name from 'LAST, FIRST MIDDLE' to 'First Middle Last'."""
        if not name or ',' not in name:
            return name
        
        try:
            last, first_middle = name.split(',', 1)
            last = last.strip().title()
            first_middle = first_middle.strip().title()
            return f"{first_middle} {last}"
        except Exception:
            return name
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize a date from MM/DD/YYYY to YYYY-MM-DD."""
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
    
    def _is_header_or_footer(self, text: str) -> bool:
        """Check if text is a header or footer."""
        patterns = [
            r'^Daily Booked In Report$',
            r'^Inmates Booked In During the Past 24 Hours',
            r'^Page:\s*\d+\s+of\s+\d+$',
            r'^[-\s]{5,}$',
            r'^Report Date:',
            r'^Inmate Name\s+Identifier',
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _convert_table_to_records(self, table: List[List[str]], path: str, page_num: int) -> List[Record]:
        """Convert a table (list of rows) to records."""
        if not table or len(table) < 2:
            return []
        
        # First row is usually headers
        headers = [str(cell).lower() if cell else "" for cell in table[0]]
        
        # Find column indices
        name_col = self._find_column_index(headers, ["name", "inmate"])
        id_col = self._find_column_index(headers, ["identifier", "id", "cid"])
        date_col = self._find_column_index(headers, ["date", "book"])
        booking_col = self._find_column_index(headers, ["booking", "no"])
        desc_col = self._find_column_index(headers, ["description", "charge"])
        
        records = []
        
        for row in table[1:]:  # Skip header row
            if not row or all(not cell for cell in row):
                continue
            
            try:
                # Create record from row
                record = self._create_new_record(path, page_num)
                
                if name_col is not None and name_col < len(row):
                    name = str(row[name_col]).strip()
                    if name and name != "nan":
                        record["name"] = name
                        record["name_normalized"] = self._normalize_name(name)
                
                if id_col is not None and id_col < len(row):
                    identifier = str(row[id_col]).strip()
                    if identifier and identifier != "nan":
                        record["identifier"] = identifier
                
                if date_col is not None and date_col < len(row):
                    date = str(row[date_col]).strip()
                    if date and date != "nan":
                        record["book_in_date"] = self._normalize_date(date)
                
                if (booking_col is not None and booking_col < len(row)) or \
                   (desc_col is not None and desc_col < len(row)):
                    booking = ""
                    description = ""
                    
                    if booking_col is not None and booking_col < len(row):
                        booking = str(row[booking_col]).strip()
                        if booking == "nan":
                            booking = ""
                    
                    if desc_col is not None and desc_col < len(row):
                        description = str(row[desc_col]).strip()
                        if description == "nan":
                            description = ""
                    
                    if booking or description:
                        record["charges"].append({
                            "booking_no": booking,
                            "description": description
                        })
                
                # Only add record if it has meaningful data
                if record["name"] or record["identifier"]:
                    records.append(record)
                    
            except Exception as e:
                logger.debug(f"Error processing table row: {e}")
                continue
        
        return records
    
    def _parse_text_to_records(self, text: str, path: str, page_num: int) -> List[Record]:
        """Parse plain text to records as fallback."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        records = []
        current_record = None
        
        for line in lines:
            if self._is_header_or_footer(line):
                continue
            
            # Look for name pattern
            name_match = re.match(r'^([A-Z][A-Z\-\.\' ]+,\s+[A-Z][A-Z\-\.\' ]+)', line)
            
            if name_match:
                # Finalize previous record
                if current_record:
                    records.append(current_record)
                
                # Start new record
                current_record = self._create_new_record(path, page_num)
                current_record["name"] = name_match.group(1)
                current_record["name_normalized"] = self._normalize_name(name_match.group(1))
                
                # Extract other data from the same line
                remaining = line[name_match.end():].strip()
                self._extract_record_data(current_record, remaining)
            
            elif current_record:
                self._extract_record_data(current_record, line)
        
        # Add the last record
        if current_record:
            records.append(current_record)
        
        return records
    
    def _parse_pdftohtml_content(self, content: str, path: str) -> List[Record]:
        """Parse pdftohtml XML/HTML content."""
        if not BS4_AVAILABLE:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        records = []
        
        # Look for text elements with position information
        text_elements = soup.find_all(['text', 'p', 'div'])
        
        # Group by position and parse
        positioned_texts = []
        for elem in text_elements:
            text = elem.get_text().strip()
            if text:
                # Try to get position from style or attributes
                style = elem.get('style', '')
                top_match = re.search(r'top:\s*(\d+)', style)
                left_match = re.search(r'left:\s*(\d+)', style)
                
                top = int(top_match.group(1)) if top_match else 0
                left = int(left_match.group(1)) if left_match else 0
                
                positioned_texts.append({
                    "text": text,
                    "x": left,
                    "y": top
                })
        
        # Sort and group into rows
        positioned_texts.sort(key=lambda x: (x["y"], x["x"]))
        rows = self._group_elements_into_rows(positioned_texts)
        
        # Parse rows to records
        return self._parse_rows_to_records(rows, path, 1)


def parse_pdf_via_enhanced_html(path: str, cfg: Config) -> List[Record]:
    """
    Parse a PDF file using enhanced HTML extraction methods.
    
    Args:
        path: Path to the PDF file
        cfg: Configuration
        
    Returns:
        List of extracted records
    """
    parser = EnhancedHTMLParser(cfg)
    return parser.parse_pdf(path)