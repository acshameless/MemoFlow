"""Timeline view for MemoFlow"""

import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from mf.core.git_engine import GitEngine

logger = logging.getLogger(__name__)
console = Console()


def show_timeline(repo_root: Path, since: str = "1 week ago", type_filter: Optional[str] = None):
    """显示时间轴视图
    
    Args:
        repo_root: 仓库根目录
        since: 时间范围
        type_filter: 提交类型过滤（feat, refactor, docs, chore）或文件类型过滤（task, meeting, note, email）
    """
    from mf.core.file_manager import FileManager
    from mf.core.hash_manager import HashManager
    from mf.core.schema_manager import SchemaManager
    
    git_engine = GitEngine(repo_root)
    
    # 解析时间轴
    timeline = git_engine.parse_timeline(since=since)
    
    # 应用类型过滤
    if type_filter:
        # 检查是提交类型还是文件类型
        commit_types = ["feat", "refactor", "docs", "chore"]
        file_types = ["task", "meeting", "note", "email"]
        
        if type_filter in commit_types:
            # 按提交类型过滤
            timeline = [entry for entry in timeline if entry["type"] == type_filter]
        elif type_filter in file_types:
            # 按文件类型过滤：需要根据 hash 或提交消息查找文件类型
            hash_mgr = HashManager(repo_root)
            schema_mgr = SchemaManager(repo_root)
            file_mgr = FileManager(repo_root, hash_mgr, schema_mgr, git_engine)
            
            filtered_timeline = []
            for entry in timeline:
                hash_id = entry.get("scope")
                message = entry.get("message", "")
                commit_hash = entry.get("hash")
                
                # 对于 "new" scope，需要通过提交找到对应的文件
                if hash_id == "new":
                    try:
                        # 获取该提交修改的文件
                        commit = git_engine.repo.commit(commit_hash) if commit_hash else None
                        if commit:
                            # 获取提交修改的文件列表
                            files_changed = [item.a_path for item in commit.stats.files.keys()]
                            
                            # 查找这些文件对应的 Memo
                            for file_path_str in files_changed:
                                file_path = repo_root / file_path_str
                                if file_path.exists() and file_path.suffix == ".md":
                                    try:
                                        memo = Memo.from_file(file_path)
                                        if memo.type == type_filter:
                                            filtered_timeline.append(entry)
                                            break
                                    except Exception:
                                        continue
                    except Exception as e:
                        logger.debug(f"Failed to get file type for commit {commit_hash}: {e}")
                        # 如果无法通过提交获取，尝试通过消息关键词匹配（降级方案）
                        type_keywords = {
                            "task": ["task", "任务"],
                            "meeting": ["meeting", "会议", "周会"],
                            "note": ["note", "笔记"],
                            "email": ["email", "邮件"]
                        }
                        message_lower = message.lower()
                        for keyword in type_keywords.get(type_filter, []):
                            if keyword in message_lower:
                                filtered_timeline.append(entry)
                                break
                elif hash_id and hash_id != "init":
                    # 对于有 hash_id 的提交，直接查找文件
                    try:
                        memo = file_mgr.read_file(hash_id)
                        if memo.type == type_filter:
                            filtered_timeline.append(entry)
                    except Exception:
                        # 如果文件不存在或读取失败，跳过
                        continue
            timeline = filtered_timeline
        else:
            # 无效的类型，按提交类型处理（向后兼容）
            timeline = [entry for entry in timeline if entry["type"] == type_filter]
    
    if not timeline:
        console.print("[yellow]No commits found in the specified time range.[/yellow]")
        return
    
    # 创建时间轴表格
    timeline_table = Table(title=f"Timeline ({since})", show_header=True, header_style="bold magenta")
    timeline_table.add_column("Time", style="cyan", width=20)
    timeline_table.add_column("Type", style="yellow", width=10)
    timeline_table.add_column("Scope", style="green", width=10)
    timeline_table.add_column("Message", style="white")
    
    # 添加条目
    for entry in timeline:
        timestamp = entry["timestamp"].strftime("%Y-%m-%d %H:%M")
        timeline_table.add_row(
            timestamp,
            entry["type"],
            entry["scope"],
            entry["message"]
        )
    
    # 统计信息
    stats = {}
    for entry in timeline:
        commit_type = entry["type"]
        stats[commit_type] = stats.get(commit_type, 0) + 1
    
    stats_text = "\n".join([f"[bold]{k}:[/bold] {v}" for k, v in sorted(stats.items())])
    stats_panel = Panel(
        stats_text,
        title="📈 Commit Statistics",
        border_style="blue"
    )
    
    console.print(stats_panel)
    console.print("\n")
    console.print(timeline_table)
