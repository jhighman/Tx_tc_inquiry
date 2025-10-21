# Texas Extract

A robust system for extracting structured arrest records from county jail "book-in" PDF reports.

## Overview

Texas Extract parses PDF reports with a consistent layout to extract inmate records including names, addresses, identifiers, book-in dates, and charges. The extracted data is output to JSON, CSV, and optionally NDJSON formats, with the ability to stream to a MongoDB database.

## Features

- **PDF Text Extraction**: Extracts text from PDF reports with OCR fallback for non-selectable text
- **State Machine Parser**: Uses a state machine with regex patterns to parse text into structured records
- **Multiple Output Formats**: Supports JSON, CSV, and NDJSON output formats
- **MongoDB Integration**: Optional integration with MongoDB for storing and querying records
- **Web Retrieval**: Fetches reports from URLs with conditional headers for efficiency
- **Backup Mechanism**: Automatically backs up reports with date-based filenames to preserve historical data
- **Command-Line Interface**: Comprehensive CLI for processing files, fetching reports, and creating backups
- **Privacy Options**: Supports redaction of address information and hashing of identifiers
- **Extensibility**: Plugin architecture for supporting different report formats
- **Name Search API**: Search for names in arrest records with alerts for matches
- **Web UI**: User-friendly interface for searching arrest records

## Installation

```bash
pip install arrestx
```

For the web UI, you'll also need to install Gradio:

```bash
pip install gradio
```

## Quick Start

### Process PDF Files

```bash
# Process PDF files and output to JSON and CSV
arrestx --in ./reports/*.pdf --json ./out/arrests.json --csv ./out/arrests.csv

# Enable OCR fallback for non-selectable text
arrestx --in ./reports/*.pdf --json ./out/arrests.json --ocr-fallback

# Apply privacy options
arrestx --in ./reports/*.pdf --json ./out/arrests.json --redact-address --hash-id
```

### Fetch and Process Daily Reports

```bash
# Fetch and process the daily report
arrestx fetch --url https://cjreports.tarrantcounty.com/Reports/JailedInmates/FinalPDF/01.PDF

# Skip processing if report already exists
arrestx fetch --url https://cjreports.tarrantcounty.com/Reports/JailedInmates/FinalPDF/01.PDF --skip-if-existing
```

### Search for Names in Arrest Records

```bash
# Search for a name in the arrest records
arrestx search "John Doe"

# Search using Last, First format
arrestx search "Doe, John"

# Output results as JSON
arrestx search "John Doe" --json
```

### Backup Management

```bash
# Manually create a backup of a report with a specific date
arrestx backup ./reports/01.PDF 2025-10-15
```

## Web UI

Texas Extract includes a web-based UI for searching arrest records.

### Starting the UI

```bash
# Start the UI on the default port (7860)
python -m arrestx.ui

# Start the UI on a specific port
python -m arrestx.ui --port 8080

# Create a public link for sharing
python -m arrestx.ui --share
```

### Using the UI

1. Enter a name in the search box (either "First Middle Last" or "Last, First Middle" format)
2. Optionally, provide a path to a custom configuration file
3. Click the "Search" button
4. View the results in the "Alerts" and "Raw JSON" tabs

## Configuration

Texas Extract can be configured using a YAML file:

```yaml
input:
  paths: ["./reports/*.pdf"]
  ocr_fallback: false
  ocr_lang: "eng"

parsing:
  name_regex_strict: true
  allow_two_line_id_date: true
  header_patterns:
    - "^Inmates Booked In.*"
    - "^Report Date:.*"
    - "^Page\\s+\\d+.*"

output:
  json_path: "./out/arrests.json"
  csv_path: "./out/arrests.csv"
  ndjson_path: null
  pretty_json: true

db:
  enabled: false
  uri: "mongodb://localhost:27017"
  database: "arrests_db"
  tenant: "TRUA"

logging:
  level: "INFO"
  emit_warnings_in_record: true

performance:
  parallel_pages: true

web_retrieval:
  url: "https://cjreports.tarrantcounty.com/Reports/JailedInmates/FinalPDF/01.PDF"
```

## Backup Mechanism

The backup mechanism ensures that when a new report is downloaded:

1. The system extracts the report date from the PDF header
2. Creates a backup of any existing file with the same name
3. Stores the backup in the `archive` subdirectory with the report date in the filename
4. Replaces the original file with the new download

This solves the problem of the source URL always pointing to the same filename (e.g., `01.PDF`), which gets overwritten daily. Without this backup mechanism, historical data would be lost when new reports are downloaded.

### Backup Naming Convention

Backup files follow this naming convention:

```
{original_filename}_{YYYY-MM-DD}.{extension}
```

For example, if the original file is `01.PDF` and the report date is October 15, 2025, the backup file will be named:

```
01_2025-10-15.PDF
```

### Directory Structure

```
reports/
  01.PDF                  # Current report
  archive/
    01_2025-10-14.PDF     # Previous day's report
    01_2025-10-13.PDF     # Report from two days ago
    ...
```

## Library Usage

### Basic Usage

```python
from arrestx.config import load_config
from arrestx.parser import parse_pdf
from arrestx.writers import write_outputs

# Load configuration
config = load_config("./config.yaml")

# Parse PDF
records = parse_pdf("./reports/01.PDF", config)

# Write outputs
write_outputs(records, config)
```

### Web Retrieval with Backup

```python
from arrestx.config import load_config
from arrestx.web import process_daily_report

# Load configuration
config = load_config("./config.yaml")

# Process daily report
result = process_daily_report(
    "https://cjreports.tarrantcounty.com/Reports/JailedInmates/FinalPDF/01.PDF",
    config
)

print(f"Status: {result['status']}")
print(f"Records: {result.get('record_count', 0)}")
```

### Name Search API

```python
from arrestx.config import load_config
from arrestx.api import search_name

# Load configuration
config = load_config("./config.yaml")

# Search for a name
result = search_name("John Doe", config)

# Check if any alerts were found
if result.alerts:
    print(f"Found {len(result.alerts)} alerts for {result.name}")
    for alert in result.alerts:
        print(f"Booking: {alert.booking_no}")
        print(f"Charge: {alert.description}")
else:
    print(f"No alerts found for {result.name}")
    print(f"Checked {result.records_checked} records")
```

### Daily Check for a List of Names

```python
from arrestx.config import load_config
from arrestx.api import search_name

# Load configuration
config = load_config("./config.yaml")

# List of names to check
names = [
    "John Doe",
    "Jane Smith",
    "Robert Johnson"
]

# Check each name
for name in names:
    result = search_name(name, config)
    if result.alerts:
        print(f"⚠️ ALERT: Found {len(result.alerts)} matches for {name}")
        for alert in result.alerts:
            print(f"  - Booking: {alert.booking_no}, Charge: {alert.description}")
    else:
        print(f"✓ No matches found for {name}")
```

### Manual Backup

```python
from arrestx.web import extract_report_date, backup_file

# Extract report date from PDF
report_date = extract_report_date("./reports/01.PDF")

if report_date:
    # Create backup with report date
    backup_path = backup_file("./reports/01.PDF", report_date)
    print(f"Created backup: {backup_path}")
```

### MongoDB Integration

```python
from arrestx.config import load_config
from arrestx.parser import parse_pdf
from arrestx.db.mongo import bulk_ingest

# Load configuration
config = load_config("./config.yaml")

# Parse PDF
records = parse_pdf("./reports/01.PDF", config)

# Ingest into MongoDB
result = bulk_ingest(
    config.db.uri,
    config.db.database,
    config.db.tenant,
    "01.PDF",
    records
)

print(f"Inserted: {result.get('upserted', 0)}")
print(f"Updated: {result.get('modified', 0)}")
```

## Data Model

Each record represents a single inmate and includes:

```json
{
  "name": "Last, First Middle",
  "name_normalized": "First Middle Last",
  "street": ["line 1", "line 2", "line 3"],
  "identifier": "1234567",
  "book_in_date": "YYYY-MM-DD",
  "charges": [
    {
      "booking_no": "25-0123456",
      "description": "Free-text offense description with wraps merged"
    }
  ],
  "source_file": "01.pdf",
  "source_page_span": [1, 3],
  "parse_warnings": ["wrapped line without booking_no"]
}
```

## Scheduled Usage

### Daily Report Retrieval

To set up a daily report retrieval job, add the following to your crontab:

```bash
# Fetch and process the daily report at 6:00 AM
0 6 * * * /usr/local/bin/arrestx fetch --url https://cjreports.tarrantcounty.com/Reports/JailedInmates/FinalPDF/01.PDF
```

### Daily Name Check

To set up a daily name check job, add the following to your crontab:

```bash
# Check a list of names at 7:00 AM
0 7 * * * /usr/local/bin/python /path/to/your/check_script.py
```

### Backup Retention

To implement a retention policy for backups, add the following to your crontab:

```bash
# Delete backups older than 90 days at 1:00 AM every Sunday
0 1 * * 0 find /path/to/reports/archive -name "*.PDF" -type f -mtime +90 -delete
```

## Troubleshooting

- **Missing Reports**: If you're not seeing any results, make sure the reports directory exists and contains PDF files.
- **OCR Issues**: If text extraction is failing, try enabling OCR fallback with `--ocr-fallback`.
- **Configuration**: Check your configuration file for any errors or missing values.
- **Dependencies**: Ensure all dependencies are installed, especially if using OCR features.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.