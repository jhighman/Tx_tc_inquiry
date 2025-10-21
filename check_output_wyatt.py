import json

def main():
    # Read the output JSON file
    with open("out/arrests.json", "r") as f:
        records = json.load(f)
    
    print(f"Found {len(records)} records")
    
    # Check if any record has WYATT in the name
    wyatt_records = []
    for record in records:
        if "WYATT" in record["name"]:
            wyatt_records.append(record)
    
    if wyatt_records:
        print(f"\nFound {len(wyatt_records)} records with WYATT in the name:")
        for record in wyatt_records:
            print(f"Name: {record['name']}")
            print(f"Identifier: {record['identifier']}")
            print(f"Book-in date: {record['book_in_date']}")
            print(f"Charges: {len(record['charges'])}")
            for i, charge in enumerate(record['charges']):
                print(f"  {i+1}. {charge['booking_no']}: {charge['description']}")
            print()
    else:
        print("\nNo records with WYATT in the name found")
    
    # Check if WYATT is in any description
    wyatt_in_desc = []
    for record in records:
        for charge in record["charges"]:
            if "WYATT" in charge["description"]:
                wyatt_in_desc.append((record["name"], charge))
    
    if wyatt_in_desc:
        print(f"\nFound {len(wyatt_in_desc)} charges with WYATT in the description:")
        for name, charge in wyatt_in_desc:
            print(f"Record: {name}")
            print(f"Booking No: {charge['booking_no']}")
            print(f"Description: {charge['description'][:100]}...")
            print()
    else:
        print("\nNo charges with WYATT in the description found")

if __name__ == "__main__":
    main()