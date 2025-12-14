"""Git Engine for MemoFlow"""

import re
import logging
from enum import Enum
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from git import Repo, InvalidGitRepositoryError

logger = logging.getLogger(__name__)


class CommitType(Enum):
    """提交类型枚举"""
    FEAT = "feat"          # 新增捕获/完成任务
    REFACTOR = "refactor"  # 移动/重组
    DOCS = "docs"         # 内容更新
    CHORE = "chore"        # 维护操作


class GitEngine:
    """Git 引擎：封装符合 Angular 规范的 Git 操作"""
    
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path).resolve()
        self.repo = self._ensure_repo()
    
    def _ensure_repo(self) -> Repo:
        """确保 Git 仓库已初始化"""
        try:
            return Repo(self.repo_path)
        except InvalidGitRepositoryError:
            # 自动初始化
            logger.info(f"Initializing Git repository at {self.repo_path}")
            repo = Repo.init(self.repo_path)
            # 创建初始提交
            try:
                repo.index.commit("chore(init): initialize MemoFlow repository")
            except Exception:
                # 如果无法创建初始提交（例如没有配置用户），跳过
                logger.warning("Could not create initial commit (user not configured)")
            return repo
    
    def auto_commit(
        self,
        commit_type: CommitType,
        scope: str,  # Hash ID 或 "new"
        message: str,
        files: List[Path]
    ) -> str:
        """自动 Stage + Commit
        
        Args:
            commit_type: 提交类型
            scope: Hash ID 或 "new"
            message: 提交消息
            files: 要提交的文件列表
        
        Returns:
            提交的 SHA
        """
        # Stage 文件
        for file in files:
            file_path = Path(file)
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                continue
            try:
                # 使用相对路径
                relative_path = file_path.relative_to(self.repo_path)
                self.repo.index.add([str(relative_path)])
            except ValueError:
                # 如果文件不在仓库内，使用绝对路径
                self.repo.index.add([str(file_path)])
        
        # 构建 Commit Message
        full_message = f"{commit_type.value}({scope}): {message}"
        
        # Commit
        try:
            commit = self.repo.index.commit(full_message)
            logger.info(f"Committed: {full_message}")
            return commit.hexsha
        except Exception as e:
            logger.error(f"Failed to commit: {e}")
            raise
    
    def parse_timeline(
        self,
        since: str = "1 week ago",
        until: Optional[datetime] = None
    ) -> List[dict]:
        """解析 Git Log 生成时间轴
        
        Args:
            since: 时间范围（如 "1 week ago", "1 day ago"）
            until: 结束时间（可选）
        
        Returns:
            时间轴条目列表
        """
        try:
            # Use git log command directly for better date parsing
            from datetime import timedelta
            
            # Parse since string to datetime
            since_dt = None
            if since == "1.week" or since == "1 week" or since == "1 week ago":
                since_dt = datetime.now() - timedelta(weeks=1)
            elif since == "1.day" or since == "1 day" or since == "1 day ago":
                since_dt = datetime.now() - timedelta(days=1)
            
            # Get commits
            if since_dt:
                commits = list(self.repo.iter_commits(since=since_dt))
            else:
                # Try to use git's date parsing or get all commits
                try:
                    commits = list(self.repo.iter_commits(since=since))
                except:
                    # Fallback: get all commits
                    commits = list(self.repo.iter_commits())
            
            # Filter by until if provided
            if until:
                commits = [c for c in commits if c.committed_datetime <= until]
        except Exception as e:
            logger.error(f"Failed to parse timeline: {e}")
            # Fallback: get all commits
            try:
                commits = list(self.repo.iter_commits())
            except:
                return []
        
        timeline = []
        for commit in commits:
            # 解析 Angular 格式: type(scope): message
            match = re.match(r'(\w+)\(([^)]+)\):\s*(.+)', commit.message)
            if match:
                timeline.append({
                    'type': match.group(1),
                    'scope': match.group(2),
                    'message': match.group(3),
                    'hash': commit.hexsha[:7],
                    'timestamp': commit.committed_datetime,
                    'author': commit.author.name
                })
            else:
                # 处理非 Angular 格式的提交
                timeline.append({
                    'type': 'chore',
                    'scope': 'unknown',
                    'message': commit.message.split('\n')[0],
                    'hash': commit.hexsha[:7],
                    'timestamp': commit.committed_datetime,
                    'author': commit.author.name
                })
        
        return sorted(timeline, key=lambda x: x['timestamp'], reverse=True)
    
    def push(self, remote: str = "origin", auto_push: bool = False) -> bool:
        """推送到远程仓库
        
        Args:
            remote: 远程仓库名称
            auto_push: 是否自动推送（配置项）
        
        Returns:
            True 如果推送成功，False 否则
        """
        if not auto_push:
            return False
        
        try:
            origin = self.repo.remote(remote)
            origin.push()
            logger.info(f"Pushed to {remote}")
            return True
        except Exception as e:
            # 推送失败不中断操作，仅记录日志
            logger.warning(f"Failed to push to {remote}: {e}")
            return False
    
    def get_repo(self) -> Repo:
        """获取 Git Repo 对象"""
        return self.repo
