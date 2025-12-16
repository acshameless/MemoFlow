"""Schema view for MemoFlow"""

import logging
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text
from mf.core.schema_manager import SchemaManager

logger = logging.getLogger(__name__)
console = Console()


def show_schema(repo_root: Path):
    """显示 Schema 配置
    
    Args:
        repo_root: 仓库根目录
    """
    schema_mgr = SchemaManager(repo_root)
    schema = schema_mgr.get_schema()
    
    # 创建主面板
    console.print("\n[bold cyan]📋 MemoFlow Schema Configuration[/bold cyan]\n")
    
    # 显示用户前缀
    prefix_panel = Panel(
        f"[bold]{schema.user_prefix}[/bold]",
        title="User Prefix",
        border_style="green"
    )
    console.print(prefix_panel)
    console.print()
    
    # 创建区域和类别表格
    schema_table = Table(
        title="Areas and Categories",
        show_header=True,
        header_style="bold magenta",
        show_lines=True
    )
    schema_table.add_column("Area ID", style="cyan", width=10)
    schema_table.add_column("Area Name", style="yellow", width=15)
    schema_table.add_column("Category ID", style="green", width=12)
    schema_table.add_column("Category Name", style="blue", width=15)
    schema_table.add_column("Range", style="white", width=20)
    
    # 添加区域和类别信息
    for area in schema.areas:
        # 第一行显示区域信息
        first_category = area.categories[0] if area.categories else None
        if first_category:
            schema_table.add_row(
                str(area.id),
                area.name,
                str(first_category.id),
                first_category.name,
                f"{first_category.range[0]:.3f} - {first_category.range[1]:.3f}"
            )
        else:
            schema_table.add_row(
                str(area.id),
                area.name,
                "-",
                "-",
                "-"
            )
        
        # 其他类别
        for category in area.categories[1:]:
            schema_table.add_row(
                "",  # 空区域 ID
                "",  # 空区域名称
                str(category.id),
                category.name,
                f"{category.range[0]:.3f} - {category.range[1]:.3f}"
            )
    
    console.print(schema_table)
    console.print()
    
    # 显示树形结构（更直观）
    tree = Tree("📁 Schema Structure")
    for area in schema.areas:
        area_node = tree.add(
            Text(f"Area {area.id}: {area.name}", style="bold cyan")
        )
        for category in area.categories:
            range_str = f"{category.range[0]:.3f} - {category.range[1]:.3f}"
            category_label = f"Category {category.id}: {category.name} ({range_str})"
            area_node.add(Text(category_label, style="green"))
    
    console.print(tree)
    console.print()
    
    # 显示使用说明
    usage_panel = Panel(
        "[dim]Tip: Use 'area.category' format (e.g., 11.1) when moving files to auto-generate IDs[/dim]",
        border_style="blue"
    )
    console.print(usage_panel)
