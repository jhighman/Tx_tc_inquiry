#!/usr/bin/env python3
"""
Test script to verify the network connectivity fix.
"""

import os
import sys
import shutil
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from arrestx.config import load_config
from arrestx.api import search_name
from arrestx.web import process_daily_report

def test_with_existing_file():
    """Test that the system works with an existing local file when network fails."""
    print("Testing with existing local file...")
    
    # Ensure we have a local file to work with
    out_pdf = Path("out/01.PDF")
    reports_pdf = Path("reports/01.PDF")
    
    if out_pdf.exists() and not reports_pdf.exists():
        # Copy from out to reports directory
        os.makedirs("reports", exist_ok=True)
        shutil.copy2(str(out_pdf), str(reports_pdf))
        print(f"Copied {out_pdf} to {reports_pdf}")
    
    # Load configuration
    config = load_config("config.yaml")
    
    try:
        # Try to search for a name - this should trigger the network fetch
        # but fall back to local file when network fails
        result = search_name("Smith", config, force_update=True)
        
        print(f"Search completed successfully!")
        print(f"Found {len(result.alerts)} alerts")
        print(f"Checked {result.records_checked} records")
        print(f"Last update: {result.last_update}")
        
        return True
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        return False

def test_process_daily_report():
    """Test the process_daily_report function directly."""
    print("\nTesting process_daily_report function...")
    
    config = load_config("config.yaml")
    url = "https://cjreports.tarrantcounty.com/Reports/JailedInmates/FinalPDF/01.PDF"
    
    try:
        result = process_daily_report(url, config)
        
        print(f"Process result: {result}")
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
        
        if result.get('status') in ['success', 'fallback_to_local', 'not_modified']:
            print("✅ Process completed successfully (with or without network)")
            return True
        else:
            print("❌ Process failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing network connectivity fix...")
    print("=" * 50)
    
    # Test 1: Search with existing file
    test1_passed = test_with_existing_file()
    
    # Test 2: Direct process_daily_report test
    test2_passed = test_process_daily_report()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Test 1 (Search with fallback): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Process daily report): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! The network connectivity fix is working.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())