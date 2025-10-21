"""
MongoDB integration for Texas Extract.
"""

import datetime
import hashlib
from typing import Dict, List, Optional

from arrestx.config import Config, MongoDBConfig
from arrestx.log import get_logger
from arrestx.model import MongoDBError, Record

logger = get_logger(__name__)

try:
    import pymongo
    MONGODB_AVAILABLE = True
except ImportError:
    logger.warning("pymongo not installed. MongoDB integration will not be available.")
    MONGODB_AVAILABLE = False


def write_mongodb(records: List[Record], cfg: MongoDBConfig) -> Dict:
    """
    Write records to MongoDB.
    
    Args:
        records: List of records to write
        cfg: MongoDB configuration
        
    Returns:
        Dictionary with operation counts
    """
    if not MONGODB_AVAILABLE:
        raise MongoDBError("pymongo not installed. Install with: pip install pymongo")
    
    if not cfg.enabled:
        logger.warning("MongoDB integration is disabled in configuration")
        return {"matched": 0, "modified": 0, "upserted": 0}
    
    logger.info(f"Writing {len(records)} records to MongoDB")
    
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(cfg.uri, retryWrites=True)
        db = client[cfg.database]
        collection = db[cfg.collection]
        
        # Prepare bulk operations
        operations = []
        for record in records:
            # Convert record to MongoDB document
            doc = to_mongodb_doc(record, cfg.tenant)
            
            # Create upsert operation
            filter_doc = {"_id": doc["_id"]}
            update = {
                "$set": {
                    "_tenant": doc["_tenant"],
                    "name": doc["name"],
                    "name_normalized": doc["name_normalized"],
                    "address": doc["address"],
                    "identifier": doc["identifier"],
                    "book_in_date": doc["book_in_date"],
                    "source.file": doc["source"]["file"],
                    "source.page_span": doc["source"]["page_span"],
                    "source.parser_version": doc["source"]["parser_version"],
                    "quality": doc["quality"]
                },
                "$setOnInsert": { "source.ingested_at": doc["source"]["ingested_at"] },
                "$addToSet": { "charges": { "$each": doc["charges"] } }
            }
            operations.append(pymongo.UpdateOne(filter_doc, update, upsert=True))
        
        # Execute bulk operations
        if operations:
            result = collection.bulk_write(operations, ordered=False)
            return {
                "matched": result.matched_count,
                "modified": result.modified_count,
                "upserted": len(result.upserted_ids or {})
            }
        
        return {"matched": 0, "modified": 0, "upserted": 0}
    except Exception as e:
        logger.error(f"Error writing to MongoDB: {e}")
        raise MongoDBError(f"Error writing to MongoDB: {e}")


def to_mongodb_doc(record: Record, tenant: str) -> Dict:
    """
    Convert a record to a MongoDB document.
    
    Args:
        record: Record to convert
        tenant: Tenant identifier
        
    Returns:
        MongoDB document
    """
    # Generate deterministic ID
    _id = keyify(tenant, record["source_file"], record)
    
    # Convert record to MongoDB document
    return {
        "_id": _id,
        "_tenant": tenant,
        "name": record["name"],
        "name_normalized": record.get("name_normalized", record["name"]),
        "address": record.get("address", []),
        "identifier": record.get("identifier"),
        "book_in_date": record["book_in_date"],
        "charges": record.get("charges", []),
        "source": {
            "file": record["source_file"],
            "page_span": record.get("source_page_span", [1, 1]),
            "ingested_at": datetime.datetime.utcnow(),
            "parser_version": "1.0.0",
            "hash": None  # Optional: compute hash of original text
        },
        "quality": {
            "warnings": record.get("parse_warnings", []),
            "ocr_used": record.get("ocr_used", False)
        }
    }


def keyify(tenant: str, source_file: str, record: Dict) -> str:
    """
    Generate a deterministic ID for a record.
    
    Args:
        tenant: Tenant identifier
        source_file: Source file name
        record: Record
        
    Returns:
        Deterministic ID
    """
    ident = record.get("identifier")
    book_in_date = record.get("book_in_date", "unknown_date")
    
    if ident:
        return f"{tenant}::{book_in_date}::{source_file}::{ident}"
    else:
        # Fall back to name hash if identifier is missing
        name_key = hashlib.sha256(record["name_normalized"].encode()).hexdigest()[:16]
        return f"{tenant}::{book_in_date}::{source_file}::{name_key}"


def write_dead_letter(record: Record, error: str, cfg: MongoDBConfig) -> None:
    """
    Write a record to the dead-letter collection.
    
    Args:
        record: Record that failed to be inserted
        error: Error message
        cfg: MongoDB configuration
    """
    if not MONGODB_AVAILABLE:
        logger.warning("pymongo not installed. Dead-letter collection not available.")
        return
    
    if not cfg.enabled:
        logger.warning("MongoDB integration is disabled in configuration")
        return
    
    logger.info(f"Writing record to dead-letter collection: {error}")
    
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(cfg.uri)
        db = client[cfg.database]
        collection = db["arrest_ingest_errors"]
        
        # Write record to dead-letter collection
        collection.insert_one({
            "record": record,
            "error": error,
            "timestamp": datetime.datetime.utcnow()
        })
    except Exception as e:
        logger.error(f"Error writing to dead-letter collection: {e}")


def setup_mongodb(cfg: MongoDBConfig) -> None:
    """
    Set up MongoDB collections and indexes.
    
    Args:
        cfg: MongoDB configuration
    """
    if not MONGODB_AVAILABLE:
        logger.warning("pymongo not installed. MongoDB setup not available.")
        return
    
    if not cfg.enabled:
        logger.warning("MongoDB integration is disabled in configuration")
        return
    
    logger.info("Setting up MongoDB collections and indexes")
    
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(cfg.uri)
        db = client[cfg.database]
        
        # Create arrest_records collection with validation
        if cfg.collection not in db.list_collection_names():
            db.create_collection(
                cfg.collection,
                validator={
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": ["_tenant", "name", "book_in_date", "charges", "source"],
                        "properties": {
                            "_tenant": { "bsonType": "string", "minLength": 1 },
                            "name": { "bsonType": "string", "minLength": 1 },
                            "name_normalized": { "bsonType": "string" },
                            "address": {
                                "bsonType": "array",
                                "items": { "bsonType": "string" }
                            },
                            "identifier": { "bsonType": ["string", "null"], "pattern": "^[0-9]{5,8}$" },
                            "book_in_date": { "bsonType": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$" },
                            "charges": {
                                "bsonType": "array",
                                "minItems": 0,
                                "items": {
                                    "bsonType": "object",
                                    "required": ["booking_no", "description"],
                                    "properties": {
                                        "booking_no": { "bsonType": "string", "pattern": "^[0-9]{2}-[0-9]{6,7}$" },
                                        "description": { "bsonType": "string", "minLength": 1 }
                                    }
                                }
                            },
                            "source": {
                                "bsonType": "object",
                                "required": ["file", "ingested_at"],
                                "properties": {
                                    "file": { "bsonType": "string" },
                                    "page_span": {
                                        "bsonType": "array",
                                        "items": { "bsonType": "int" },
                                        "minItems": 2, "maxItems": 2
                                    },
                                    "ingested_at": { "bsonType": "date" },
                                    "parser_version": { "bsonType": "string" },
                                    "hash": { "bsonType": ["string", "null"] }
                                }
                            },
                            "quality": {
                                "bsonType": "object",
                                "properties": {
                                    "warnings": { "bsonType": "array", "items": { "bsonType": "string" } },
                                    "ocr_used": { "bsonType": "bool" }
                                }
                            }
                        }
                    }
                },
                validationLevel="moderate"
            )
        
        # Create indexes
        collection = db[cfg.collection]
        
        # Idempotency & point lookups
        collection.create_index(
            [("_tenant", pymongo.ASCENDING), 
             ("source.file", pymongo.ASCENDING), 
             ("identifier", pymongo.ASCENDING), 
             ("book_in_date", pymongo.ASCENDING)],
            unique=True, 
            partialFilterExpression={"identifier": {"$type": "string"}}
        )
        
        # Fallback uniqueness when identifier is absent
        collection.create_index(
            [("_tenant", pymongo.ASCENDING), 
             ("source.file", pymongo.ASCENDING), 
             ("name_normalized", pymongo.ASCENDING), 
             ("book_in_date", pymongo.ASCENDING)],
            unique=True, 
            partialFilterExpression={"identifier": {"$exists": False}}
        )
        
        # Query by date and charge booking number inside array
        collection.create_index([("book_in_date", pymongo.ASCENDING)])
        collection.create_index([("_tenant", pymongo.ASCENDING), ("charges.booking_no", pymongo.ASCENDING)])
        
        # Name search (exact or prefix)
        collection.create_index([("name_normalized", pymongo.ASCENDING)])
        
        # Create arrest_reports collection
        if "arrest_reports" not in db.list_collection_names():
            db.create_collection("arrest_reports")
            
        # Create indexes for arrest_reports
        reports_collection = db["arrest_reports"]
        reports_collection.create_index([("url", pymongo.ASCENDING), ("report_date", pymongo.ASCENDING)], unique=True)
        reports_collection.create_index([("report_date", pymongo.ASCENDING)])
        reports_collection.create_index([("pulled_at", pymongo.ASCENDING)])
        
        # Create arrest_sources collection
        if "arrest_sources" not in db.list_collection_names():
            db.create_collection("arrest_sources")
            
        # Create indexes for arrest_sources
        sources_collection = db["arrest_sources"]
        sources_collection.create_index([("url", pymongo.ASCENDING)], unique=True)
        
        # Create arrest_ingest_errors collection
        if "arrest_ingest_errors" not in db.list_collection_names():
            db.create_collection("arrest_ingest_errors")
            
        # Create indexes for arrest_ingest_errors
        errors_collection = db["arrest_ingest_errors"]
        errors_collection.create_index([("timestamp", pymongo.ASCENDING)])
        
        logger.info("MongoDB setup complete")
    except Exception as e:
        logger.error(f"Error setting up MongoDB: {e}")
        raise MongoDBError(f"Error setting up MongoDB: {e}")