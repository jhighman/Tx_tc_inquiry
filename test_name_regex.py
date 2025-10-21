import re

def main():
    # Sample lines
    lines = [
        "WILLIAMS, KICSCA",
        "WYATT, JOSH 0672672 10/14/2025 2400 CYPRESS ST",
        "25-0240404 SEX OFFENDERS DUTY TO REGISTER LIFE/ANNUALLY FORT WORTH TX 76116 WYATT, JOSH",
        "WILSON, ERIK MICHAEL 0581914 10/14/2025 611 JAMBOREE WAY",
        "WOODS, EZAIVION RONSHAD 1063430 10/14/2025 8126 MOSSBERG DR"
    ]
    
    # Original strict name regex
    strict_regex = re.compile(r"^(?P<last>[A-Z][A-Z\-\.' ]+),\s+(?P<firstmid>[A-Z][A-Z\-\.' ]+)$")
    
    # New embedded name regex
    embedded_regex = re.compile(r"(?P<last>[A-Z][A-Z\-\.' ]+),\s+(?P<firstmid>[A-Z][A-Z\-\.' ]+)")
    
    # Test each line
    print("Testing strict regex (matches only at beginning of line):")
    for line in lines:
        match = strict_regex.match(line)
        if match:
            print(f"MATCH: {line}")
            print(f"  Last: {match.group('last')}, First/Mid: {match.group('firstmid')}")
        else:
            print(f"NO MATCH: {line}")
    
    print("\nTesting embedded regex (matches anywhere in line):")
    for line in lines:
        match = embedded_regex.search(line)
        if match:
            print(f"MATCH: {line}")
            print(f"  Last: {match.group('last')}, First/Mid: {match.group('firstmid')}")
            print(f"  Position: {match.start()}-{match.end()}")
        else:
            print(f"NO MATCH: {line}")

if __name__ == "__main__":
    main()