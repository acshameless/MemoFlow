"""Tests for Git Engine"""

import pytest
from pathlib import Path
from mf.core.git_engine import GitEngine, CommitType


def test_git_engine_init(tmp_path):
    """Test GitEngine initialization"""
    engine = GitEngine(tmp_path)
    
    assert engine.repo_path == tmp_path.resolve()
    assert engine.repo is not None
    # Git should be initialized
    assert (tmp_path / ".git").exists()


def test_git_engine_auto_commit(tmp_path):
    """Test auto commit"""
    engine = GitEngine(tmp_path)
    
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    # Commit
    commit_sha = engine.auto_commit(
        CommitType.FEAT,
        "new",
        "test commit",
        [test_file]
    )
    
    assert commit_sha is not None
    assert len(commit_sha) == 40  # SHA length
    
    # Check commit message
    commits = list(engine.repo.iter_commits(max_count=1))
    assert len(commits) > 0
    assert "feat(new): test commit" in commits[0].message


def test_git_engine_parse_timeline(tmp_path):
    """Test timeline parsing"""
    engine = GitEngine(tmp_path)
    
    # Create and commit a file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")
    engine.auto_commit(CommitType.FEAT, "abc123", "test message", [test_file])
    
    # Parse timeline (get all commits since it's a new repo)
    timeline = engine.parse_timeline(since="1 day ago")
    
    # Should have at least the commit we just made (and possibly init commit)
    assert len(timeline) > 0
    
    # Find our commit
    our_commit = None
    for entry in timeline:
        if entry.get("scope") == "abc123" and "test message" in entry.get("message", ""):
            our_commit = entry
            break
    
    assert our_commit is not None
    assert our_commit["type"] == "feat"
    assert our_commit["scope"] == "abc123"
