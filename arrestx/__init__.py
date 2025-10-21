"""
Texas Extract - Arrest Record Extraction System.

A system for extracting structured arrest records from county jail "book-in" PDF reports.
"""

__version__ = "0.1.0"

from arrestx.model import Record, Charge, ParserState
from arrestx.config import Config, MongoDBConfig, load_config
from arrestx.parser import parse_pdf, parse_lines
from arrestx.writers import write_json, write_csv, write_ndjson, write_outputs
from arrestx.db.mongo import write_mongodb

__all__ = [
    "Record",
    "Charge",
    "ParserState",
    "Config",
    "MongoDBConfig",
    "load_config",
    "parse_pdf",
    "parse_lines",
    "write_json",
    "write_csv",
    "write_ndjson",
    "write_outputs",
    "write_mongodb",
]