"""Tests for CI commands"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
from mf.commands.ci import handle_ci


def test_ci_morning_mode(tmp_path):
    """Test CI morning mode"""
    from mf.commands.init import handle_init
    from mf.core.file_manager import FileManager
    from mf.core.hash_manager import HashManager
    from mf.core.schema_manager import SchemaManager
    from mf.core.git_engine import GitEngine
    
    # Initialize
    handle_init(tmp_path)
    
    # Create tasks
    hash_mgr = HashManager(tmp_path)
    schema_mgr = SchemaManager(tmp_path)
    git_engine = GitEngine(tmp_path)
    file_mgr = FileManager(tmp_path, hash_mgr, schema_mgr, git_engine)
    
    # Create task with due date today
    hash_id, _ = file_mgr.create_file("task", "Today's task", "")
    today = datetime.now()
    file_mgr.update_file(hash_id, frontmatter_updates={"due_date": today.isoformat()})
    
    # Generate morning report
    report = handle_ci("morning", tmp_path)
    
    assert "今日聚焦" in report
    assert "Today's task" in report
    assert hash_id in report


def test_ci_evening_mode(tmp_path):
    """Test CI evening mode"""
    from mf.commands.init import handle_init
    from mf.commands.capture import handle_capture
    from mf.commands.engage import mark_finished
    
    # Initialize and create files
    handle_init(tmp_path)
    hash_id, _ = handle_capture("task", "Test task", tmp_path)
    mark_finished(hash_id, tmp_path)
    
    # Generate evening report
    report = handle_ci("evening", tmp_path)
    
    assert "今日复盘" in report
    assert "统计" in report


def test_ci_invalid_mode(tmp_path):
    """Test CI with invalid mode"""
    from mf.commands.init import handle_init
    handle_init(tmp_path)
    
    with pytest.raises(ValueError, match="Invalid mode"):
        handle_ci("invalid", tmp_path)
