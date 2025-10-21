#!/usr/bin/env python3
"""
Simple test script for embedded name detection.
"""

from arrestx.parser import parse_lines
from arrestx.config import Config

def test_embedded_name():
    """Test detection of embedded names in charge descriptions."""
    cfg = Config()
    
    # Test case from test_embedded_name_in_charge_description
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
    
    print("Test case 1: Basic embedded name")
    records = parse_lines(lines, "test.pdf", cfg)
    print(f"Records found: {len(records)}")
    for i, r in enumerate(records):
        print(f"\nRecord {i+1}: {r['name']}")
        print(f"Identifier: {r['identifier']}")
        print(f"Book-in date: {r['book_in_date']}")
        print(f"Address: {r['address']}")
        print(f"Charges: {len(r['charges'])}")
        for j, c in enumerate(r['charges']):
            print(f"  Charge {j+1}: {c['booking_no']} - {c['description']}")
    
    # Test case from test_multiple_embedded_names
    lines2 = [
        "ADAMS, NINA KISHA",
        "123 MAIN ST",
        "ORLANDO, FL 32801",
        "1234567 10/15/2025",
        "25-0240350 NO VALID DL WYATT, JOSH 1234567 10/15/2025",
        "123 PINE AVE",
        "ORLANDO, FL 32802",
        "25-0240351 FAILURE TO APPEAR JOHNSON, MIKE 7654321 10/16/2025",
        "456 OAK ST",
        "ORLANDO, FL 32803",
        "25-0240352 SPEEDING"
    ]
    
    print("\n\nTest case 2: Multiple embedded names")
    records2 = parse_lines(lines2, "test.pdf", cfg)
    print(f"Records found: {len(records2)}")
    for i, r in enumerate(records2):
        print(f"\nRecord {i+1}: {r['name']}")
        print(f"Identifier: {r['identifier']}")
        print(f"Book-in date: {r['book_in_date']}")
        print(f"Address: {r['address']}")
        print(f"Charges: {len(r['charges'])}")
        for j, c in enumerate(r['charges']):
            print(f"  Charge {j+1}: {c['booking_no']} - {c['description']}")

if __name__ == "__main__":
    test_embedded_name()