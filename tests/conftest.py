"""
Pytest configuration and fixtures.
"""

import os
import tempfile
from typing import Dict, List

import pytest

from arrestx.config import Config
from arrestx.model import Charge, Record


@pytest.fixture
def sample_config():
    """Return a sample configuration."""
    return Config()


@pytest.fixture
def sample_charge() -> Charge:
    """Return a sample charge."""
    return {
        "booking_no": "25-0123456",
        "description": "NO VALID DL"
    }


@pytest.fixture
def sample_record() -> Record:
    """Return a sample record."""
    return {
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


@pytest.fixture
def sample_records() -> List[Record]:
    """Return a list of sample records."""
    return [
        {
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
        },
        {
            "name": "JOHNSON, MARY",
            "name_normalized": "Mary Johnson",
            "address": ["456 OAK AVE", "SOMEWHERE, TX 54321"],
            "identifier": "87654321",
            "book_in_date": "2025-01-03",
            "charges": [
                {
                    "booking_no": "25-0123457",
                    "description": "FAILURE TO APPEAR"
                },
                {
                    "booking_no": "25-0123458",
                    "description": "SPEEDING"
                }
            ],
            "source_file": "test.pdf",
            "source_page_span": [2, 2],
            "parse_warnings": [],
            "ocr_used": False
        }
    ]


@pytest.fixture
def sample_lines() -> List[str]:
    """Return a list of sample lines."""
    return [
        "Inmates Booked In During the Past 24 Hours  Report Date: 01/02/2025 Page: 1 of 1",
        "",
        "SMITH, JOHN",
        "123 MAIN ST",
        "ANYTOWN, TX 12345",
        "12345678 01/02/2025",
        "25-0123456 NO VALID DL",
        "",
        "JOHNSON, MARY",
        "456 OAK AVE",
        "SOMEWHERE, TX 54321",
        "87654321 01/03/2025",
        "25-0123457 FAILURE TO APPEAR",
        "25-0123458 SPEEDING"
    ]


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def temp_file():
    """Create a temporary file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    yield tmp_path
    
    # Clean up
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def temp_pdf():
    """Create a temporary PDF file."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"%PDF-1.4\n%\xc3\xa4\xc3\xbc\xc3\xb6\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>/Contents 4 0 R>>\nendobj\n4 0 obj\n<</Length 21>>stream\nBT\n/F1 12 Tf\n(Test) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000018 00000 n \n0000000066 00000 n \n0000000122 00000 n \n0000000210 00000 n \ntrailer\n<</Size 5/Root 1 0 R>>\nstartxref\n280\n%%EOF")
        tmp_path = tmp.name
    
    yield tmp_path
    
    # Clean up
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def expected_json() -> Dict:
    """Return expected JSON output."""
    return [
        {
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
        },
        {
            "name": "JOHNSON, MARY",
            "name_normalized": "Mary Johnson",
            "address": ["456 OAK AVE", "SOMEWHERE, TX 54321"],
            "identifier": "87654321",
            "book_in_date": "2025-01-03",
            "charges": [
                {
                    "booking_no": "25-0123457",
                    "description": "FAILURE TO APPEAR"
                },
                {
                    "booking_no": "25-0123458",
                    "description": "SPEEDING"
                }
            ],
            "source_file": "test.pdf",
            "source_page_span": [1, 1],
            "parse_warnings": [],
            "ocr_used": False
        }
    ]


@pytest.fixture
def expected_csv() -> str:
    """Return expected CSV output."""
    return """name,identifier,book_in_date,booking_no,description,address,source_file
SMITH, JOHN,12345678,2025-01-02,25-0123456,NO VALID DL,123 MAIN ST | ANYTOWN, TX 12345,test.pdf
JOHNSON, MARY,87654321,2025-01-03,25-0123457,FAILURE TO APPEAR,456 OAK AVE | SOMEWHERE, TX 54321,test.pdf
JOHNSON, MARY,87654321,2025-01-03,25-0123458,SPEEDING,456 OAK AVE | SOMEWHERE, TX 54321,test.pdf
"""