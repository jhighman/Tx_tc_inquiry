#!/usr/bin/env python3
"""
Test script for the improved parser with a sample text file.
"""

import os
import sys
import json
import csv
from typing import List

from arrestx.config import Config
from arrestx.parser import parse_lines
from arrestx.model import Record


def main():
    """
    Main function to test the improved parser with a sample text file.
    """
    # Path to the sample text file
    sample_path = os.path.join("tests", "data", "embedded_names_sample.txt")
    
    # Create output directory if it doesn't exist
    out_dir = "./out"
    os.makedirs(out_dir, exist_ok=True)

    # Create configuration
    cfg = Config(
        input={
            "paths": [sample_path],
            "ocr_fallback": False,
            "ocr_lang": "eng"
        },
        parsing={
            "name_regex_strict": True,
            "allow_two_line_id_date": True,
            "header_patterns": [
                "^Inmates Booked In.*",
                "^Report Date:.*",
                "^Page\\s+\\d+.*",
                "^Inmate Name.*",
                "^Identifier.*",
                "^CID.*",
                "^Book In Date.*",
                "^Booking No\\..*",
                "^Description.*"
            ]
        },
        output={
            "json_path": os.path.join(out_dir, "sample_text.json"),
            "csv_path": os.path.join(out_dir, "sample_text.csv"),
            "ndjson_path": None,
            "pretty_json": True
        },
        logging={
            "level": "INFO",
            "emit_warnings_in_record": True
        },
        performance={
            "parallel_pages": True
        }
    )

    # Read the sample text file
    print(f"Reading {sample_path}...")
    try:
        with open(sample_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]
        
        # Parse the lines
        print(f"Parsing {len(lines)} lines...")
        records = parse_lines(lines, sample_path, cfg)
        print(f"Extracted {len(records)} records")

        # Write the records to JSON
        json_path = os.path.join(out_dir, "sample_text.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        print(f"Wrote {len(records)} records to {json_path}")

        # Write the records to CSV
        csv_path = os.path.join(out_dir, "sample_text.csv")
        write_csv(records, csv_path)
        print(f"Wrote {len(records)} records to {csv_path}")

        # Print statistics
        print_statistics(records)

        return 0
    except Exception as e:
        print(f"Error parsing text file: {e}")
        return 1


def write_csv(records: List[Record], csv_path: str) -> None:
    """
    Write records to a CSV file.
    
    Args:
        records: List of records
        csv_path: Path to the CSV file
    """
    import csv

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        
        # Write header
        writer.writerow(["name", "identifier", "book_in_date", "booking_no", "description", "address", "source_file"])
        
        # Write rows
        for record in records:
            name = record["name"]
            identifier = record["identifier"] or ""
            book_in_date = record["book_in_date"] or ""
            address = " | ".join(record["address"])
            source_file = record["source_file"]
            
            if record["charges"]:
                # One row per charge
                for charge in record["charges"]:
                    booking_no = charge["booking_no"]
                    description = charge["description"]
                    writer.writerow([name, identifier, book_in_date, booking_no, description, address, source_file])
            else:
                # No charges, write a single row
                writer.writerow([name, identifier, book_in_date, "", "", address, source_file])


def print_statistics(records: List[Record]) -> None:
    """
    Print statistics about the extracted records.
    
    Args:
        records: List of records
    """
    # Count records with missing fields
    missing_id = sum(1 for r in records if not r["identifier"])
    missing_date = sum(1 for r in records if not r["book_in_date"])
    missing_charges = sum(1 for r in records if not r["charges"])
    
    # Count records with warnings
    with_warnings = sum(1 for r in records if r["parse_warnings"])
    
    # Count total charges
    total_charges = sum(len(r["charges"]) for r in records)
    
    # Print statistics
    print("\nStatistics:")
    print(f"Total records: {len(records)}")
    print(f"Records with missing identifier: {missing_id} ({missing_id / len(records) * 100:.1f}%)")
    print(f"Records with missing book-in date: {missing_date} ({missing_date / len(records) * 100:.1f}%)")
    print(f"Records with missing charges: {missing_charges} ({missing_charges / len(records) * 100:.1f}%)")
    print(f"Records with warnings: {with_warnings} ({with_warnings / len(records) * 100:.1f}%)")
    print(f"Total charges: {total_charges}")
    print(f"Average charges per record: {total_charges / len(records):.1f}")
    
    # Print the most common warnings
    warnings = {}
    for record in records:
        for warning in record["parse_warnings"]:
            warnings[warning] = warnings.get(warning, 0) + 1
    
    if warnings:
        print("\nMost common warnings:")
        for warning, count in sorted(warnings.items(), key=lambda x: x[1], reverse=True):
            print(f"  {warning}: {count} ({count / len(records) * 100:.1f}%)")
    
    # Print record details
    print("\nRecord details:")
    for i, record in enumerate(records, 1):
        print(f"\n{i}. {record['name']} - {record['identifier']} - {record['book_in_date']}")
        print(f"   Address: {record['address']}")
        print(f"   Charges: {len(record['charges'])}")
        for charge in record["charges"]:
            print(f"     - {charge['booking_no']}: {charge['description']}")


if __name__ == "__main__":
    sys.exit(main())