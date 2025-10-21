"""
Tests for the configuration module.
"""

import os
import tempfile
from unittest.mock import patch

import pytest
import yaml

from arrestx.config import (
    Config,
    InputConfig,
    LoggingConfig,
    MongoDBConfig,
    OutputConfig,
    ParsingConfig,
    PerformanceConfig,
    WebRetrievalConfig,
    load_config,
)


def test_default_config():
    """Test default configuration."""
    cfg = Config()
    
    # Verify default values
    assert cfg.input.paths == ["./reports/*.pdf"]
    assert cfg.input.ocr_fallback is False
    assert cfg.input.ocr_lang == "eng"
    
    assert cfg.parsing.name_regex_strict is True
    assert cfg.parsing.allow_two_line_id_date is True
    assert len(cfg.parsing.header_patterns) == 3
    
    assert cfg.output.json_path == "./out/arrests.json"
    assert cfg.output.csv_path == "./out/arrests.csv"
    assert cfg.output.ndjson_path is None
    assert cfg.output.pretty_json is True
    
    assert cfg.logging.level == "INFO"
    assert cfg.logging.emit_warnings_in_record is True
    
    assert cfg.performance.parallel_pages is True
    
    assert cfg.mongodb is None
    assert cfg.web_retrieval is None


def test_config_override():
    """Test configuration override."""
    cfg = Config(
        input=InputConfig(
            paths=["./custom/*.pdf"],
            ocr_fallback=True,
            ocr_lang="deu"
        ),
        output=OutputConfig(
            json_path="./custom/output.json",
            csv_path=None,
            ndjson_path="./custom/output.ndjson",
            pretty_json=False
        ),
        mongodb=MongoDBConfig(
            enabled=True,
            uri="mongodb://example.com:27017",
            database="custom_db",
            collection="custom_collection",
            tenant="CUSTOM"
        )
    )
    
    # Verify overridden values
    assert cfg.input.paths == ["./custom/*.pdf"]
    assert cfg.input.ocr_fallback is True
    assert cfg.input.ocr_lang == "deu"
    
    assert cfg.output.json_path == "./custom/output.json"
    assert cfg.output.csv_path is None
    assert cfg.output.ndjson_path == "./custom/output.ndjson"
    assert cfg.output.pretty_json is False
    
    assert cfg.mongodb is not None
    assert cfg.mongodb.enabled is True
    assert cfg.mongodb.uri == "mongodb://example.com:27017"
    assert cfg.mongodb.database == "custom_db"
    assert cfg.mongodb.collection == "custom_collection"
    assert cfg.mongodb.tenant == "CUSTOM"


def test_load_config_yaml():
    """Test loading configuration from YAML file."""
    # Create a temporary YAML file
    config_data = {
        "input": {
            "paths": ["./custom/*.pdf"],
            "ocr_fallback": True,
            "ocr_lang": "deu"
        },
        "output": {
            "json_path": "./custom/output.json",
            "csv_path": None,
            "ndjson_path": "./custom/output.ndjson",
            "pretty_json": False
        },
        "mongodb": {
            "enabled": True,
            "uri": "mongodb://example.com:27017",
            "database": "custom_db",
            "collection": "custom_collection",
            "tenant": "CUSTOM"
        }
    }
    
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp:
        yaml.dump(config_data, tmp)
        tmp_path = tmp.name
    
    try:
        # Load configuration
        cfg = load_config(tmp_path)
        
        # Verify loaded values
        assert cfg.input.paths == ["./custom/*.pdf"]
        assert cfg.input.ocr_fallback is True
        assert cfg.input.ocr_lang == "deu"
        
        assert cfg.output.json_path == "./custom/output.json"
        assert cfg.output.csv_path is None
        assert cfg.output.ndjson_path == "./custom/output.ndjson"
        assert cfg.output.pretty_json is False
        
        assert cfg.mongodb is not None
        assert cfg.mongodb.enabled is True
        assert cfg.mongodb.uri == "mongodb://example.com:27017"
        assert cfg.mongodb.database == "custom_db"
        assert cfg.mongodb.collection == "custom_collection"
        assert cfg.mongodb.tenant == "CUSTOM"
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_load_config_json():
    """Test loading configuration from JSON file."""
    # Create a temporary JSON file
    config_data = {
        "input": {
            "paths": ["./custom/*.pdf"],
            "ocr_fallback": True,
            "ocr_lang": "deu"
        },
        "output": {
            "json_path": "./custom/output.json",
            "csv_path": None,
            "ndjson_path": "./custom/output.ndjson",
            "pretty_json": False
        }
    }
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        import json
        json.dump(config_data, tmp)
        tmp_path = tmp.name
    
    try:
        # Load configuration
        cfg = load_config(tmp_path)
        
        # Verify loaded values
        assert cfg.input.paths == ["./custom/*.pdf"]
        assert cfg.input.ocr_fallback is True
        assert cfg.input.ocr_lang == "deu"
        
        assert cfg.output.json_path == "./custom/output.json"
        assert cfg.output.csv_path is None
        assert cfg.output.ndjson_path == "./custom/output.ndjson"
        assert cfg.output.pretty_json is False
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_load_config_unsupported_format():
    """Test loading configuration from unsupported file format."""
    # Create a temporary file with unsupported extension
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp.write(b"test")
        tmp_path = tmp.name
    
    try:
        # Load configuration
        with pytest.raises(ValueError) as excinfo:
            load_config(tmp_path)
        
        # Verify error message
        assert "Unsupported configuration file format" in str(excinfo.value)
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@patch("arrestx.config.os.path.exists")
def test_load_config_default_locations(mock_exists):
    """Test loading configuration from default locations."""
    # Mock os.path.exists to return True for config.yaml
    mock_exists.side_effect = lambda path: path == "./config.yaml"
    
    # Mock open to return a file-like object
    mock_file = """
    input:
      paths: ["./custom/*.pdf"]
    """
    
    with patch("builtins.open", return_value=mock_file):
        # This will fail because mock_file is not a proper file object,
        # but it's enough to test the default locations logic
        try:
            load_config()
        except:
            pass
    
    # Verify os.path.exists was called with default locations
    mock_exists.assert_any_call("./config.yaml")
    mock_exists.assert_any_call("./config.yml")
    mock_exists.assert_any_call("./config.json")
    mock_exists.assert_any_call(os.path.expanduser("~/.config/arrestx/config.yaml"))


def test_web_retrieval_config():
    """Test web retrieval configuration."""
    cfg = Config(
        web_retrieval=WebRetrievalConfig(
            enabled=True,
            url="https://example.com/test.pdf",
            schedule="0 12 * * *",
            skip_if_existing=False
        )
    )
    
    # Verify web retrieval configuration
    assert cfg.web_retrieval is not None
    assert cfg.web_retrieval.enabled is True
    assert cfg.web_retrieval.url == "https://example.com/test.pdf"
    assert cfg.web_retrieval.schedule == "0 12 * * *"
    assert cfg.web_retrieval.skip_if_existing is False