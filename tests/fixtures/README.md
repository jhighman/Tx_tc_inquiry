# Test Fixtures

This directory contains test fixtures for the Texas Extract test suite.

## Required Files

For the test suite to run successfully, the following files should be placed in this directory:

1. `sample_selectable.pdf`: A sample PDF with selectable text
2. `expected.json`: Expected JSON output for the selectable sample
3. `expected.csv`: Expected CSV output for the selectable sample
4. `sample_ocr_only.pdf`: A sample PDF requiring OCR
5. `expected_ocr.json`: Expected JSON output for the OCR sample
6. `expected_ocr.csv`: Expected CSV output for the OCR sample

## Creating Test Fixtures

### Sample PDFs

You can create sample PDFs with the following content:

```
Inmates Booked In During the Past 24 Hours  Report Date: 10/15/2025 Page: 1 of 1

SMITH, JOHN
123 MAIN ST
ANYTOWN, TX 12345
12345678 10/15/2025
25-0123456 NO VALID DL

JOHNSON, MARY
456 OAK AVE
SOMEWHERE, TX 54321
87654321 10/15/2025
25-0123457 FAILURE TO APPEAR
25-0123458 SPEEDING
```

### Expected JSON

The expected JSON output for the above sample would be:

```json
[
  {
    "name": "SMITH, JOHN",
    "name_normalized": "John Smith",
    "address": [
      "123 MAIN ST",
      "ANYTOWN, TX 12345"
    ],
    "identifier": "12345678",
    "book_in_date": "2025-10-15",
    "charges": [
      {
        "booking_no": "25-0123456",
        "description": "NO VALID DL"
      }
    ],
    "source_file": "sample_selectable.pdf",
    "source_page_span": [1, 1],
    "parse_warnings": [],
    "ocr_used": false
  },
  {
    "name": "JOHNSON, MARY",
    "name_normalized": "Mary Johnson",
    "address": [
      "456 OAK AVE",
      "SOMEWHERE, TX 54321"
    ],
    "identifier": "87654321",
    "book_in_date": "2025-10-15",
    "charges": [
      {
        "booking_no": "25-0123457",
        "description": "FAILURE TO APPEAR"
      },
      {
        "booking_no": "25-0123458",
        "description": "SPEEDING"
      }
    ],
    "source_file": "sample_selectable.pdf",
    "source_page_span": [1, 1],
    "parse_warnings": [],
    "ocr_used": false
  }
]
```

### Expected CSV

The expected CSV output for the above sample would be:

```csv
name,identifier,book_in_date,booking_no,description,address,source_file
SMITH, JOHN,12345678,2025-10-15,25-0123456,NO VALID DL,123 MAIN ST | ANYTOWN, TX 12345,sample_selectable.pdf
JOHNSON, MARY,87654321,2025-10-15,25-0123457,FAILURE TO APPEAR,456 OAK AVE | SOMEWHERE, TX 54321,sample_selectable.pdf
JOHNSON, MARY,87654321,2025-10-15,25-0123458,SPEEDING,456 OAK AVE | SOMEWHERE, TX 54321,sample_selectable.pdf
```

## OCR Sample

For the OCR sample, you can use the same content but save it as an image-based PDF that requires OCR. The expected output would be the same, except with `"ocr_used": true` in the JSON.