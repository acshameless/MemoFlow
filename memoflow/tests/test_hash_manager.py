"""Tests for Hash Manager"""

import pytest
from pathlib import Path
from mf.core.hash_manager import HashManager


def test_hash_manager_init(tmp_path):
    """Test HashManager initialization"""
    mgr = HashManager(tmp_path)
    assert mgr.repo_root == tmp_path.resolve()
    assert mgr.index_file == tmp_path / ".mf" / "hash_index.json"


def test_hash_generation(tmp_path):
    """Test hash generation"""
    mgr = HashManager(tmp_path)
    
    # Generate multiple hashes
    hashes = {mgr.generate_hash() for _ in range(100)}
    assert len(hashes) == 100  # 无碰撞


def test_hash_register(tmp_path):
    """Test hash registration"""
    mgr = HashManager(tmp_path)
    test_file = tmp_path / "test.md"
    test_file.touch()
    
    mgr.register("7f9a2b", test_file, "HANK-12.04")
    
    assert "7f9a2b" in mgr.index
    assert mgr.index["7f9a2b"]["id"] == "HANK-12.04"


def test_hash_resolve(tmp_path):
    """Test hash resolution with partial matching"""
    mgr = HashManager(tmp_path)
    test_file = tmp_path / "test.md"
    test_file.touch()
    
    mgr.register("7f9a2b", test_file, "HANK-12.04")
    
    # Exact match
    paths = mgr.resolve("7f9a2b")
    assert len(paths) == 1
    assert paths[0] == test_file
    
    # Partial match
    paths = mgr.resolve("7f9")
    assert len(paths) == 1
    
    paths = mgr.resolve("7f9a")
    assert len(paths) == 1


def test_hash_resolve_not_found(tmp_path):
    """Test hash resolution when not found"""
    mgr = HashManager(tmp_path)
    
    with pytest.raises(FileNotFoundError):
        mgr.resolve("nonexistent")


def test_hash_resolve_ambiguous(tmp_path):
    """Test hash resolution with ambiguous matches"""
    mgr = HashManager(tmp_path)
    file1 = tmp_path / "file1.md"
    file2 = tmp_path / "file2.md"
    file1.touch()
    file2.touch()
    
    mgr.register("7f9a2b", file1)
    mgr.register("7f9a3c", file2)
    
    # Partial match with multiple results
    paths = mgr.resolve("7f9a")
    assert len(paths) == 2


def test_hash_update_path(tmp_path):
    """Test updating hash path"""
    mgr = HashManager(tmp_path)
    old_file = tmp_path / "old.md"
    new_file = tmp_path / "new.md"
    old_file.touch()
    new_file.touch()
    
    mgr.register("7f9a2b", old_file, "HANK-00.01")
    mgr.update_path("7f9a2b", new_file, "HANK-12.04")
    
    assert mgr.index["7f9a2b"]["id"] == "HANK-12.04"
    assert "new.md" in mgr.index["7f9a2b"]["path"]


def test_hash_rebuild_index(tmp_path):
    """Test rebuilding index"""
    from mf.models.memo import Memo
    import frontmatter
    
    # Create test markdown files
    file1 = tmp_path / "file1.md"
    file2 = tmp_path / "file2.md"
    
    post1 = frontmatter.Post("Content 1", uuid="abc123", id="HANK-10.01", 
                            type="note", title="Test 1", status="open",
                            created_at="2023-01-01T00:00:00")
    post2 = frontmatter.Post("Content 2", uuid="def456", id="HANK-10.02",
                            type="task", title="Test 2", status="open",
                            created_at="2023-01-02T00:00:00")
    
    file1.write_text(frontmatter.dumps(post1), encoding='utf-8')
    file2.write_text(frontmatter.dumps(post2), encoding='utf-8')
    
    mgr = HashManager(tmp_path)
    count = mgr.rebuild_index()
    
    assert count == 2
    assert "abc123" in mgr.index
    assert "def456" in mgr.index
