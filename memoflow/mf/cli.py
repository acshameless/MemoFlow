"""CLI entry point for MemoFlow"""

import typer
from pathlib import Path
from typing import Optional

try:
    from typing import Annotated
except ImportError:
    try:
        from typing_extensions import Annotated
    except ImportError:
        # Fallback for older Python versions
        Annotated = lambda x, **kwargs: x

app = typer.Typer(
    name="mf",
    help="MemoFlow - Your Second Brain",
    add_completion=False,
    no_args_is_help=False,  # 设置为 False，让无参数时执行 callback 启动 TUI
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)

# Sub-app for repo management
repo_app = typer.Typer(
    name="repo",
    help="Manage MemoFlow repositories (list, info, etc.)",
)
app.add_typer(repo_app, name="repo")

# 全局上下文，用于存储 --repo 选项
_global_repo: Optional[str] = None


def get_repo_root(repo_path: Optional[str] = None) -> Path:
    """获取仓库根目录
    
    Args:
        repo_path: 仓库路径（可以是相对路径、绝对路径或子仓库名称）
    
    Returns:
        仓库根目录路径
    """
    # 优先使用传入的 repo_path
    if repo_path:
        repo_path_obj = Path(repo_path)
        
        # 如果是绝对路径，直接使用
        if repo_path_obj.is_absolute():
            if (repo_path_obj / ".mf").exists() or (repo_path_obj / "schema.yaml").exists():
                return repo_path_obj
            raise ValueError(f"Repository not found at {repo_path_obj}")
        
        # 如果是相对路径，从当前目录查找
        current = Path.cwd()
        candidate = (current / repo_path_obj).resolve()
        
        # 检查候选路径是否是仓库
        if candidate.exists() and ((candidate / ".mf").exists() or (candidate / "schema.yaml").exists()):
            return candidate
        
        # 如果直接路径不存在，尝试在当前目录的子目录中递归查找
        def find_repo_in_dir(directory: Path, target_name: str, max_depth: int = 3) -> Optional[Path]:
            """递归查找仓库"""
            if max_depth <= 0:
                return None
            for item in directory.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # 检查是否是目标仓库
                    if item.name == target_name:
                        if (item / ".mf").exists() or (item / "schema.yaml").exists():
                            return item.resolve()
                    # 递归查找子目录
                    found = find_repo_in_dir(item, target_name, max_depth - 1)
                    if found:
                        return found
            return None
        
        if current.is_dir():
            found = find_repo_in_dir(current, repo_path)
            if found:
                return found
        
        raise ValueError(f"Repository not found: {repo_path}")
    
    # 如果没有指定 repo_path，使用默认查找逻辑
    current = Path.cwd()
    
    # 优先检查当前目录（支持嵌套仓库）
    if (current / ".mf").exists() or (current / "schema.yaml").exists():
        return current
    
    # 如果当前目录不是仓库，向上查找
    for path in current.parents:
        if (path / ".mf").exists() or (path / "schema.yaml").exists():
            return path
    
    # 如果没找到，使用当前目录
    return current


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    repo: Optional[str] = typer.Option(
        None,
        "--repo",
        "-r",
        help="Repository path or name (e.g., 'test_repo', 'test_repo/sub_repo')",
        hidden=True,
    ),
    editor: Optional[str] = typer.Option(
        None,
        "--editor",
        "-e",
        help="External editor command (e.g., typora, code, vim). Overrides repository config.",
    ),
):
    """MemoFlow - Your Second Brain
    
    Run 'mf' without arguments to launch the interactive TUI dashboard.
    Use 'mf <command>' for specific operations.
    """
    global _global_repo
    if repo:
        _global_repo = repo
    
    # 如果没有命令，启动 TUI
    if ctx.invoked_subcommand is None:
        repo_path = repo or _global_repo
        repo_root = get_repo_root(repo_path)
        
        try:
            from mf.views.status_tui import show_status_tui
            show_status_tui(repo_root, editor=editor)
        except ImportError:
            typer.echo("✗ Textual library not installed. Install with: pip install 'memoflow[tui]'", err=True)
            typer.echo("\nFor static status output, use: mf status", err=True)
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"✗ Failed to start TUI: {e}", err=True)
            typer.echo("\nFor static status output, use: mf status", err=True)
            raise typer.Exit(1)


@app.command()
def version():
    """Show version information"""
    from mf import __version__
    typer.echo(f"MemoFlow version {__version__}")


@app.command()
def init(
    path: Optional[str] = typer.Argument(None, help="Repository path (default: current directory)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinitialization"),
    preserve_schema: bool = typer.Option(True, "--preserve-schema/--no-preserve-schema", help="Preserve existing schema.yaml when reinitializing (default: True)"),
    editor: Optional[str] = typer.Option(None, "--editor", "-e", help="Default editor for opening markdown files (vim, typora, code, notepad, etc.). If not specified, auto-detect."),
):
    """Initialize a new MemoFlow repository
    
    Examples:
        mf init                    # Initialize in current directory
        mf init my_repo            # Initialize in my_repo directory
        mf init --force            # Reinitialize, preserving schema if valid
        mf init --editor vim       # Initialize with vim as default editor
        mf init --editor typora    # Initialize with typora as default editor
    """
    from mf.commands.init import handle_init
    
    repo_root = Path(path).resolve() if path else Path.cwd()
    
    try:
        handle_init(repo_root, force=force, preserve_schema=preserve_schema, editor=editor)
        typer.echo(f"✓ Initialized MemoFlow repository at {repo_root}")
        if editor:
            typer.echo(f"✓ Configured default editor: {editor}")
    except ValueError as e:
        typer.echo(f"✗ Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"✗ Failed to initialize: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="capture", hidden=True)
def capture(
    content: str = typer.Argument(..., help="Content to capture"),
    type: Optional[str] = typer.Option(None, "-t", "--type", help="File type (meeting, note, task, email). If not specified, creates untyped file in inbox"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository path (overrides global --repo)"),
):
    """Quick capture: mf capture -t task "Fix bug #123" or mf capture "Quick note"
    
    Note: This command is also available in interactive TUI (run 'mf' and press 'n' key).
    Use CLI for scripting/automation, use TUI for interactive use.
    """
    from mf.commands.capture import handle_capture
    
    # 优先使用命令级别的 --repo，否则使用全局 --repo
    repo_path = repo or _global_repo
    repo_root = get_repo_root(repo_path)
    
    try:
        hash_id, file_path = handle_capture(type, content, repo_root)
        if type:
            typer.echo(f"✓ Captured: {file_path.name} (hash: {hash_id}, type: {type})")
        else:
            typer.echo(f"✓ Captured: {file_path.name} (hash: {hash_id}, untyped)")
    except ValueError as e:
        typer.echo(f"✗ Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"✗ Failed to capture: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="new")
def new(
    content: str = typer.Argument(..., help="Content to capture"),
    type: Optional[str] = typer.Option(None, "-t", "--type", help="File type (meeting, note, task, email). If not specified, creates untyped file in inbox"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository path (overrides global --repo)"),
):
    """Quick capture (alias): mf new -t task "Fix bug #123" or mf new "Quick note" """
    # 调用 capture 命令的处理逻辑
    capture(content, type, repo)


@app.command(name="move", hidden=True)
def move(
    hash: str = typer.Argument(..., help="File hash (supports partial match)"),
    old_path: str = typer.Argument(..., help="Old path (JD ID or relative path)"),
    new_path: str = typer.Argument(..., help="New path (JD ID or relative path)"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository path (overrides global --repo)"),
):
    """Move file: mf move 7f9a HANK-00.01 HANK-12.04
    
    Note: This command is also available in interactive TUI (run 'mf' and press 'm' key).
    Use CLI for scripting/automation, use TUI for interactive use.
    """
    from mf.commands.organize import handle_move
    
    repo_path = repo or _global_repo
    repo_root = get_repo_root(repo_path)
    
    try:
        new_file_path = handle_move(hash, old_path, new_path, repo_root)
        typer.echo(f"✓ Moved to: {new_file_path}")
    except ValueError as e:
        typer.echo(f"✗ Error: {e}", err=True)
        raise typer.Exit(1)
    except FileNotFoundError as e:
        typer.echo(f"✗ File not found: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"✗ Failed to move: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="mv")
def mv(
    hash: str = typer.Argument(..., help="File hash (supports partial match)"),
    old_path: str = typer.Argument(..., help="Old path (JD ID or relative path)"),
    new_path: str = typer.Argument(..., help="New path (JD ID or relative path)"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository path (overrides global --repo)"),
):
    """Move file (alias): mf mv 7f9a HANK-00.01 HANK-12.04"""
    # 调用 move 命令的处理逻辑
    move(hash, old_path, new_path, repo)


@app.command()
def finish(
    hash: str = typer.Argument(..., help="File hash"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository path (overrides global --repo)"),
):
    """Mark task as done: mf finish 7f9a
    
    Note: This command is also available in interactive TUI (run 'mf' and press 'f' key).
    Use CLI for scripting/automation, use TUI for interactive use.
    """
    from mf.commands.engage import mark_finished
    
    repo_path = repo or _global_repo
    repo_root = get_repo_root(repo_path)
    
    try:
        result = mark_finished(hash, repo_root)
        if result:
            typer.echo(f"✓ Marked {hash} as done")
        else:
            typer.echo(f"ℹ File {hash} is already done")
    except FileNotFoundError as e:
        typer.echo(f"✗ File not found: {e}", err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(f"✗ Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"✗ Failed to finish: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def type(
    hash: str = typer.Argument(..., help="File hash (supports partial match)"),
    new_type: str = typer.Argument(..., help="New type (task, meeting, note, email)"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository path (overrides global --repo)"),
):
    """Change file type: mf type 7f9a task
    
    Note: This command is also available in interactive TUI (run 'mf' and press 'c' key).
    Use CLI for scripting/automation, use TUI for interactive use.
    """
    from mf.commands.update import handle_update_type
    
    repo_path = repo or _global_repo
    repo_root = get_repo_root(repo_path)
    
    try:
        result = handle_update_type(hash, new_type, repo_root)
        if result:
            typer.echo(f"✓ Updated {hash} type to {new_type}")
        else:
            typer.echo(f"ℹ File {hash} is already type {new_type}")
    except ValueError as e:
        typer.echo(f"✗ Error: {e}", err=True)
        raise typer.Exit(1)
    except FileNotFoundError as e:
        typer.echo(f"✗ File not found: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"✗ Failed to update type: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def rebuild_index(
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository path (overrides global --repo)"),
):
    """Rebuild hash index
    
    Note: This command is also available in interactive TUI (run 'mf' and press 'R' key).
    Use CLI for scripting/automation, use TUI for interactive use.
    """
    from mf.commands.organize import handle_rebuild_index
    
    repo_path = repo or _global_repo
    repo_root = get_repo_root(repo_path)
    
    try:
        count = handle_rebuild_index(repo_root)
        typer.echo(f"✓ Rebuilt index with {count} files")
    except Exception as e:
        typer.echo(f"✗ Failed to rebuild index: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def migrate_prefix(
    old_prefix: str = typer.Argument(..., help="Old user prefix (e.g., 'HANK')"),
    new_prefix: str = typer.Argument(..., help="New user prefix (e.g., 'AC')"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository path (overrides global --repo)"),
):
    """Update all file IDs to use new user prefix: mf migrate-prefix HANK AC
    
    This command updates the 'id' field in all memo files from old prefix to new prefix.
    For example, HANK-11.001 becomes AC-11.001.
    """
    from mf.commands.migrate import handle_update_prefix
    
    repo_path = repo or _global_repo
    repo_root = get_repo_root(repo_path)
    
    try:
        count = handle_update_prefix(old_prefix, new_prefix, repo_root)
        typer.echo(f"✓ Updated {count} files from {old_prefix} to {new_prefix}")
    except Exception as e:
        typer.echo(f"✗ Failed to migrate prefix: {e}", err=True)
        raise typer.Exit(1)




@app.command()
def status(
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository path (overrides global --repo)"),
    limit: Optional[int] = typer.Option(None, "--limit", "-n", help="Limit number of files to display (default: 20)"),
    all: bool = typer.Option(False, "--all", "-a", help="Show all files"),
    type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by file type (task, meeting, note, email)"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (open, done)"),
):
    """Show repository statistics and file list
    
    Displays a summary of repository statistics (Inbox count, open tasks, etc.)
    and a table of files. For interactive TUI mode, run 'mf' without arguments.

    Examples:
      mf status                    # Show statistics and file list (default: 20 files)
      mf status --all              # Show all files
      mf status --limit 50         # Show 50 most recent files
      mf status --type task         # Show only tasks
      mf status --status open      # Show only open files
      mf status --type task --status open  # Show only open tasks
    """
    repo_path = repo or _global_repo
    repo_root = get_repo_root(repo_path)
    
    from mf.views.status_view import show_status
    
    # 验证过滤选项
    if type and type not in ["task", "meeting", "note", "email"]:
        typer.echo(f"✗ Invalid type: {type}. Must be one of: task, meeting, note, email", err=True)
        raise typer.Exit(1)
    
    if status and status not in ["open", "done"]:
        typer.echo(f"✗ Invalid status: {status}. Must be one of: open, done", err=True)
        raise typer.Exit(1)
    
    try:
        show_status(repo_root, limit=limit, show_all=all, type_filter=type, status_filter=status)
    except Exception as e:
        typer.echo(f"✗ Failed to show status: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def ci(
    mode: str = typer.Option(..., "--mode", help="Mode: morning or evening"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository path (overrides global --repo)"),
):
    """CI command for GitHub Actions: mf ci --mode morning"""
    from mf.commands.ci import handle_ci
    
    repo_path = repo or _global_repo
    repo_root = get_repo_root(repo_path)
    
    try:
        report = handle_ci(mode, repo_root)
        # 输出报告（供 GitHub Actions 使用）
        print(report)
    except ValueError as e:
        typer.echo(f"✗ Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"✗ Failed to generate report: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="schema")
def schema_cmd(
    action: str = typer.Argument(..., help="Action: 'reload' to reload schema, 'validate' to validate schema"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository path (overrides global --repo)"),
):
    """Manage schema: mf schema reload or mf schema validate"""
    from mf.commands.schema import handle_schema_reload, handle_schema_validate
    
    repo_path = repo or _global_repo
    repo_root = get_repo_root(repo_path)
    
    try:
        if action == "reload":
            handle_schema_reload(repo_root)
            typer.echo("✓ Schema reloaded successfully")
        elif action == "validate":
            handle_schema_validate(repo_root)
            typer.echo("✓ Schema is valid")
        else:
            typer.echo(f"✗ Invalid action: {action}. Use 'reload' or 'validate'", err=True)
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"✗ Failed: {e}", err=True)
        raise typer.Exit(1)


@repo_app.command(name="list")
def repo_list():
    """List registered MemoFlow repositories."""
    from mf.core.repo_registry import RepoRegistry

    registry = RepoRegistry()
    repos = registry.list_repos()
    if not repos:
        typer.echo("No repositories registered yet. Initialize one with 'mf init'.")
        return

    typer.echo("Registered MemoFlow repositories:")
    for repo in repos:
        typer.echo(f"  {repo.name:15} {repo.path}")


@repo_app.command(name="info")
def repo_info(
    name: Optional[str] = typer.Argument(
        None,
        help="Repository name (from registry). If omitted, uses --repo/-r or current directory.",
    ),
    repo: Optional[str] = typer.Option(
        None,
        "--repo",
        "-r",
        help="Repository path or name (overrides global --repo)",
    ),
):
    """Show detailed information about a MemoFlow repository."""
    from mf.core.repo_registry import RepoRegistry
    from mf.core.schema_manager import SchemaManager
    from mf.core.hash_manager import HashManager
    from mf.core.git_engine import GitEngine
    from mf.core.file_manager import FileManager

    registry = RepoRegistry()

    # 1) 优先使用 name 参数（注册名称）
    repo_root: Optional[Path] = None
    repo_name: Optional[str] = None

    if name:
        registered = registry.get_by_name(name)
        if not registered:
            typer.echo(f"✗ Repo '{name}' not found in registry", err=True)
            raise typer.Exit(1)
        repo_root = registered.path
        repo_name = registered.name
    else:
        # 2) 其次使用 --repo/-r 或全局 _global_repo
        repo_path = repo or _global_repo
        if repo_path:
            repo_root = get_repo_root(repo_path)
        else:
            repo_root = get_repo_root(None)

        registered = registry.find_by_path(repo_root)
        if registered:
            repo_name = registered.name
        else:
            # 未在注册表中，使用目录名作为名称并自动注册
            repo_root = repo_root.resolve()
            repo_name = repo_root.name
            try:
                registry.add_repo(repo_name, repo_root)
            except Exception as e:
                typer.echo(f"⚠ Failed to register repo in registry: {e}", err=True)

    repo_root = repo_root.resolve()

    # 收集基本信息
    try:
        schema_mgr = SchemaManager(repo_root)
        schema = schema_mgr.load_schema()
        prefix = schema.user_prefix
        areas_count = len(schema.areas)
        categories_count = sum(len(a.categories) for a in schema.areas)
    except Exception as e:
        typer.echo(f"✗ Failed to load schema from {repo_root}: {e}", err=True)
        raise typer.Exit(1)

    try:
        hash_mgr = HashManager(repo_root)
        git_engine = GitEngine(repo_root)
        file_mgr = FileManager(repo_root, hash_mgr, schema_mgr, git_engine)
        files = file_mgr.query()
        total_files = len(files)

        # 计算 Inbox 数量（与 status 视图保持一致）
        inbox_count = 0
        for f in files:
            if not f.type or f.type == "":
                if f.id.startswith(f"{prefix}-00.") or f.id.startswith(
                    f"{prefix}-00.0"
                ) or f.id.startswith(f"{prefix}-00.00"):
                    inbox_count += 1
    except Exception as e:
        typer.echo(f"✗ Failed to inspect files in {repo_root}: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Repo name   : {repo_name}")
    typer.echo(f"Path        : {repo_root}")
    typer.echo(f"User prefix : {prefix}")
    typer.echo(f"Areas       : {areas_count}")
    typer.echo(f"Categories  : {categories_count}")
    typer.echo(f"Files       : {total_files} (Inbox: {inbox_count})")


@repo_app.command(name="rm")
def repo_rm(
    name: Optional[str] = typer.Argument(
        None,
        help="Repository name (from registry). If omitted, uses --repo/-r or current directory.",
    ),
    repo: Optional[str] = typer.Option(
        None,
        "--repo",
        "-r",
        help="Repository path or name (overrides global --repo)",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Confirm removal without prompt",
    ),
):
    """Remove MemoFlow repo data: mf repo rm NAME --yes

    Deletes all MemoFlow-related content in the target repo and removes it
    from the global registry:
      - .mf directory (config, hash index, etc.)
      - schema.yaml
      - default folders (00-Inbox, numeric ranges like 10-20, 11-21, etc.)
    """
    from mf.commands.cleanup import handle_remove_repo
    from mf.core.repo_registry import RepoRegistry

    if not yes:
        typer.echo("✗ This is a dangerous operation. Re-run with --yes to confirm.", err=True)
        raise typer.Exit(1)

    registry = RepoRegistry()

    # 解析 repo_root 和名称
    repo_root: Optional[Path]
    repo_name: Optional[str] = None

    if name:
        registered = registry.get_by_name(name)
        if not registered:
            typer.echo(f"✗ Repo '{name}' not found in registry", err=True)
            raise typer.Exit(1)
        repo_root = registered.path
        repo_name = registered.name
    else:
        repo_path = repo or _global_repo
        if repo_path:
            repo_root = get_repo_root(repo_path)
        else:
            repo_root = get_repo_root(None)

        registered = registry.find_by_path(repo_root)
        repo_name = registered.name if registered else None

    repo_root = repo_root.resolve()

    try:
        deleted = handle_remove_repo(repo_root, force=True)
        # 从注册表中移除
        if repo_name:
            registry.remove_by_name(repo_name)
        else:
            registry.remove_by_path(repo_root)
        typer.echo(f"✓ Removed MemoFlow data ({deleted} items) from {repo_root}")
    except Exception as e:
        typer.echo(f"✗ Failed to remove repo data: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
