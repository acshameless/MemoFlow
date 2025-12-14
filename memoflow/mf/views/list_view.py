"""List view for MemoFlow"""

import logging
from pathlib import Path
from typing import List, Dict
from rich.console import Console
from rich.tree import Tree
from rich.text import Text
from mf.models.memo import Memo
from mf.core.file_manager import FileManager
from mf.core.hash_manager import HashManager
from mf.core.schema_manager import SchemaManager
from mf.core.git_engine import GitEngine

logger = logging.getLogger(__name__)
console = Console()


def build_tree_structure(repo_root: Path) -> Dict:
    """构建目录树结构"""
    structure = {}
    
    # 扫描所有 Markdown 文件
    for md_file in repo_root.rglob("*.md"):
        try:
            memo = Memo.from_file(md_file)
            relative_path = md_file.relative_to(repo_root)
            
            # 解析路径层级
            parts = relative_path.parts
            if len(parts) == 0:
                continue
            
            # 构建树结构
            current = structure
            for part in parts[:-1]:  # 排除文件名
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # 添加文件
            filename = parts[-1]
            if "files" not in current:
                current["files"] = []
            current["files"].append({
                "memo": memo,
                "path": relative_path
            })
        except Exception as e:
            logger.debug(f"Failed to parse {md_file}: {e}")
    
    return structure


def render_tree(tree_data: Dict, tree: Tree, prefix: str = ""):
    """递归渲染树结构"""
    # 先添加目录
    for key, value in tree_data.items():
        if key == "files":
            continue
        
        # 目录节点
        dir_label = f"{prefix}{key}/"
        dir_node = tree.add(Text(dir_label, style="bold blue"))
        
        # 递归处理子目录
        if isinstance(value, dict):
            render_tree(value, dir_node, "")
    
    # 再添加文件
    if "files" in tree_data:
        for file_info in tree_data["files"]:
            memo = file_info["memo"]
            file_label = f"{memo.id} {memo.title} [{memo.uuid}]"
            file_node = tree.add(Text(file_label, style="green"))
            
            # 添加元数据
            display_type = memo.type if memo.type else "untyped"
            meta = f"  {display_type} | {memo.status}"
            file_node.add(Text(meta, style="dim"))


def show_list(repo_root: Path, tree_format: bool = True):
    """显示列表视图
    
    Args:
        repo_root: 仓库根目录
        tree_format: 是否使用树形格式
    """
    # 初始化服务
    hash_mgr = HashManager(repo_root)
    schema_mgr = SchemaManager(repo_root)
    git_engine = GitEngine(repo_root)
    file_mgr = FileManager(repo_root, hash_mgr, schema_mgr, git_engine)
    
    if tree_format:
        # 构建树结构
        tree_data = build_tree_structure(repo_root)
        
        # 渲染树
        tree = Tree("📁 MemoFlow Repository")
        render_tree(tree_data, tree)
        console.print(tree)
    else:
        # 简单列表格式
        all_files = file_mgr.query()
        
        console.print("\n[bold]MemoFlow Files[/bold]\n")
        for memo in sorted(all_files, key=lambda x: x.created_at, reverse=True):
            display_type = memo.type if memo.type else "untyped"
            console.print(
                f"[green]{memo.uuid}[/green] "
                f"[cyan]{memo.id}[/cyan] "
                f"[yellow]{display_type}[/yellow] "
                f"[white]{memo.title}[/white] "
                f"[dim]({memo.status})[/dim]"
            )
