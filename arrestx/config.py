"""
Configuration module for Texas Extract.
"""

import os
from pathlib import Path
from typing import List, Optional, Union

import yaml
from pydantic import BaseModel, Field


class InputConfig(BaseModel):
    """
    Configuration for input.
    """

    paths: List[str] = ["./reports/*.pdf"]  # Input file paths/globs
    ocr_fallback: bool = False  # Whether to use OCR when text extraction fails
    ocr_lang: str = "eng"  # OCR language


class ParsingConfig(BaseModel):
    """
    Configuration for parsing.
    """

    name_regex_strict: bool = True  # Whether to use strict name regex
    allow_two_line_id_date: bool = True  # Support ID and date on separate lines
    header_patterns: List[str] = [  # Patterns to identify headers/footers
        r"^Inmates Booked In.*",
        r"^Report Date:.*",
        r"^Page\s+\d+.*",
    ]


class OutputConfig(BaseModel):
    """
    Configuration for output.
    """

    json_path: Optional[str] = "./out/arrests.json"  # JSON output path
    csv_path: Optional[str] = "./out/arrests.csv"  # CSV output path
    ndjson_path: Optional[str] = None  # NDJSON output path (disabled by default)
    pretty_json: bool = True  # Whether to pretty-print JSON


class LoggingConfig(BaseModel):
    """
    Configuration for logging.
    """

    level: str = "INFO"  # Logging level (DEBUG/INFO/WARN/ERROR)
    emit_warnings_in_record: bool = True  # Include warnings in record objects


class PerformanceConfig(BaseModel):
    """
    Configuration for performance.
    """

    parallel_pages: bool = True  # Process pages in parallel


class MongoDBConfig(BaseModel):
    """
    Configuration for MongoDB integration.
    """

    enabled: bool = False  # Whether MongoDB integration is enabled
    uri: str = "mongodb://localhost:27017"  # MongoDB connection URI
    database: str = "arrest_records"  # Database name
    collection: str = "arrest_records"  # Collection name
    tenant: str = "DEFAULT"  # Multi-tenant identifier


class WebRetrievalConfig(BaseModel):
    """
    Configuration for web retrieval.
    """

    enabled: bool = False  # Whether web retrieval is enabled
    url: str = "https://cjreports.tarrantcounty.com/Reports/JailedInmates/FinalPDF/01.PDF"  # URL to fetch
    schedule: str = "0 6 * * *"  # Cron schedule (run daily at 6:00 AM)
    skip_if_existing: bool = True  # Skip processing if report already exists


class Config(BaseModel):
    """
    Main configuration.
    """

    input: InputConfig = Field(default_factory=InputConfig)
    parsing: ParsingConfig = Field(default_factory=ParsingConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    mongodb: Optional[MongoDBConfig] = None  # MongoDB config (optional)
    web_retrieval: Optional[WebRetrievalConfig] = None  # Web retrieval config (optional)


def load_config(path: Optional[str] = None) -> Config:
    """
    Load configuration from a file.
    
    Args:
        path: Path to the configuration file
        
    Returns:
        Configuration object
    """
    if path:
        # Load configuration from file
        with open(path, "r") as f:
            if path.endswith(".yaml") or path.endswith(".yml"):
                config_dict = yaml.safe_load(f)
            elif path.endswith(".json"):
                import json

                config_dict = json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {path}")

        # Create configuration object
        return Config(**config_dict)
    else:
        # Try to load from default locations
        default_locations = [
            "./config.yaml",
            "./config.yml",
            "./config.json",
            os.path.expanduser("~/.config/arrestx/config.yaml"),
        ]

        for loc in default_locations:
            if os.path.exists(loc):
                return load_config(loc)

        # Return default configuration
        return Config()