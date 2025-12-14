"""Organize commands for MemoFlow"""

import logging
from pathlib import Path
from mf.core.file_manager import FileManager
from mf.core.hash_manager import HashManager
from mf.core.schema_manager import SchemaManager
from mf.core.git_engine import GitEngine

logger = logging.getLogger(__name__)


def handle_move(
    hash: str,
    old_path: str,
    new_path: str,
    repo_root: Path
) -> Path:
    """处理 move 命令
    
    Args:
        hash: 文件哈希（支持部分匹配）
        old_path: 旧路径（JD ID 或相对路径，用于验证）
        new_path: 新路径（JD ID 或相对路径）
        repo_root: 仓库根目录
    
    Returns:
        新文件路径
    """
    # 初始化服务
    hash_mgr = HashManager(repo_root)
    schema_mgr = SchemaManager(repo_root)
    git_engine = GitEngine(repo_root)
    file_mgr = FileManager(repo_root, hash_mgr, schema_mgr, git_engine)
    
    # 处理相对路径：如果是相对路径，转换为 JD ID
    # 检查 new_path 是否是相对路径（包含 / 或 .md）
    if "/" in new_path or new_path.endswith(".md"):
        # 相对路径，需要解析为 JD ID
        new_path_obj = (repo_root / new_path).resolve()
        
        # 确保路径在仓库内
        try:
            relative_path = new_path_obj.relative_to(repo_root)
        except ValueError:
            raise ValueError(f"Path {new_path} is outside repository root")
        
        if new_path_obj.is_file():
            # 文件存在，读取其 JD ID
            try:
                from mf.models.memo import Memo
                memo = Memo.from_file(new_path_obj)
                new_path = memo.id
            except Exception:
                raise ValueError(f"Cannot read JD ID from file: {new_path}")
        elif new_path_obj.is_dir() or not new_path_obj.exists():
            # 目录路径或不存在（将创建），从目录结构推断 JD ID
            # 格式: {area_range}/{category_range}/ 例如: "10-20/10.01-10.09/"
            parts = relative_path.parts
            if len(parts) >= 2:
                # 从目录结构推断 JD ID
                area_part = parts[0]  # 如 "10-20"
                cat_part = parts[1]   # 如 "10.01-10.09"
                
                # 从 category 范围中提取第一个 ID
                if "." in cat_part and "-" in cat_part:
                    # 格式: "10.01-10.09" -> 提取 "10.01"
                    first_id = cat_part.split("-")[0]
                    # 构建 JD ID（需要 schema 的 user_prefix）
                    schema = schema_mgr.get_schema()
                    new_path = f"{schema.user_prefix}-{first_id}"
                else:
                    raise ValueError(f"Cannot determine JD ID from directory path: {new_path}. Expected format: area_range/category_range/ (e.g., 10-20/10.01-10.09/)")
            else:
                raise ValueError(f"Invalid relative path format: {new_path}. Expected format: area_range/category_range/ or file path")
    
    # 验证新路径（JD ID）
    if not schema_mgr.validate_path(new_path):
        raise ValueError(
            f"Invalid target path: {new_path}. "
            "Please check your schema.yaml configuration."
        )
    
    # 处理 old_path：如果是相对路径，也需要转换
    if "/" in old_path or old_path.endswith(".md"):
        old_path_obj = (repo_root / old_path).resolve()
        if old_path_obj.exists() and old_path_obj.is_file():
            try:
                from mf.models.memo import Memo
                memo = Memo.from_file(old_path_obj)
                old_path = memo.id
            except Exception:
                pass  # 如果无法读取，保持原值用于验证
    
    # 移动文件
    new_file_path = file_mgr.move_file(hash, old_path, new_path)
    
    logger.info(f"Moved file from {old_path} to {new_path} (hash: {hash})")
    return new_file_path


def handle_rebuild_index(repo_root: Path) -> int:
    """处理 rebuild-index 命令
    
    Args:
        repo_root: 仓库根目录
    
    Returns:
        重建的文件数量
    """
    hash_mgr = HashManager(repo_root)
    git_engine = GitEngine(repo_root)
    count = hash_mgr.rebuild_index()
    
    # 提交 hash_index.json 的更改
    hash_index_file = repo_root / ".mf" / "hash_index.json"
    if hash_index_file.exists():
        try:
            from mf.core.git_engine import CommitType
            git_engine.auto_commit(
                CommitType.CHORE,
                "index",
                f"rebuild index with {count} files",
                [hash_index_file]
            )
        except Exception as e:
            logger.warning(f"Failed to auto-commit index rebuild: {e}")
    
    logger.info(f"Rebuilt index with {count} files")
    return count
