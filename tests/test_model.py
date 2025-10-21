"""
Tests for the model module.
"""

import pytest

from arrestx.model import (
    ArrestXError,
    Charge,
    ConfigError,
    MongoDBError,
    OutputError,
    ParseError,
    ParserState,
    Record,
    WebRetrievalError,
)


def test_parser_state_enum():
    """Test ParserState enum."""
    # Verify enum values
    assert ParserState.SEEK_NAME.value == "seek_name"
    assert ParserState.CAPTURE_ADDRESS.value == "capture_address"
    assert ParserState.SEEK_ID_DATE.value == "seek_id_date"
    assert ParserState.CAPTURE_CHARGES.value == "capture_charges"


def test_charge_type():
    """Test Charge type."""
    # Create a charge
    charge: Charge = {
        "booking_no": "25-0123456",
        "description": "NO VALID DL"
    }
    
    # Verify charge
    assert charge["booking_no"] == "25-0123456"
    assert charge["description"] == "NO VALID DL"


def test_record_type():
    """Test Record type."""
    # Create a record
    record: Record = {
        "name": "SMITH, JOHN",
        "name_normalized": "John Smith",
        "address": ["123 MAIN ST", "ANYTOWN, TX 12345"],
        "identifier": "12345678",
        "book_in_date": "2025-01-02",
        "charges": [
            {
                "booking_no": "25-0123456",
                "description": "NO VALID DL"
            }
        ],
        "source_file": "test.pdf",
        "source_page_span": [1, 1],
        "parse_warnings": [],
        "ocr_used": False
    }
    
    # Verify record
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
    assert record["ocr_used"] is False


def test_record_type_optional_fields():
    """Test Record type with optional fields."""
    # Create a record with optional fields
    record: Record = {
        "name": "SMITH, JOHN",
        "charges": [],
        "source_file": "test.pdf",
        "source_page_span": [1, 1],
    }
    
    # Verify record
    assert record["name"] == "SMITH, JOHN"
    assert record["charges"] == []
    assert record["source_file"] == "test.pdf"
    assert record["source_page_span"] == [1, 1]
    
    # Optional fields should not be present
    assert "name_normalized" not in record
    assert "address" not in record
    assert "identifier" not in record
    assert "book_in_date" not in record
    assert "parse_warnings" not in record
    assert "ocr_used" not in record


def test_arrestx_error():
    """Test ArrestXError."""
    # Create an error
    error = ArrestXError("Test error")
    
    # Verify error
    assert str(error) == "Test error"
    assert isinstance(error, Exception)


def test_parse_error():
    """Test ParseError."""
    # Create an error
    error = ParseError("Test parse error")
    
    # Verify error
    assert str(error) == "Test parse error"
    assert isinstance(error, ArrestXError)
    assert isinstance(error, Exception)


def test_config_error():
    """Test ConfigError."""
    # Create an error
    error = ConfigError("Test config error")
    
    # Verify error
    assert str(error) == "Test config error"
    assert isinstance(error, ArrestXError)
    assert isinstance(error, Exception)


def test_output_error():
    """Test OutputError."""
    # Create an error
    error = OutputError("Test output error")
    
    # Verify error
    assert str(error) == "Test output error"
    assert isinstance(error, ArrestXError)
    assert isinstance(error, Exception)


def test_mongodb_error():
    """Test MongoDBError."""
    # Create an error
    error = MongoDBError("Test MongoDB error")
    
    # Verify error
    assert str(error) == "Test MongoDB error"
    assert isinstance(error, ArrestXError)
    assert isinstance(error, Exception)


def test_web_retrieval_error():
    """Test WebRetrievalError."""
    # Create an error
    error = WebRetrievalError("Test web retrieval error")
    
    # Verify error
    assert str(error) == "Test web retrieval error"
    assert isinstance(error, ArrestXError)
    assert isinstance(error, Exception)