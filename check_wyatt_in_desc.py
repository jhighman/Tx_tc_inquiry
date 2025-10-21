import json

def main():
    # Read the output JSON file
    with open("out/arrests.json", "r") as f:
        records = json.load(f)
    
    # Check if WYATT is in any description
    wyatt_in_desc = []
    for record in records:
        for charge in record["charges"]:
            if "WYATT" in charge["description"]:
                wyatt_in_desc.append((record["name"], charge["description"]))
    
    print(f"Found {len(wyatt_in_desc)} charges with WYATT in description")
    for name, desc in wyatt_in_desc:
        print(f"Record: {name}")
        print(f"Description: {desc[:100]}...")
        print()

if __name__ == "__main__":
    main()