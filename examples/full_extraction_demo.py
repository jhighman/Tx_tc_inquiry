#!/usr/bin/env python3
"""
Full Extraction Demo

This script demonstrates the complete extraction process:
1. Creating a sample PDF with inmate records
2. Extracting the report date
3. Creating a backup with the report date
4. Parsing the PDF to extract records
5. Writing the records to JSON and CSV
6. Displaying the extracted data

Usage:
    python full_extraction_demo.py

Requirements:
    - arrestx package installed
    - reportlab package installed (for sample PDF creation)
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import arrestx
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from arrestx.config import Config
from arrestx.log import configure_logging, get_logger
from arrestx.web import extract_report_date, backup_file
from arrestx.parser import parse_pdf
from arrestx.writers import write_json, write_csv

# Configure logging
configure_logging(None)
logger = get_logger(__name__)


def create_sample_pdf(output_path):
    """
    Create a sample PDF with inmate records for testing.
    
    Args:
        output_path: Path to save the PDF
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create a PDF with inmate records
        c = canvas.Canvas(output_path, pagesize=letter)
        
        # Header
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, 750, "Inmates Booked In")
        c.drawString(100, 730, "Report Date: 10/15/2025")
        c.drawString(500, 750, "Page 1")
        
        # Records
        c.setFont("Helvetica", 12)
        y = 700
        
        # Record 1
        c.drawString(100, y, "SMITH, JOHN ROBERT")
        y -= 20
        c.drawString(100, y, "123 MAIN ST")
        y -= 20
        c.drawString(100, y, "ANYTOWN, TX 12345")
        y -= 20
        c.drawString(100, y, "1234567 10/15/2025")
        y -= 20
        c.drawString(100, y, "25-0123456 DRIVING WHILE INTOXICATED")
        y -= 20
        c.drawString(100, y, "25-0123457 PUBLIC INTOXICATION")
        y -= 40
        
        # Record 2
        c.drawString(100, y, "JONES, MARY ELLEN")
        y -= 20
        c.drawString(100, y, "456 OAK AVE")
        y -= 20
        c.drawString(100, y, "ANYTOWN, TX 12345")
        y -= 20
        c.drawString(100, y, "7654321 10/14/2025")
        y -= 20
        c.drawString(100, y, "25-0123458 THEFT UNDER $100")
        y -= 40
        
        # Record 3
        c.drawString(100, y, "WILLIAMS, ROBERT JAMES")
        y -= 20
        c.drawString(100, y, "789 PINE ST")
        y -= 20
        c.drawString(100, y, "ANYTOWN, TX 12345")
        y -= 20
        c.drawString(100, y, "9876543 10/13/2025")
        y -= 20
        c.drawString(100, y, "25-0123459 ASSAULT")
        y -= 20
        c.drawString(100, y, "25-0123460 RESISTING ARREST")
        
        # Footer
        c.setFont("Helvetica", 10)
        c.drawString(100, 50, "End of Report")
        
        c.save()
        
        print(f"Created sample PDF with inmate records at: {output_path}")
        return True
    
    except ImportError:
        print("Error: reportlab package is required to create sample PDFs")
        print("Install it with: pip install reportlab")
        return False
    except Exception as e:
        print(f"Error creating sample PDF: {e}")
        return False


def extract_and_backup(pdf_path):
    """
    Extract the report date from a PDF and create a backup.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Tuple of (report_date, backup_path) or (None, None) if failed
    """
    print(f"\nExtracting report date from: {pdf_path}")
    
    try:
        # Extract the report date
        report_date = extract_report_date(pdf_path)
        
        if report_date:
            print(f"✅ Successfully extracted report date: {report_date}")
            
            # Create a backup with the report date
            backup_path = backup_file(pdf_path, report_date)
            
            if backup_path:
                print(f"✅ Created backup at: {backup_path}")
                return report_date, backup_path
            else:
                print("❌ Failed to create backup")
                return report_date, None
        else:
            print("❌ Could not extract report date from the PDF")
            return None, None
    
    except Exception as e:
        print(f"Error during extraction and backup: {e}")
        return None, None


def parse_and_output(pdf_path, output_dir):
    """
    Parse a PDF and write the records to JSON and CSV.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to write output files
        
    Returns:
        List of extracted records or None if failed
    """
    print(f"\nParsing PDF: {pdf_path}")
    
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Create configuration
        config = Config()
        config.input.ocr_fallback = False
        config.parsing.name_regex_strict = True
        config.parsing.allow_two_line_id_date = True
        
        # Parse the PDF
        records = parse_pdf(pdf_path, config)
        
        if records:
            print(f"✅ Successfully extracted {len(records)} records")
            
            # Write to JSON
            json_path = os.path.join(output_dir, "arrests.json")
            write_json(records, json_path, pretty=True)
            print(f"✅ Wrote JSON to: {json_path}")
            
            # Write to CSV
            csv_path = os.path.join(output_dir, "arrests.csv")
            write_csv(records, csv_path)
            print(f"✅ Wrote CSV to: {csv_path}")
            
            return records
        else:
            print("❌ No records extracted from the PDF")
            return None
    
    except Exception as e:
        print(f"Error during parsing and output: {e}")
        return None


def display_records(records):
    """
    Display the extracted records in a readable format.
    
    Args:
        records: List of extracted records
    """
    if not records:
        print("\nNo records to display")
        return
    
    print(f"\nDisplaying {len(records)} extracted records:")
    print("=" * 50)
    
    for i, record in enumerate(records, 1):
        print(f"Record #{i}:")
        print(f"  Name: {record.get('name')}")
        print(f"  Name (normalized): {record.get('name_normalized')}")
        print(f"  Address: {', '.join(record.get('address', []))}")
        print(f"  Identifier: {record.get('identifier')}")
        print(f"  Book-in Date: {record.get('book_in_date')}")
        print(f"  Charges:")
        
        for charge in record.get('charges', []):
            print(f"    - {charge.get('booking_no')}: {charge.get('description')}")
        
        if record.get('parse_warnings'):
            print(f"  Warnings: {', '.join(record.get('parse_warnings'))}")
        
        print("-" * 50)


def main():
    """
    Main function demonstrating the full extraction process.
    """
    print("=== Full Extraction Demo ===\n")
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    reports_dir = os.path.join(temp_dir, "reports")
    output_dir = os.path.join(temp_dir, "output")
    
    try:
        # Create sample PDF
        pdf_path = os.path.join(reports_dir, "sample.pdf")
        if not create_sample_pdf(pdf_path):
            return
        
        # Extract report date and create backup
        report_date, backup_path = extract_and_backup(pdf_path)
        
        if not report_date:
            return
        
        # Parse PDF and write output
        records = parse_and_output(pdf_path, output_dir)
        
        if records:
            # Display the extracted records
            display_records(records)
            
            # Show output files
            print("\nOutput files:")
            json_path = os.path.join(output_dir, "arrests.json")
            csv_path = os.path.join(output_dir, "arrests.csv")
            
            print(f"JSON: {json_path}")
            print(f"CSV: {csv_path}")
            
            # Display JSON content
            print("\nJSON content:")
            with open(json_path, "r") as f:
                print(f.read())
    
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
            print(f"\nCleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"Error cleaning up temporary directory: {e}")


if __name__ == "__main__":
    main()