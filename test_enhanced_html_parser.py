#!/usr/bin/env python3
"""
Test script for the enhanced HTML parser.

This script demonstrates the new HTML parsing capabilities with multiple
extraction methods that can handle various PDF structures.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from arrestx.config import Config
from arrestx.html_parser import parse_pdf_via_html
from arrestx.log import get_logger

logger = get_logger(__name__)


def test_enhanced_html_parser():
    """Test the enhanced HTML parser with the sample PDF."""
    
    # Path to the sample PDF
    pdf_path = "out/01.PDF"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF file not found: {pdf_path}")
        print("Please ensure the PDF file exists before running this test.")
        return False
    
    print("🔍 Testing Enhanced HTML Parser")
    print("=" * 50)
    
    # Create configuration with enhanced HTML parser enabled
    cfg = Config()
    cfg.parsing.use_html_parser = True
    cfg.parsing.use_enhanced_html_parser = True
    
    print(f"📄 Processing PDF: {pdf_path}")
    print(f"🔧 Enhanced HTML parser: {cfg.parsing.use_enhanced_html_parser}")
    print(f"📋 Available extraction methods: {cfg.parsing.enhanced_extraction_methods}")
    print()
    
    try:
        # Parse the PDF using enhanced HTML parser
        records = parse_pdf_via_html(pdf_path, cfg)
        
        print(f"✅ Successfully extracted {len(records)} records")
        print()
        
        if records:
            print("📊 Sample Records:")
            print("-" * 30)
            
            # Show first few records
            for i, record in enumerate(records[:3]):
                print(f"Record {i+1}:")
                print(f"  Name: {record.get('name', 'N/A')}")
                print(f"  Normalized: {record.get('name_normalized', 'N/A')}")
                print(f"  Identifier: {record.get('identifier', 'N/A')}")
                print(f"  Date: {record.get('book_in_date', 'N/A')}")
                print(f"  Street: {record.get('street', [])}")
                print(f"  Charges: {len(record.get('charges', []))}")
                if record.get('charges'):
                    for j, charge in enumerate(record['charges'][:2]):  # Show first 2 charges
                        print(f"    Charge {j+1}: {charge.get('booking_no', 'N/A')} - {charge.get('description', 'N/A')}")
                print(f"  Warnings: {record.get('parse_warnings', [])}")
                print()
            
            if len(records) > 3:
                print(f"... and {len(records) - 3} more records")
                print()
            
            # Show statistics
            print("📈 Statistics:")
            print(f"  Total records: {len(records)}")
            
            records_with_names = sum(1 for r in records if r.get('name'))
            print(f"  Records with names: {records_with_names}")
            
            records_with_ids = sum(1 for r in records if r.get('identifier'))
            print(f"  Records with identifiers: {records_with_ids}")
            
            records_with_dates = sum(1 for r in records if r.get('book_in_date'))
            print(f"  Records with dates: {records_with_dates}")
            
            total_charges = sum(len(r.get('charges', [])) for r in records)
            print(f"  Total charges: {total_charges}")
            
            records_with_warnings = sum(1 for r in records if r.get('parse_warnings'))
            print(f"  Records with warnings: {records_with_warnings}")
            
            return True
        else:
            print("⚠️  No records extracted")
            return False
            
    except Exception as e:
        print(f"❌ Error during parsing: {e}")
        logger.exception("Enhanced HTML parser test failed")
        return False


def test_extraction_methods():
    """Test individual extraction methods."""
    
    pdf_path = "out/01.PDF"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return False
    
    print("\n🧪 Testing Individual Extraction Methods")
    print("=" * 50)
    
    # Import the enhanced parser directly
    try:
        from arrestx.html_parser_enhanced import EnhancedHTMLParser
        
        cfg = Config()
        parser = EnhancedHTMLParser(cfg)
        
        # Test each method individually
        methods = [
            ("tabula", parser._extract_with_tabula),
            ("camelot", parser._extract_with_camelot),
            ("pymupdf_positioned", parser._extract_with_pymupdf_positioned),
            ("pdfplumber_enhanced", parser._extract_with_pdfplumber_enhanced),
            ("pdftohtml", parser._extract_with_pdftohtml),
        ]
        
        results = {}
        
        for method_name, method_func in methods:
            print(f"🔍 Testing {method_name}...")
            
            try:
                records = method_func(pdf_path)
                record_count = len(records) if records else 0
                results[method_name] = {
                    "success": True,
                    "records": record_count,
                    "error": None
                }
                print(f"  ✅ Success: {record_count} records")
                
            except ImportError as e:
                results[method_name] = {
                    "success": False,
                    "records": 0,
                    "error": f"Missing dependency: {e}"
                }
                print(f"  ⚠️  Skipped: {e}")
                
            except Exception as e:
                results[method_name] = {
                    "success": False,
                    "records": 0,
                    "error": str(e)
                }
                print(f"  ❌ Failed: {e}")
        
        print("\n📊 Method Comparison:")
        print("-" * 30)
        
        for method_name, result in results.items():
            status = "✅" if result["success"] else "❌"
            print(f"{status} {method_name:20} | {result['records']:3} records | {result['error'] or 'OK'}")
        
        # Find the best method
        successful_methods = [(name, result) for name, result in results.items() 
                            if result["success"] and result["records"] > 0]
        
        if successful_methods:
            best_method = max(successful_methods, key=lambda x: x[1]["records"])
            print(f"\n🏆 Best method: {best_method[0]} ({best_method[1]['records']} records)")
        else:
            print("\n⚠️  No methods successfully extracted records")
        
        return len(successful_methods) > 0
        
    except ImportError as e:
        print(f"❌ Could not import enhanced parser: {e}")
        return False


def main():
    """Main test function."""
    
    print("🚀 Enhanced HTML Parser Test Suite")
    print("=" * 60)
    
    # Test 1: Enhanced HTML parser
    success1 = test_enhanced_html_parser()
    
    # Test 2: Individual extraction methods
    success2 = test_extraction_methods()
    
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"  Enhanced HTML Parser: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"  Individual Methods:   {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 or success2:
        print("\n🎉 Enhanced HTML parser is working!")
        print("\nNext steps:")
        print("1. Install optional dependencies for better results:")
        print("   pip install tabula-py camelot-py[cv]")
        print("2. Install pdftohtml for additional extraction method:")
        print("   # On Ubuntu/Debian: sudo apt-get install poppler-utils")
        print("   # On macOS: brew install poppler")
        print("3. Configure extraction methods in config.yaml")
    else:
        print("\n⚠️  Enhanced HTML parser needs attention")
        print("Check the error messages above for troubleshooting")


if __name__ == "__main__":
    main()