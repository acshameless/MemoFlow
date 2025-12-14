"""Calendar view for MemoFlow"""

import logging
from pathlib import Path
from datetime import datetime, timedelta
from calendar import monthrange
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from mf.core.file_manager import FileManager
from mf.core.hash_manager import HashManager
from mf.core.schema_manager import SchemaManager
from mf.core.git_engine import GitEngine
from mf.models.memo import Memo

logger = logging.getLogger(__name__)
console = Console()


def get_calendar_month(year: int, month: int) -> Dict[int, List[Memo]]:
    """获取指定月份的文件（按日期组织）
    
    Args:
        year: 年份
        month: 月份（1-12）
    
    Returns:
        字典：{日期: [Memo列表]}
    """
    calendar_data = {}
    
    # 计算月份的开始和结束日期
    start_date = datetime(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = datetime(year, month, last_day, 23, 59, 59)
    
    return calendar_data


def show_calendar(repo_root: Path, month: Optional[int] = None, year: Optional[int] = None, type_filter: Optional[str] = None):
    """显示日历视图
    
    Args:
        repo_root: 仓库根目录
        month: 月份（1-12），None 表示当前月
        year: 年份，None 表示当前年
        type_filter: 类型过滤（task, meeting, note, email），None 表示显示所有类型
    """
    # 初始化服务
    hash_mgr = HashManager(repo_root)
    schema_mgr = SchemaManager(repo_root)
    git_engine = GitEngine(repo_root)
    file_mgr = FileManager(repo_root, hash_mgr, schema_mgr, git_engine)
    
    # 确定月份和年份
    now = datetime.now()
    target_month = month if month else now.month
    target_year = year if year else now.year
    
    # 查询所有有 due_date 的文件
    all_files = file_mgr.query(file_type=type_filter) if type_filter else file_mgr.query()
    files_with_due_date = [f for f in all_files if f.due_date]
    
    # 按日期组织文件
    calendar_data: Dict[int, List[Memo]] = {}
    today = datetime.now().date()
    
    for memo in files_with_due_date:
        if memo.due_date:
            due_date = memo.due_date.date()
            # 只显示目标月份的文件
            if due_date.year == target_year and due_date.month == target_month:
                day = due_date.day
                if day not in calendar_data:
                    calendar_data[day] = []
                calendar_data[day].append(memo)
    
    # 创建日历表格
    month_names = ["", "January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    
    # 构建标题
    title = f"{month_names[target_month]} {target_year}"
    if type_filter:
        title += f" ({type_filter})"
    
    calendar_table = Table(
        title=title,
        show_header=True,
        header_style="bold magenta"
    )
    calendar_table.add_column("Date", style="cyan", width=12)
    calendar_table.add_column("Items", style="white")
    calendar_table.add_column("Type", style="blue", width=10)
    calendar_table.add_column("Status", style="yellow")
    
    # 获取月份的天数
    _, last_day = monthrange(target_year, target_month)
    
    # 添加每一天
    for day in range(1, last_day + 1):
        date_str = f"{target_year}-{target_month:02d}-{day:02d}"
        date_obj = datetime(target_year, target_month, day).date()
        
        # 检查是否是今天
        date_display = date_str
        if date_obj == today:
            date_display = f"[bold green]{date_str}[/bold green] (Today)"
        elif date_obj < today:
            date_display = f"[dim]{date_str}[/dim] (Past)"
        
        # 获取当天的文件
        day_items = calendar_data.get(day, [])
        
        if day_items:
            item_list = []
            type_list = []
            status_list = []
            for item in day_items:
                item_display = f"{item.title} [{item.uuid}]"
                if date_obj < today and item.status != "done":
                    item_display = f"[red]{item_display}[/red] (Overdue)"
                item_list.append(item_display)
                type_list.append(item.type if item.type else "untyped")
                status_list.append(item.status)
            
            calendar_table.add_row(
                date_display,
                "\n".join(item_list),
                "\n".join(type_list),
                "\n".join(status_list)
            )
        else:
            calendar_table.add_row(date_display, "-", "-", "-")
    
    # 统计信息
    total_items = len(files_with_due_date)
    overdue_count = sum(1 for f in files_with_due_date 
                       if f.due_date and f.due_date.date() < today and f.status != "done")
    
    # 按类型统计
    type_stats = {}
    for f in files_with_due_date:
        file_type = f.type if f.type else "untyped"
        type_stats[file_type] = type_stats.get(file_type, 0) + 1
    
    # 构建统计文本
    stats_lines = [
        f"[bold]Total Items with Due Date:[/bold] {total_items}",
        f"[bold]Overdue Items:[/bold] [red]{overdue_count}[/red]"
    ]
    
    # 添加类型统计
    if type_stats:
        stats_lines.append("")
        stats_lines.append("[bold]By Type:[/bold]")
        for file_type in ["task", "meeting", "note", "email"]:
            if file_type in type_stats:
                stats_lines.append(f"  - {file_type.capitalize()}: {type_stats[file_type]}")
        if "untyped" in type_stats:
            stats_lines.append(f"  - Untyped: {type_stats['untyped']}")
    
    stats_panel = Panel(
        "\n".join(stats_lines),
        title="📅 Calendar Statistics",
        border_style="blue"
    )
    
    console.print(stats_panel)
    console.print("\n")
    console.print(calendar_table)
