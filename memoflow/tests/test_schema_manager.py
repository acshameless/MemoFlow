"""Tests for Schema Manager"""

import pytest
from pathlib import Path
from mf.core.schema_manager import SchemaManager


def test_schema_manager_init(tmp_path):
    """Test SchemaManager initialization"""
    mgr = SchemaManager(tmp_path)
    assert mgr.repo_root == tmp_path.resolve()
    assert mgr.schema_file == tmp_path / "schema.yaml"


def test_schema_manager_load_default(tmp_path):
    """Test loading default schema when file doesn't exist"""
    mgr = SchemaManager(tmp_path)
    schema = mgr.load_schema()
    
    assert schema.user_prefix == "HANK"
    assert len(schema.areas) > 0
    # Default schema file should be created
    assert mgr.schema_file.exists()


def test_schema_manager_validate_path(tmp_path):
    """Test path validation"""
    mgr = SchemaManager(tmp_path)
    mgr.load_schema()  # Create default schema
    
    assert mgr.validate_path("HANK-10.05") is True
    assert mgr.validate_path("OTHER-10.05") is False
    assert mgr.validate_path("invalid") is False


def test_schema_manager_generate_temp_id(tmp_path):
    """Test temporary ID generation"""
    mgr = SchemaManager(tmp_path)
    mgr.load_schema()
    
    temp_id = mgr.generate_temp_id(1)
    assert temp_id.startswith("HANK-00.")
    assert "01" in temp_id
    
    temp_id2 = mgr.generate_temp_id(2)
    assert "02" in temp_id2


def test_schema_manager_get_directory_path(tmp_path):
    """Test getting directory path"""
    mgr = SchemaManager(tmp_path)
    mgr.load_schema()
    
    path = mgr.get_directory_path("HANK-10.05")
    assert "10-" in str(path)
    assert path.is_absolute() or str(path).startswith(str(tmp_path))
