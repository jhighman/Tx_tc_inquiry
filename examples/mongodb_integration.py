"""
MongoDB integration example for Texas Extract.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from arrestx import parse_pdf, write_mongodb, Config, MongoDBConfig


def main():
    """
    MongoDB integration example.
    """
    # Load configuration
    cfg = Config()
    cfg.input.ocr_fallback = True
    
    # Configure MongoDB
    mongodb_cfg = MongoDBConfig(
        enabled=True,
        uri="mongodb://localhost:27017",
        database="arrest_records",
        collection="arrest_records",
        tenant="TRUA"
    )
    
    # Set MongoDB configuration in main config
    cfg.mongodb = mongodb_cfg
    
    # Process a PDF file
    try:
        # Replace with your PDF file path
        pdf_path = "./reports/sample.pdf"
        
        print(f"Processing {pdf_path}...")
        records = parse_pdf(pdf_path, cfg)
        print(f"Extracted {len(records)} records")
        
        # Write to MongoDB
        print("Writing to MongoDB...")
        result = write_mongodb(records, mongodb_cfg)
        
        # Print results
        print(f"MongoDB results:")
        print(f"  Matched: {result['matched']}")
        print(f"  Modified: {result['modified']}")
        print(f"  Upserted: {result['upserted']}")
        
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
    except ImportError:
        print("Error: pymongo not installed. Install with: pip install pymongo")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()