# Reports Directory

This directory contains the PDF reports downloaded from the county jail booking system.

## Structure

- `*.PDF` - The most recent reports downloaded from the system
- `archive/` - Directory containing archived/backup reports

## Backup Mechanism

When a new report is downloaded, the system:

1. Extracts the report date from the PDF header (looking for "Report Date: MM/DD/YYYY" pattern)
2. Creates a backup of any existing file with the same name
3. Stores the backup in the `archive` subdirectory with the report date in the filename

### Backup Naming Convention

Backup files follow this naming convention:

```
{original_filename}_{YYYY-MM-DD}.{extension}
```

For example, if the original file is `01.PDF` and the report date is October 15, 2025, the backup file will be named:

```
01_2025-10-15.PDF
```

### Manual Backup

You can manually create a backup of a report using the CLI:

```bash
arrestx backup ./reports/01.PDF 2025-10-15
```

This will create a backup of `01.PDF` in the `reports/archive` directory with the name `01_2025-10-15.PDF`.

## Retention Policy

By default, all backup files are retained indefinitely. If you need to implement a retention policy to limit disk usage, consider:

1. Setting up a cron job to delete backups older than a certain date
2. Using the `find` command to identify and remove old backups:

```bash
# Example: Delete backups older than 90 days
find ./reports/archive -name "*.PDF" -type f -mtime +90 -delete
```

## Troubleshooting

If the system fails to create a backup, check:

1. File permissions - ensure the process has write access to the `archive` directory
2. Disk space - ensure there is sufficient disk space available
3. Report date extraction - if the report date cannot be extracted, the backup will fail

Backup failures are logged with a warning message but will not prevent the new report from being processed.