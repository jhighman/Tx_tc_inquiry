# CLI and API Documentation

This document outlines the command-line interface (CLI) and application programming interface (API) for the Texas Extract system.

## Command-Line Interface (CLI)

The Texas Extract system provides a comprehensive CLI for processing PDF reports, fetching reports from URLs, and managing backups.

### Main Command

The main command processes PDF files and extracts structured records.

```bash
arrestx --in ./reports/*.pdf \
        --json ./out/arrests.json \
        --csv ./out/arrests.csv \
        --ndjson ./out/arrests.ndjson \
        --ocr-fallback
```

#### Options

| Option | Description |
|--------|-------------|
| `--in`, `-i` | Input PDF files or globs |
| `--json`, `-j` | JSON output file path |
| `--csv`, `-c` | CSV output file path |
| `--ndjson`, `-n` | NDJSON output file path |
| `--ocr-fallback`, `-o` | Enable OCR fallback for non-selectable text |
| `--config`, `-f` | Path to config file |
| `--redact-address`, `-r` | Redact address information |
| `--hash-id`, `-h` | Hash identifier for privacy |
| `--verbose`, `-v` | Enable verbose logging |
| `--quiet`, `-q` | Suppress all output except errors |
| `--version` | Show version information |

#### Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Parse errors (partial output produced) |
| 2 | Fatal errors (IO, format, etc.) |

### Fetch Command

The fetch command downloads a PDF report from a URL and processes it.

```bash
arrestx fetch --url https://cjreports.tarrantcounty.com/Reports/JailedInmates/FinalPDF/01.PDF \
              --skip-if-existing
```

#### Options

| Option | Description |
|--------|-------------|
| `--url` | URL to fetch (default: Tarrant County URL) |
| `--skip-if-existing` | Skip processing if report already exists |
| `--config`, `-f` | Path to config file |
| `--verbose`, `-v` | Enable verbose logging |
| `--quiet`, `-q` | Suppress all output except errors |

### Backup Command

The backup command creates a backup of a file with the report date in the filename.

```bash
arrestx backup ./reports/01.PDF 2025-10-15
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `file_path` | Path to the file to backup |
| `report_date` | Report date in YYYY-MM-DD format |

#### Options

| Option | Description |
|--------|-------------|
| `--verbose`, `-v` | Enable verbose logging |
| `--quiet`, `-q` | Suppress all output except errors |

## Library API

The Texas Extract system can also be used as a library in other Python applications.

### Core Functions

#### Parsing

```python
from arrestx.parser import parse_pdf

# Parse a PDF file
records = parse_pdf("./reports/01.PDF", config)

# Parse text lines
from arrestx.parser import parse_text_lines
records = parse_text_lines(lines, config)
```

#### Output

```python
from arrestx.writers import write_json, write_csv, write_ndjson

# Write to JSON
write_json(records, "./out/arrests.json", pretty=True)

# Write to CSV
write_csv(records, "./out/arrests.csv")

# Write to NDJSON
write_ndjson(records, "./out/arrests.ndjson")

# Write to all formats
from arrestx.writers import write_outputs
write_outputs(records, config)

# Apply privacy options
from arrestx.writers import redact_records
redacted_records = redact_records(records, redact_address=True, hash_id=True)
```

#### Web Retrieval and Backup

```python
from arrestx.web import fetch_pdf, process_daily_report, backup_file, extract_report_date

# Fetch a PDF from a URL
result = fetch_pdf("https://example.com/report.pdf", "./reports/report.pdf")

# Process a daily report (fetch, backup, parse, and output)
result = process_daily_report("https://example.com/report.pdf", config)

# Extract report date from a PDF
report_date = extract_report_date("./reports/report.pdf")

# Create a backup of a file with the report date
backup_path = backup_file("./reports/report.pdf", "2025-10-15")
```

#### MongoDB Integration

```python
from arrestx.db.mongo import bulk_ingest

# Ingest records into MongoDB
result = bulk_ingest(
    "mongodb://localhost:27017",
    "arrests_db",
    "TRUA",
    "01.PDF",
    records
)
```

### Configuration

```python
from arrestx.config import Config, load_config

# Load configuration from file
config = load_config("./config.yaml")

# Create configuration programmatically
config = Config()
config.output.json_path = "./out/arrests.json"
config.output.csv_path = "./out/arrests.csv"
config.input.ocr_fallback = True
config.db.enabled = True
config.db.uri = "mongodb://localhost:27017"
config.db.database = "arrests_db"
config.db.tenant = "TRUA"
```

### Logging

```python
from arrestx.log import configure_logging, get_logger

# Configure logging
configure_logging("DEBUG")

# Get a logger
logger = get_logger(__name__)
logger.info("Processing file...")
```

## Data Model

The core data model is the `Record` class, which represents a single inmate record.

```python
class Record(TypedDict):
    name: str
    name_normalized: str
    address: list[str]
    identifier: str | None
    book_in_date: str | None
    charges: list[dict[str, str]]    # {booking_no, description}
    source_file: str
    source_page_span: list[int]
    parse_warnings: list[str]
```

## Examples

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

## Advanced Usage

### Scheduled Daily Retrieval

```python
# crontab entry for daily retrieval at 6:00 AM
# 0 6 * * * /usr/local/bin/arrestx fetch --url https://cjreports.tarrantcounty.com/Reports/JailedInmates/FinalPDF/01.PDF
```

### Custom Backup Retention

```python
# Shell script to delete backups older than 90 days
#!/bin/bash
find ./reports/archive -name "*.PDF" -type f -mtime +90 -delete
```

### Parallel Processing

```python
import concurrent.futures
from arrestx.config import load_config
from arrestx.parser import parse_pdf
from arrestx.writers import write_json

config = load_config("./config.yaml")
files = ["./reports/01.PDF", "./reports/02.PDF", "./reports/03.PDF"]

def process_file(file):
    records = parse_pdf(file, config)
    output_file = f"./out/{file.split('/')[-1].split('.')[0]}.json"
    write_json(records, output_file)
    return len(records)

with concurrent.futures.ProcessPoolExecutor() as executor:
    results = list(executor.map(process_file, files))

print(f"Total records: {sum(results)}")