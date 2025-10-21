#!/usr/bin/env python3
"""
Test the API with mock data.
"""

import json
import sys
from pathlib import Path
import datetime

from arrestx.config import load_config
from arrestx.api import Alert, SearchResult, name_matches

def create_mock_records():
    """
    Create mock records for testing.
    """
    return [
        {
            "name": "SMITH, JOHN",
            "name_normalized": "John Smith",
            "street": ["123 MAIN ST", "FORT WORTH, TX 76102"],
            "identifier": "12345678",
            "book_in_date": "2025-10-20",
            "charges": [
                {"booking_no": "25-0123456", "description": "THEFT PROPERTY > $2,500 < $30,000"}
            ],
            "source_file": "reports/sample.txt",
            "source_page_span": [1, 1],
            "parse_warnings": []
        },
        {
            "name": "JONES, MARY",
            "name_normalized": "Mary Jones",
            "street": ["456 OAK ST", "DALLAS, TX 75201"],
            "identifier": "87654321",
            "book_in_date": "2025-10-20",
            "charges": [
                {"booking_no": "25-0123457", "description": "ASSAULT BODILY INJURY"}
            ],
            "source_file": "reports/sample.txt",
            "source_page_span": [1, 1],
            "parse_warnings": []
        },
        {
            "name": "JOHNSON, MIKE",
            "name_normalized": "Mike Johnson",
            "street": ["789 PINE ST", "AUSTIN, TX 78701"],
            "identifier": "7654321",
            "book_in_date": "2025-10-20",
            "charges": [
                {"booking_no": "25-0123458", "description": "DWI BAC >= 0.15"}
            ],
            "source_file": "reports/sample.txt",
            "source_page_span": [1, 1],
            "parse_warnings": []
        },
        {
            "name": "WILLIAMS, SARAH",
            "name_normalized": "Sarah Williams",
            "street": ["321 CEDAR ST", "HOUSTON, TX 77002"],
            "identifier": "54321678",
            "book_in_date": "2025-10-20",
            "charges": [
                {"booking_no": "25-0123459", "description": "POSSESSION CONTROLLED SUBSTANCE PG 1 < 1G"}
            ],
            "source_file": "reports/sample.txt",
            "source_page_span": [2, 2],
            "parse_warnings": []
        },
        {
            "name": "BROWN, DAVID",
            "name_normalized": "David Brown",
            "street": ["654 MAPLE ST", "SAN ANTONIO, TX 78205"],
            "identifier": "65432187",
            "book_in_date": "2025-10-20",
            "charges": [
                {"booking_no": "25-0123460", "description": "BURGLARY OF HABITATION"}
            ],
            "source_file": "reports/sample.txt",
            "source_page_span": [2, 2],
            "parse_warnings": []
        }
    ]

def mock_search_name(name, records):
    """
    Mock the search_name function to use our sample data.
    
    Args:
        name: Name to search for
        records: List of records to search in
        
    Returns:
        SearchResult object
    """
    alerts = []
    for record in records:
        if name_matches(record["name"], name):
            # Create an alert for each charge
            for charge in record["charges"]:
                alert = Alert(
                    name=record["name"],
                    booking_no=charge["booking_no"],
                    description=charge["description"],
                    identifier=record.get("identifier", ""),
                    book_in_date=record.get("book_in_date", ""),
                    source_file=record["source_file"]
                )
                alerts.append(alert)
    
    # Create the search result
    result = SearchResult(
        name=name,
        alerts=alerts,
        records_checked=len(records),
        last_update=datetime.date.today()
    )
    
    return result

def main():
    """
    Main entry point.
    """
    # Create output directory if it doesn't exist
    Path("out").mkdir(exist_ok=True)
    
    # Create mock records
    records = create_mock_records()
    
    # Names to search for
    names = [
        "Smith, John",
        "Jones, Mary",
        "Johnson, Mike",
        "Williams, Sarah",
        "Brown, David",
        "Smith",  # Partial name
        "Unknown Person"  # Not in the data
    ]
    
    # Search for each name
    for name in names:
        print(f"\n=== Searching for: {name} ===")
        
        # Search for the name using our mock function
        result = mock_search_name(name, records)
        
        # Print the result
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
    
    # Save the last result as JSON for inspection
    with open("out/last_search_result.json", "w") as f:
        json.dump(result.to_dict(), f, indent=2)
    
    print("\nLast search result saved to out/last_search_result.json")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())