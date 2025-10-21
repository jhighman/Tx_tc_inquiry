#!/usr/bin/env python3
"""
Demonstration of the name search API, CLI, and UI.

This script shows how to use the name search functionality in different ways:
1. Using the API directly
2. Using the CLI
3. Using the UI
"""

import json
import subprocess
import sys
from pathlib import Path

from arrestx.config import load_config
from arrestx.api import search_name

def api_demo(name: str) -> None:
    """
    Demonstrate using the API directly.
    
    Args:
        name: Name to search for
    """
    print("\n=== API Demo ===")
    
    # Load configuration
    config = load_config("config.yaml")
    
    # Search for the name
    result = search_name(name, config)
    
    # Print the result
    if result.alerts:
        print(f"\n⚠️  {result.get_due_diligence_message()}")
        print("\nMatches found:")
        for i, alert in enumerate(result.alerts, 1):
            print(f"\n--- Match {i} ---")
            print(f"Name: {alert.name}")
            print(f"Booking #: {alert.booking_no}")
            print(f"Charge: {alert.description}")
            print(f"Identifier: {alert.identifier}")
            print(f"Book-in Date: {alert.book_in_date}")
            print(f"Source: {alert.source}")
    else:
        print(f"\n✓ {result.get_due_diligence_message()}")
    
    # Print raw JSON
    print("\nRaw JSON:")
    print(json.dumps(result.to_dict(), indent=2))

def cli_demo(name: str) -> None:
    """
    Demonstrate using the CLI.
    
    Args:
        name: Name to search for
    """
    print("\n=== CLI Demo ===")
    
    # Run the CLI command
    cmd = [sys.executable, "-m", "arrestx.cli", "search", name]
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("\nOutput:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error output: {e.stderr}")

def ui_demo() -> None:
    """
    Demonstrate using the UI.
    """
    print("\n=== UI Demo ===")
    print("To start the UI, run the following command:")
    print(f"{sys.executable} -m arrestx.ui")
    print("\nThen open a web browser and navigate to http://localhost:7860")
    print("Enter a name in the search box and click 'Search'")
    
    # Ask if the user wants to start the UI
    response = input("\nDo you want to start the UI now? (y/n): ")
    if response.lower() in ["y", "yes"]:
        cmd = [sys.executable, "-m", "arrestx.ui"]
        print(f"Running command: {' '.join(cmd)}")
        
        try:
            # Run the UI in a subprocess
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            print(f"Error output: {e.stderr}")
        except KeyboardInterrupt:
            print("\nUI stopped by user")

def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    # Check if a name was provided
    if len(sys.argv) > 1:
        name = sys.argv[1]
    else:
        name = input("Enter a name to search for: ")
    
    # Run the demos
    api_demo(name)
    cli_demo(name)
    ui_demo()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())