"""Cleanup commands for MemoFlow."""

import logging
import shutil
from pathlib import Path
from typing import List

from mf.core.git_engine import CommitType, GitEngine

logger = logging.getLogger(__name__)


def handle_remove_repo(repo_root: Path, force: bool = False) -> int:
    """删除 MemoFlow 在仓库中的所有相关内容（危险操作）。

    删除以下内容：
    - .mf/ 目录及其文件（配置、hash_index 等）
    - schema.yaml
    - 默认目录（00-Inbox、数字区间目录如 10-20、11-21 等）

    Args:
        repo_root: 仓库根目录
        force: 如果为 True，则跳过安全检查

    Returns:
        实际删除的文件/目录数量
    """
    repo_root = Path(repo_root).resolve()
    if not repo_root.exists():
        raise FileNotFoundError(f"Repository not found: {repo_root}")

    # 需要删除的路径列表
    targets: List[Path] = []

    # .mf 目录
    mf_dir = repo_root / ".mf"
    if mf_dir.exists():
        targets.append(mf_dir)

    # schema.yaml
    schema_file = repo_root / "schema.yaml"
    if schema_file.exists():
        targets.append(schema_file)

    # 默认目录：00-Inbox
    inbox_dir = repo_root / "00-Inbox"
    if inbox_dir.exists():
        targets.append(inbox_dir)

    # 数字区间目录（如 10-20, 11-21 等）
    for item in repo_root.iterdir():
        name = item.name
        if item.is_dir():
            # 匹配形如 "10-20"、"11-21"、"20-30" 等
            parts = name.split("-")
            if len(parts) == 2 and all(part.isdigit() for part in parts):
                targets.append(item)

    if not targets:
        logger.info("No MemoFlow-related files found to remove.")
        return 0

    if not force:
        raise PermissionError("Dangerous operation. Use --yes to confirm removal.")

    # 记录要提交的删除文件列表（展开目录中的所有文件）
    removed_files: List[Path] = []
    for target in targets:
        if target.is_dir():
            for path in target.rglob("*"):
                if path.is_file():
                    removed_files.append(path)
        elif target.is_file():
            removed_files.append(target)

    # 实际删除
    deleted_count = 0
    for target in targets:
        try:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            deleted_count += 1
            logger.info(f"Removed: {target}")
        except Exception as e:
            logger.error(f"Failed to remove {target}: {e}")
            raise

    # Git 提交删除
    try:
        git_engine = GitEngine(repo_root)
        git_engine.auto_commit(
            CommitType.CHORE,
            "cleanup",
            "remove memoflow repo data",
            files=[],
            removed_files=removed_files,
        )
    except Exception as e:
        logger.warning(f"Failed to auto-commit removal: {e}")

    return deleted_count
