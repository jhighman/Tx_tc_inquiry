"""
Tests for the writers module.
"""

import json
import os
import tempfile
from typing import Dict, List

import pytest

from arrestx.model import Charge, Record
from arrestx.writers import (
    write_json,
    write_csv,
    write_ndjson,
    validate_records,
    redact_records,
)


def create_test_record(name="SMITH, JOHN") -> Record:
    """Create a test record for use in tests."""
    from arrestx.parser import NAME_REGEX_STRICT, normalize_name
    
    name_match = NAME_REGEX_STRICT.match(name)
    name_normalized = normalize_name(name_match) if name_match else name
    
    record = {
        "name": name,
        "name_normalized": name_normalized,
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
    return record


def test_write_json():
    """Test writing records to JSON."""
    records = [create_test_record()]
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name
        
    try:
        # Write JSON
        write_json(records, tmp_path, pretty=True)
        
        # Read JSON back
        with open(tmp_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Verify content
        assert len(data) == 1
        assert data[0]["name"] == "SMITH, JOHN"
        assert data[0]["charges"][0]["booking_no"] == "25-0123456"
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_write_csv():
    """Test writing records to CSV."""
    records = [create_test_record()]
    
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name
        
    try:
        # Write CSV
        write_csv(records, tmp_path)
        
        # Read CSV back
        import csv
        with open(tmp_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        # Verify content
        assert len(rows) == 1
        assert rows[0]["name"] == "SMITH, JOHN"
        assert rows[0]["booking_no"] == "25-0123456"
        assert rows[0]["description"] == "NO VALID DL"
        assert rows[0]["address"] == "123 MAIN ST | ANYTOWN, TX 12345"
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_write_ndjson():
    """Test writing records to NDJSON."""
    records = [create_test_record(), create_test_record("JOHNSON, MARY")]
    
    with tempfile.NamedTemporaryFile(suffix=".ndjson", delete=False) as tmp:
        tmp_path = tmp.name
        
    try:
        # Write NDJSON
        write_ndjson(records, tmp_path)
        
        # Read NDJSON back
        with open(tmp_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        # Verify content
        assert len(lines) == 2
        assert json.loads(lines[0])["name"] == "SMITH, JOHN"
        assert json.loads(lines[1])["name"] == "JOHNSON, MARY"
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_write_ndjson_denormalized():
    """Test writing records to NDJSON in denormalized format."""
    # Create a record with multiple charges
    record = create_test_record()
    record["charges"].append({
        "booking_no": "25-0123457",
        "description": "FAILURE TO APPEAR"
    })
    records = [record]
    
    with tempfile.NamedTemporaryFile(suffix=".ndjson", delete=False) as tmp:
        tmp_path = tmp.name
        
    try:
        # Write denormalized NDJSON
        write_ndjson(records, tmp_path, denormalize=True)
        
        # Read NDJSON back
        with open(tmp_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        # Verify content
        assert len(lines) == 2  # One line per charge
        
        line1 = json.loads(lines[0])
        line2 = json.loads(lines[1])
        
        assert line1["name"] == "SMITH, JOHN"
        assert line2["name"] == "SMITH, JOHN"
        
        assert line1["charge"]["booking_no"] == "25-0123456"
        assert line2["charge"]["booking_no"] == "25-0123457"
        
        assert line1["charge"]["description"] == "NO VALID DL"
        assert line2["charge"]["description"] == "FAILURE TO APPEAR"
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_validate_records():
    """Test record validation."""
    # Valid record
    valid_record = create_test_record()
    assert validate_records([valid_record]) == []
    
    # Invalid record (missing name)
    invalid_record = create_test_record()
    invalid_record["name"] = ""
    errors = validate_records([invalid_record])
    assert len(errors) == 1
    assert "Missing name" in errors[0]
    
    # Invalid record (invalid booking number)
    invalid_record = create_test_record()
    invalid_record["charges"][0]["booking_no"] = "250123456"  # Missing dash
    errors = validate_records([invalid_record])
    assert len(errors) == 1
    assert "Invalid booking number format" in errors[0]
    
    # Invalid record (missing charge description)
    invalid_record = create_test_record()
    invalid_record["charges"][0]["description"] = ""
    errors = validate_records([invalid_record])
    assert len(errors) == 1
    assert "Missing charge description" in errors[0]
    
    # Invalid record (invalid date format)
    invalid_record = create_test_record()
    invalid_record["book_in_date"] = "01/02/2025"  # Wrong format
    errors = validate_records([invalid_record])
    assert len(errors) == 1
    assert "Invalid book-in date format" in errors[0]


def test_redact_records():
    """Test record redaction."""
    record = create_test_record()
    
    # Test redacting address
    redacted = redact_records([record], redact_address=True, hash_id=False)
    assert redacted[0]["address"] == ["[REDACTED]"]
    assert redacted[0]["identifier"] == "12345678"  # Unchanged
    
    # Test hashing identifier
    redacted = redact_records([record], redact_address=False, hash_id=True)
    assert redacted[0]["address"] == ["123 MAIN ST", "ANYTOWN, TX 12345"]  # Unchanged
    assert redacted[0]["identifier"] != "12345678"  # Hashed
    assert len(redacted[0]["identifier"]) == 64  # SHA-256 hash length
    
    # Test both redactions
    redacted = redact_records([record], redact_address=True, hash_id=True)
    assert redacted[0]["address"] == ["[REDACTED]"]
    assert redacted[0]["identifier"] != "12345678"
    assert len(redacted[0]["identifier"]) == 64