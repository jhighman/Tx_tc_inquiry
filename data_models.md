# Data Models and Configuration Schema

## Core Data Models

### Record Model
The primary data structure representing an inmate record:

```python
class Charge(TypedDict):
    booking_no: str  # Format: YY-XXXXXXX (2 digits, dash, 6-7 digits)
    description: str  # Free-text offense description

class Record(TypedDict):
    name: str  # Format: "LASTNAME, FIRST MIDDLE"
    name_normalized: str  # Optional, format: "First Middle Last"
    address: list[str]  # 0-3 lines of address information
    identifier: Optional[str]  # 5-8 digit string, may be None
    book_in_date: Optional[str]  # ISO 8601 format (YYYY-MM-DD), may be None
    charges: list[Charge]  # List of booking charges
    source_file: str  # Source PDF filename
    source_page_span: list[int]  # [first_page, last_page] the record spans
    parse_warnings: list[str]  # Optional list of parsing warnings/errors
```

### Parser State Enum
```python
class ParserState(Enum):
    SEEK_NAME = "seek_name"
    CAPTURE_ADDRESS = "capture_address"
    SEEK_ID_DATE = "seek_id_date"
    CAPTURE_CHARGES = "capture_charges"
```

## Configuration Schema

The configuration schema defines all configurable aspects of the application:

```python
class InputConfig(BaseModel):
    paths: list[str] = ["./reports/*.pdf"]  # Input file paths/globs
    ocr_fallback: bool = False  # Whether to use OCR when text extraction fails
    ocr_lang: str = "eng"  # OCR language

class ParsingConfig(BaseModel):
    name_regex_strict: bool = True  # Whether to use strict name regex
    allow_two_line_id_date: bool = True  # Support ID and date on separate lines
    header_patterns: list[str] = [  # Patterns to identify headers/footers
        r"^Inmates Booked In.*",
        r"^Report Date:.*",
        r"^Page\s+\d+.*"
    ]

class OutputConfig(BaseModel):
    json_path: Optional[str] = "./out/arrests.json"  # JSON output path
    csv_path: Optional[str] = "./out/arrests.csv"  # CSV output path
    ndjson_path: Optional[str] = None  # NDJSON output path (disabled by default)
    pretty_json: bool = True  # Whether to pretty-print JSON

class LoggingConfig(BaseModel):
    level: str = "INFO"  # Logging level (DEBUG/INFO/WARN/ERROR)
    emit_warnings_in_record: bool = True  # Include warnings in record objects

class PerformanceConfig(BaseModel):
    parallel_pages: bool = True  # Process pages in parallel

class MongoDBConfig(BaseModel):
    enabled: bool = False  # Whether MongoDB integration is enabled
    uri: str = "mongodb://localhost:27017"  # MongoDB connection URI
    database: str = "arrest_records"  # Database name
    collection: str = "arrest_records"  # Collection name
    tenant: str = "DEFAULT"  # Multi-tenant identifier

class Config(BaseModel):
    input: InputConfig = InputConfig()
    parsing: ParsingConfig = ParsingConfig()
    output: OutputConfig = OutputConfig()
    logging: LoggingConfig = LoggingConfig()
    performance: PerformanceConfig = PerformanceConfig()
    mongodb: Optional[MongoDBConfig] = None  # MongoDB config (optional)
```

## Default Configuration (YAML)

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

logging:
  level: "INFO"
  emit_warnings_in_record: true

performance:
  parallel_pages: true

# MongoDB integration is disabled by default
# mongodb:
#   enabled: false
#   uri: "mongodb://localhost:27017"
#   database: "arrest_records"
#   collection: "arrest_records"
#   tenant: "DEFAULT"
```

## Regex Patterns

The following regex patterns will be used for parsing:

### Name Line (Strict, All Caps)
```python
NAME_REGEX_STRICT = r"^(?P<last>[A-Z][A-Z\-\.' ]+),\s+(?P<firstmid>[A-Z][A-Z\-\.' ]+)$"
```

### Name Line (Tolerant, Mixed Case)
```python
NAME_REGEX_TOLERANT = r"^(?P<last>[A-Za-z][A-Za-z\-\.' ]+),\s+(?P<firstmid>[A-Za-z][A-Za-z\-\.' ]+)$"
```

### Identifier + Date (One Line)
```python
ID_DATE_REGEX = r"(?P<id>\b\d{5,8}\b)\s+(?P<date>\b\d{1,2}/\d{1,2}/\d{4}\b)"
```

### Identifier Only
```python
IDENTIFIER_REGEX = r"^\s*(?P<id>\d{5,8})\s*$"
```

### Date Only
```python
DATE_REGEX = r"^\s*(?P<date>\d{1,2}/\d{1,2}/\d{4})\s*$"
```

### Booking Line
```python
BOOKING_REGEX = r"^(?P<booking>\d{2}-\d{6,7})\s+(?P<desc>.+)$"
```

### Header/Footer Skip Patterns
These are defined in the configuration and compiled at runtime.