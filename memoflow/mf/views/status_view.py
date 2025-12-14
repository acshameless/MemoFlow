"""Status view for MemoFlow"""

import logging
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from mf.core.file_manager import FileManager
from mf.core.hash_manager import HashManager
from mf.core.schema_manager import SchemaManager
from mf.core.git_engine import GitEngine

logger = logging.getLogger(__name__)
console = Console()


def show_status(
    repo_root: Path,
    limit: Optional[int] = None,
    show_all: bool = False,
    type_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
):
    """显示状态视图
    
    Args:
        repo_root: 仓库根目录
        limit: 限制显示的文件数量（默认 20）
        show_all: 是否显示所有文件
        type_filter: 按类型过滤（task, meeting, note, email）
        status_filter: 按状态过滤（open, done）
    """
    # 初始化服务
    hash_mgr = HashManager(repo_root)
    schema_mgr = SchemaManager(repo_root)
    git_engine = GitEngine(repo_root)
    file_mgr = FileManager(repo_root, hash_mgr, schema_mgr, git_engine)
    
    # 获取所有文件
    all_files = file_mgr.query()
    
    # 应用过滤
    filtered_files = all_files
    if type_filter:
        filtered_files = [f for f in filtered_files if (f.type or "untyped") == type_filter]
    if status_filter:
        filtered_files = [f for f in filtered_files if f.status == status_filter]
    
    # 计算 Inbox 文件数量（只有没有指定类型的文件才归类到 inbox）
    # Inbox 文件是指：type 为空或 None，或者 ID 以 HANK-00. 开头（临时 ID）
    inbox_count = sum(1 for f in all_files if (not f.type or f.type == "") and f.id.startswith("HANK-00."))
    
    # 按类型统计开放文件
    type_counts = {}
    for memo in all_files:
        if memo.status == "open":
            file_type = memo.type if memo.type else "untyped"
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
    
    # 构建统计信息文本
    stats_lines = []
    
    # 显示 Inbox（只有没有类型的文件）
    if inbox_count > 0:
        stats_lines.append(f"[bold]Inbox (untyped):[/bold] {inbox_count} files")
    
    # 显示各类型的开放文件数量（按固定顺序）
    for file_type in ["task", "meeting", "note", "email"]:
        count = type_counts.get(file_type, 0)
        if count > 0:
            # 处理单复数
            label = file_type.capitalize() + ("s" if count > 1 else "")
            stats_lines.append(f"[bold]Open {label}:[/bold] {count} file{'s' if count > 1 else ''}")
    
    stats_lines.append(f"[bold]Total Files:[/bold] {len(all_files)} file{'s' if len(all_files) != 1 else ''}")
    
    # 构建哈希映射表
    hash_table = Table(title="Hash Index", show_header=True, header_style="bold magenta")
    hash_table.add_column("#", style="dim", width=4, justify="right")
    hash_table.add_column("Hash", style="cyan", width=8)
    hash_table.add_column("ID", style="yellow")
    hash_table.add_column("Title", style="green")
    hash_table.add_column("Type", style="blue")
    hash_table.add_column("Status", style="red")
    
    # 确定显示数量
    if show_all:
        display_limit = len(filtered_files)
    elif limit is not None:
        display_limit = limit
    else:
        display_limit = 20  # 默认显示 20 个
    
    # 获取要显示的文件（限制显示数量）
    sorted_files = sorted(filtered_files, key=lambda x: x.created_at, reverse=True)[:display_limit]
    
    for idx, memo in enumerate(sorted_files, start=1):
        display_type = memo.type if memo.type else "untyped"
        hash_table.add_row(
            str(idx),
            memo.uuid,
            memo.id,
            memo.title[:30] + "..." if len(memo.title) > 30 else memo.title,
            display_type,
            memo.status
        )
    
    # 显示统计信息
    stats_panel = Panel(
        "\n".join(stats_lines),
        title="📊 Status Summary",
        border_style="green"
    )
    
    console.print(stats_panel)
    console.print("\n")
    console.print(hash_table)
    
    # 显示提示信息
    if len(filtered_files) > display_limit:
        remaining = len(filtered_files) - display_limit
        console.print(f"\n[dim]... and {remaining} more file{'s' if remaining > 1 else ''} (use --all or --limit to see more)[/dim]")
    elif type_filter or status_filter:
        console.print(f"\n[dim]Showing {len(sorted_files)} of {len(all_files)} files (filtered)[/dim]")
