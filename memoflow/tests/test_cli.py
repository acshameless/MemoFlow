"""Tests for CLI module"""

from typer.testing import CliRunner

from mf.cli import app
from mf.core.repo_registry import RepoRegistry

runner = CliRunner()


def test_cli_app_exists():
    """Test that CLI app is properly initialized"""
    assert app is not None
    assert hasattr(app, "command")


def test_version_function_exists():
    """Test that version function can be imported"""
    from mf import __version__

    assert __version__ == "0.1.0"


def test_repo_list_and_info_flow(tmp_path):
    """End-to-end test for repo list/info commands."""
    registry = RepoRegistry()
    # 清理可能存在的旧记录以避免命名冲突
    registry.remove_by_name("my_repo")

    # 初始化新的 repo
    repo_root = tmp_path / "my_repo"
    repo_root.mkdir()
    result_init = runner.invoke(app, ["init", str(repo_root)])
    assert result_init.exit_code == 0

    # repo list 应该包含 my_repo
    result_list = runner.invoke(app, ["repo", "list"])
    assert result_list.exit_code == 0
    assert "my_repo" in result_list.stdout

    # repo info by name
    result_info = runner.invoke(app, ["repo", "info", "my_repo"])
    assert result_info.exit_code == 0
    assert "Repo name   : my_repo" in result_info.stdout
    assert "User prefix :" in result_info.stdout


def test_repo_rm_command(tmp_path):
    """End-to-end test for repo rm command."""
    registry = RepoRegistry()
    registry.remove_by_name("to_remove")

    # 手动创建一个 MemoFlow 仓库结构并注册
    repo_root = tmp_path / "to_remove"
    repo_root.mkdir()
    (repo_root / ".mf").mkdir()
    (repo_root / "00-Inbox").mkdir()
    (repo_root / "schema.yaml").write_text("user_prefix: AC\nareas: []\n", encoding="utf-8")

    registry.add_repo("to_remove", repo_root)

    # 运行 repo rm
    result_rm = runner.invoke(app, ["repo", "rm", "to_remove", "--yes"])
    assert result_rm.exit_code == 0
    assert "Removed MemoFlow data" in result_rm.stdout

    # 资源应被删除
    assert not (repo_root / ".mf").exists()
    assert not (repo_root / "schema.yaml").exists()
    assert not (repo_root / "00-Inbox").exists()

    # 注册表中不再存在该条目
    registry_after = RepoRegistry()
    repos_after = registry_after.list_repos()
    assert all(r.name != "to_remove" for r in repos_after)
