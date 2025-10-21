"""
Tests for the MongoDB integration.
"""

import datetime
from unittest.mock import MagicMock, patch

import pytest

from arrestx.config import MongoDBConfig
from arrestx.db.mongo import (
    keyify,
    setup_mongodb,
    to_mongodb_doc,
    write_dead_letter,
    write_mongodb,
)
from arrestx.model import MongoDBError


def create_test_record():
    """Create a test record for use in tests."""
    return {
        "name": "SMITH, JOHN",
        "name_normalized": "John Smith",
        "address": ["123 MAIN ST", "ANYTOWN, TX 12345"],
        "identifier": "12345678",
        "book_in_date": "2025-01-02",
        "charges": [
            {
                "booking_no": "25-0123456",
                "description": "NO VALID DL"
            }
        ],
        "source_file": "test.pdf",
        "source_page_span": [1, 1],
        "parse_warnings": [],
        "ocr_used": False
    }


def test_keyify_with_identifier():
    """Test keyify with identifier."""
    record = create_test_record()
    key = keyify("TEST", "test.pdf", record)
    assert key == "TEST::2025-01-02::test.pdf::12345678"


def test_keyify_without_identifier():
    """Test keyify without identifier."""
    record = create_test_record()
    record["identifier"] = None
    key = keyify("TEST", "test.pdf", record)
    assert key.startswith("TEST::2025-01-02::test.pdf::")
    assert len(key.split("::")[3]) == 16  # SHA-256 hash truncated to 16 chars


def test_to_mongodb_doc():
    """Test converting a record to a MongoDB document."""
    record = create_test_record()
    doc = to_mongodb_doc(record, "TEST")
    
    assert doc["_id"] == "TEST::2025-01-02::test.pdf::12345678"
    assert doc["_tenant"] == "TEST"
    assert doc["name"] == "SMITH, JOHN"
    assert doc["name_normalized"] == "John Smith"
    assert doc["address"] == ["123 MAIN ST", "ANYTOWN, TX 12345"]
    assert doc["identifier"] == "12345678"
    assert doc["book_in_date"] == "2025-01-02"
    assert doc["charges"] == [{"booking_no": "25-0123456", "description": "NO VALID DL"}]
    assert doc["source"]["file"] == "test.pdf"
    assert doc["source"]["page_span"] == [1, 1]
    assert isinstance(doc["source"]["ingested_at"], datetime.datetime)
    assert doc["source"]["parser_version"] == "1.0.0"
    assert doc["source"]["hash"] is None
    assert doc["quality"]["warnings"] == []
    assert doc["quality"]["ocr_used"] is False


@patch("arrestx.db.mongo.MONGODB_AVAILABLE", False)
def test_write_mongodb_not_available():
    """Test writing to MongoDB when pymongo is not available."""
    with pytest.raises(MongoDBError) as excinfo:
        write_mongodb([create_test_record()], MongoDBConfig(enabled=True))
    
    assert "pymongo not installed" in str(excinfo.value)


@patch("arrestx.db.mongo.MONGODB_AVAILABLE", True)
def test_write_mongodb_disabled():
    """Test writing to MongoDB when it's disabled."""
    result = write_mongodb([create_test_record()], MongoDBConfig(enabled=False))
    assert result == {"matched": 0, "modified": 0, "upserted": 0}


@patch("arrestx.db.mongo.MONGODB_AVAILABLE", True)
@patch("arrestx.db.mongo.pymongo.MongoClient")
def test_write_mongodb(mock_mongo_client):
    """Test writing to MongoDB."""
    # Mock MongoDB client and collection
    mock_collection = MagicMock()
    mock_db = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_client = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    mock_mongo_client.return_value = mock_client
    
    # Mock bulk_write result
    mock_result = MagicMock()
    mock_result.matched_count = 1
    mock_result.modified_count = 1
    mock_result.upserted_ids = {"0": "id1"}
    mock_collection.bulk_write.return_value = mock_result
    
    # Write to MongoDB
    result = write_mongodb([create_test_record()], MongoDBConfig(
        enabled=True,
        uri="mongodb://localhost:27017",
        database="test_db",
        collection="test_collection",
        tenant="TEST"
    ))
    
    # Verify result
    assert result["matched"] == 1
    assert result["modified"] == 1
    assert result["upserted"] == 1
    
    # Verify MongoDB client was created with correct URI
    mock_mongo_client.assert_called_once_with("mongodb://localhost:27017", retryWrites=True)
    
    # Verify database and collection were accessed
    mock_client.__getitem__.assert_called_once_with("test_db")
    mock_db.__getitem__.assert_called_once_with("test_collection")
    
    # Verify bulk_write was called
    mock_collection.bulk_write.assert_called_once()
    assert len(mock_collection.bulk_write.call_args[0][0]) == 1  # One operation
    assert mock_collection.bulk_write.call_args[1]["ordered"] is False


@patch("arrestx.db.mongo.MONGODB_AVAILABLE", False)
def test_write_dead_letter_not_available():
    """Test writing to dead-letter collection when pymongo is not available."""
    # Should not raise an exception, just log a warning
    write_dead_letter(create_test_record(), "Test error", MongoDBConfig(enabled=True))


@patch("arrestx.db.mongo.MONGODB_AVAILABLE", True)
def test_write_dead_letter_disabled():
    """Test writing to dead-letter collection when MongoDB is disabled."""
    # Should not raise an exception, just log a warning
    write_dead_letter(create_test_record(), "Test error", MongoDBConfig(enabled=False))


@patch("arrestx.db.mongo.MONGODB_AVAILABLE", True)
@patch("arrestx.db.mongo.pymongo.MongoClient")
def test_write_dead_letter(mock_mongo_client):
    """Test writing to dead-letter collection."""
    # Mock MongoDB client and collection
    mock_collection = MagicMock()
    mock_db = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_client = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    mock_mongo_client.return_value = mock_client
    
    # Write to dead-letter collection
    write_dead_letter(create_test_record(), "Test error", MongoDBConfig(
        enabled=True,
        uri="mongodb://localhost:27017",
        database="test_db",
        collection="test_collection",
        tenant="TEST"
    ))
    
    # Verify MongoDB client was created with correct URI
    mock_mongo_client.assert_called_once_with("mongodb://localhost:27017")
    
    # Verify database and collection were accessed
    mock_client.__getitem__.assert_called_once_with("test_db")
    mock_db.__getitem__.assert_called_once_with("arrest_ingest_errors")
    
    # Verify insert_one was called
    mock_collection.insert_one.assert_called_once()
    doc = mock_collection.insert_one.call_args[0][0]
    assert doc["record"] == create_test_record()
    assert doc["error"] == "Test error"
    assert isinstance(doc["timestamp"], datetime.datetime)


@patch("arrestx.db.mongo.MONGODB_AVAILABLE", False)
def test_setup_mongodb_not_available():
    """Test setting up MongoDB when pymongo is not available."""
    # Should not raise an exception, just log a warning
    setup_mongodb(MongoDBConfig(enabled=True))


@patch("arrestx.db.mongo.MONGODB_AVAILABLE", True)
def test_setup_mongodb_disabled():
    """Test setting up MongoDB when it's disabled."""
    # Should not raise an exception, just log a warning
    setup_mongodb(MongoDBConfig(enabled=False))