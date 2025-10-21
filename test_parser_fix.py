#!/usr/bin/env python3
"""
Test script to verify that the parser no longer gets stuck in infinite loops.
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

def test_parser_with_timeout(lines, timeout=5):
    """
    Test the parser with a timeout to catch infinite loops.
    
    Args:
        lines: List of lines to parse
        timeout: Maximum time in seconds to allow the parser to run
        
    Returns:
        True if the parser completed within the timeout, False otherwise
    """
    config = Config()
    
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
        logger.error(f"Parser timed out after {timeout} seconds")
        return False
    
    # Check if the parser completed successfully
    if result["success"]:
        elapsed_time = time.time() - start_time
        logger.info(f"Parser completed in {elapsed_time:.2f} seconds")
        logger.info(f"Extracted {len(result['records'])} records")
        return True
    else:
        logger.error(f"Parser failed with error: {result['error']}")
        return False

def test_problematic_cases():
    """
    Test the parser with known problematic cases that previously caused infinite loops.
    """
    # Test case 1: SEEK_NAME state without advancing
    case1 = [
        "SMITH, JOHN 12345678 01/01/2025",
        "123 MAIN ST",
        "FORT WORTH, TX 76102",
        "JONES, MARY",  # This line should trigger a new record
        "456 OAK ST",
        "DALLAS, TX 75201"
    ]
    
    # Test case 2: CAPTURE_CHARGES state with name match but no increment
    case2 = [
        "SMITH, JOHN 12345678 01/01/2025",
        "123 MAIN ST",
        "FORT WORTH, TX 76102",
        "25-0123456 THEFT",
        "JONES, MARY",  # This line should trigger a new record
        "456 OAK ST",
        "DALLAS, TX 75201"
    ]
    
    # Test case 3: Complex case with multiple state transitions
    case3 = [
        "SMITH, JOHN 12345678 01/01/2025",
        "123 MAIN ST",
        "FORT WORTH, TX 76102",
        "25-0123456 THEFT",
        "Additional charge description",
        "JONES, MARY 87654321 02/01/2025",
        "456 OAK ST",
        "DALLAS, TX 75201",
        "25-0123457 ASSAULT",
        "JOHNSON, MIKE",  # This line should trigger a new record
        "789 PINE ST",
        "AUSTIN, TX 78701"
    ]
    
    # Run the tests
    logger.info("Testing case 1: SEEK_NAME state without advancing")
    if not test_parser_with_timeout(case1):
        logger.error("Test case 1 failed")
        return False
    
    logger.info("Testing case 2: CAPTURE_CHARGES state with name match but no increment")
    if not test_parser_with_timeout(case2):
        logger.error("Test case 2 failed")
        return False
    
    logger.info("Testing case 3: Complex case with multiple state transitions")
    if not test_parser_with_timeout(case3):
        logger.error("Test case 3 failed")
        return False
    
    logger.info("All test cases passed!")
    return True

if __name__ == "__main__":
    success = test_problematic_cases()
    sys.exit(0 if success else 1)