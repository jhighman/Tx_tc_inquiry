"""
Data models for Texas Extract.
"""

from enum import Enum
from typing import Dict, List, Optional, TypedDict, Union


class Charge(TypedDict):
    """
    Represents a booking charge.
    """

    booking_no: str  # Format: YY-XXXXXXX (2 digits, dash, 6-7 digits)
    description: str  # Free-text offense description


class Record(TypedDict, total=False):
    """
    Represents an inmate record.
    """

    name: str  # Format: "LASTNAME, FIRST MIDDLE"
    name_normalized: str  # Optional, format: "First Middle Last"
    street: List[str]  # 0-3 lines of street/address information
    identifier: Optional[str]  # 5-8 digit string, may be None
    book_in_date: Optional[str]  # ISO 8601 format (YYYY-MM-DD), may be None
    charges: List[Charge]  # List of booking charges
    source_file: str  # Source PDF filename
    source_page_span: List[int]  # [first_page, last_page] the record spans
    parse_warnings: List[str]  # Optional list of parsing warnings/errors
    ocr_used: bool  # Whether OCR was used to extract text
    _tenant: Optional[str]  # Multi-tenant identifier (for MongoDB)


class ParserState(Enum):
    """
    States for the parser state machine.
    """

    SEEK_NAME = "seek_name"
    CAPTURE_ADDRESS = "capture_address"
    SEEK_ID_DATE = "seek_id_date"
    CAPTURE_CHARGES = "capture_charges"


class ArrestXError(Exception):
    """Base class for all arrestx exceptions."""

    pass


class ParseError(ArrestXError):
    """Exception raised for parsing errors."""

    pass


class ConfigError(ArrestXError):
    """Exception raised for configuration errors."""

    pass


class OutputError(ArrestXError):
    """Exception raised for output errors."""

    pass


class MongoDBError(ArrestXError):
    """Exception raised for MongoDB errors."""

    pass


class WebRetrievalError(ArrestXError):
    """Exception raised for web retrieval errors."""

    pass