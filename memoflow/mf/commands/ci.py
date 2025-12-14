"""CI commands for MemoFlow"""

import logging
from pathlib import Path
from datetime import datetime
from mf.core.file_manager import FileManager
from mf.core.hash_manager import HashManager
from mf.core.schema_manager import SchemaManager
from mf.core.git_engine import GitEngine

logger = logging.getLogger(__name__)


def handle_ci(mode: str, repo_root: Path) -> str:
    """供 GitHub Actions 调用
    
    Args:
        mode: 模式（"morning" 或 "evening"）
        repo_root: 仓库根目录
    
    Returns:
        生成的报告内容（Markdown 格式）
    """
    # 初始化服务
    hash_mgr = HashManager(repo_root)
    schema_mgr = SchemaManager(repo_root)
    git_engine = GitEngine(repo_root)
    file_mgr = FileManager(repo_root, hash_mgr, schema_mgr, git_engine)
    
    if mode == "morning":
        return _generate_morning_focus(file_mgr)
    elif mode == "evening":
        return _generate_evening_review(git_engine, file_mgr)
    else:
        raise ValueError(f"Invalid mode: {mode}. Must be 'morning' or 'evening'")


def _generate_morning_focus(file_mgr: FileManager) -> str:
    """生成晨间焦点文档"""
    today = datetime.now().date()
    
    # 扫描今日到期任务
    all_tasks = file_mgr.query(file_type="task", status="open")
    today_tasks = [
        task for task in all_tasks
        if task.due_date and task.due_date.date() == today
    ]
    
    # 开放任务摘要
    open_tasks = file_mgr.query(status="open")
    
    # 生成 Markdown
    report = f"# 今日聚焦\n\n"
    report += f"**日期**: {today.strftime('%Y-%m-%d')}\n\n"
    
    report += "## 今日到期任务\n\n"
    if today_tasks:
        for task in today_tasks:
            report += f"- [ ] {task.title} `{task.uuid}`\n"
            if task.tags:
                report += f"  标签: {', '.join(task.tags)}\n"
    else:
        report += "无今日到期任务\n"
    
    report += f"\n## 开放任务总数: {len(open_tasks)}\n\n"
    
    # 按类型分类
    by_type = {}
    for task in open_tasks:
        task_type = task.type or "untyped"
        by_type[task_type] = by_type.get(task_type, 0) + 1
    
    if by_type:
        report += "### 按类型分类\n\n"
        for task_type, count in sorted(by_type.items()):
            report += f"- **{task_type}**: {count}\n"
    
    return report


def _generate_evening_review(git_engine: GitEngine, file_mgr: FileManager) -> str:
    """生成晚间复盘文档"""
    today = datetime.now().date()
    
    # 分析今日 Git Log
    timeline = git_engine.parse_timeline(since="1 day ago")
    
    # 过滤今天的提交
    today_commits = [
        entry for entry in timeline
        if entry["timestamp"].date() == today
    ]
    
    # 统计
    stats = {
        'captured': sum(1 for t in today_commits if t['type'] == 'feat' and t['scope'] == 'new'),
        'organized': sum(1 for t in today_commits if t['type'] == 'refactor'),
        'finished': sum(1 for t in today_commits if 'mark as done' in t['message'].lower()),
        'updated': sum(1 for t in today_commits if t['type'] == 'docs')
    }
    
    # 生成 Markdown
    report = f"# 今日复盘\n\n"
    report += f"**日期**: {today.strftime('%Y-%m-%d')}\n\n"
    
    report += "## 今日统计\n\n"
    report += f"- **捕获**: {stats['captured']} 项\n"
    report += f"- **整理**: {stats['organized']} 项\n"
    report += f"- **完成**: {stats['finished']} 项\n"
    report += f"- **更新**: {stats['updated']} 项\n"
    
    if today_commits:
        report += "\n## 今日活动\n\n"
        for entry in today_commits[:20]:  # 最近 20 条
            timestamp = entry['timestamp'].strftime("%H:%M")
            report += f"- `{timestamp}` `{entry['hash']}` {entry['message']}\n"
    
    # 任务状态统计
    all_files = file_mgr.query()
    open_count = len([f for f in all_files if f.status == "open"])
    done_count = len([f for f in all_files if f.status == "done"])
    
    report += f"\n## 任务状态\n\n"
    report += f"- **开放**: {open_count}\n"
    report += f"- **完成**: {done_count}\n"
    
    return report
