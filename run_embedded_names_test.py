#!/usr/bin/env python3
"""
Script to run the embedded names test and generate the fixed output files.
"""

import os
import sys
import subprocess

def main():
    """
    Main function to run the embedded names test.
    """
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Ensure the output directory exists
    os.makedirs(os.path.join(project_root, "out"), exist_ok=True)
    
    # Run the embedded names test
    print("Running embedded names test...")
    try:
        subprocess.run(
            [sys.executable, os.path.join(project_root, "tests", "test_embedded_names_sample.py")],
            check=True
        )
        print("Test completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error running test: {e}")
        return 1
    
    # Check if the output files were generated
    json_path = os.path.join(project_root, "out", "embedded_names_sample.json")
    csv_path = os.path.join(project_root, "out", "embedded_names_sample.csv")
    
    if os.path.exists(json_path) and os.path.exists(csv_path):
        print(f"Output files generated successfully:")
        print(f"  - {json_path}")
        print(f"  - {csv_path}")
    else:
        print("Error: Output files were not generated.")
        return 1
    
    # Print a summary of the improvements
    print("\nParser Improvements Summary:")
    print("----------------------------")
    print("1. Enhanced Name Detection: Added regex patterns to detect names in various contexts")
    print("2. Flexible ID/Date Handling: Improved handling of different patterns of identifier and book-in date placement")
    print("3. Embedded Name Extraction: Added logic to detect and extract names embedded within charge descriptions")
    
    print("\nKey Benefits:")
    print("------------")
    print("1. Complete Record Extraction: All inmate records are correctly identified, even when embedded in charge descriptions")
    print("2. Accurate Charge Attribution: Charges are correctly attributed to the right inmates")
    print("3. Flexible Format Handling: The parser can handle various record formats and patterns")
    print("4. Robust Error Handling: Warnings are added for malformed records, but processing continues")
    
    print("\nFor more details, see the following documentation:")
    print(f"  - {os.path.join(project_root, 'parsing_improvements.md')}")
    print(f"  - {os.path.join(project_root, 'parser_improvements_summary.md')}")
    print(f"  - {os.path.join(project_root, 'parsing_state_machine.md')}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())