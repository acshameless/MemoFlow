"""Update commands for MemoFlow"""

import logging
from pathlib import Path
from mf.core.file_manager import FileManager
from mf.core.hash_manager import HashManager
from mf.core.schema_manager import SchemaManager
from mf.core.git_engine import GitEngine

logger = logging.getLogger(__name__)


def handle_update_type(
    hash: str,
    new_type: str,
    repo_root: Path
) -> bool:
    """修改文件类型
    
    Args:
        hash: 文件哈希（支持部分匹配）
        new_type: 新类型（task, meeting, note, email）
        repo_root: 仓库根目录
    
    Returns:
        True 如果成功
    """
    # 验证类型
    valid_types = ["task", "meeting", "note", "email"]
    if new_type not in valid_types:
        raise ValueError(f"Invalid type: {new_type}. Must be one of: {', '.join(valid_types)}")
    
    # 初始化服务
    hash_mgr = HashManager(repo_root)
    schema_mgr = SchemaManager(repo_root)
    git_engine = GitEngine(repo_root)
    file_mgr = FileManager(repo_root, hash_mgr, schema_mgr, git_engine)
    
    # 读取文件
    memo = file_mgr.read_file(hash)
    
    # 检查类型是否已经相同
    if memo.type == new_type:
        logger.info(f"File {hash} is already type {new_type}")
        return False
    
    # 更新类型
    file_mgr.update_file(
        hash,
        frontmatter_updates={"type": new_type},
        commit_message=f"change type from {memo.type} to {new_type}"
    )
    
    logger.info(f"Updated file {hash} type from {memo.type} to {new_type}")
    return True
