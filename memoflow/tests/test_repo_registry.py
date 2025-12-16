"""Tests for RepoRegistry (namespace management)."""

from pathlib import Path

from mf.core.repo_registry import RepoRegistry, RegisteredRepo


def test_repo_registry_add_and_list(tmp_path):
    registry_file = tmp_path / "repos.json"
    registry = RepoRegistry(registry_file=registry_file)

    repo_path = tmp_path / "repo1"
    repo_path.mkdir()

    registry.add_repo("repo1", repo_path)
    repos = registry.list_repos()

    assert len(repos) == 1
    assert repos[0].name == "repo1"
    assert repos[0].path == repo_path.resolve()


def test_repo_registry_prevent_duplicate_name_or_path(tmp_path):
    registry_file = tmp_path / "repos.json"
    registry = RepoRegistry(registry_file=registry_file)

    repo1 = tmp_path / "repo1"
    repo2 = tmp_path / "repo2"
    repo1.mkdir()
    repo2.mkdir()

    registry.add_repo("same", repo1)
    # 同名不同路径：应忽略第二个
    registry.add_repo("same", repo2)

    repos = registry.list_repos()
    assert len(repos) == 1
    assert repos[0].path == repo1.resolve()

    # 不同名同路径：也应忽略第二个
    registry.add_repo("other", repo1)
    repos2 = registry.list_repos()
    assert len(repos2) == 1


def test_repo_registry_get_and_find(tmp_path):
    registry_file = tmp_path / "repos.json"
    registry = RepoRegistry(registry_file=registry_file)

    repo_path = tmp_path / "repo1"
    repo_path.mkdir()
    registry.add_repo("repo1", repo_path)

    by_name = registry.get_by_name("repo1")
    assert isinstance(by_name, RegisteredRepo)
    assert by_name.path == repo_path.resolve()

    by_path = registry.find_by_path(repo_path)
    assert by_path is not None
    assert by_path.name == "repo1"


def test_repo_registry_remove(tmp_path):
    registry_file = tmp_path / "repos.json"
    registry = RepoRegistry(registry_file=registry_file)

    repo1 = tmp_path / "repo1"
    repo2 = tmp_path / "repo2"
    repo1.mkdir()
    repo2.mkdir()

    registry.add_repo("r1", repo1)
    registry.add_repo("r2", repo2)

    assert registry.remove_by_name("r1") is True
    assert registry.get_by_name("r1") is None

    assert registry.remove_by_path(repo2) is True
    assert registry.get_by_name("r2") is None

    # Removing again should be a no-op
    assert registry.remove_by_name("r1") is False
    assert registry.remove_by_path(repo2) is False
