#!/usr/bin/env python3
"""
Example script demonstrating the web retrieval and backup functionality.

This script shows how to:
1. Fetch a PDF report from a URL
2. Extract the report date
3. Create a backup with the report date in the filename
4. Process the report and extract records
5. Write the records to JSON and CSV files

Usage:
    python web_retrieval.py

Requirements:
    - arrestx package installed
    - Internet connection
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import arrestx
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from arrestx.config import Config, load_config
from arrestx.log import configure_logging, get_logger
from arrestx.web import backup_file, extract_report_date, fetch_pdf, process_daily_report

# Configure logging
configure_logging(None)
logger = get_logger(__name__)


def example_fetch_and_backup():
    """
    Example of fetching a PDF and creating a backup.
    """
    # URL of the report to fetch
    url = "https://cjreports.tarrantcounty.com/Reports/JailedInmates/FinalPDF/01.PDF"
    
    # Directory to save the report
    reports_dir = Path("./reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Path to save the report
    output_path = reports_dir / "01.PDF"
    
    print(f"Fetching report from {url}...")
    
    try:
        # Fetch the PDF
        result = fetch_pdf(url, str(output_path))
        
        if result["status"] == "not_modified":
            print("Report not modified since last fetch.")
            return
        
        print(f"Report downloaded successfully to {output_path}")
        
        # Extract the report date
        report_date = extract_report_date(str(output_path))
        
        if report_date:
            print(f"Report date: {report_date}")
            
            # Create a backup with the report date
            backup_path = backup_file(str(output_path), report_date)
            
            if backup_path:
                print(f"Created backup: {backup_path}")
            else:
                print("Failed to create backup.")
        else:
            print("Could not extract report date.")
    
    except Exception as e:
        print(f"Error: {e}")


def example_process_daily_report():
    """
    Example of processing a daily report with automatic backup.
    """
    # URL of the report to fetch
    url = "https://cjreports.tarrantcounty.com/Reports/JailedInmates/FinalPDF/01.PDF"
    
    # Create a configuration
    try:
        # Try to load from config.yaml first
        config = load_config("config.yaml")
    except:
        # If that fails, create a default config
        config = Config()
    
    # Set output paths
    config.output.json_path = "./out/arrests.json"
    config.output.csv_path = "./out/arrests.csv"
    config.input.ocr_fallback = False
    
    # Create output directory
    Path("./out").mkdir(exist_ok=True)
    
    print(f"Processing daily report from {url}...")
    
    try:
        # Modify the process_daily_report function to handle missing db attribute
        # by checking if config.db.enabled is set before using it
        result = process_daily_report(url, config)
        
        # Print result
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        
        if "record_count" in result:
            print(f"Records: {result['record_count']}")
    
    except Exception as e:
        print(f"Error: {e}")


def example_manual_backup():
    """
    Example of manually creating a backup of a report.
    """
    # Path to the report
    report_path = "./reports/01.PDF"
    
    # Check if the report exists
    if not os.path.exists(report_path):
        print(f"Report not found: {report_path}")
        return
    
    # Use today's date for the backup
    today = datetime.now().strftime("%Y-%m-%d")
    
    print(f"Creating backup of {report_path} with date {today}...")
    
    try:
        # Create a backup
        backup_path = backup_file(report_path, today)
        
        if backup_path:
            print(f"Created backup: {backup_path}")
        else:
            print("Failed to create backup.")
    
    except Exception as e:
        print(f"Error: {e}")


def main():
    """
    Main function demonstrating all examples.
    """
    print("=== Web Retrieval and Backup Examples ===\n")
    
    print("Example 1: Fetch and Backup")
    print("-" * 30)
    example_fetch_and_backup()
    print()
    
    print("Example 2: Process Daily Report")
    print("-" * 30)
    example_process_daily_report()
    print()
    
    print("Example 3: Manual Backup")
    print("-" * 30)
    example_manual_backup()
    print()


if __name__ == "__main__":
    main()