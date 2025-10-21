# Web Retrieval Module Design

This document outlines the design of the web retrieval module for the Texas Extract system, including the backup mechanism for daily downloaded files.

## Overview

The web retrieval module is responsible for:

1. Fetching PDF reports from a specified URL
2. Backing up existing files before replacing them
3. Processing the downloaded reports
4. Storing the extracted data in the configured outputs (JSON, CSV, NDJSON, MongoDB)

## Components

### 1. `fetch_pdf` Function

Responsible for downloading a PDF from a URL and saving it to the specified path.

**Features:**
- Conditional GET requests using If-Modified-Since and ETag headers
- Streaming download for large files
- Error handling for network issues

**Return Value:**
```python
{
    "status": "success" | "not_modified" | "error",
    "message": str,
    "modified": bool,
    "etag": Optional[str],
    "last_modified": Optional[str]
}
```

### 2. `extract_report_date` Function

Extracts the report date from a PDF file by searching for specific patterns in the text.

**Patterns:**
- `Report Date: MM/DD/YYYY`
- Standalone `MM/DD/YYYY` format

**Return Value:**
- ISO 8601 formatted date string (`YYYY-MM-DD`) or `None` if not found

### 3. `backup_file` Function

Creates a backup of a file with the report date in the filename.

**Process:**
1. Check if the file exists
2. Create the archive directory if it doesn't exist
3. Generate the backup filename with the report date
4. Check if the backup already exists
5. Copy the file to the backup location

**Return Value:**
- Path to the backup file or `None` if backup failed

### 4. `process_daily_report` Function

Orchestrates the entire process of fetching, backing up, and processing a report.

**Process:**
1. Determine the output path
2. Check if the file already exists
3. Fetch the PDF from the URL
4. If the file was modified and previously existed:
   - Extract the report date
   - Create a backup with the report date
5. Process the PDF to extract records
6. Write the records to the configured outputs
7. Store the records in MongoDB if configured

**Return Value:**
```python
{
    "status": "success" | "not_modified" | "error",
    "message": str,
    "record_count": Optional[int],
    "inserted_count": Optional[int],
    "updated_count": Optional[int]
}
```

## Backup Mechanism

### Problem Statement

The source URL for daily reports always points to the same filename (e.g., `01.PDF`), which gets overwritten daily. Without a backup mechanism, historical data would be lost when new reports are downloaded.

### Solution

The backup mechanism ensures that when a new report is downloaded:

1. The system extracts the report date from the PDF header
2. Creates a backup of any existing file with the same name
3. Stores the backup in the `archive` subdirectory with the report date in the filename
4. Replaces the original file with the new download

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

### Error Handling

- If the report date cannot be extracted, the backup will fail but the download will proceed
- If the backup fails (e.g., due to permissions or disk space), a warning is logged but the download will proceed
- If a backup with the same name already exists, it will not be overwritten

## CLI Integration

The backup functionality is exposed through the CLI:

```bash
# Automatic backup during fetch
arrestx fetch --url https://example.com/01.PDF

# Manual backup
arrestx backup ./reports/01.PDF 2025-10-15
```

## Future Enhancements

1. **Hierarchical Archive Structure**: Organize backups by year/month for better scalability
   ```
   archive/2025/10/01_2025-10-15.PDF
   ```

2. **Retention Policy**: Implement automatic cleanup of old backups based on age or count

3. **Compression**: Compress older backups to save disk space

4. **Metadata Storage**: Store metadata about each backup (size, hash, record count) in a database

5. **Parallel Processing**: Download and process multiple reports in parallel

## Implementation Considerations

1. **File Locking**: Ensure atomic operations when backing up and replacing files

2. **Disk Space Monitoring**: Check available disk space before downloading large files

3. **Logging**: Comprehensive logging of all operations for audit and troubleshooting

4. **Error Recovery**: Ability to recover from partial downloads or interrupted operations

5. **Configurability**: Make backup behavior configurable (enable/disable, naming convention, etc.)