"""Migration commands for MemoFlow"""

import logging
from pathlib import Path
from typing import List
from mf.core.file_manager import FileManager
from mf.core.hash_manager import HashManager
from mf.core.schema_manager import SchemaManager
from mf.core.git_engine import GitEngine
from mf.models.memo import Memo
import re

logger = logging.getLogger(__name__)


def handle_update_prefix(
    old_prefix: str,
    new_prefix: str,
    repo_root: Path
) -> int:
    """批量更新所有文件的 user_prefix
    
    Args:
        old_prefix: 旧的用户前缀（如 'HANK'）
        new_prefix: 新的用户前缀（如 'AC'）
        repo_root: 仓库根目录
    
    Returns:
        更新的文件数量
    """
    # 初始化服务
    hash_mgr = HashManager(repo_root)
    schema_mgr = SchemaManager(repo_root)
    git_engine = GitEngine(repo_root)
    file_mgr = FileManager(repo_root, hash_mgr, schema_mgr, git_engine)
    
    # 获取所有文件
    all_files = file_mgr.query()
    
    updated_count = 0
    
    for memo in all_files:
        # 检查当前 ID 是否使用旧前缀
        if memo.id.startswith(f"{old_prefix}-"):
            # 提取新的 ID（替换前缀）
            new_id = memo.id.replace(f"{old_prefix}-", f"{new_prefix}-", 1)
            
            try:
                # 先更新 hash_index 中的 id（如果存在）
                if memo.uuid in hash_mgr.index:
                    hash_mgr.update_path(memo.uuid, memo.file_path, new_id)
                
                # 更新文件的 frontmatter 中的 id 字段
                # 准备提交的文件列表（包括 hash_index.json）
                files_to_commit = [memo.file_path]
                hash_index_file = repo_root / ".mf" / "hash_index.json"
                if hash_index_file.exists():
                    files_to_commit.append(hash_index_file)
                
                # 手动更新文件并提交（包括 hash_index.json）
                import frontmatter
                post = frontmatter.load(memo.file_path)
                post.metadata['id'] = new_id
                
                with open(memo.file_path, 'w', encoding='utf-8') as f:
                    f.write(frontmatter.dumps(post))
                
                # 提交文件更改和 hash_index.json
                from mf.core.git_engine import CommitType
                git_engine.auto_commit(
                    CommitType.REFACTOR,
                    memo.uuid,
                    f"update prefix from {old_prefix} to {new_prefix}",
                    files_to_commit
                )
                
                updated_count += 1
                logger.info(f"Updated {memo.uuid}: {memo.id} -> {new_id}")
            except Exception as e:
                logger.error(f"Failed to update {memo.uuid}: {e}")
                logger.error(f"Error details: {e}", exc_info=True)
    
    logger.info(f"Updated {updated_count} files with new prefix {new_prefix}")
    return updated_count
