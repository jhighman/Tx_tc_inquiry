import sys
import json
from arrestx.config import Config
from arrestx.parser import parse_lines

def main():
    # Read the output JSON file
    with open("out/arrests.json", "r") as f:
        records = json.load(f)
    
    # Print the number of records
    print(f"Found {len(records)} records in the output JSON")
    
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
    
    # Create a new config
    cfg = Config()
    
    # Create a simple test file with WYATT, JOSH
    test_lines = [
        "Inmates Booked In Between 10/14/2025 00:00 and 10/14/2025 23:59",
        "Report Date: 10/15/2025 08:00",
        "WILLIAMS, KICSCA",
        "25-0240386 CRIMINAL MISCHIEF >=$100<$750",
        "WYATT, JOSH 0672672 10/14/2025 2400 CYPRESS ST",
        "25-0240308 CRIMINAL TRESPASS"
    ]
    
    # Parse the test lines
    test_records = parse_lines(test_lines, "test.txt", cfg)
    
    # Print the test records
    print("\nTest records:")
    print(json.dumps(test_records, indent=2))
    
    # Check if WYATT, JOSH is a separate record in the test
    wyatt_test_record = None
    for record in test_records:
        if "WYATT, JOSH" in record["name"]:
            wyatt_test_record = record
            break
    
    if wyatt_test_record:
        print("\nWYATT, JOSH found as a separate record in the test:")
        print(json.dumps(wyatt_test_record, indent=2))
    else:
        print("\nWYATT, JOSH not found as a separate record in the test")

if __name__ == "__main__":
    main()