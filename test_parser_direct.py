#!/usr/bin/env python3
"""
Direct test of the enhanced HTML parser without CLI dependencies.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from arrestx.config import Config
from arrestx.parser import parse_pdf
import json

def test_parser_direct():
    """Test the parser directly."""
    
    pdf_path = "out/01.PDF"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return False
    
    print("🔍 Testing Enhanced HTML Parser (Direct)")
    print("=" * 50)
    
    # Create configuration with enhanced HTML parser enabled
    cfg = Config()
    cfg.parsing.use_html_parser = True
    cfg.parsing.use_enhanced_html_parser = True
    
    print(f"📄 Processing PDF: {pdf_path}")
    print(f"🔧 Enhanced HTML parser: {cfg.parsing.use_enhanced_html_parser}")
    print()
    
    try:
        # Parse the PDF using enhanced HTML parser
        records = parse_pdf(pdf_path, cfg)
        
        print(f"✅ Successfully extracted {len(records)} records")
        print()
        
        if records:
            # Save results to JSON
            output_path = "out/enhanced_parser_results.json"
            with open(output_path, 'w') as f:
                json.dump(records, f, indent=2, default=str)
            
            print(f"💾 Results saved to: {output_path}")
            print()
            
            # Show first few records
            print("📊 Sample Records:")
            print("-" * 30)
            
            for i, record in enumerate(records[:3]):
                print(f"Record {i+1}:")
                print(f"  Name: {record.get('name', 'N/A')}")
                print(f"  Normalized: {record.get('name_normalized', 'N/A')}")
                print(f"  Identifier: {record.get('identifier', 'N/A')}")
                print(f"  Date: {record.get('book_in_date', 'N/A')}")
                print(f"  Street: {record.get('street', [])}")
                print(f"  Charges: {len(record.get('charges', []))}")
                if record.get('charges'):
                    for j, charge in enumerate(record['charges'][:2]):
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
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_parser_direct()
    if success:
        print("\n🎉 Enhanced HTML parser is working!")
    else:
        print("\n⚠️  Enhanced HTML parser needs attention")