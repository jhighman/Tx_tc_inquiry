"""
Script to clean output files and rerun the extraction process.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def main():
    """
    Clean output files and rerun the extraction process.
    """
    # Create output directory if it doesn't exist
    out_dir = Path("out")
    if not out_dir.exists():
        out_dir.mkdir(parents=True)
    
    # Clean output files
    print("Cleaning output files...")
    for file in out_dir.glob("*"):
        if file.is_file():
            print(f"  Removing {file}")
            file.unlink()
    
    # Check if reports directory exists
    reports_dir = Path("reports")
    if not reports_dir.exists():
        print("Error: reports directory not found")
        return 1
    
    # Check if there are PDF files in the reports directory
    pdf_files = list(reports_dir.glob("*.pdf")) + list(reports_dir.glob("*.PDF"))
    if not pdf_files:
        print("Error: No PDF files found in reports directory")
        return 1
    
    # Run the extraction process
    print("\nRunning extraction process...")
    for pdf_file in pdf_files:
        print(f"  Processing {pdf_file}")
        cmd = [
            "python", "-m", "arrestx", "main",
            "-i", str(pdf_file),
            "-j", str(out_dir / "arrests.json"),
            "-c", str(out_dir / "arrests.csv"),
            "-v"
        ]
        try:
            subprocess.run(cmd, check=True)
            print(f"  Successfully processed {pdf_file}")
        except subprocess.CalledProcessError as e:
            print(f"  Error processing {pdf_file}: {e}")
            # Try with OCR fallback
            print(f"  Retrying with OCR fallback...")
            cmd.append("-o")
            try:
                subprocess.run(cmd, check=True)
                print(f"  Successfully processed {pdf_file} with OCR fallback")
            except subprocess.CalledProcessError as e:
                print(f"  Error processing {pdf_file} with OCR fallback: {e}")
                return 1
    
    # Check if output files were created
    json_file = out_dir / "arrests.json"
    csv_file = out_dir / "arrests.csv"
    
    if json_file.exists() and csv_file.exists():
        print("\nExtraction completed successfully!")
        print(f"  JSON output: {json_file}")
        print(f"  CSV output: {csv_file}")
        
        # Count records in JSON file
        import json
        with open(json_file, "r") as f:
            records = json.load(f)
            print(f"\nExtracted {len(records)} records")
            
            # Check if WYATT, JOSH is a separate record
            wyatt_record = None
            for record in records:
                if "WYATT, JOSH" in record["name"]:
                    wyatt_record = record
                    break
            
            if wyatt_record:
                print("\nWYATT, JOSH found as a separate record:")
                print(json.dumps(wyatt_record, indent=2))
            else:
                print("\nWYATT, JOSH not found as a separate record")
                
                # Check if it's in any description
                for record in records:
                    for charge in record["charges"]:
                        if "WYATT, JOSH" in charge["description"]:
                            print(f"Found in description of {record['name']}:")
                            print(json.dumps(charge, indent=2))
        
        return 0
    else:
        print("\nError: Output files not created")
        return 1

if __name__ == "__main__":
    sys.exit(main())