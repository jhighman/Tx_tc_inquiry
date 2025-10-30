"""
Web retrieval module for fetching PDF reports from URLs.
"""

import os
import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

import requests
from pdfplumber import PDF, open as pdf_open

from arrestx.config import Config
from arrestx.log import get_logger
from arrestx.model import ArrestXError, WebRetrievalError
from arrestx.parser import parse_pdf

logger = get_logger(__name__)


class WebRetrievalError(ArrestXError):
    """Exception raised for errors in web retrieval."""
    pass


def extract_report_date(pdf_path: str) -> Optional[str]:
    """
    Extract the report date from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Report date in YYYY-MM-DD format or None if not found
    """
    try:
        with pdf_open(pdf_path) as pdf:
            # Check first page for report date
            if len(pdf.pages) > 0:
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                
                # Look for "Report Date: MM/DD/YYYY" pattern
                date_match = re.search(r"Report Date:\s+(\d{1,2})/(\d{1,2})/(\d{4})", text)
                if date_match:
                    month, day, year = date_match.groups()
                    # Normalize to YYYY-MM-DD
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                
                # Alternative pattern: "MM/DD/YYYY" standalone
                alt_match = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", text)
                if alt_match:
                    month, day, year = alt_match.groups()
                    # Normalize to YYYY-MM-DD
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except Exception as e:
        logger.warning(f"Failed to extract report date: {e}")
    
    return None


def backup_file(file_path: str, report_date: str) -> Optional[str]:
    """
    Create a backup of a file with the report date in the filename.
    
    Args:
        file_path: Path to the file to backup
        report_date: Report date in YYYY-MM-DD format
        
    Returns:
        Path to the backup file or None if backup failed
    """
    if not os.path.exists(file_path):
        logger.warning(f"Cannot backup non-existent file: {file_path}")
        return None
    
    # Create archive directory if it doesn't exist
    file_dir = os.path.dirname(file_path)
    archive_dir = os.path.join(file_dir, "archive")
    os.makedirs(archive_dir, exist_ok=True)
    
    # Get file basename and extension
    basename = os.path.basename(file_path)
    name, ext = os.path.splitext(basename)
    
    # Create backup filename with report date
    backup_name = f"{name}_{report_date}{ext}"
    backup_path = os.path.join(archive_dir, backup_name)
    
    # Check if backup already exists
    if os.path.exists(backup_path):
        logger.info(f"Backup already exists: {backup_path}")
        return backup_path
    
    try:
        # Copy file to backup location
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return None


def fetch_pdf_with_retry(url: str, output_path: str, headers: Optional[Dict[str, str]] = None,
                        max_retries: int = 3, backoff_factor: float = 1.0) -> Dict[str, Union[str, bool]]:
    """
    Fetch a PDF from a URL with retry logic and exponential backoff.
    
    Args:
        url: URL to fetch
        output_path: Path to save the PDF
        headers: Optional request headers
        max_retries: Maximum number of retry attempts
        backoff_factor: Factor for exponential backoff
        
    Returns:
        Dictionary with status information
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return fetch_pdf(url, output_path, headers)
        except requests.exceptions.ConnectionError as e:
            last_exception = e
            if "Failed to resolve" in str(e) or "nodename nor servname provided" in str(e):
                logger.warning(f"DNS resolution failed for {url} (attempt {attempt + 1}/{max_retries + 1}): {e}")
            else:
                logger.warning(f"Connection error for {url} (attempt {attempt + 1}/{max_retries + 1}): {e}")
        except requests.exceptions.Timeout as e:
            last_exception = e
            logger.warning(f"Timeout error for {url} (attempt {attempt + 1}/{max_retries + 1}): {e}")
        except requests.exceptions.RequestException as e:
            last_exception = e
            logger.warning(f"Request error for {url} (attempt {attempt + 1}/{max_retries + 1}): {e}")
        except Exception as e:
            last_exception = e
            logger.warning(f"Unexpected error for {url} (attempt {attempt + 1}/{max_retries + 1}): {e}")
        
        # Don't sleep after the last attempt
        if attempt < max_retries:
            sleep_time = backoff_factor * (2 ** attempt)
            logger.info(f"Retrying in {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
    
    # All retries failed
    raise WebRetrievalError(f"Failed to fetch PDF after {max_retries + 1} attempts: {last_exception}")


def fetch_pdf(url: str, output_path: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Union[str, bool]]:
    """
    Fetch a PDF from a URL and save it to the specified path.
    
    Args:
        url: URL to fetch
        output_path: Path to save the PDF
        headers: Optional request headers
        
    Returns:
        Dictionary with status information
    """
    result = {
        "status": "error",
        "message": "",
        "modified": False,
        "etag": None,
        "last_modified": None
    }
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Set up headers
    request_headers = headers or {}
    
    # Add conditional headers if file exists
    if os.path.exists(output_path):
        # Get file modification time
        file_mtime = datetime.fromtimestamp(os.path.getmtime(output_path))
        file_mtime_str = file_mtime.strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        # Add If-Modified-Since header
        request_headers["If-Modified-Since"] = file_mtime_str
    
    try:
        # Fetch the PDF
        response = requests.get(url, headers=request_headers, stream=True)
        
        # Check if file was modified
        if response.status_code == 304:  # Not Modified
            result["status"] = "not_modified"
            result["message"] = "File not modified since last fetch"
            result["modified"] = False
            return result
        
        # Check for errors
        response.raise_for_status()
        
        # Save the PDF
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Update result
        result["status"] = "success"
        result["message"] = "File downloaded successfully"
        result["modified"] = True
        result["etag"] = response.headers.get("ETag")
        result["last_modified"] = response.headers.get("Last-Modified")
        
        return result
    
    except requests.exceptions.RequestException as e:
        raise WebRetrievalError(f"Failed to fetch PDF: {e}")


def process_daily_report(url: str, config: Config) -> Dict[str, Union[str, int]]:
    """
    Fetch and process the daily report from the given URL.
    
    Args:
        url: URL to fetch
        config: Configuration object
        
    Returns:
        Dictionary with processing results
    """
    result = {
        "status": "error",
        "message": "",
    }
    
    # PDF reports should always go to the reports directory
    output_dir = "reports"
    
    # Create reports directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract filename from URL
    url_path = Path(url)
    filename = url_path.name
    output_path = os.path.join(output_dir, filename)
    
    try:
        # Check if file exists before fetching
        file_exists = os.path.exists(output_path)
        
        # Try to fetch the PDF with retry logic
        fetch_result = None
        try:
            fetch_result = fetch_pdf_with_retry(url, output_path, max_retries=3, backoff_factor=2.0)
        except WebRetrievalError as e:
            logger.error(f"Failed to fetch PDF from {url}: {e}")
            
            # Check if we have a local file to work with
            if file_exists:
                logger.info(f"Network fetch failed, but local file exists: {output_path}")
                fetch_result = {
                    "status": "fallback_to_local",
                    "message": "Using existing local file due to network failure",
                    "modified": False
                }
            else:
                # Check for alternative local files (like in out/ directory)
                alternative_paths = [
                    os.path.join("out", filename),
                    os.path.join(".", filename),
                    os.path.join("reports", "archive", filename)
                ]
                
                local_file_found = False
                for alt_path in alternative_paths:
                    if os.path.exists(alt_path):
                        logger.info(f"Network fetch failed, copying from alternative location: {alt_path}")
                        try:
                            shutil.copy2(alt_path, output_path)
                            fetch_result = {
                                "status": "fallback_to_local",
                                "message": f"Copied from alternative location: {alt_path}",
                                "modified": True
                            }
                            local_file_found = True
                            break
                        except Exception as copy_error:
                            logger.warning(f"Failed to copy from {alt_path}: {copy_error}")
                
                if not local_file_found:
                    # No local file available, re-raise the original error
                    raise e
        
        # If file was not modified, return early
        if fetch_result["status"] == "not_modified":
            result["status"] = "not_modified"
            result["message"] = "Report not modified since last fetch"
            return result
        
        # Handle fallback to local file scenario
        if fetch_result["status"] == "fallback_to_local":
            result["status"] = "fallback_to_local"
            result["message"] = fetch_result["message"]
            logger.warning(f"Using local file due to network issues: {output_path}")
        
        # If file was modified and previously existed, create a backup
        if file_exists and fetch_result.get("modified", False):
            # Extract report date from the PDF
            report_date = extract_report_date(output_path)
            
            if report_date:
                # Create backup with report date
                backup_path = backup_file(output_path, report_date)
                
                if backup_path:
                    logger.info(f"Created backup of previous report: {backup_path}")
                else:
                    logger.warning("Failed to create backup of previous report")
            else:
                logger.warning("Could not extract report date for backup")
        
        # Process the PDF
        records = parse_pdf(output_path, config)
        
        # Write outputs
        from arrestx.writers import write_outputs
        write_outputs(records, config)
        
        # Update result - preserve fallback status if applicable
        if result.get("status") != "fallback_to_local":
            result["status"] = "success"
            result["message"] = f"Processed {len(records)} records from {filename}"
        else:
            # Keep fallback status but update message to include processing info
            result["message"] += f" - Processed {len(records)} records from {filename}"
        
        result["record_count"] = len(records)
        
        # Store in database if configured
        # Check if db attribute exists and is enabled
        if hasattr(config, 'db') and hasattr(config.db, 'enabled') and config.db.enabled:
            try:
                from arrestx.db.mongo import bulk_ingest
                
                db_result = bulk_ingest(
                    config.db.uri,
                    config.db.database,
                    config.db.tenant,
                    filename,
                    records
                )
                
                result["inserted_count"] = db_result.get("upserted", 0)
                result["updated_count"] = db_result.get("modified", 0)
            except Exception as e:
                logger.warning(f"Database storage failed: {e}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing daily report: {e}")
        raise WebRetrievalError(f"Failed to process daily report: {e}")