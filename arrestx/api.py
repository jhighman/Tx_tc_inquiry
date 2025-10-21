"""
API module for Texas Extract.

This module provides an API for searching names in arrest records.
"""

import os
import re
import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from arrestx.config import Config
from arrestx.parser import parse_pdf
from arrestx.model import Record
from arrestx.web import process_daily_report

logger = logging.getLogger(__name__)

class Alert:
    """Alert for a name match in arrest records."""
    
    def __init__(self, name: str, booking_no: str, description: str, 
                 identifier: str, book_in_date: str, source_file: str):
        self.name = name
        self.booking_no = booking_no
        self.description = description
        self.identifier = identifier
        self.book_in_date = book_in_date
        self.source = "Tarrant County"
        self.source_file = source_file
        
    def to_dict(self) -> Dict[str, str]:
        """Convert alert to dictionary."""
        return {
            "name": self.name,
            "booking_no": self.booking_no,
            "description": self.description,
            "identifier": self.identifier,
            "book_in_date": self.book_in_date,
            "source": self.source,
            "source_file": self.source_file
        }

class SearchResult:
    """Result of a name search in arrest records."""
    
    def __init__(self, name: str, alerts: List[Alert], records_checked: int, 
                 last_update: Optional[datetime.date] = None):
        self.name = name
        self.alerts = alerts
        self.records_checked = records_checked
        self.last_update = last_update
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert search result to dictionary."""
        return {
            "name": self.name,
            "alerts": [alert.to_dict() for alert in self.alerts],
            "records_checked": self.records_checked,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "due_diligence_message": self.get_due_diligence_message()
        }
        
    def get_due_diligence_message(self) -> str:
        """Get due diligence message."""
        if self.alerts:
            return f"ALERT: Found {len(self.alerts)} matches for {self.name} in Tarrant County records."
        else:
            return (f"No matches found for {self.name} in Tarrant County records. "
                   f"Checked {self.records_checked} records as of {self.last_update}.")

def normalize_name(name: str) -> str:
    """
    Normalize a name for comparison.
    
    Args:
        name: Name to normalize
        
    Returns:
        Normalized name
    """
    # Handle "Last, First Middle" format
    if "," in name:
        parts = name.split(",", 1)
        last = parts[0].strip()
        first_middle = parts[1].strip()
        name = f"{first_middle} {last}"
    
    # Remove extra whitespace and convert to lowercase
    name = re.sub(r'\s+', ' ', name).strip().lower()
    return name

def name_matches(record_name: str, search_name: str) -> bool:
    """
    Check if a record name matches a search name.
    
    Args:
        record_name: Name from record
        search_name: Name to search for
        
    Returns:
        True if names match, False otherwise
    """
    record_name_norm = normalize_name(record_name)
    search_name_norm = normalize_name(search_name)
    
    # Check for exact match
    if record_name_norm == search_name_norm:
        return True
    
    # Check if search name is a subset of record name
    search_parts = search_name_norm.split()
    record_parts = record_name_norm.split()
    
    # If search has both first and last name, check if they're in the record
    if len(search_parts) >= 2:
        first_name = search_parts[0]
        last_name = search_parts[-1]
        
        if first_name in record_parts and last_name in record_parts:
            return True
    
    # Check if the search name is just a single name (first or last)
    # that matches any part of the record name
    if len(search_parts) == 1:
        search_term = search_parts[0]
        if search_term in record_parts:
            return True
    
    return False

def get_latest_report_date() -> Optional[datetime.date]:
    """
    Get the date of the latest report in the archive.
    
    Returns:
        Date of the latest report, or None if no reports found
    """
    archive_dir = Path("reports/archive")
    if not archive_dir.exists():
        return None
    
    latest_date = None
    date_pattern = re.compile(r'.*_(\d{4}-\d{2}-\d{2})\.PDF$', re.IGNORECASE)
    
    for file in archive_dir.glob("*.PDF"):
        match = date_pattern.match(str(file.name))
        if match:
            date_str = match.group(1)
            try:
                file_date = datetime.date.fromisoformat(date_str)
                if latest_date is None or file_date > latest_date:
                    latest_date = file_date
            except ValueError:
                continue
    
    return latest_date

def is_report_current() -> bool:
    """
    Check if the latest report is from today.
    
    Returns:
        True if the latest report is from today, False otherwise
    """
    latest_date = get_latest_report_date()
    if latest_date is None:
        return False
    
    today = datetime.date.today()
    return latest_date == today

def ensure_current_report(cfg: Config) -> bool:
    """
    Ensure that the latest report is from today.
    
    Args:
        cfg: Configuration
        
    Returns:
        True if the report is current, False otherwise
    """
    if is_report_current():
        logger.info("Report is already current")
        return True
    
    # Get the URL from config or use default
    url = getattr(cfg.web_retrieval, "url", 
                 "https://cjreports.tarrantcounty.com/Reports/JailedInmates/FinalPDF/01.PDF")
    
    # Process the daily report
    result = process_daily_report(url, cfg)
    
    # Check if the report was processed successfully
    if result.get("status") == "success":
        logger.info("Successfully updated report")
        return True
    else:
        logger.error(f"Failed to update report: {result.get('error')}")
        return False

def search_name(name: str, cfg: Config, force_update: bool = False) -> SearchResult:
    """
    Search for a name in arrest records.
    
    Args:
        name: Name to search for
        cfg: Configuration
        force_update: Force update of the report
        
    Returns:
        Search result
    """
    # Ensure the report is current
    if force_update or not is_report_current():
        ensure_current_report(cfg)
    
    # Get the latest report date
    latest_date = get_latest_report_date()
    
    # Get the path to the latest report
    report_path = Path("reports/01.PDF")
    if not report_path.exists():
        logger.error(f"Report not found: {report_path}")
        return SearchResult(name, [], 0, latest_date)
    
    # Parse the report
    records = parse_pdf(str(report_path), cfg)
    
    # Search for the name in the records
    alerts = []
    for record in records:
        if name_matches(record["name"], name):
            # Create an alert for each charge
            for charge in record["charges"]:
                alert = Alert(
                    name=record["name"],
                    booking_no=charge["booking_no"],
                    description=charge["description"],
                    identifier=record.get("identifier", ""),
                    book_in_date=record.get("book_in_date", ""),
                    source_file=record["source_file"]
                )
                alerts.append(alert)
    
    # Create the search result
    result = SearchResult(name, alerts, len(records), latest_date)
    
    return result