import sys
import json
import csv
from arrestx.config import Config
from arrestx.parser import parse_lines

def main():
    # Create a default config
    cfg = Config()
    
    # Read the complex sample file
    with open("reports/complex_sample.txt", "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    # Parse the lines
    records = parse_lines(lines, "reports/complex_sample.txt", cfg)
    
    # Write to JSON
    with open("out/fixed_arrests.json", "w") as f:
        json.dump(records, f, indent=2)
    
    # Write to CSV
    with open("out/fixed_arrests.csv", "w", newline="") as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(["name", "identifier", "book_in_date", "booking_no", "description", "address", "source_file"])
        
        # Write rows
        for record in records:
            name = record["name"]
            identifier = record["identifier"] or ""
            book_in_date = record["book_in_date"] or ""
            address = " | ".join(record["address"])
            source_file = record["source_file"]
            
            # One row per charge
            for charge in record["charges"]:
                booking_no = charge["booking_no"]
                description = charge["description"]
                writer.writerow([name, identifier, book_in_date, booking_no, description, address, source_file])
    
    print(f"Generated output files with {len(records)} records")
    
    # Print the records
    for i, record in enumerate(records):
        print(f"\nRecord {i+1}: {record['name']}")
        print(f"  Identifier: {record['identifier']}")
        print(f"  Book-in date: {record['book_in_date']}")
        print(f"  Charges: {len(record['charges'])}")
        for j, charge in enumerate(record['charges']):
            print(f"    {j+1}. {charge['booking_no']}: {charge['description']}")

if __name__ == "__main__":
    main()