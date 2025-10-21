#!/usr/bin/env python3
"""
Example test cases for the parser, including both positive and negative tests.

This file demonstrates how to test the parser for infinite loops and other issues.
"""

import sys
import time
import logging
from pathlib import Path

from arrestx.config import Config
from arrestx.parser import parse_lines

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_parser_with_timeout(lines, timeout=5, description=""):
    """
    Test the parser with a timeout to catch infinite loops.
    
    Args:
        lines: List of lines to parse
        timeout: Maximum time in seconds to allow the parser to run
        description: Description of the test case
        
    Returns:
        True if the parser completed within the timeout, False otherwise
    """
    config = Config()
    
    logger.info(f"Testing: {description}")
    
    # Start a timer
    start_time = time.time()
    
    # Run the parser in a separate thread
    import threading
    result = {"success": False, "records": None, "error": None}
    
    def parse_thread():
        try:
            records = parse_lines(lines, "test_file.txt", config)
            result["success"] = True
            result["records"] = records
        except Exception as e:
            result["error"] = e
    
    thread = threading.Thread(target=parse_thread)
    thread.daemon = True
    thread.start()
    
    # Wait for the thread to complete or timeout
    thread.join(timeout)
    
    # Check if the thread is still alive (indicating a timeout)
    if thread.is_alive():
        logger.error(f"❌ FAILED: Parser timed out after {timeout} seconds")
        return False
    
    # Check if the parser completed successfully
    if result["success"]:
        elapsed_time = time.time() - start_time
        logger.info(f"✅ PASSED: Parser completed in {elapsed_time:.2f} seconds")
        logger.info(f"Extracted {len(result['records'])} records")
        return True
    else:
        logger.error(f"❌ FAILED: Parser failed with error: {result['error']}")
        return False

def run_positive_tests():
    """
    Run positive test cases that should pass with the fixed parser.
    """
    logger.info("=== POSITIVE TEST CASES ===")
    
    # Test case 1: Basic record with name, ID, date, address, and charges
    case1 = [
        "SMITH, JOHN 12345678 01/01/2025",
        "123 MAIN ST",
        "FORT WORTH, TX 76102",
        "25-0123456 THEFT"
    ]
    
    # Test case 2: Multiple records with state transitions
    case2 = [
        "SMITH, JOHN 12345678 01/01/2025",
        "123 MAIN ST",
        "FORT WORTH, TX 76102",
        "25-0123456 THEFT",
        "JONES, MARY 87654321 02/01/2025",  # New record
        "456 OAK ST",
        "DALLAS, TX 75201",
        "25-0123457 ASSAULT"
    ]
    
    # Test case 3: Record with name on one line, ID/date on next line
    case3 = [
        "SMITH, JOHN",
        "12345678 01/01/2025",
        "123 MAIN ST",
        "FORT WORTH, TX 76102",
        "25-0123456 THEFT"
    ]
    
    # Test case 4: Record with embedded name in charge description
    case4 = [
        "SMITH, JOHN 12345678 01/01/2025",
        "123 MAIN ST",
        "FORT WORTH, TX 76102",
        "25-0123456 THEFT involving JONES, MARY 87654321 02/01/2025",
        "456 OAK ST",
        "DALLAS, TX 75201"
    ]
    
    # Run the tests
    tests = [
        (case1, "Basic record with name, ID, date, address, and charges"),
        (case2, "Multiple records with state transitions"),
        (case3, "Record with name on one line, ID/date on next line"),
        (case4, "Record with embedded name in charge description")
    ]
    
    all_passed = True
    for lines, description in tests:
        if not test_parser_with_timeout(lines, timeout=5, description=description):
            all_passed = False
    
    return all_passed

def run_negative_tests():
    """
    Run negative test cases that would cause infinite loops in the unfixed parser.
    These should now pass with the fixed parser due to the stall detection watchdog.
    """
    logger.info("\n=== NEGATIVE TEST CASES (Should now pass with fixes) ===")
    
    # Test case 1: SEEK_NAME state without advancing (unfixed parser would loop)
    # This case would cause an infinite loop in the unfixed parser because it
    # would change state to CAPTURE_ADDRESS but not increment i
    case1 = [
        "SMITH, JOHN",  # Name line that would trigger state change without i increment
        "123 MAIN ST",
        "FORT WORTH, TX 76102"
    ]
    
    # Test case 2: CAPTURE_CHARGES state with name match but no increment (unfixed parser would loop)
    # This case would cause an infinite loop in the unfixed parser because it
    # would find a name in CAPTURE_CHARGES state but not increment i
    case2 = [
        "SMITH, JOHN 12345678 01/01/2025",
        "123 MAIN ST",
        "FORT WORTH, TX 76102",
        "25-0123456 THEFT",
        "JONES, MARY"  # Name line that would trigger state change without i increment
    ]
    
    # Test case 3: Malformed input that could cause parsing issues
    case3 = [
        "SMITH, JOHN 12345678 01/01/2025",
        "123 MAIN ST",
        "FORT WORTH, TX 76102",
        "25-0123456",  # Booking number without description
        "",  # Empty line
        "Additional charge info without booking number"  # Line that doesn't match any pattern
    ]
    
    # Test case 4: Simulate a case where the stall watchdog would kick in
    # This is a contrived example to demonstrate the watchdog
    # In a real scenario, you would need to modify the parser code to create a loop
    case4 = [
        "SMITH, JOHN 12345678 01/01/2025",
        "123 MAIN ST",
        "FORT WORTH, TX 76102",
        "25-0123456 THEFT",
        "This line has unusual formatting that might confuse the parser"
    ]
    
    # Run the tests
    tests = [
        (case1, "SEEK_NAME state without advancing (would loop in unfixed parser)"),
        (case2, "CAPTURE_CHARGES state with name match but no increment (would loop in unfixed parser)"),
        (case3, "Malformed input that could cause parsing issues"),
        (case4, "Case that might trigger the stall watchdog")
    ]
    
    all_passed = True
    for lines, description in tests:
        if not test_parser_with_timeout(lines, timeout=5, description=description):
            all_passed = False
    
    return all_passed

def demonstrate_stall_watchdog():
    """
    Demonstrate how to test if the stall watchdog is working.
    
    Note: This requires temporarily modifying the parser code to create an infinite loop.
    """
    logger.info("\n=== STALL WATCHDOG DEMONSTRATION ===")
    logger.info("To test if the stall watchdog is working:")
    logger.info("1. Temporarily modify the parser.py file to create an infinite loop")
    logger.info("   For example, comment out an 'i += 1' line in the SEEK_NAME state")
    logger.info("2. Run this test script and observe the watchdog in action")
    logger.info("3. You should see a warning message like:")
    logger.info("   'Parser made no progress near line X: 'line content' – forcing advance'")
    logger.info("4. The test should still pass because the watchdog forces advancement")
    logger.info("5. Remember to revert your changes to parser.py after testing!")

if __name__ == "__main__":
    positive_passed = run_positive_tests()
    negative_passed = run_negative_tests()
    demonstrate_stall_watchdog()
    
    if positive_passed and negative_passed:
        logger.info("\n✅ All tests passed!")
        sys.exit(0)
    else:
        logger.error("\n❌ Some tests failed!")
        sys.exit(1)