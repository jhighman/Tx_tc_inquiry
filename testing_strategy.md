# Testing Strategy

This document outlines the testing strategy for the Texas Extract system, including unit tests, integration tests, and acceptance criteria.

## Testing Levels

### 1. Unit Tests

Unit tests verify the functionality of individual components in isolation. Each module should have corresponding unit tests.

#### 1.1 PDF I/O Tests

- Test text extraction from PDFs with selectable text
- Test OCR fallback for non-selectable text
- Test handling of multi-page PDFs
- Test error handling for corrupted PDFs

#### 1.2 Parser Tests

- Test regex patterns for name, identifier, date, and booking
- Test state machine transitions
- Test handling of edge cases (wrapped lines, missing fields)
- Test warning collection
- Test normalization functions

#### 1.3 Writers Tests

- Test JSON output formatting
- Test CSV output formatting
- Test NDJSON output formatting
- Test privacy options (redaction, hashing)

#### 1.4 Web Retrieval and Backup Tests

- Test fetching PDFs from URLs
- Test conditional headers (If-Modified-Since, ETag)
- Test error handling for network issues
- Test extracting report dates from PDFs
- Test creating backups with report dates
- Test handling existing backups
- Test directory creation for archives

#### 1.5 MongoDB Tests

- Test document schema
- Test bulk ingestion
- Test idempotent upsert logic
- Test query functionality

#### 1.6 CLI Tests

- Test command-line argument parsing
- Test configuration loading
- Test error handling and reporting
- Test backup command functionality

### 2. Integration Tests

Integration tests verify the interaction between components.

#### 2.1 End-to-End Tests

- Test processing a PDF from start to finish
- Test web retrieval, backup, parsing, and output
- Test MongoDB integration with real database

#### 2.2 Golden Sample Tests

- Test with known inputs and expected outputs
- Verify deterministic output

### 3. Performance Tests

- Test processing time for large PDFs
- Test memory usage
- Test MongoDB performance with large datasets
- Test parallel processing

## Test Data

### 1. Sample PDFs

- `sample_selectable.pdf`: PDF with selectable text
- `sample_ocr_only.pdf`: PDF without selectable text (requires OCR)
- `sample_multi_page.pdf`: PDF with multiple pages
- `sample_edge_cases.pdf`: PDF with edge cases (wrapped lines, missing fields)

### 2. Expected Outputs

- `expected.json`: Expected JSON output for sample PDFs
- `expected.csv`: Expected CSV output for sample PDFs
- `expected_ocr.json`: Expected JSON output for OCR sample

## Test Implementation

### 1. Framework

Use pytest for all tests.

```python
import pytest

def test_parse_pdf():
    # Test code here
    pass
```

### 2. Fixtures

Use fixtures for common setup and teardown.

```python
@pytest.fixture
def sample_pdf():
    # Create a sample PDF
    return "path/to/sample.pdf"

def test_parse_pdf(sample_pdf):
    # Test using the fixture
    pass
```

### 3. Mocking

Use mocking for external dependencies.

```python
from unittest.mock import patch

@patch("arrestx.pdfio.extract_text")
def test_parse_pdf_with_mock(mock_extract_text):
    mock_extract_text.return_value = ["Line 1", "Line 2"]
    # Test code here
    pass
```

## Web Retrieval and Backup Tests

### 1. Backup File Tests

```python
def test_backup_file(temp_dir, sample_pdf):
    """Test backing up a file with a report date."""
    # Set up test
    report_date = "2025-10-15"
    
    # Call function
    backup_path = backup_file(sample_pdf, report_date)
    
    # Verify results
    assert backup_path is not None
    assert os.path.exists(backup_path)
    assert "archive" in backup_path
    assert f"sample_{report_date}.pdf" in backup_path
    
    # Verify file content is the same
    with open(sample_pdf, "rb") as f1, open(backup_path, "rb") as f2:
        assert f1.read() == f2.read()
```

### 2. Extract Report Date Tests

```python
@patch("arrestx.web.pdf_open")
def test_extract_report_date(mock_pdf_open, temp_dir):
    """Test extracting report date from a PDF."""
    # Set up mock
    mock_pdf = mock.MagicMock()
    mock_page = mock.MagicMock()
    mock_page.extract_text.return_value = "Inmates Booked In\nReport Date: 10/15/2025\nPage 1"
    mock_pdf.pages = [mock_page]
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf
    
    # Call function
    report_date = extract_report_date("mock.pdf")
    
    # Verify results
    assert report_date == "2025-10-15"
```

### 3. Fetch PDF Tests

```python
@patch("arrestx.web.requests.get")
def test_fetch_pdf_success(mock_get, temp_dir):
    """Test fetching a PDF successfully."""
    # Set up mock
    mock_response = mock.MagicMock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = [b"PDF content"]
    mock_response.headers = {"ETag": "123", "Last-Modified": "Wed, 15 Oct 2025 12:00:00 GMT"}
    mock_get.return_value = mock_response
    
    # Set up test
    output_path = os.path.join(temp_dir, "output.pdf")
    
    # Call function
    result = fetch_pdf("http://example.com/test.pdf", output_path)
    
    # Verify results
    assert result["status"] == "success"
    assert result["modified"] is True
    assert result["etag"] == "123"
    assert os.path.exists(output_path)
    
    # Verify file content
    with open(output_path, "rb") as f:
        assert f.read() == b"PDF content"
```

### 4. Process Daily Report Tests

```python
@patch("arrestx.web.fetch_pdf")
@patch("arrestx.web.extract_report_date")
@patch("arrestx.web.backup_file")
@patch("arrestx.web.parse_pdf")
@patch("arrestx.web.write_outputs")
def test_process_daily_report_success(
    mock_write_outputs, mock_parse_pdf, mock_backup_file, 
    mock_extract_report_date, mock_fetch_pdf, mock_config, temp_dir
):
    """Test processing a daily report successfully."""
    # Set up mocks
    mock_fetch_pdf.return_value = {
        "status": "success",
        "message": "File downloaded successfully",
        "modified": True
    }
    mock_extract_report_date.return_value = "2025-10-15"
    mock_backup_file.return_value = os.path.join(temp_dir, "archive", "01_2025-10-15.PDF")
    mock_parse_pdf.return_value = [{"name": "Test Person"}]
    
    # Call function
    result = process_daily_report("http://example.com/01.PDF", mock_config)
    
    # Verify results
    assert result["status"] == "success"
    assert result["record_count"] == 1
    
    # Verify backup was created
    assert mock_backup_file.called
```

## CLI Tests

### 1. Backup Command Tests

```python
from typer.testing import CliRunner
from arrestx.cli import app

def test_backup_command(temp_dir, sample_pdf):
    """Test the backup command."""
    runner = CliRunner()
    result = runner.invoke(app, ["backup", sample_pdf, "2025-10-15"])
    
    assert result.exit_code == 0
    assert "Successfully backed up" in result.stdout
    
    # Verify backup was created
    backup_path = os.path.join(os.path.dirname(sample_pdf), "archive", f"{os.path.basename(sample_pdf).split('.')[0]}_2025-10-15.{os.path.basename(sample_pdf).split('.')[1]}")
    assert os.path.exists(backup_path)
```

### 2. Fetch Command Tests

```python
@patch("arrestx.cli.process_daily_report")
def test_fetch_command(mock_process_daily_report):
    """Test the fetch command."""
    # Set up mock
    mock_process_daily_report.return_value = {
        "status": "success",
        "message": "Processed 10 records",
        "record_count": 10
    }
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(app, ["fetch"])
    
    # Verify results
    assert result.exit_code == 0
    assert "Status: success" in result.stdout
    assert "Records: 10" in result.stdout
```

## Acceptance Criteria

### 1. Basic Functionality

- System correctly extracts records from all test PDFs
- JSON and CSV outputs match expected formats
- OCR fallback works for non-selectable text
- All tests pass with > 90% coverage

### 2. Web Retrieval and Backup

- System successfully fetches PDFs from URLs
- Conditional headers prevent unnecessary downloads
- Report dates are correctly extracted from PDFs
- Backups are created with the correct naming convention
- Archive directory structure is maintained
- CLI backup command works as expected

### 3. Performance

- Processing time < 5 seconds per page
- Memory usage < 500MB for typical reports
- MongoDB operations complete in reasonable time

### 4. Error Handling

- System gracefully handles corrupted PDFs
- Network errors are properly reported
- Missing fields generate appropriate warnings
- CLI provides clear error messages

## Continuous Integration

Set up a CI pipeline to run tests automatically:

1. Run unit tests on every commit
2. Run integration tests on pull requests
3. Run performance tests weekly
4. Generate coverage reports
5. Enforce minimum coverage threshold (90%)

## Test Execution

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_web.py

# Run with coverage
pytest --cov=arrestx

# Generate coverage report
pytest --cov=arrestx --cov-report=html