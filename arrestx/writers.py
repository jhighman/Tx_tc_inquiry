"""
Output writers for Texas Extract.
"""

import csv
import hashlib
import json
import os
import re
from typing import Dict, List, Optional

from arrestx.config import Config
from arrestx.log import get_logger
from arrestx.model import OutputError, Record

logger = get_logger(__name__)


def write_outputs(records: List[Record], cfg: Config) -> None:
    """
    Write records to all configured output formats.
    
    Args:
        records: List of records to write
        cfg: Application configuration
    """
    logger.info(f"Writing {len(records)} records to outputs")
    
    # Validate records
    validation_errors = validate_records(records)
    if validation_errors:
        for error in validation_errors:
            logger.warning(f"Validation error: {error}")
    
    # Write JSON if configured
    if cfg.output.json_path:
        write_json(records, cfg.output.json_path, cfg.output.pretty_json)
        
    # Write CSV if configured
    if cfg.output.csv_path:
        write_csv(records, cfg.output.csv_path)
        
    # Write NDJSON if configured
    if cfg.output.ndjson_path:
        write_ndjson(records, cfg.output.ndjson_path)


def write_json(records: List[Record], path: str, pretty: bool = True) -> None:
    """
    Write records to a JSON file.
    
    Args:
        records: List of records to write
        path: Output file path
        pretty: Whether to pretty-print the JSON
    """
    logger.info(f"Writing JSON to {path}")
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        
        # Write JSON file
        with open(path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(records, f, indent=2, ensure_ascii=False)
            else:
                json.dump(records, f, ensure_ascii=False)
                
        logger.info(f"Wrote {len(records)} records to {path}")
    except Exception as e:
        logger.error(f"Error writing JSON to {path}: {e}")
        raise OutputError(f"Error writing JSON to {path}: {e}")


def write_csv(records: List[Record], path: str) -> None:
    """
    Write records to a CSV file.
    
    Args:
        records: List of records to write
        path: Output file path
    """
    logger.info(f"Writing CSV to {path}")
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        
        # Define CSV columns
        fieldnames = ['name', 'identifier', 'book_in_date', 'booking_no', 
                     'description', 'address', 'source_file']
        
        # Write CSV file
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            row_count = 0
            for record in records:
                # Join address lines with pipe separator
                address = " | ".join(record.get("address", []))
                
                # Write one row per charge
                for charge in record.get("charges", []):
                    writer.writerow({
                        'name': record.get("name", ""),
                        'identifier': record.get("identifier", ""),
                        'book_in_date': record.get("book_in_date", ""),
                        'booking_no': charge.get("booking_no", ""),
                        'description': charge.get("description", ""),
                        'address': address,
                        'source_file': record.get("source_file", "")
                    })
                    row_count += 1
                    
        logger.info(f"Wrote {row_count} rows to {path}")
    except Exception as e:
        logger.error(f"Error writing CSV to {path}: {e}")
        raise OutputError(f"Error writing CSV to {path}: {e}")


def write_ndjson(records: List[Record], path: str, denormalize: bool = False) -> None:
    """
    Write records to an NDJSON file.
    
    Args:
        records: List of records to write
        path: Output file path
        denormalize: Whether to denormalize records (one line per charge)
    """
    logger.info(f"Writing NDJSON to {path}")
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        
        # Write NDJSON file
        with open(path, 'w', encoding='utf-8') as f:
            line_count = 0
            if denormalize:
                # Denormalized format (one line per charge)
                for record in records:
                    base_record = {k: v for k, v in record.items() if k != 'charges'}
                    for charge in record.get("charges", []):
                        line_record = base_record.copy()
                        line_record["charge"] = charge
                        f.write(json.dumps(line_record, ensure_ascii=False) + '\n')
                        line_count += 1
            else:
                # Normalized format (one line per record)
                for record in records:
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
                    line_count += 1
                    
        logger.info(f"Wrote {line_count} lines to {path}")
    except Exception as e:
        logger.error(f"Error writing NDJSON to {path}: {e}")
        raise OutputError(f"Error writing NDJSON to {path}: {e}")


def validate_records(records: List[Record]) -> List[str]:
    """
    Validate records before writing outputs.
    
    Args:
        records: List of records to validate
        
    Returns:
        List of validation errors
    """
    errors = []
    
    for i, record in enumerate(records):
        # Validate required fields
        if not record.get("name"):
            errors.append(f"Record {i}: Missing name")
            
        # Validate booking numbers
        for j, charge in enumerate(record.get("charges", [])):
            booking_no = charge.get("booking_no", "")
            if not re.match(r"^\d{2}-\d{6,7}$", booking_no):
                errors.append(f"Record {i}, Charge {j}: Invalid booking number format: {booking_no}")
                
            if not charge.get("description"):
                errors.append(f"Record {i}, Charge {j}: Missing charge description")
                
        # Validate date format
        book_in_date = record.get("book_in_date")
        if book_in_date and not re.match(r"^\d{4}-\d{2}-\d{2}$", book_in_date):
            errors.append(f"Record {i}: Invalid book-in date format: {book_in_date}")
            
    return errors


def redact_records(records: List[Record], redact_address: bool = False, hash_id: bool = False) -> List[Record]:
    """
    Redact sensitive information from records.
    
    Args:
        records: List of records to redact
        redact_address: Whether to redact address information
        hash_id: Whether to hash identifier
        
    Returns:
        Redacted records
    """
    logger.info(f"Redacting records (redact_address={redact_address}, hash_id={hash_id})")
    
    redacted = []
    
    for record in records:
        redacted_record = record.copy()
        
        # Redact address if requested
        if redact_address:
            redacted_record["address"] = ["[REDACTED]"]
            
        # Hash identifier if requested
        if hash_id and record.get("identifier"):
            redacted_record["identifier"] = hashlib.sha256(
                record["identifier"].encode()
            ).hexdigest()
            
        redacted.append(redacted_record)
        
    return redacted