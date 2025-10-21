#!/usr/bin/env python3
"""
Comprehensive test script for Texas Extract.

This script tests:
1. Parser fixes for infinite loops
2. API functionality for name searching
3. CLI interface
"""

import os
import sys
import json
import time
import logging
import datetime
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

from arrestx.config import Config, load_config
from arrestx.parser import parse_lines
from arrestx.api import search_name, normalize_name, name_matches, Alert, SearchResult

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_parser_with_timeout(lines: List[str], timeout: int = 5, description: str = "") -> bool:
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
    
    logger.info(f"Testing parser: {description}")
    
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

def test_parser_fixes():
    """
    Test the parser fixes for infinite loops.
    """
    logger.info("=== Testing Parser Fixes ===")
    
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
    tests = [
        (case1, "SEEK_NAME state without advancing"),
        (case2, "CAPTURE_CHARGES state with name match but no increment"),
        (case3, "Complex case with multiple state transitions")
    ]
    
    all_passed = True
    for lines, description in tests:
        if not test_parser_with_timeout(lines, timeout=5, description=description):
            all_passed = False
    
    return all_passed

def test_api_functionality():
    """
    Test the API functionality for name searching.
    """
    logger.info("\n=== Testing API Functionality ===")
    
    # Create a mock config
    config = Config()
    
    # Create a mock record
    record = {
        "name": "SMITH, JOHN",
        "name_normalized": "John Smith",
        "street": ["123 MAIN ST", "FORT WORTH, TX 76102"],
        "identifier": "12345678",
        "book_in_date": "2025-01-01",
        "charges": [
            {"booking_no": "25-0123456", "description": "THEFT"},
            {"booking_no": "25-0123457", "description": "ASSAULT"}
        ],
        "source_file": "test_file.txt",
        "source_page_span": [1, 1],
        "parse_warnings": []
    }
    
    # Test name normalization
    logger.info("Testing name normalization")
    test_cases = [
        ("SMITH, JOHN", "john smith"),
        ("John Smith", "john smith"),
        ("SMITH, JOHN ROBERT", "john robert smith"),
        ("John Robert Smith", "john robert smith")
    ]
    
    for input_name, expected_output in test_cases:
        output = normalize_name(input_name)
        if output == expected_output:
            logger.info(f"✅ PASSED: normalize_name({input_name}) = {output}")
        else:
            logger.error(f"❌ FAILED: normalize_name({input_name}) = {output}, expected {expected_output}")
            return False
    
    # Test name matching
    logger.info("\nTesting name matching")
    test_cases = [
        ("SMITH, JOHN", "John Smith", True),
        ("SMITH, JOHN", "John Doe", False),
        ("SMITH, JOHN", "Smith", True),
        ("SMITH, JOHN", "John", True),
        ("SMITH, JOHN ROBERT", "John Smith", True),
        ("SMITH, JOHN ROBERT", "Robert Smith", True)
    ]
    
    for record_name, search_name, expected_output in test_cases:
        output = name_matches(record_name, search_name)
        if output == expected_output:
            logger.info(f"✅ PASSED: name_matches({record_name}, {search_name}) = {output}")
        else:
            logger.error(f"❌ FAILED: name_matches({record_name}, {search_name}) = {output}, expected {expected_output}")
            return False
    
    # Test Alert class
    logger.info("\nTesting Alert class")
    alert = Alert(
        name="SMITH, JOHN",
        booking_no="25-0123456",
        description="THEFT",
        identifier="12345678",
        book_in_date="2025-01-01",
        source_file="test_file.txt"
    )
    
    alert_dict = alert.to_dict()
    expected_keys = ["name", "booking_no", "description", "identifier", "book_in_date", "source", "source_file"]
    
    if all(key in alert_dict for key in expected_keys):
        logger.info(f"✅ PASSED: Alert.to_dict() contains all expected keys")
    else:
        logger.error(f"❌ FAILED: Alert.to_dict() missing keys: {[key for key in expected_keys if key not in alert_dict]}")
        return False
    
    # Test SearchResult class
    logger.info("\nTesting SearchResult class")
    search_result = SearchResult(
        name="John Smith",
        alerts=[alert],
        records_checked=1,
        last_update=datetime.date.today()
    )
    
    search_result_dict = search_result.to_dict()
    expected_keys = ["name", "alerts", "records_checked", "last_update", "due_diligence_message"]
    
    if all(key in search_result_dict for key in expected_keys):
        logger.info(f"✅ PASSED: SearchResult.to_dict() contains all expected keys")
    else:
        logger.error(f"❌ FAILED: SearchResult.to_dict() missing keys: {[key for key in expected_keys if key not in search_result_dict]}")
        return False
    
    # Test due diligence message
    logger.info("\nTesting due diligence message")
    
    # With alerts
    message = search_result.get_due_diligence_message()
    if "ALERT" in message and "matches" in message:
        logger.info(f"✅ PASSED: Due diligence message with alerts: {message}")
    else:
        logger.error(f"❌ FAILED: Due diligence message with alerts: {message}")
        return False
    
    # Without alerts
    search_result.alerts = []
    message = search_result.get_due_diligence_message()
    if "No matches found" in message and "Checked" in message:
        logger.info(f"✅ PASSED: Due diligence message without alerts: {message}")
    else:
        logger.error(f"❌ FAILED: Due diligence message without alerts: {message}")
        return False
    
    return True

def test_cli_interface():
    """
    Test the CLI interface.
    """
    logger.info("\n=== Testing CLI Interface ===")
    
    # Test the help command
    logger.info("Testing help command")
    cmd = [sys.executable, "-m", "arrestx.cli", "--help"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if "search" in result.stdout:
            logger.info(f"✅ PASSED: CLI help command includes 'search'")
        else:
            logger.error(f"❌ FAILED: CLI help command does not include 'search'")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ FAILED: CLI help command failed: {e}")
        return False
    
    # Test the search command help
    logger.info("\nTesting search command help")
    cmd = [sys.executable, "-m", "arrestx.cli", "search", "--help"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if "name" in result.stdout and "--force-update" in result.stdout:
            logger.info(f"✅ PASSED: CLI search help command includes expected options")
        else:
            logger.error(f"❌ FAILED: CLI search help command does not include expected options")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ FAILED: CLI search help command failed: {e}")
        return False
    
    logger.info("\nNote: Full CLI testing would require actual data files and is skipped")
    
    return True

def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    # Run the tests
    parser_passed = test_parser_fixes()
    api_passed = test_api_functionality()
    cli_passed = test_cli_interface()
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Parser fixes: {'✅ PASSED' if parser_passed else '❌ FAILED'}")
    logger.info(f"API functionality: {'✅ PASSED' if api_passed else '❌ FAILED'}")
    logger.info(f"CLI interface: {'✅ PASSED' if cli_passed else '❌ FAILED'}")
    
    # Return exit code
    if parser_passed and api_passed and cli_passed:
        logger.info("\n✅ All tests passed!")
        return 0
    else:
        logger.error("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())