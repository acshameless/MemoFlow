"""Tests for File Manager"""

import pytest
from pathlib import Path
from datetime import datetime
from mf.core.file_manager import FileManager
from mf.core.hash_manager import HashManager
from mf.core.schema_manager import SchemaManager
from mf.core.git_engine import GitEngine


@pytest.fixture
def file_manager(tmp_path):
    """Create a FileManager instance for testing"""
    hash_mgr = HashManager(tmp_path)
    schema_mgr = SchemaManager(tmp_path)
    git_engine = GitEngine(tmp_path)
    return FileManager(tmp_path, hash_mgr, schema_mgr, git_engine)


def test_file_manager_create_file(file_manager):
    """Test file creation"""
    hash_id, file_path = file_manager.create_file(
        file_type="task",
        title="Test Task",
        content="Test content"
    )
    
    assert hash_id is not None
    assert len(hash_id) >= 6
    assert file_path.exists()
    assert file_path.name.startswith(hash_id)
    
    # Verify file content
    from mf.models.memo import Memo
    memo = Memo.from_file(file_path)
    assert memo.title == "Test Task"
    assert memo.type == "task"
    assert memo.status == "open"
    assert memo.content == "Test content"


def test_file_manager_create_file_invalid_type(file_manager):
    """Test file creation with invalid type"""
    with pytest.raises(ValueError, match="Invalid file type"):
        file_manager.create_file(
            file_type="invalid",
            title="Test"
        )


def test_file_manager_read_file(file_manager):
    """Test reading file by hash"""
    hash_id, file_path = file_manager.create_file(
        file_type="note",
        title="Test Note",
        content="Note content"
    )
    
    memo = file_manager.read_file(hash_id)
    assert memo.title == "Test Note"
    assert memo.type == "note"


def test_file_manager_read_file_not_found(file_manager):
    """Test reading non-existent file"""
    with pytest.raises(FileNotFoundError):
        file_manager.read_file("nonexistent")


def test_file_manager_update_file(file_manager):
    """Test updating file"""
    hash_id, file_path = file_manager.create_file(
        file_type="task",
        title="Original Title",
        content="Original content"
    )
    
    # Update content
    updated_memo = file_manager.update_file(
        hash_id,
        content="Updated content",
        frontmatter_updates={"status": "done"}
    )
    
    assert updated_memo.content == "Updated content"
    assert updated_memo.status == "done"


def test_file_manager_query(file_manager):
    """Test querying files"""
    # Create multiple files (all will be created with status="open" by default)
    file_manager.create_file("task", "Task 1")
    file_manager.create_file("note", "Note 1")
    file_manager.create_file("task", "Task 2")
    
    # Update one task to done
    all_files = file_manager.query()
    task_files = [f for f in all_files if f.type == "task"]
    if task_files:
        file_manager.update_file(task_files[0].uuid, frontmatter_updates={"status": "done"})
    
    # Query by status
    open_tasks = file_manager.query(status="open", file_type="task")
    assert len(open_tasks) >= 1
    
    # Query by type
    all_tasks = file_manager.query(file_type="task")
    assert len(all_tasks) >= 2


def test_file_manager_sanitize_filename(file_manager):
    """Test filename sanitization"""
    # Test with special characters
    safe = file_manager._sanitize_filename("Test/File:Name")
    assert "/" not in safe
    assert ":" not in safe
    
    # Test with long name
    long_name = "a" * 100
    safe = file_manager._sanitize_filename(long_name)
    assert len(safe) <= 50
