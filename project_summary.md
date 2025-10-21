# Texas Extract - Project Summary

## Overview

Texas Extract is a robust system for extracting structured arrest records from county jail "book-in" PDF reports. The system parses PDF reports with a consistent layout to extract inmate records including names, addresses, identifiers, book-in dates, and charges. The extracted data is output to JSON, CSV, and optionally NDJSON formats, with the ability to stream to a MongoDB database.

## Key Features

1. **PDF Text Extraction**: Extracts text from PDF reports with OCR fallback for non-selectable text.
2. **State Machine Parser**: Uses a state machine with regex patterns to parse text into structured records.
3. **Multiple Output Formats**: Supports JSON, CSV, and NDJSON output formats.
4. **MongoDB Integration**: Optional integration with MongoDB for storing and querying records.
5. **Web Retrieval**: Fetches reports from URLs with conditional headers for efficiency.
6. **Backup Mechanism**: Automatically backs up reports with date-based filenames to preserve historical data.
7. **Command-Line Interface**: Comprehensive CLI for processing files, fetching reports, and creating backups.
8. **Privacy Options**: Supports redaction of address information and hashing of identifiers.
9. **Extensibility**: Plugin architecture for supporting different report formats.

## Architecture

The system is organized into several modules:

- **PDF I/O**: Handles PDF text extraction with OCR fallback.
- **Parser**: Implements the state machine for parsing text into records.
- **Writers**: Handles output to JSON, CSV, and NDJSON formats.
- **Web**: Manages web retrieval and backup of reports.
- **DB**: Provides MongoDB integration for storing records.
- **CLI**: Implements the command-line interface.
- **Config**: Manages configuration loading and validation.
- **Log**: Handles logging throughout the system.

## Backup Mechanism

The backup mechanism ensures that when a new report is downloaded:

1. The system extracts the report date from the PDF header
2. Creates a backup of any existing file with the same name
3. Stores the backup in the `archive` subdirectory with the report date in the filename
4. Replaces the original file with the new download

This solves the problem of the source URL always pointing to the same filename (e.g., `01.PDF`), which gets overwritten daily. Without this backup mechanism, historical data would be lost when new reports are downloaded.

## Data Model

Each record represents a single inmate and includes:

- Name (original and normalized)
- Address (0-3 lines)
- Identifier (5-8 digit string)
- Book-in date (ISO 8601 format)
- Charges (array of booking numbers and descriptions)
- Source information (file, page span)
- Parse warnings (optional)

## Testing Strategy

The system includes comprehensive tests:

- Unit tests for each module
- Integration tests for end-to-end functionality
- Golden sample tests with known inputs and expected outputs
- Performance tests for large reports

## Deployment

The system can be deployed as:

1. A command-line tool for manual processing
2. A scheduled job for daily report retrieval
3. A service for continuous monitoring and processing
4. A library integrated into other applications

## Future Enhancements

1. **Advanced Entity Resolution**: De-duplication across reports and entity resolution.
2. **Charge Coding**: Mapping free-text charge descriptions to standard codes.
3. **Data Visualization**: Dashboard for visualizing arrest trends.
4. **API**: REST API for querying and retrieving records.
5. **Hierarchical Archive Structure**: Organizing backups by year/month for better scalability.
6. **Retention Policy**: Automatic cleanup of old backups based on age or count.
7. **Compression**: Compressing older backups to save disk space.