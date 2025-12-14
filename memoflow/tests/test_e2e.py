"""End-to-end tests for MemoFlow"""

import pytest
from pathlib import Path
from mf.commands.init import handle_init
from mf.commands.capture import handle_capture
from mf.commands.organize import handle_move
from mf.commands.engage import mark_finished
from mf.models.memo import Memo
from mf.core.git_engine import GitEngine


def test_e2e_workflow_init_capture_move_finish(tmp_path):
    """测试完整工作流：初始化 → 捕获 → 移动 → 完成"""
    # 1. 初始化
    handle_init(tmp_path)
    assert (tmp_path / ".mf").exists()
    assert (tmp_path / "schema.yaml").exists()
    assert (tmp_path / "00-Inbox").exists()
    assert (tmp_path / ".git").exists()
    
    # 2. 捕获
    hash_id, file_path = handle_capture("task", "Test task for E2E", tmp_path)
    assert file_path.exists()
    assert hash_id is not None
    
    # 验证文件内容
    memo = Memo.from_file(file_path)
    assert memo.type == "task"
    assert memo.title == "Test task for E2E"
    assert memo.status == "open"
    assert memo.id.startswith("HANK-00.")
    
    # 3. 移动
    old_id = memo.id
    new_file_path = handle_move(hash_id, old_id, "HANK-10.05", tmp_path)
    assert new_file_path.exists()
    assert not file_path.exists()  # 旧文件应被删除
    
    # 验证新位置
    new_memo = Memo.from_file(new_file_path)
    assert new_memo.id == "HANK-10.05"
    assert new_memo.uuid == hash_id  # UUID 不变
    
    # 4. 完成
    result = mark_finished(hash_id, tmp_path)
    assert result is True
    
    # 验证状态更新
    final_memo = Memo.from_file(new_file_path)
    assert final_memo.status == "done"


def test_e2e_git_commit_messages(tmp_path):
    """测试 Git 提交消息格式"""
    handle_init(tmp_path)
    
    # 捕获文件
    hash_id, _ = handle_capture("note", "Test note", tmp_path)
    
    # 检查提交消息
    git_engine = GitEngine(tmp_path)
    commits = list(git_engine.repo.iter_commits(max_count=2))
    
    # 应该有两个提交：init 和 capture
    assert len(commits) >= 2
    
    # 检查 capture 提交消息格式
    capture_commit = commits[0]  # 最新的提交
    assert "feat(new):" in capture_commit.message
    assert "capture" in capture_commit.message.lower()
    
    # 完成任务
    mark_finished(hash_id, tmp_path)
    
    # 检查 finish 提交消息（可能有多个提交，查找包含 hash 的）
    commits = list(git_engine.repo.iter_commits(max_count=5))
    finish_commit = None
    for commit in commits:
        if hash_id in commit.message and "mark as done" in commit.message.lower():
            finish_commit = commit
            break
    
    assert finish_commit is not None, "Should have a commit for finishing task"
    assert "feat(" in finish_commit.message or "docs(" in finish_commit.message


def test_e2e_file_system_structure(tmp_path):
    """测试文件系统结构"""
    handle_init(tmp_path)
    
    # 创建多个文件
    hash1, _ = handle_capture("task", "Task 1", tmp_path)
    hash2, _ = handle_capture("note", "Note 1", tmp_path)
    
    # 移动文件到不同位置
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
    
    memo1 = file_mgr.read_file(hash1)
    handle_move(hash1, memo1.id, "HANK-10.05", tmp_path)
    
    # 验证目录结构（默认schema使用三位小数格式：10.001-10.099）
    assert (tmp_path / "10-20").exists()
    assert (tmp_path / "10-20" / "10.001-10.099").exists()
    
    # 验证文件在正确位置
    moved_file = list((tmp_path / "10-20" / "10.001-10.099").glob("*.md"))
    assert len(moved_file) > 0
    assert hash1 in moved_file[0].name


def test_e2e_hash_index_consistency(tmp_path):
    """测试哈希索引一致性"""
    handle_init(tmp_path)
    
    # 创建文件
    hash_id, file_path = handle_capture("task", "Test", tmp_path)
    
    # 检查索引
    from mf.core.hash_manager import HashManager
    hash_mgr = HashManager(tmp_path)
    
    # 应该能在索引中找到
    paths = hash_mgr.resolve(hash_id)
    assert len(paths) == 1
    assert paths[0] == file_path
    
    # 移动文件后索引应该更新
    from mf.core.file_manager import FileManager
    from mf.core.schema_manager import SchemaManager
    from mf.core.git_engine import GitEngine
    
    file_mgr = FileManager(tmp_path, hash_mgr, SchemaManager(tmp_path), GitEngine(tmp_path))
    memo = file_mgr.read_file(hash_id)
    handle_move(hash_id, memo.id, "HANK-10.05", tmp_path)
    
    # 重新加载索引（因为 move 命令会更新索引）
    hash_mgr = HashManager(tmp_path)  # 重新加载
    new_paths = hash_mgr.resolve(hash_id)
    assert len(new_paths) == 1
    # 验证新路径包含目标目录（默认schema使用三位小数格式：10.001-10.099）
    assert "10-20" in str(new_paths[0]) or "10.001-10.099" in str(new_paths[0])


def test_e2e_view_commands(tmp_path):
    """测试视图命令输出"""
    handle_init(tmp_path)
    
    # 创建多个文件
    handle_capture("task", "Task 1", tmp_path)
    handle_capture("note", "Note 1", tmp_path)
    handle_capture("task", "Task 2", tmp_path)
    
    # 测试 status 视图
    from mf.views.status_view import show_status
    # 应该不抛出异常
    show_status(tmp_path)
    
    # 测试 list 视图
    from mf.views.list_view import show_list
    show_list(tmp_path, tree_format=True)
    show_list(tmp_path, tree_format=False)
    
    # 测试 timeline 视图
    from mf.views.timeline_view import show_timeline
    show_timeline(tmp_path, since="1 day ago")
    
    # 测试 calendar 视图
    from mf.views.calendar_view import show_calendar
    show_calendar(tmp_path)


def test_e2e_ci_commands(tmp_path):
    """测试 CI 命令"""
    handle_init(tmp_path)
    
    # 创建文件
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
    
    hash_id, _ = file_mgr.create_file("task", "Today's task", "")
    from datetime import datetime
    file_mgr.update_file(hash_id, frontmatter_updates={"due_date": datetime.now().isoformat()})
    
    # 测试 morning CI
    from mf.commands.ci import handle_ci
    morning_report = handle_ci("morning", tmp_path)
    assert "今日聚焦" in morning_report
    assert "Today's task" in morning_report or "task" in morning_report.lower()
    
    # 测试 evening CI
    evening_report = handle_ci("evening", tmp_path)
    assert "今日复盘" in evening_report
    assert "统计" in evening_report
