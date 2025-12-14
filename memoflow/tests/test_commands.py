"""Tests for CLI commands"""

import pytest
from pathlib import Path
from mf.commands.capture import handle_capture
from mf.commands.organize import handle_move, handle_rebuild_index
from mf.commands.engage import mark_finished
from mf.commands.init import handle_init


def test_init_command(tmp_path):
    """Test init command"""
    result = handle_init(tmp_path)
    assert result is True
    
    # Check that directories and files are created
    assert (tmp_path / ".mf").exists()
    assert (tmp_path / "schema.yaml").exists()
    assert (tmp_path / "00-Inbox").exists()
    assert (tmp_path / ".git").exists()


def test_init_command_already_initialized(tmp_path):
    """Test init command when already initialized"""
    handle_init(tmp_path)
    
    # Should raise error without force
    with pytest.raises(ValueError, match="already initialized"):
        handle_init(tmp_path, force=False)
    
    # Should work with force
    result = handle_init(tmp_path, force=True)
    assert result is True


def test_capture_command(tmp_path):
    """Test capture command"""
    # Initialize first
    handle_init(tmp_path)
    
    # Capture a note
    hash_id, file_path = handle_capture(
        file_type="note",
        content="Test note content",
        repo_root=tmp_path
    )
    
    assert hash_id is not None
    assert file_path.exists()
    assert file_path.name.startswith(hash_id)
    
    # Verify content
    from mf.models.memo import Memo
    memo = Memo.from_file(file_path)
    assert memo.type == "note"
    assert "Test note" in memo.title or "note content" in memo.content


def test_capture_command_invalid_type(tmp_path):
    """Test capture command with invalid type"""
    handle_init(tmp_path)
    
    with pytest.raises(ValueError, match="Invalid file type"):
        handle_capture("invalid", "content", tmp_path)


def test_move_command(tmp_path):
    """Test move command"""
    # Initialize and create a file
    handle_init(tmp_path)
    hash_id, old_file = handle_capture("note", "Test content", tmp_path)
    
    # Get the old path from the file
    from mf.models.memo import Memo
    memo = Memo.from_file(old_file)
    old_path = memo.id
    
    # Move to new location
    new_file = handle_move(hash_id, old_path, "HANK-10.05", tmp_path)
    
    assert new_file.exists()
    assert new_file != old_file
    assert not old_file.exists()  # Old file should be deleted
    
    # Verify new path
    new_memo = Memo.from_file(new_file)
    assert new_memo.id == "HANK-10.05"


def test_move_command_invalid_path(tmp_path):
    """Test move command with invalid path"""
    handle_init(tmp_path)
    hash_id, _ = handle_capture("note", "Test", tmp_path)
    
    from mf.models.memo import Memo
    from mf.core.file_manager import FileManager
    from mf.core.hash_manager import HashManager
    from mf.core.schema_manager import SchemaManager
    from mf.core.git_engine import GitEngine
    
    file_mgr = FileManager(
        tmp_path,
        HashManager(tmp_path),
        SchemaManager(tmp_path),
        GitEngine(tmp_path)
    )
    memo = file_mgr.read_file(hash_id)
    
    with pytest.raises(ValueError, match="Invalid target path"):
        handle_move(hash_id, memo.id, "INVALID-99.99", tmp_path)


def test_finish_command(tmp_path):
    """Test finish command"""
    # Initialize and create a task
    handle_init(tmp_path)
    hash_id, _ = handle_capture("task", "Test task", tmp_path)
    
    # Mark as finished
    result = mark_finished(hash_id, tmp_path)
    assert result is True
    
    # Verify status
    from mf.core.file_manager import FileManager
    from mf.core.hash_manager import HashManager
    from mf.core.schema_manager import SchemaManager
    from mf.core.git_engine import GitEngine
    
    file_mgr = FileManager(
        tmp_path,
        HashManager(tmp_path),
        SchemaManager(tmp_path),
        GitEngine(tmp_path)
    )
    memo = file_mgr.read_file(hash_id)
    assert memo.status == "done"


def test_finish_command_already_done(tmp_path):
    """Test finish command when already done"""
    handle_init(tmp_path)
    hash_id, _ = handle_capture("task", "Test", tmp_path)
    
    # Mark as finished twice
    result1 = mark_finished(hash_id, tmp_path)
    result2 = mark_finished(hash_id, tmp_path)
    
    assert result1 is True
    assert result2 is False  # Already done


def test_rebuild_index_command(tmp_path):
    """Test rebuild-index command"""
    handle_init(tmp_path)
    
    # Create some files
    handle_capture("note", "Note 1", tmp_path)
    handle_capture("task", "Task 1", tmp_path)
    
    # Rebuild index
    count = handle_rebuild_index(tmp_path)
    assert count >= 2
