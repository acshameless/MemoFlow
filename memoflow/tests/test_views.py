"""Tests for view modules"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
from mf.views.status_view import show_status
from mf.views.timeline_view import show_timeline
from mf.views.calendar_view import show_calendar
from mf.views.list_view import show_list


def test_status_view(tmp_path, capsys):
    """Test status view"""
    from mf.commands.init import handle_init
    from mf.commands.capture import handle_capture
    
    # Initialize and create files
    handle_init(tmp_path)
    handle_capture("task", "Test Task 1", tmp_path)
    handle_capture("note", "Test Note 1", tmp_path)
    
    # Show status
    show_status(tmp_path)
    
    # Check output contains expected information
    # (We can't easily test rich output, but we can verify it doesn't crash)


def test_timeline_view(tmp_path, capsys):
    """Test timeline view"""
    from mf.commands.init import handle_init
    from mf.commands.capture import handle_capture
    
    # Initialize and create files
    handle_init(tmp_path)
    handle_capture("task", "Test Task", tmp_path)
    
    # Show timeline
    show_timeline(tmp_path, since="1 day ago")
    
    # Verify it doesn't crash


def test_calendar_view(tmp_path, capsys):
    """Test calendar view"""
    from mf.commands.init import handle_init
    from mf.core.file_manager import FileManager
    from mf.core.hash_manager import HashManager
    from mf.core.schema_manager import SchemaManager
    from mf.core.git_engine import GitEngine
    
    # Initialize
    handle_init(tmp_path)
    
    # Create a file with due date
    hash_mgr = HashManager(tmp_path)
    schema_mgr = SchemaManager(tmp_path)
    git_engine = GitEngine(tmp_path)
    file_mgr = FileManager(tmp_path, hash_mgr, schema_mgr, git_engine)
    
    hash_id, _ = file_mgr.create_file("task", "Task with due date", "")
    
    # Add due date
    tomorrow = datetime.now() + timedelta(days=1)
    file_mgr.update_file(hash_id, frontmatter_updates={"due_date": tomorrow.isoformat()})
    
    # Show calendar
    show_calendar(tmp_path)
    
    # Verify it doesn't crash


def test_list_view(tmp_path, capsys):
    """Test list view"""
    from mf.commands.init import handle_init
    from mf.commands.capture import handle_capture
    
    # Initialize and create files
    handle_init(tmp_path)
    handle_capture("task", "Test Task", tmp_path)
    handle_capture("note", "Test Note", tmp_path)
    
    # Show list
    show_list(tmp_path, tree_format=True)
    show_list(tmp_path, tree_format=False)
    
    # Verify it doesn't crash
