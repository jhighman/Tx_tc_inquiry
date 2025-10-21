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
                 last_update: Optional[datetime.date] = None,
                 person_bio: Optional[str] = None,
                 organization: Optional[str] = None):
        self.name = name
        self.alerts = alerts
        self.records_checked = records_checked
        self.last_update = last_update
        self.person_bio = person_bio
        self.organization = organization
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert search result to dictionary."""
        result = {
            "name": self.name,
            "alerts": [alert.to_dict() for alert in self.alerts],
            "records_checked": self.records_checked,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "due_diligence_message": self.get_due_diligence_message()
        }
        
        # Add optional correlation identifiers if provided
        if self.person_bio is not None:
            result["person_bio"] = self.person_bio
        if self.organization is not None:
            result["organization"] = self.organization
            
        return result
        
    def get_due_diligence_message(self) -> str:
        """Get due diligence message."""
        if self.alerts:
            return f"ALERT: Found {len(self.alerts)} matches for {self.name} in Tarrant County records."
        else:
            return (f"No matches found for {self.name} in Tarrant County records. "
                   f"Checked {self.records_checked} records as of {self.last_update}.")
    
    def to_enterprise_format(self) -> Dict[str, Any]:
        """Convert search result to enterprise event format."""
        import uuid
        from datetime import datetime
        
        # Generate unique IDs
        event_id = f"EVT-{uuid.uuid4().hex[:15].upper()}"
        audit_id = str(uuid.uuid4())
        
        # Base event structure
        events = []
        
        for alert in self.alerts:
            # Parse name components
            name_parts = alert.name.split(", ")
            if len(name_parts) >= 2:
                last_name = name_parts[0].strip()
                first_middle = name_parts[1].strip().split()
                first_name = first_middle[0] if first_middle else ""
                middle_name = " ".join(first_middle[1:]) if len(first_middle) > 1 else ""
            else:
                # Handle "First Last" format
                name_parts = alert.name.split()
                first_name = name_parts[0] if name_parts else ""
                last_name = name_parts[-1] if len(name_parts) > 1 else ""
                middle_name = " ".join(name_parts[1:-1]) if len(name_parts) > 2 else ""
            
            # Create enterprise event
            event = {
                "_id": f"EVT-{uuid.uuid4().hex[:15].upper()}",
                "providerInfo": {
                    "audit": {"$ref": "etsAuditTrail", "$id": audit_id},
                    "dataProviderId": "201",  # Texas Extract provider ID
                    "serviceName": "arrestSearch",
                    "searchType": "CRIMINAL"
                },
                "personBio": {"$ref": "person_bio", "$id": self.person_bio} if self.person_bio else None,
                "organization": self.organization,
                "aliasMatch": {
                    "fromIdentityValue": self.name,
                    "entity": "com.etx.dto.AliasDTO",
                    "fromEventId": f"ALS-{uuid.uuid4().hex[:15].upper()}",
                    "fromIdentityId": f"ALS-{uuid.uuid4().hex[:15].upper()}",
                    "dtoMatch": True,
                    "matchingMethods": {
                        "firstName": "stringExactMatch",
                        "lastName": "stringExactMatch"
                    },
                    "fields": [
                        {
                            "field": "firstName",
                            "fromEventValue": first_name.upper(),
                            "fromIdentityValue": first_name,
                            "confidence": "1",
                            "methods": ["stringExactMatch"],
                            "salience": 2,
                            "match": True,
                            "firstMethod": "stringExactMatch"
                        },
                        {
                            "field": "lastName",
                            "fromEventValue": last_name.upper(),
                            "fromIdentityValue": last_name,
                            "confidence": "1",
                            "methods": ["stringExactMatch"],
                            "salience": 1,
                            "match": True,
                            "firstMethod": "stringExactMatch"
                        }
                    ] + ([{
                        "field": "middleName",
                        "fromEventValue": middle_name.upper(),
                        "fromIdentityValue": middle_name,
                        "confidence": "1",
                        "methods": ["stringExactMatch"],
                        "salience": 3,
                        "match": True,
                        "firstMethod": "stringExactMatch"
                    }] if middle_name else []),
                    "sources": []
                },
                "unmapped": {
                    "type": "BOOKING",
                    "inmateNbr": alert.identifier,
                    "bookingNo": alert.booking_no
                },
                "dtoClassName": "com.etx.dto.ArrestChargeDTO",
                "dto": {
                    "_id": f"ARS-{uuid.uuid4().hex[:15].upper()}",
                    "personBio": {"$ref": "person_bio", "$id": self.person_bio} if self.person_bio else None,
                    "referenceDtos": [
                        {
                            "dtoId": f"ALS-{uuid.uuid4().hex[:15].upper()}",
                            "dtoName": "com.etx.dto.AliasDTO"
                        }
                    ],
                    "bookingDate": f"{alert.book_in_date} 00:00:00" if alert.book_in_date else None,
                    "bookingNbr": alert.booking_no,
                    "bookingSid": alert.identifier,
                    "sourceState": "TX",
                    "sourceCounty": "Tarrant",
                    "sourceAddress": "200 Taylor St",
                    "sourceCity": "Fort Worth",
                    "sourceZip": "76102",
                    "sourceDesc": "Tarrant County Sheriff's Office",
                    "offenderId": alert.identifier,
                    "released": "N",  # Assume not released since it's a booking report
                    "date_created": datetime.utcnow().isoformat() + "Z",
                    "last_update": datetime.utcnow().isoformat() + "Z",
                    "source_type": "EXTERNAL",
                    "verification_status": "UNVERIFIED",
                    "sources": ["Tarrant County Sheriff's Office"],
                    "auditId": audit_id,
                    "_class": "com.etx.scoring.domain.ArrestCharge"
                },
                "metadata": {
                    "what": alert.description,
                    "when": {
                        "sortable": int(alert.book_in_date.replace("-", "")) if alert.book_in_date else None,
                        "data": alert.book_in_date
                    },
                    "where": {
                        "description": "Tarrant County Sheriff's Office",
                        "city": "Fort Worth",
                        "state": "TX",
                        "county": "Tarrant",
                        "country": "USA"
                    },
                    "disposition": "Booking",
                    "severity": "UNKNOWN",
                    "stage": {"started": "Arrest/Booking"},
                    "category": "Criminal",
                    "className": "Criminal",
                    "sources": []
                },
                "selectedDTOAttributes": [
                    "bookingDate", "bookingNbr", "bookingSid",
                    "sourceState", "sourceCounty", "sourceAddress",
                    "sourceCity", "sourceZip", "sourceDesc",
                    "offenderId"
                ],
                "hashString": str(hash(f"{alert.booking_no}{alert.identifier}")),
                "recordType": "ACTIVE",
                "eventWorkFlow": {
                    "_id": f"EVE-WF-{uuid.uuid4().hex[:15].upper()}",
                    "event": {"$ref": "events", "$id": event_id},
                    "status": "PUBLISHED",
                    "publishedDate": datetime.utcnow().isoformat() + "Z",
                    "updatedBy": "texas-extract@system.com",
                    "date_created": datetime.utcnow().isoformat() + "Z",
                    "last_update": datetime.utcnow().isoformat() + "Z",
                    "sources": []
                },
                "archived": False,
                "packageId": f"PKG{uuid.uuid4().hex[:7].upper()}",
                "date_created": datetime.utcnow().isoformat() + "Z",
                "last_update": datetime.utcnow().isoformat() + "Z",
                "source_type": "EXTERNAL",
                "sources": [],
                "auditId": audit_id,
                "_class": "com.etx.scoring.domain.CeEventEntity"
            }
            
            # Remove None values from personBio if not provided
            if not self.person_bio:
                event.pop("personBio", None)
                if event["dto"]:
                    event["dto"].pop("personBio", None)
            
            events.append(event)
        
        return {
            "events": events,
            "summary": {
                "searchName": self.name,
                "totalMatches": len(self.alerts),
                "recordsChecked": self.records_checked,
                "lastUpdate": self.last_update.isoformat() if self.last_update else None,
                "personBio": self.person_bio,
                "organization": self.organization
            }
        }

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

def get_current_report_date() -> Optional[datetime.date]:
    """
    Get the date of the current report by extracting it from the PDF.
    
    Returns:
        Date of the current report, or None if not found
    """
    from arrestx.web import extract_report_date
    
    report_path = Path("reports/01.PDF")
    if not report_path.exists():
        return None
    
    # Extract date from the current report
    date_str = extract_report_date(str(report_path))
    if date_str:
        try:
            return datetime.date.fromisoformat(date_str)
        except ValueError:
            pass
    
    # Fallback to file modification time
    try:
        file_mtime = report_path.stat().st_mtime
        return datetime.date.fromtimestamp(file_mtime)
    except Exception:
        return None

def get_latest_report_date() -> Optional[datetime.date]:
    """
    Get the date of the latest report (current or archived).
    
    Returns:
        Date of the latest report, or None if no reports found
    """
    # First check the current report
    current_date = get_current_report_date()
    
    # Then check archived reports
    archive_dir = Path("reports/archive")
    latest_archived_date = None
    
    if archive_dir.exists():
        date_pattern = re.compile(r'.*_(\d{4}-\d{2}-\d{2})\.PDF$', re.IGNORECASE)
        
        for file in archive_dir.glob("*.PDF"):
            match = date_pattern.match(str(file.name))
            if match:
                date_str = match.group(1)
                try:
                    file_date = datetime.date.fromisoformat(date_str)
                    if latest_archived_date is None or file_date > latest_archived_date:
                        latest_archived_date = file_date
                except ValueError:
                    continue
    
    # Return the most recent date
    if current_date and latest_archived_date:
        return max(current_date, latest_archived_date)
    elif current_date:
        return current_date
    elif latest_archived_date:
        return latest_archived_date
    else:
        return None

def is_report_current() -> bool:
    """
    Check if the current report is from today.
    
    Returns:
        True if the current report is from today, False otherwise
    """
    current_date = get_current_report_date()
    if current_date is None:
        return False
    
    today = datetime.date.today()
    return current_date == today

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

def search_name(name: str, cfg: Config, force_update: bool = False,
                person_bio: Optional[str] = None, organization: Optional[str] = None) -> SearchResult:
    """
    Search for a name in arrest records.
    
    Args:
        name: Name to search for
        cfg: Configuration
        force_update: Force update of the report
        person_bio: Optional identifier for correlation by calling system
        organization: Optional organization identifier for correlation
        
    Returns:
        Search result
    """
    # Ensure the report is current
    if force_update or not is_report_current():
        ensure_current_report(cfg)
    
    # Get the current report date
    current_date = get_current_report_date()
    
    # Get the path to the current report
    report_path = Path("reports/01.PDF")
    if not report_path.exists():
        logger.error(f"Report not found: {report_path}")
        return SearchResult(name, [], 0, current_date, person_bio, organization)
    
    # Parse the report
    records = parse_pdf(str(report_path), cfg)
    
    # Search for the name in the records
    alerts = []
    for record in records:
        # Use name_normalized for matching, but keep original name in alert
        search_name = record.get("name_normalized", record["name"])
        if name_matches(search_name, name):
            # Create an alert for each charge
            for charge in record["charges"]:
                alert = Alert(
                    name=record["name"],  # Keep original format for display
                    booking_no=charge["booking_no"],
                    description=charge["description"],
                    identifier=record.get("identifier", ""),
                    book_in_date=record.get("book_in_date", ""),
                    source_file=record["source_file"]
                )
                alerts.append(alert)
    
    # Create the search result
    result = SearchResult(name, alerts, len(records), current_date, person_bio, organization)
    
    return result