"""
Test script for demonstrating the embedded name detection with a sample file.
"""

import os
import json
import csv
from arrestx.parser import parse_lines
from arrestx.config import Config

def main():
    """
    Main function to demonstrate embedded name detection.
    """
    # Load the sample data
    sample_path = os.path.join(os.path.dirname(__file__), "data", "embedded_names_sample.txt")
    with open(sample_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
    
    # Create a configuration
    cfg = Config(
        input={
            "paths": ["./reports/*.pdf"],
            "ocr_fallback": False,
            "ocr_lang": "eng"
        },
        parsing={
            "name_regex_strict": True,
            "allow_two_line_id_date": True,
            "header_patterns": [
                "^Inmates Booked In.*",
                "^Report Date:.*",
                "^Page\\s+\\d+.*"
            ]
        },
        output={
            "json_path": "./out/arrests.json",
            "csv_path": "./out/arrests.csv",
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
    
    # Parse the lines
    records = parse_lines(lines, "embedded_names_sample.txt", cfg)
    
    # Print the number of records found
    print(f"Found {len(records)} records")
    
    # Create output directory if it doesn't exist
    os.makedirs("./out", exist_ok=True)
    
    # Write the records to JSON
    with open("./out/embedded_names_sample.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    
    # Write the records to CSV
    with open("./out/embedded_names_sample.csv", "w", encoding="utf-8", newline="") as f:
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
    
    # Print the names of all records
    print("\nRecords found:")
    for i, record in enumerate(records, 1):
        print(f"{i}. {record['name']} - {record['identifier']} - {record['book_in_date']}")
        print(f"   Address: {' | '.join(record['address'])}")
        print(f"   Charges: {len(record['charges'])}")
        for charge in record["charges"]:
            print(f"     - {charge['booking_no']}: {charge['description']}")
        print()
    
    # Verify embedded names were detected correctly
    embedded_names = ["WYATT, JOSH", "JOHNSON, MIKE", "TAYLOR, ROBERT"]
    for name in embedded_names:
        found = any(record["name"] == name for record in records)
        print(f"Embedded name '{name}' detected: {found}")

if __name__ == "__main__":
    main()