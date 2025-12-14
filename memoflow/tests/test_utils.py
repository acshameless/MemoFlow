"""Tests for utility functions"""

import pytest
from mf.utils.jd import parse_jd_id, format_jd_id, validate_jd_id, extract_area_id, extract_item_id
from mf.utils.markdown import extract_wikilinks, extract_hashtags, validate_frontmatter


def test_parse_jd_id():
    """Test parsing JD ID"""
    result = parse_jd_id("HANK-12.04")
    assert result is not None
    assert result[0] == "HANK"
    assert result[1] == 12
    assert result[2] == 12.04
    
    assert parse_jd_id("invalid") is None
    assert parse_jd_id("HANK-12") is None


def test_format_jd_id():
    """Test formatting JD ID"""
    jd_id = format_jd_id("HANK", 12, 12.04)
    assert jd_id == "HANK-12.04"


def test_validate_jd_id():
    """Test validating JD ID"""
    assert validate_jd_id("HANK-12.04") is True
    assert validate_jd_id("invalid") is False
    assert validate_jd_id("HANK-12") is False


def test_extract_area_id():
    """Test extracting area ID"""
    assert extract_area_id("HANK-12.04") == 12
    assert extract_area_id("invalid") is None


def test_extract_item_id():
    """Test extracting item ID"""
    assert extract_item_id("HANK-12.04") == 12.04
    assert extract_item_id("invalid") is None


def test_extract_wikilinks():
    """Test extracting wikilinks"""
    content = "This is a [[link]] to another [[page]]."
    links = extract_wikilinks(content)
    assert "link" in links
    assert "page" in links
    assert len(links) == 2


def test_extract_hashtags():
    """Test extracting hashtags"""
    content = "This is a #tag and another #hashtag."
    tags = extract_hashtags(content)
    assert "tag" in tags
    assert "hashtag" in tags
    
    # Test with frontmatter
    metadata = {"tags": ["frontmatter-tag"]}
    tags = extract_hashtags(content, metadata)
    assert "frontmatter-tag" in tags
    assert "tag" in tags


def test_validate_frontmatter():
    """Test validating frontmatter"""
    # Valid frontmatter
    valid_meta = {
        "uuid": "abc123",
        "id": "HANK-12.04",
        "type": "task",
        "title": "Test",
        "status": "open",
        "created_at": "2023-01-01"
    }
    assert validate_frontmatter(valid_meta) == []
    
    # Missing field
    invalid_meta = {"uuid": "abc123"}
    errors = validate_frontmatter(invalid_meta)
    assert len(errors) > 0
    
    # Invalid type
    invalid_type = valid_meta.copy()
    invalid_type["type"] = "invalid"
    errors = validate_frontmatter(invalid_type)
    assert any("Invalid type" in e for e in errors)
