"""
Command-line interface for Texas Extract.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

from arrestx.config import load_config
from arrestx.parser import parse_pdf
from arrestx.writers import write_outputs
from arrestx.web import process_daily_report, extract_report_date, backup_file
from arrestx.api import search_name

logger = logging.getLogger(__name__)

def setup_logging(level: str) -> None:
    """
    Set up logging.
    
    Args:
        level: Logging level
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def process_command(args: argparse.Namespace) -> int:
    """
    Process command-line arguments.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code
    """
    # Load configuration
    config = load_config(args.config)
    
    # Set up logging
    setup_logging(args.log_level or config.logging.level)
    
    # Process command
    if args.command == "fetch":
        result = process_daily_report(args.url, config, args.skip_if_existing)
        if result["status"] == "success":
            logger.info(f"Successfully processed report: {result.get('record_count', 0)} records")
            return 0
        else:
            logger.error(f"Failed to process report: {result.get('error')}")
            return 1
    elif args.command == "backup":
        if not args.date:
            logger.error("Date is required for backup command")
            return 1
        
        backup_path = backup_file(args.file, args.date)
        if backup_path:
            logger.info(f"Created backup: {backup_path}")
            return 0
        else:
            logger.error(f"Failed to create backup for {args.file}")
            return 1
    elif args.command == "search":
        # Search for a name in arrest records
        result = search_name(args.name, config, args.force_update)
        
        # Print the result
        if args.json:
            # Output as JSON
            print(json.dumps(result.to_dict(), indent=2))
        else:
            # Output as text
            if result.alerts:
                print(f"\n⚠️  {result.get_due_diligence_message()}")
                print("\nMatches found:")
                for i, alert in enumerate(result.alerts, 1):
                    print(f"\n--- Match {i} ---")
                    print(f"Name: {alert.name}")
                    print(f"Booking #: {alert.booking_no}")
                    print(f"Charge: {alert.description}")
                    print(f"Identifier: {alert.identifier}")
                    print(f"Book-in Date: {alert.book_in_date}")
                    print(f"Source: {alert.source}")
            else:
                print(f"\n✓ {result.get_due_diligence_message()}")
        
        return 0
    else:
        # Default command (process files)
        # Get input files
        input_files = []
        for path_pattern in args.input or config.input.paths:
            for path in Path().glob(path_pattern):
                if path.is_file():
                    input_files.append(str(path))
        
        if not input_files:
            logger.error("No input files found")
            return 1
        
        # Process each file
        all_records = []
        for file in input_files:
            logger.info(f"Processing {file}")
            records = parse_pdf(file, config)
            all_records.extend(records)
        
        # Write outputs
        write_outputs(all_records, config)
        
        logger.info(f"Processed {len(input_files)} files, extracted {len(all_records)} records")
        return 0

def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Texas Extract")
    parser.add_argument("--config", default="config.yaml", help="Path to configuration file")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Logging level")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Default command (process files)
    parser.add_argument("--in", dest="input", nargs="+", help="Input files")
    parser.add_argument("--json", help="JSON output file")
    parser.add_argument("--csv", help="CSV output file")
    parser.add_argument("--ndjson", help="NDJSON output file")
    parser.add_argument("--ocr-fallback", action="store_true", help="Use OCR as fallback")
    parser.add_argument("--redact-address", action="store_true", help="Redact address information")
    parser.add_argument("--hash-id", action="store_true", help="Hash identifiers")
    
    # Fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch and process daily report")
    fetch_parser.add_argument("--url", required=True, help="URL to fetch")
    fetch_parser.add_argument("--skip-if-existing", action="store_true", help="Skip if report already exists")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create backup of a report")
    backup_parser.add_argument("file", help="File to backup")
    backup_parser.add_argument("date", help="Date for backup (YYYY-MM-DD)")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for a name in arrest records")
    search_parser.add_argument("name", help="Name to search for (First Middle Last or Last, First Middle)")
    search_parser.add_argument("--force-update", action="store_true", help="Force update of the report")
    search_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    try:
        return process_command(args)
    except Exception as e:
        logger.exception(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())