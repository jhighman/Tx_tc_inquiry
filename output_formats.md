# Output Formats Design

## Overview

The system supports three output formats:

1. **JSON**: An array of records with pretty-printing option
2. **CSV**: One row per charge (denormalized)
3. **NDJSON**: One record per line (optional)

Each format has specific requirements and considerations for data representation.

## JSON Format

### Structure

```json
[
  {
    "name": "LASTNAME, FIRST MIDDLE",
    "name_normalized": "First Middle Lastname",
    "address": ["123 MAIN ST", "ANYTOWN, TX 12345"],
    "identifier": "1234567",
    "book_in_date": "2025-10-15",
    "charges": [
      {
        "booking_no": "25-0123456",
        "description": "Free-text offense description with wraps merged"
      },
      {
        "booking_no": "25-0123457",
        "description": "Another charge description"
      }
    ],
    "source_file": "01.pdf",
    "source_page_span": [1, 3],
    "parse_warnings": ["wrapped line without booking_no"]
  },
  // Additional records...
]
```

### Implementation

```python
def write_json(records: list[Record], path: str, pretty: bool = True) -> None:
    """
    Write records to a JSON file.
    
    Args:
        records: List of records to write
        path: Output file path
        pretty: Whether to pretty-print the JSON
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Write JSON file
    with open(path, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(records, f, indent=2, ensure_ascii=False)
        else:
            json.dump(records, f, ensure_ascii=False)
```

### Considerations

1. **UTF-8 Encoding**: Ensures proper handling of special characters
2. **Pretty-Printing**: Optional for human readability (configurable)
3. **ensure_ascii=False**: Preserves non-ASCII characters in the output

## CSV Format

### Structure

The CSV format denormalizes the data, with one row per charge:

| name | identifier | book_in_date | booking_no | description | address | source_file |
|------|------------|--------------|------------|-------------|---------|-------------|
| LASTNAME, FIRST MIDDLE | 1234567 | 2025-10-15 | 25-0123456 | Free-text offense description | 123 MAIN ST \| ANYTOWN, TX 12345 | 01.pdf |
| LASTNAME, FIRST MIDDLE | 1234567 | 2025-10-15 | 25-0123457 | Another charge description | 123 MAIN ST \| ANYTOWN, TX 12345 | 01.pdf |

### Implementation

```python
def write_csv(records: list[Record], path: str) -> None:
    """
    Write records to a CSV file.
    
    Args:
        records: List of records to write
        path: Output file path
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Define CSV columns
    fieldnames = ['name', 'identifier', 'book_in_date', 'booking_no', 
                 'description', 'address', 'source_file']
    
    # Write CSV file
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in records:
            # Join address lines with pipe separator
            address = " | ".join(record.get("address", []))
            
            # Write one row per charge
            for charge in record.get("charges", []):
                writer.writerow({
                    'name': record.get("name", ""),
                    'identifier': record.get("identifier", ""),
                    'book_in_date': record.get("book_in_date", ""),
                    'booking_no': charge.get("booking_no", ""),
                    'description': charge.get("description", ""),
                    'address': address,
                    'source_file': record.get("source_file", "")
                })
```

### Considerations

1. **Denormalization**: Each charge gets its own row
2. **Address Joining**: Address lines are joined with " | " separator
3. **UTF-8 Encoding**: Ensures proper handling of special characters
4. **RFC 4180 Compliance**: Uses standard CSV format with proper quoting

## NDJSON Format

### Structure

NDJSON (Newline Delimited JSON) format has one complete JSON object per line:

```
{"name":"LASTNAME, FIRST MIDDLE","name_normalized":"First Middle Lastname","address":["123 MAIN ST","ANYTOWN, TX 12345"],"identifier":"1234567","book_in_date":"2025-10-15","charges":[{"booking_no":"25-0123456","description":"Free-text offense description with wraps merged"}],"source_file":"01.pdf","source_page_span":[1,3],"parse_warnings":["wrapped line without booking_no"]}
{"name":"ANOTHER, PERSON","name_normalized":"Person Another","address":["456 OAK AVE"],"identifier":"7654321","book_in_date":"2025-10-15","charges":[{"booking_no":"25-0123458","description":"Some other charge"}],"source_file":"01.pdf","source_page_span":[4,4],"parse_warnings":[]}
```

### Implementation

```python
def write_ndjson(records: list[Record], path: str, denormalize: bool = False) -> None:
    """
    Write records to an NDJSON file.
    
    Args:
        records: List of records to write
        path: Output file path
        denormalize: Whether to denormalize records (one line per charge)
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Write NDJSON file
    with open(path, 'w', encoding='utf-8') as f:
        if denormalize:
            # Denormalized format (one line per charge)
            for record in records:
                base_record = {k: v for k, v in record.items() if k != 'charges'}
                for charge in record.get("charges", []):
                    line_record = base_record.copy()
                    line_record["charge"] = charge
                    f.write(json.dumps(line_record, ensure_ascii=False) + '\n')
        else:
            # Normalized format (one line per record)
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
```

### Considerations

1. **Streaming-Friendly**: Each line is a complete JSON object
2. **Normalized or Denormalized**: Supports both formats
3. **UTF-8 Encoding**: Ensures proper handling of special characters
4. **No Pretty-Printing**: Each record is on a single line

## Output Manager

To coordinate the different output formats, we implement an output manager:

```python
def write_outputs(records: list[Record], cfg: Config) -> None:
    """
    Write records to all configured output formats.
    
    Args:
        records: List of records to write
        cfg: Application configuration
    """
    # Write JSON if configured
    if cfg.output.json_path:
        write_json(records, cfg.output.json_path, cfg.output.pretty_json)
        
    # Write CSV if configured
    if cfg.output.csv_path:
        write_csv(records, cfg.output.csv_path)
        
    # Write NDJSON if configured
    if cfg.output.ndjson_path:
        write_ndjson(records, cfg.output.ndjson_path)
```

## Data Validation

Before writing outputs, we perform validation to ensure data quality:

```python
def validate_records(records: list[Record]) -> list[str]:
    """
    Validate records before writing outputs.
    
    Args:
        records: List of records to validate
        
    Returns:
        List of validation errors
    """
    errors = []
    
    for i, record in enumerate(records):
        # Validate required fields
        if not record.get("name"):
            errors.append(f"Record {i}: Missing name")
            
        # Validate booking numbers
        for j, charge in enumerate(record.get("charges", [])):
            booking_no = charge.get("booking_no", "")
            if not re.match(r"^\d{2}-\d{6,7}$", booking_no):
                errors.append(f"Record {i}, Charge {j}: Invalid booking number format: {booking_no}")
                
            if not charge.get("description"):
                errors.append(f"Record {i}, Charge {j}: Missing charge description")
                
        # Validate date format
        book_in_date = record.get("book_in_date")
        if book_in_date and not re.match(r"^\d{4}-\d{2}-\d{2}$", book_in_date):
            errors.append(f"Record {i}: Invalid book-in date format: {book_in_date}")
            
    return errors
```

## Security and Privacy

For privacy-sensitive deployments, we provide redaction options:

```python
def redact_records(records: list[Record], redact_address: bool = False, hash_id: bool = False) -> list[Record]:
    """
    Redact sensitive information from records.
    
    Args:
        records: List of records to redact
        redact_address: Whether to redact address information
        hash_id: Whether to hash identifier
        
    Returns:
        Redacted records
    """
    redacted = []
    
    for record in records:
        redacted_record = record.copy()
        
        # Redact address if requested
        if redact_address:
            redacted_record["address"] = ["[REDACTED]"]
            
        # Hash identifier if requested
        if hash_id and record.get("identifier"):
            redacted_record["identifier"] = hashlib.sha256(
                record["identifier"].encode()
            ).hexdigest()
            
        redacted.append(redacted_record)
        
    return redacted
```

## Error Handling

The output writers include robust error handling:

1. File system errors (permission denied, disk full)
2. Encoding errors
3. Data validation errors

Each error is logged and, where possible, the system continues with partial results.