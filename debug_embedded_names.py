#!/usr/bin/env python3
"""
Debug script for embedded names in charge descriptions.
"""

from arrestx.parser import parse_lines, ID_DATE_REGEX
from arrestx.config import Config
import re

def test_embedded_name():
    """Test detection of embedded names in charge descriptions."""
    cfg = Config()
    
    lines = [
        "ADAMS, NINA KISHA",
        "123 MAIN ST",
        "ORLANDO, FL 32801",
        "1234567 10/15/2025",
        "25-0240350 NO VALID DL WYATT, JOSH 1234567 10/15/2025",
        "123 PINE AVE",
        "ORLANDO, FL 32802",
        "25-0240351 FAILURE TO APPEAR"
    ]
    
    # Test ID/Date regex
    line = "25-0240350 NO VALID DL WYATT, JOSH 1234567 10/15/2025"
    name_regex = re.compile(r"\b(?P<last>[A-Z]+),\s+(?P<firstmid>[A-Z]+)")
    name_match = name_regex.search(line)
    
    if name_match:
        print(f"Name match found: '{name_match.group(0)}'")
        print(f"Start: {name_match.start()}, End: {name_match.end()}")
        
        # Check for ID/Date after the name
        rest = line[name_match.end():].strip()
        print(f"Text after name: '{rest}'")
        
        id_date_match = ID_DATE_REGEX.search(rest)
        if id_date_match:
            print(f"ID/Date match found: '{id_date_match.group(0)}'")
            print(f"ID: '{id_date_match.group('id')}'")
            print(f"Date: '{id_date_match.group('date')}'")
        else:
            print("No ID/Date match found")
    else:
        print("No name match found")
    
    print("\nParsing lines...")
    records = parse_lines(lines, "test.pdf", cfg)
    
    print(f"\nRecords: {len(records)}")
    for i, r in enumerate(records):
        print(f"\nRecord {i+1}: {r['name']}")
        print(f"Identifier: {r['identifier']}")
        print(f"Book-in date: {r['book_in_date']}")
        print(f"Address: {r['address']}")
        print(f"Charges: {len(r['charges'])}")
        for j, c in enumerate(r['charges']):
            print(f"  Charge {j+1}: {c['booking_no']} - {c['description']}")

if __name__ == "__main__":
    test_embedded_name()