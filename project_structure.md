# Project Structure for Texas Extract

## Directory Structure
```
texas_extract/
├── arrestx/                      # Main package
│   ├── __init__.py               # Package initialization
│   ├── cli.py                    # Command-line interface
│   ├── config.py                 # Configuration handling
│   ├── model.py                  # Data models
│   ├── parser.py                 # Core parsing logic
│   ├── pdfio.py                  # PDF extraction
│   ├── ocr.py                    # OCR fallback
│   ├── writers.py                # Output writers (JSON, CSV, NDJSON)
│   ├── log.py                    # Logging utilities
│   └── db/                       # Database integration (optional)
│       ├── __init__.py
│       └── mongo.py              # MongoDB integration
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── test_parser.py            # Parser tests
│   ├── test_pdfio.py             # PDF extraction tests
│   ├── test_writers.py           # Output format tests
│   └── fixtures/                 # Test data
│       ├── sample_selectable.pdf # Sample with selectable text
│       ├── expected.json         # Expected output for sample
│       ├── expected.csv          # Expected CSV for sample
│       ├── sample_ocr_only.pdf   # Sample requiring OCR
│       ├── expected_ocr.json     # Expected output for OCR sample
│       └── expected_ocr.csv      # Expected CSV for OCR sample
├── pyproject.toml                # Project metadata and dependencies
├── config.yaml                   # Default configuration
├── README.md                     # Project documentation
└── examples/                     # Example usage
    ├── basic_usage.py            # Basic usage example
    └── mongodb_integration.py    # MongoDB integration example
```

## Key Components

### 1. Core Components
- **model.py**: Defines the data structures (Record, Charge)
- **config.py**: Configuration handling with validation
- **parser.py**: State machine implementation for parsing
- **pdfio.py**: PDF text extraction with OCR fallback

### 2. I/O Components
- **cli.py**: Command-line interface
- **writers.py**: Output formatters (JSON, CSV, NDJSON)
- **db/mongo.py**: MongoDB integration (optional)

### 3. Utility Components
- **log.py**: Logging and diagnostics
- **ocr.py**: OCR handling for non-selectable text

## Dependencies
- pdfplumber or PyMuPDF (fitz): PDF text extraction
- pdf2image + pytesseract: OCR fallback
- pydantic: Data validation
- typer: CLI interface
- pyyaml: Configuration parsing
- pymongo (optional): MongoDB integration