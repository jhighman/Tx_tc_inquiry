"""
Tests for the parser module.
"""

import os
import re
from typing import Match

import pytest

from arrestx.model import ParserState, Record
from arrestx.parser import (
    NAME_REGEX_STRICT,
    NAME_REGEX_TOLERANT,
    ID_DATE_REGEX,
    BOOKING_REGEX,
    normalize_name,
    normalize_date,
    create_new_record,
    finalize_record,
    add_warning,
    parse_lines,
)


def test_name_regex_strict():
    """Test strict name regex pattern."""
    # Valid cases
    assert NAME_REGEX_STRICT.match("SMITH, JOHN")
    assert NAME_REGEX_STRICT.match("O'CONNOR, MARY JANE")
    assert NAME_REGEX_STRICT.match("JOHNSON-SMITH, ROBERT")
    
    # Invalid cases
    assert not NAME_REGEX_STRICT.match("Smith, John")  # Mixed case
    assert not NAME_REGEX_STRICT.match("SMITH JOHN")   # No comma
    assert not NAME_REGEX_STRICT.match("123, ABC")     # Invalid characters


def test_name_regex_tolerant():
    """Test tolerant name regex pattern."""
    # Valid cases
    assert NAME_REGEX_TOLERANT.match("SMITH, JOHN")
    assert NAME_REGEX_TOLERANT.match("Smith, John")      # Mixed case
    assert NAME_REGEX_TOLERANT.match("O'Connor, Mary")   # Mixed case with apostrophe
    
    # Invalid cases
    assert not NAME_REGEX_TOLERANT.match("SMITH JOHN")   # No comma
    assert not NAME_REGEX_TOLERANT.match("123, ABC")     # Invalid characters


def test_id_date_regex():
    """Test identifier and date regex pattern."""
    # Valid cases
    match = ID_DATE_REGEX.search("12345 01/02/2025")
    assert match
    assert match.group("id") == "12345"
    assert match.group("date") == "01/02/2025"
    
    match = ID_DATE_REGEX.search("Text before 12345 01/02/2025 text after")
    assert match
    assert match.group("id") == "12345"
    assert match.group("date") == "01/02/2025"
    
    # Invalid cases
    assert not ID_DATE_REGEX.search("1234 01/02/2025")  # ID too short
    assert not ID_DATE_REGEX.search("12345 01/02/25")   # Date wrong format


def test_booking_regex():
    """Test booking line regex pattern."""
    # Valid cases
    match = BOOKING_REGEX.match("25-0123456 NO VALID DL")
    assert match
    assert match.group("booking") == "25-0123456"
    assert match.group("desc") == "NO VALID DL"
    
    # Invalid cases
    assert not BOOKING_REGEX.match("250123456 NO VALID DL")  # No dash
    assert not BOOKING_REGEX.match("25-0123456")             # No description


def test_normalize_name():
    """Test name normalization."""
    # Test with strict regex
    match = NAME_REGEX_STRICT.match("SMITH, JOHN ROBERT")
    assert normalize_name(match) == "John Robert Smith"
    
    # Test with apostrophes and hyphens
    match = NAME_REGEX_STRICT.match("O'CONNOR-SMITH, MARY JANE")
    assert normalize_name(match) == "Mary Jane O'Connor-Smith"


def test_normalize_date():
    """Test date normalization."""
    assert normalize_date("1/2/2025") == "2025-01-02"
    assert normalize_date("01/02/2025") == "2025-01-02"
    assert normalize_date("12/31/2025") == "2025-12-31"
    
    # Invalid date should return original
    assert normalize_date("13/45/2025") == "13/45/2025"


def test_create_new_record():
    """Test record creation."""
    record = create_new_record("test.pdf", 1)
    
    assert record["name"] == ""
    assert record["name_normalized"] == ""
    assert record["address"] == []
    assert record["identifier"] is None
    assert record["book_in_date"] is None
    assert record["charges"] == []
    assert record["source_file"] == "test.pdf"
    assert record["source_page_span"] == [1, 1]
    assert record["parse_warnings"] == []


def test_finalize_record():
    """Test record finalization."""
    record = create_new_record("test.pdf", 1)
    finalize_record(record, 3)
    
    assert record["source_page_span"] == [1, 3]
    assert "Missing identifier" in record["parse_warnings"]
    assert "Missing book-in date" in record["parse_warnings"]
    assert "No charges found" in record["parse_warnings"]


def test_add_warning():
    """Test adding warnings to a record."""
    record = create_new_record("test.pdf", 1)
    
    # Add a warning
    add_warning(record, "Test warning")
    assert "Test warning" in record["parse_warnings"]
    
    # Add the same warning again (should not duplicate)
    add_warning(record, "Test warning")
    assert record["parse_warnings"].count("Test warning") == 1
    
    # Add a different warning
    add_warning(record, "Another warning")
    assert "Another warning" in record["parse_warnings"]
    assert len(record["parse_warnings"]) == 2


def test_parse_lines_single_record_single_charge():
    """Test parsing a single record with a single charge."""
    from arrestx.config import Config
    
    lines = [
        "SMITH, JOHN",
        "123 MAIN ST",
        "ANYTOWN, TX 12345",
        "12345678 01/02/2025",
        "25-0123456 NO VALID DL"
    ]
    
    records = parse_lines(lines, "test.pdf", Config())
    
    assert len(records) == 1
    record = records[0]
    
    assert record["name"] == "SMITH, JOHN"
    assert record["name_normalized"] == "John Smith"
    assert record["address"] == ["123 MAIN ST", "ANYTOWN, TX 12345"]
    assert record["identifier"] == "12345678"
    assert record["book_in_date"] == "2025-01-02"
    assert len(record["charges"]) == 1
    assert record["charges"][0]["booking_no"] == "25-0123456"
    assert record["charges"][0]["description"] == "NO VALID DL"
    assert record["source_file"] == "test.pdf"
    assert record["source_page_span"] == [1, 1]
    assert record["parse_warnings"] == []


def test_parse_lines_single_record_multiple_charges():
    """Test parsing a single record with multiple charges."""
    from arrestx.config import Config
    
    lines = [
        "SMITH, JOHN",
        "123 MAIN ST",
        "ANYTOWN, TX 12345",
        "12345678 01/02/2025",
        "25-0123456 NO VALID DL",
        "25-0123457 FAILURE TO APPEAR"
    ]
    
    records = parse_lines(lines, "test.pdf", Config())
    
    assert len(records) == 1
    record = records[0]
    
    assert len(record["charges"]) == 2
    assert record["charges"][0]["booking_no"] == "25-0123456"
    assert record["charges"][0]["description"] == "NO VALID DL"
    assert record["charges"][1]["booking_no"] == "25-0123457"
    assert record["charges"][1]["description"] == "FAILURE TO APPEAR"


def test_parse_lines_multiple_records():
    """Test parsing multiple records."""
    from arrestx.config import Config
    
    lines = [
        "SMITH, JOHN",
        "123 MAIN ST",
        "12345678 01/02/2025",
        "25-0123456 NO VALID DL",
        "JOHNSON, MARY",
        "456 OAK AVE",
        "87654321 01/03/2025",
        "25-0123458 SPEEDING"
    ]
    
    records = parse_lines(lines, "test.pdf", Config())
    
    assert len(records) == 2
    
    assert records[0]["name"] == "SMITH, JOHN"
    assert records[0]["charges"][0]["description"] == "NO VALID DL"
    
    assert records[1]["name"] == "JOHNSON, MARY"
    assert records[1]["charges"][0]["description"] == "SPEEDING"


def test_parse_lines_wrapped_charge():
    """Test parsing a charge with wrapped description."""
    from arrestx.config import Config
    
    lines = [
        "SMITH, JOHN",
        "123 MAIN ST",
        "12345678 01/02/2025",
        "25-0123456 DRIVING WHILE LICENSE",
        "INVALID - 2ND OFFENSE"
    ]
    
    records = parse_lines(lines, "test.pdf", Config())
    
    assert len(records) == 1
    assert records[0]["charges"][0]["description"] == "DRIVING WHILE LICENSE INVALID - 2ND OFFENSE"


def test_parse_lines_with_headers_footers():
    """Test parsing with headers and footers."""
    from arrestx.config import Config
    
    lines = [
        "Inmates Booked In Between 01/01/2025 and 01/31/2025",
        "Report Date: 02/01/2025",
        "Page 1",
        "SMITH, JOHN",
        "123 MAIN ST",
        "12345678 01/02/2025",
        "25-0123456 NO VALID DL",
        "Page 2",
        "JOHNSON, MARY",
        "456 OAK AVE",
        "87654321 01/03/2025",
        "25-0123458 SPEEDING"
    ]
    
    records = parse_lines(lines, "test.pdf", Config())
    
    assert len(records) == 2
    assert records[0]["name"] == "SMITH, JOHN"
    assert records[1]["name"] == "JOHNSON, MARY"