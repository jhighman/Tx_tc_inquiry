#!/usr/bin/env python3
"""
Test the API with sample data.
"""

import json
import sys
from pathlib import Path

from arrestx.config import load_config
from arrestx.api import search_name

def process_sample_data():
    """
    Process the sample data file and return records.
    """
    from arrestx.parser import parse_lines
    
    # Read the sample file
    with open("reports/sample.txt", "r") as f:
        lines = f.readlines()
    
    # Parse the lines
    config = load_config("config.yaml")
    records = parse_lines([line.rstrip() for line in lines], "reports/sample.txt", config)
    
    return records

def main():
    """
    Main entry point.
    """
    # Create output directory if it doesn't exist
    Path("out").mkdir(exist_ok=True)
    
    # Load configuration
    config = load_config("config.yaml")
    
    # Get records from sample data
    records = process_sample_data()
    
    # Mock the search_name function to use our sample data
    def mock_search_name(name, cfg, force_update=False):
        from arrestx.api import Alert, SearchResult, name_matches
        import datetime
        
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
        result = mock_search_name(name, config)
        
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