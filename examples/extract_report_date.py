#!/usr/bin/env python3
"""
Example script demonstrating the extraction of report dates from PDFs.

This script shows how to:
1. Extract the report date from a PDF file
2. Handle different date formats
3. Test the extraction with sample PDFs

Usage:
    python extract_report_date.py [pdf_file]

Requirements:
    - arrestx package installed
    - pdfplumber package installed
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import arrestx
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from arrestx.web import extract_report_date
from arrestx.log import configure_logging, get_logger

# Configure logging
configure_logging(None)
logger = get_logger(__name__)


def test_with_file(pdf_path):
    """
    Test report date extraction with a specific file.
    
    Args:
        pdf_path: Path to the PDF file
    """
    print(f"Testing report date extraction with: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return
    
    try:
        # Extract the report date
        report_date = extract_report_date(pdf_path)
        
        if report_date:
            print(f"✅ Successfully extracted report date: {report_date}")
        else:
            print("❌ Could not extract report date from the PDF")
            print("\nTrying to debug the issue...")
            
            # Import pdfplumber for manual inspection
            import pdfplumber
            
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) > 0:
                    first_page = pdf.pages[0]
                    text = first_page.extract_text()
                    
                    print("\nFirst page text (first 500 characters):")
                    print("-" * 50)
                    print(text[:500])
                    print("-" * 50)
                    
                    print("\nSearching for date patterns:")
                    import re
                    
                    # Look for common date patterns
                    patterns = [
                        r"Report Date:\s+(\d{1,2}/\d{1,2}/\d{4})",
                        r"Date:\s+(\d{1,2}/\d{1,2}/\d{4})",
                        r"\b(\d{1,2}/\d{1,2}/\d{4})\b",
                        r"\b(\d{4}-\d{2}-\d{2})\b"
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, text)
                        if matches:
                            print(f"Found date(s) with pattern '{pattern}':")
                            for match in matches:
                                print(f"  - {match}")
                        else:
                            print(f"No matches found with pattern '{pattern}'")
    
    except Exception as e:
        print(f"Error extracting report date: {e}")


def create_sample_pdf():
    """
    Create a sample PDF with a report date for testing.
    
    Returns:
        Path to the created PDF file
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        import tempfile
        
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        
        # Create a PDF with a report date
        c = canvas.Canvas(path, pagesize=letter)
        c.drawString(100, 750, "Inmates Booked In")
        c.drawString(100, 730, "Report Date: 10/15/2025")
        c.drawString(100, 710, "Page 1")
        c.save()
        
        print(f"Created sample PDF with report date at: {path}")
        return path
    
    except ImportError:
        print("Error: reportlab package is required to create sample PDFs")
        print("Install it with: pip install reportlab")
        return None


def main():
    """
    Main function to test report date extraction.
    """
    print("=== Report Date Extraction Test ===\n")
    
    # Check if a file path was provided
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        test_with_file(pdf_path)
    else:
        # Create a sample PDF for testing
        sample_pdf = create_sample_pdf()
        
        if sample_pdf:
            test_with_file(sample_pdf)
            
            # Clean up the sample file
            try:
                os.remove(sample_pdf)
                print(f"\nRemoved sample PDF: {sample_pdf}")
            except Exception as e:
                print(f"Error removing sample PDF: {e}")


if __name__ == "__main__":
    main()