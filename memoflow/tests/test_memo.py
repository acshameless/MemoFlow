"""Tests for Memo model"""

import pytest
from datetime import datetime
from pathlib import Path
from mf.models.memo import Memo


def test_memo_creation():
    """Test creating a Memo instance"""
    memo = Memo(
        uuid="7f9a2b",
        id="HANK-12.04",
        type="task",
        title="Test Task",
        status="open",
        created_at=datetime.now(),
    )
    
    assert memo.uuid == "7f9a2b"
    assert memo.id == "HANK-12.04"
    assert memo.type == "task"
    assert memo.status == "open"
    assert memo.tags == []


def test_memo_to_frontmatter():
    """Test converting Memo to frontmatter"""
    memo = Memo(
        uuid="7f9a2b",
        id="HANK-12.04",
        type="task",
        title="Test Task",
        status="open",
        created_at=datetime(2023, 10, 27, 10, 0, 0),
        due_date=datetime(2023, 10, 28),
        tags=["dev", "test"],
        content="Test content",
    )
    
    frontmatter = memo.to_frontmatter()
    
    assert frontmatter["uuid"] == "7f9a2b"
    assert frontmatter["id"] == "HANK-12.04"
    assert frontmatter["type"] == "task"
    assert frontmatter["title"] == "Test Task"
    assert frontmatter["status"] == "open"
    assert frontmatter["tags"] == ["dev", "test"]
    assert "due_date" in frontmatter


def test_memo_from_file(tmp_path):
    """Test parsing Memo from file"""
    # Create a test markdown file
    test_file = tmp_path / "test.md"
    content = """---
uuid: "7f9a2b"
id: "HANK-12.04"
type: "task"
title: "Test Task"
status: "open"
created_at: 2023-10-27T10:00:00
due_date: 2023-10-28
tags: ["dev", "test"]
---

# Test Task

This is test content.
"""
    test_file.write_text(content, encoding='utf-8')
    
    # Parse the file
    memo = Memo.from_file(test_file)
    
    assert memo.uuid == "7f9a2b"
    assert memo.id == "HANK-12.04"
    assert memo.type == "task"
    assert memo.title == "Test Task"
    assert memo.status == "open"
    assert memo.tags == ["dev", "test"]
    assert memo.content.strip() == "# Test Task\n\nThis is test content."
    assert memo.due_date is not None


def test_memo_from_file_missing_fields(tmp_path):
    """Test parsing Memo from file with missing required fields"""
    test_file = tmp_path / "test.md"
    content = """---
uuid: "7f9a2b"
type: "task"
---

# Test Task
"""
    test_file.write_text(content, encoding='utf-8')
    
    with pytest.raises(ValueError, match="Missing required fields"):
        Memo.from_file(test_file)


def test_memo_to_markdown():
    """Test converting Memo to Markdown format"""
    memo = Memo(
        uuid="7f9a2b",
        id="HANK-12.04",
        type="task",
        title="Test Task",
        status="open",
        created_at=datetime(2023, 10, 27, 10, 0, 0),
        content="Test content",
    )
    
    markdown = memo.to_markdown()
    
    # Check that frontmatter and content are present
    assert "uuid" in markdown
    assert "7f9a2b" in markdown
    assert "HANK-12.04" in markdown
    assert "Test content" in markdown
    assert "---" in markdown  # Frontmatter separator


def test_memo_validation():
    """Test Memo validation"""
    # Valid memo
    valid_memo = Memo(
        uuid="7f9a2b",
        id="HANK-12.04",
        type="task",
        title="Test",
        status="open",
        created_at=datetime.now(),
    )
    assert valid_memo.validate() == []
    
    # Invalid type
    invalid_type = Memo(
        uuid="7f9a2b",
        id="HANK-12.04",
        type="invalid",
        title="Test",
        status="open",
        created_at=datetime.now(),
    )
    errors = invalid_type.validate()
    assert len(errors) > 0
    assert "Invalid type" in errors[0]
    
    # Invalid status
    invalid_status = Memo(
        uuid="7f9a2b",
        id="HANK-12.04",
        type="task",
        title="Test",
        status="invalid",
        created_at=datetime.now(),
    )
    errors = invalid_status.validate()
    assert len(errors) > 0
    assert "Invalid status" in errors[0]
