"""
Basic usage example for Texas Extract.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from arrestx import parse_pdf, write_json, write_csv, Config


def main():
    """
    Basic usage example.
    """
    # Create output directory if it doesn't exist
    os.makedirs("./out", exist_ok=True)
    
    # Load configuration
    cfg = Config()
    cfg.input.ocr_fallback = True
    
    # Process a PDF file
    try:
        # Replace with your PDF file path
        pdf_path = "./reports/sample.pdf"
        
        print(f"Processing {pdf_path}...")
        records = parse_pdf(pdf_path, cfg)
        print(f"Extracted {len(records)} records")
        
        # Write outputs
        write_json(records, "./out/arrests.json", pretty=True)
        print(f"Wrote JSON to ./out/arrests.json")
        
        write_csv(records, "./out/arrests.csv")
        print(f"Wrote CSV to ./out/arrests.csv")
        
        # Print some information about the records
        for i, record in enumerate(records):
            print(f"\nRecord {i+1}:")
            print(f"  Name: {record['name']}")
            print(f"  Normalized Name: {record['name_normalized']}")
            print(f"  Identifier: {record['identifier']}")
            print(f"  Book-in Date: {record['book_in_date']}")
            print(f"  Address: {' | '.join(record['address'])}")
            print(f"  Charges ({len(record['charges'])}):")
            
            for j, charge in enumerate(record['charges']):
                print(f"    {j+1}. {charge['booking_no']}: {charge['description']}")
                
            if record['parse_warnings']:
                print(f"  Warnings: {', '.join(record['parse_warnings'])}")
    
    except FileNotFoundError:
        print(f"Error: File not found: {pdf_path}")
        print("Please place a sample PDF file in the ./reports directory")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()