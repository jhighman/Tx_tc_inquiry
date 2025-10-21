# MongoDB Integration

## Overview

The MongoDB integration allows the system to store extracted arrest records in a MongoDB database. This enables:

1. Persistent storage of records
2. Advanced querying capabilities
3. Integration with other systems
4. Multi-tenant support

## Collection Design

We'll use a single collection with embedded charges, which is the recommended approach for this data model.

### Collection: `arrest_records`

One document per person per report (or per person+book_in_date if the same person can appear across days).

#### Document Structure

```json
{
  "_id": "TRUA::2025-10-12::01.pdf::1234567",        // deterministic
  "_tenant": "TRUA",                                  // multi-tenant safety
  "name": "ADAMS, NINA KISHA",
  "name_normalized": "Nina Kisha Adams",
  "address": ["123 MAIN ST", "ORLANDO, FL 32801"],
  "identifier": "1234567",
  "book_in_date": "2025-10-12",
  "charges": [
    { "booking_no": "25-0240350", "description": "NO VALID DL" },
    { "booking_no": "25-0240351", "description": "FAILURE TO APPEAR" }
  ],
  "source": {
    "file": "01.pdf",
    "page_span": [1, 2],
    "ingested_at": { "$date": "2025-10-15T17:04:31.000Z" },
    "parser_version": "1.0.0",
    "hash": "sha256:..."                                // optional: text block hash
  },
  "quality": {
    "warnings": [],
    "ocr_used": false
  }
}
```

### Natural Key (Idempotency)

The natural key for idempotent operations is:

```
(_tenant, source_file, identifier, book_in_date)
```

If identifier can be missing, fall back to:

```
(_tenant, source_file, name_normalized, book_in_date)
```

We'll compute a deterministic `_id` field based on these values:

```python
def keyify(tenant, source_file, r):
    ident = r.get("identifier")
    name_key = hashlib.sha256(r["name_normalized"].encode()).hexdigest()[:16]
    base = f"{tenant}::{r['book_in_date']}::{source_file}::" + (ident or name_key)
    return base
```

## MongoDB Schema Validation

We'll apply JSON Schema validation to the collection to ensure data integrity:

```javascript
db.createCollection("arrest_records", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["_tenant", "name", "book_in_date", "charges", "source"],
      properties: {
        _tenant: { bsonType: "string", minLength: 1 },
        name: { bsonType: "string", minLength: 1 },
        name_normalized: { bsonType: "string" },
        address: {
          bsonType: "array",
          items: { bsonType: "string" }
        },
        identifier: { bsonType: ["string", "null"], pattern: "^[0-9]{5,8}$" },
        book_in_date: { bsonType: "string", pattern: "^[0-9]{4}-[0-9]{2}-[0-9]{2}$" },
        charges: {
          bsonType: "array",
          minItems: 0,
          items: {
            bsonType: "object",
            required: ["booking_no", "description"],
            properties: {
              booking_no: { bsonType: "string", pattern: "^[0-9]{2}-[0-9]{6,7}$" },
              description: { bsonType: "string", minLength: 1 }
            }
          }
        },
        source: {
          bsonType: "object",
          required: ["file", "ingested_at"],
          properties: {
            file: { bsonType: "string" },
            page_span: {
              bsonType: "array",
              items: { bsonType: "int" },
              minItems: 2, maxItems: 2
            },
            ingested_at: { bsonType: "date" },
            parser_version: { bsonType: "string" },
            hash: { bsonType: "string" }
          }
        },
        quality: {
          bsonType: "object",
          properties: {
            warnings: { bsonType: "array", items: { bsonType: "string" } },
            ocr_used: { bsonType: "bool" }
          }
        }
      }
    }
  },
  validationLevel: "moderate"
});
```

## Indexing Strategy

We'll create the following indexes to optimize query performance:

```javascript
// Idempotency & point lookups
db.arrest_records.createIndex(
  { _tenant: 1, "source.file": 1, identifier: 1, book_in_date: 1 },
  { unique: true, partialFilterExpression: { identifier: { $type: "string" } } }
);

// Fallback uniqueness when identifier is absent (optional):
db.arrest_records.createIndex(
  { _tenant: 1, "source.file": 1, name_normalized: 1, book_in_date: 1 },
  { unique: true, partialFilterExpression: { identifier: { $exists: false } } }
);

// Query by date and charge booking number inside array
db.arrest_records.createIndex({ book_in_date: 1 });
db.arrest_records.createIndex({ "_tenant": 1, "charges.booking_no": 1 });

// Name search (exact or prefix)
db.arrest_records.createIndex({ name_normalized: 1 });
```

## Python Implementation

### MongoDB Writer

```python
def write_mongodb(records: list[Record], cfg: MongoDBConfig) -> dict:
    """
    Write records to MongoDB.
    
    Args:
        records: List of records to write
        cfg: MongoDB configuration
        
    Returns:
        Dictionary with operation counts
    """
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
            "upserted": len(result.upserted_ids)
        }
    
    return {"matched": 0, "modified": 0, "upserted": 0}
```

### Record to MongoDB Document Conversion

```python
def to_mongodb_doc(record: Record, tenant: str) -> dict:
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
```

## Integration with Main Application

The MongoDB integration is optional and can be enabled via configuration:

```python
def write_outputs(records: list[Record], cfg: Config) -> None:
    """
    Write records to all configured output formats.
    
    Args:
        records: List of records to write
        cfg: Application configuration
    """
    # Write JSON if configured
    if cfg.output.json_path:
        write_json(records, cfg.output.json_path, cfg.output.pretty_json)
        
    # Write CSV if configured
    if cfg.output.csv_path:
        write_csv(records, cfg.output.csv_path)
        
    # Write NDJSON if configured
    if cfg.output.ndjson_path:
        write_ndjson(records, cfg.output.ndjson_path)
        
    # Write to MongoDB if configured
    if cfg.mongodb and cfg.mongodb.enabled:
        write_mongodb(records, cfg.mongodb)
```

## Query Examples

### Find all bookings for a specific booking number:

```javascript
db.arrest_records.find(
  { "_tenant": "TRUA", "charges.booking_no": "25-0240350" },
  { name: 1, book_in_date: 1, charges: { $elemMatch: { booking_no: "25-0240350" } } }
)
```

### Arrests by date range:

```javascript
db.arrest_records.find(
  { _tenant: "TRUA", book_in_date: { $gte: "2025-10-01", $lte: "2025-10-15" } },
  { name: 1, charges: 1 }
)
```

### Daily counts:

```javascript
db.arrest_records.aggregate([
  { $match: { _tenant: "TRUA" } },
  { $group: { _id: "$book_in_date", cnt: { $sum: 1 } } },
  { $sort: { _id: 1 } }
])
```

## Security and Privacy

### Network Security

- Enforce TLS connections
- Use retryWrites=true for resilience
- Use role-scoped users (read/write on target DB only)

### Data Security

- At-rest encryption (Atlas encryption or encrypted storage volume)
- Optional Client-side Field-Level Encryption (FLE2) for sensitive fields:
  - identifier
  - address

### Minimal sensitive fields to encrypt (if using FLE2):

```json
{
  "fieldsToEncrypt": ["identifier", "address"]
}
```

## Error Handling

The MongoDB integration includes robust error handling:

1. Connection errors
2. Authentication errors
3. Validation errors
4. Duplicate key errors

Each error is logged and, where possible, the system continues with partial results.

## Dead-Letter Collection

For records that fail to be inserted due to validation errors, we'll create a dead-letter collection:

```python
def write_dead_letter(record: Record, error: str, cfg: MongoDBConfig) -> None:
    """
    Write a record to the dead-letter collection.
    
    Args:
        record: Record that failed to be inserted
        error: Error message
        cfg: MongoDB configuration
    """
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
```

## Operational Notes

1. **Idempotent Operations**: The system is designed to be idempotent, so the same PDF can be processed multiple times without creating duplicates.

2. **Reprocessing**: If a PDF is reprocessed, the system will update existing records and add any new charges.

3. **Monitoring**: The system should be monitored for:
   - Connection errors
   - Validation errors
   - Performance issues

4. **Backup**: Regular backups of the MongoDB database should be configured.