"""Engage commands for MemoFlow"""

import logging
from pathlib import Path
from mf.core.file_manager import FileManager
from mf.core.hash_manager import HashManager
from mf.core.schema_manager import SchemaManager
from mf.core.git_engine import GitEngine

logger = logging.getLogger(__name__)


def mark_finished(
    hash: str,
    repo_root: Path
) -> bool:
    """标记任务为完成
    
    Args:
        hash: 文件哈希（支持部分匹配）
        repo_root: 仓库根目录
    
    Returns:
        True 如果成功，False 如果已经完成
    """
    # 初始化服务
    hash_mgr = HashManager(repo_root)
    schema_mgr = SchemaManager(repo_root)
    git_engine = GitEngine(repo_root)
    file_mgr = FileManager(repo_root, hash_mgr, schema_mgr, git_engine)
    
    # 读取文件
    memo = file_mgr.read_file(hash)
    
    # 检查是否已经完成
    if memo.status == "done":
        logger.info(f"File {hash} is already marked as done")
        return False
    
    # 更新状态
    # 注意：update_file 会自动提交，但使用 docs 类型
    # 我们需要手动提交使用 feat 类型（因为这是完成任务）
    memo = file_mgr.read_file(hash)
    
    # 直接更新文件而不通过 update_file（避免自动提交）
    import frontmatter
    post = frontmatter.load(memo.file_path)
    post.metadata['status'] = 'done'
    
    with open(memo.file_path, 'w', encoding='utf-8') as f:
        f.write(frontmatter.dumps(post))
    
    # 使用 feat 类型提交
    from mf.core.git_engine import CommitType
    git_engine.auto_commit(
        CommitType.FEAT,
        hash,
        "mark as done",
        [memo.file_path]
    )
    
    logger.info(f"Marked file {hash} as done")
    return True
