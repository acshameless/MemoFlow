"""Capture command for MemoFlow"""

import logging
from pathlib import Path
from typing import Optional
from mf.core.file_manager import FileManager
from mf.core.hash_manager import HashManager
from mf.core.schema_manager import SchemaManager
from mf.core.git_engine import GitEngine

logger = logging.getLogger(__name__)


def handle_capture(
    file_type: Optional[str],
    content: str,
    repo_root: Path
) -> tuple[str, Path]:
    """处理 capture 命令
    
    Args:
        file_type: 文件类型（meeting, note, task, email），None 表示未分类
        content: 文件内容
        repo_root: 仓库根目录
    
    Returns:
        (hash_id, file_path) 元组
    """
    # 验证文件类型（如果提供）
    if file_type is not None:
        valid_types = ['meeting', 'note', 'task', 'email']
        if file_type not in valid_types:
            raise ValueError(
                f"Invalid file type: {file_type}. "
                f"Must be one of {', '.join(valid_types)}"
            )
    
    # 初始化服务
    hash_mgr = HashManager(repo_root)
    schema_mgr = SchemaManager(repo_root)
    git_engine = GitEngine(repo_root)
    file_mgr = FileManager(repo_root, hash_mgr, schema_mgr, git_engine)
    
    # 从内容提取标题（第一行或前50个字符）
    lines = content.strip().split('\n')
    title = lines[0].strip() if lines else "Untitled"
    if len(title) > 50:
        title = title[:50] + "..."
    
    # 创建文件
    hash_id, file_path = file_mgr.create_file(
        file_type=file_type,
        title=title,
        content=content
    )
    
    logger.info(f"Created file: {file_path} (hash: {hash_id})")
    return hash_id, file_path
