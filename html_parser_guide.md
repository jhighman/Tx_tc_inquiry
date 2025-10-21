# HTML-Based Parser Guide

## Overview

The HTML-based parser is a new, more reliable approach to extracting structured data from PDF arrest reports. Instead of parsing raw text with complex regex patterns, it converts PDFs to HTML and then parses the structured table data.

## Why HTML Parsing?

The original text-based parser faces several challenges:

- **Complex regex patterns**: Over 20 different regex patterns to identify names, dates, booking numbers
- **State machine complexity**: 1800+ lines of parsing logic with complex state transitions
- **Fragmented data handling**: Difficulty with embedded names and split data across lines
- **Maintenance burden**: Hard to debug and modify parsing rules

The HTML approach solves these issues by:

- **Leveraging structure**: Uses the existing table structure in PDFs
- **Simpler logic**: DOM parsing is more straightforward than regex parsing
- **Better reliability**: Less prone to parsing errors
- **Easier maintenance**: Cleaner, more maintainable code

## How It Works

### 1. PDF to HTML Conversion

The parser tries multiple conversion methods in order of preference:

1. **pdfplumber**: Extracts table data directly from PDF structure
2. **pdftohtml**: Command-line tool for PDF to HTML conversion
3. **PyMuPDF**: Alternative PDF processing library

### 2. HTML Table Parsing

Once converted to HTML, the parser:

1. Finds table elements using BeautifulSoup
2. Identifies column headers (Name, Identifier, Date, Booking, Description)
3. Extracts data from each table row
4. Handles continuation rows and multi-line data

### 3. Fallback Mechanism

If HTML parsing fails, the system automatically falls back to the original text-based parser.

## Configuration

Add these options to your `config.yaml`:

```yaml
parsing:
  # Enable HTML parsing (default: true)
  use_html_parser: true
  
  # Preferred conversion methods in order
  html_conversion_methods:
    - "pdfplumber"
    - "pdftohtml"
    - "pymupdf"
  
  # Text parsing options (fallback)
  name_regex_strict: true
  allow_two_line_id_date: true
```

## Installation

The HTML parser requires additional dependencies:

```bash
pip install beautifulsoup4 PyMuPDF
```

For the `pdftohtml` method, install poppler-utils:

```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows
# Download from https://poppler.freedesktop.org/
```

## Usage

The HTML parser is automatically used when available. No code changes are needed:

```python
from arrestx.parser import parse_pdf
from arrestx.config import Config

cfg = Config()
records = parse_pdf("arrest_report.pdf", cfg)
```

## Example: Table Structure

The parser expects PDF tables with this structure:

| Inmate Name | Identifier CID | Book In Date | Booking No. | Description |
|-------------|----------------|--------------|-------------|-------------|
| SMITH, JOHN DOE<br/>123 MAIN ST<br/>CITY TX 12345 | 1234567 | 10/20/2025 | 25-0241234 | ASSAULT FAMILY VIOLENCE |
| | | | 25-0241235 | DRIVING WHILE INTOXICATED |

This becomes:

```html
<table>
  <tr>
    <th>Inmate Name</th>
    <th>Identifier CID</th>
    <th>Book In Date</th>
    <th>Booking No.</th>
    <th>Description</th>
  </tr>
  <tr>
    <td>SMITH, JOHN DOE<br/>123 MAIN ST<br/>CITY TX 12345</td>
    <td>1234567</td>
    <td>10/20/2025</td>
    <td>25-0241234</td>
    <td>ASSAULT FAMILY VIOLENCE</td>
  </tr>
  <tr>
    <td></td>
    <td></td>
    <td></td>
    <td>25-0241235</td>
    <td>DRIVING WHILE INTOXICATED</td>
  </tr>
</table>
```

## Parsed Output

The HTML parser produces the same record structure as the text parser:

```python
{
    "name": "SMITH, JOHN DOE",
    "name_normalized": "John Doe Smith",
    "street": ["123 MAIN ST", "CITY TX 12345"],
    "identifier": "1234567",
    "book_in_date": "2025-10-20",
    "charges": [
        {
            "booking_no": "25-0241234",
            "description": "ASSAULT FAMILY VIOLENCE"
        },
        {
            "booking_no": "25-0241235", 
            "description": "DRIVING WHILE INTOXICATED"
        }
    ],
    "source_file": "arrest_report.pdf",
    "source_page_span": [1, 1],
    "parse_warnings": [],
    "ocr_used": false
}
```

## Advantages

### Reliability
- **Structured parsing**: Uses existing table structure instead of guessing
- **Better accuracy**: Less prone to parsing errors
- **Handles complex cases**: Multi-line addresses, continuation rows

### Maintainability
- **Simpler code**: ~500 lines vs 1800+ lines
- **Cleaner logic**: DOM parsing vs complex state machines
- **Easier debugging**: Clear HTML structure to inspect

### Flexibility
- **Multiple conversion methods**: Tries different approaches automatically
- **Graceful fallback**: Falls back to text parsing if needed
- **Configurable**: Control conversion method preferences

## Troubleshooting

### HTML Conversion Fails
If all HTML conversion methods fail, the parser automatically falls back to text parsing. Check logs for specific error messages.

### Missing Dependencies
```
ImportError: BeautifulSoup4 is required for HTML parsing
```
Install with: `pip install beautifulsoup4`

### Poor Table Detection
If the PDF doesn't have proper table structure, the HTML conversion may not work well. The text parser fallback will handle these cases.

### Performance
HTML conversion adds some overhead, but the improved accuracy usually makes it worthwhile. For high-volume processing, you can disable HTML parsing:

```yaml
parsing:
  use_html_parser: false
```

## Testing

Run the HTML parser tests:

```bash
pytest tests/test_html_parser.py -v
```

See the demonstration:

```bash
python demo_html_parser.py
```

## Migration

The HTML parser is designed to be a drop-in replacement. Existing code continues to work without changes. The parser automatically:

1. Tries HTML parsing first
2. Falls back to text parsing if needed
3. Produces the same output format
4. Maintains backward compatibility

## Future Enhancements

Potential improvements:

- **OCR integration**: Better handling of scanned PDFs
- **Table detection**: Improved table boundary detection
- **Performance optimization**: Caching and parallel processing
- **Custom extractors**: Support for different PDF layouts