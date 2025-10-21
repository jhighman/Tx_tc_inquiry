import sys
import json
from arrestx.config import Config
from arrestx.parser import parse_lines

def main():
    # Read the sample file
    with open("reports/complex_sample.txt", "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    # Print the lines for debugging
    print("Input lines:")
    for i, line in enumerate(lines):
        print(f"{i+1}: {line}")
    
    # Create a default config
    cfg = Config()
    
    # Create a name regex for testing
    import re
    name_regex = re.compile(r"^(?P<last>[A-Z][A-Z\-\.' ]+),\s+(?P<firstmid>[A-Z][A-Z\-\.' ]+)$")
    
    # Test each line against the name regex
    print("\nName regex matches:")
    for i, line in enumerate(lines):
        match = name_regex.match(line)
        if match:
            print(f"{i+1}: {line} -> MATCH")
        else:
            print(f"{i+1}: {line} -> NO MATCH")
    
    # Parse the lines
    records = parse_lines(lines, "reports/complex_sample.txt", cfg)
    
    # Print the records
    print("\nParsed records:")
    print(json.dumps(records, indent=2))
    
    # Print the number of records
    print(f"\nFound {len(records)} records")

if __name__ == "__main__":
    main()