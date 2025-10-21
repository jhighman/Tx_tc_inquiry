import sys
import json
from arrestx.config import Config
from arrestx.parser import parse_lines

def main():
    # Read the sample file
    with open("reports/sample.txt", "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    # Create a default config
    cfg = Config()
    
    # Parse the lines
    records = parse_lines(lines, "reports/sample.txt", cfg)
    
    # Print the records
    print(json.dumps(records, indent=2))
    
    # Print the number of records
    print(f"\nFound {len(records)} records")

if __name__ == "__main__":
    main()