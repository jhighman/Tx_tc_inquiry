import sys
import json
from arrestx.config import Config
from arrestx.parser import parse_pdf

def main():
    # Create a default config
    cfg = Config()
    
    # Parse the PDF
    records = parse_pdf("./reports/01.PDF", cfg)
    
    # Print the records
    print(json.dumps(records, indent=2))
    
    # Print the number of records
    print(f"\nFound {len(records)} records")
    
    # Check if WYATT, JOSH is a separate record
    wyatt_record = None
    for record in records:
        if "WYATT, JOSH" in record["name"]:
            wyatt_record = record
            break
    
    if wyatt_record:
        print("\nWYATT, JOSH found as a separate record:")
        print(json.dumps(wyatt_record, indent=2))
    else:
        print("\nWYATT, JOSH not found as a separate record")
        
        # Check if it's in any description
        for record in records:
            for charge in record["charges"]:
                if "WYATT, JOSH" in charge["description"]:
                    print(f"Found in description of {record['name']}:")
                    print(json.dumps(charge, indent=2))

if __name__ == "__main__":
    main()