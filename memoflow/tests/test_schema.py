"""Tests for Schema model"""

import pytest
from pathlib import Path
from mf.models.schema import Schema, Area, Category


def test_schema_default():
    """Test creating default schema"""
    schema = Schema.default()
    
    assert schema.user_prefix == "HANK"
    assert len(schema.areas) > 0
    assert schema.areas[0].id == 10
    assert schema.areas[0].name == "项目"


def test_schema_validate_path():
    """Test validating JD paths"""
    schema = Schema.default()
    
    # Valid path (using area 10 which exists in default schema)
    assert schema.validate_path("HANK-10.05") is True
    
    # Invalid prefix
    assert schema.validate_path("OTHER-10.05") is False
    
    # Invalid format
    assert schema.validate_path("invalid") is False
    assert schema.validate_path("HANK-12") is False
    
    # Path not in schema
    assert schema.validate_path("HANK-99.99") is False


def test_schema_get_directory_path(tmp_path):
    """Test getting directory path from JD ID"""
    schema = Schema.default()
    
    # Test with valid JD ID
    path = schema.get_directory_path("HANK-10.05", tmp_path)
    # Path should be calculated correctly (directory may not exist yet)
    # 默认schema使用三位小数格式：10.001-10.099 或 10.100-10.199
    assert "10-" in str(path)
    assert "10.001-10.099" in str(path) or "10.100-10.199" in str(path)
    assert path.is_absolute() or str(path).startswith(str(tmp_path))
    
    # Test with invalid JD ID
    with pytest.raises(ValueError):
        schema.get_directory_path("INVALID", tmp_path)


def test_category_contains():
    """Test Category.contains method"""
    category = Category(id=1, name="规划", range=(10.01, 10.09))
    
    assert category.contains(10.05) is True
    assert category.contains(10.01) is True
    assert category.contains(10.09) is True
    assert category.contains(10.10) is False
    assert category.contains(9.99) is False


def test_schema_from_yaml(tmp_path):
    """Test loading schema from YAML file"""
    yaml_content = """user_prefix: TEST
areas:
  - id: 10
    name: 项目
    categories:
      - id: 1
        name: 规划
        range: [10.01, 10.09]
      - id: 2
        name: 执行
        range: [10.10, 10.19]
"""
    yaml_file = tmp_path / "schema.yaml"
    yaml_file.write_text(yaml_content, encoding='utf-8')
    
    schema = Schema.from_yaml(yaml_file)
    
    assert schema.user_prefix == "TEST"
    assert len(schema.areas) == 1
    assert schema.areas[0].id == 10
    assert len(schema.areas[0].categories) == 2


def test_schema_to_yaml():
    """Test converting schema to YAML"""
    schema = Schema.default()
    yaml_str = schema.to_yaml()
    
    assert "user_prefix" in yaml_str
    assert "HANK" in yaml_str
    assert "areas" in yaml_str


def test_schema_get_area():
    """Test getting area by ID"""
    schema = Schema.default()
    
    area = schema.get_area(10)
    assert area is not None
    assert area.id == 10
    
    area = schema.get_area(99)
    assert area is None
