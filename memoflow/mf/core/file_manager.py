"""File Manager for MemoFlow"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from mf.models.memo import Memo
from mf.core.hash_manager import HashManager
from mf.core.schema_manager import SchemaManager
from mf.core.git_engine import GitEngine, CommitType

logger = logging.getLogger(__name__)


class FileManager:
    """文件管理器：Markdown 文件的 CRUD 与 Frontmatter 管理"""
    
    def __init__(
        self,
        repo_root: Path,
        hash_mgr: HashManager,
        schema_mgr: SchemaManager,
        git_engine: GitEngine
    ):
        self.repo_root = Path(repo_root).resolve()
        self.hash_mgr = hash_mgr
        self.schema_mgr = schema_mgr
        self.git_engine = git_engine
        self.inbox_dir = self.repo_root / "00-Inbox"
        self.inbox_dir.mkdir(exist_ok=True)
    
    def create_file(
        self,
        file_type: str,
        title: str,
        content: str = "",
        target_dir: Optional[Path] = None
    ) -> tuple[str, Path]:
        """创建文件并返回 (hash, path)
        
        Args:
            file_type: 文件类型（meeting, note, task, email）
            title: 文件标题
            content: 文件内容
            target_dir: 目标目录（默认 Inbox）
        
        Returns:
            (hash_id, file_path) 元组
        """
        # 验证类型（如果提供）
        if file_type is not None:
            valid_types = ['meeting', 'note', 'task', 'email']
            if file_type not in valid_types:
                raise ValueError(f"Invalid file type: {file_type}. Must be one of {valid_types}")
        
        # 生成 Hash
        hash_id = self.hash_mgr.generate_hash()
        
        # 确定位置 (默认 Inbox)
        if target_dir is None:
            target_dir = self.inbox_dir
        
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成临时 ID
        # 计算 Inbox 中已有文件数量
        inbox_count = len(list(self.inbox_dir.glob("*.md"))) + 1
        temp_id = self.schema_mgr.generate_temp_id(inbox_count)
        
        # 构建 Frontmatter
        metadata = {
            'uuid': hash_id,
            'id': temp_id,
            'title': title,
            'status': 'open',
            'created_at': datetime.now().isoformat(),
            'tags': []
        }
        # 只有当 type 不为 None 时才添加 type 字段
        if file_type is not None:
            metadata['type'] = file_type
        
        # 创建 Memo 对象（type 可以为 None）
        memo = Memo(
            uuid=hash_id,
            id=temp_id,
            type=file_type,  # 可以是 None
            title=title,
            status='open',
            created_at=datetime.now(),
            content=content,
        )
        
        # 写入文件
        safe_title = self._sanitize_filename(title)
        file_path = target_dir / f"{hash_id}_{safe_title}.md"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(memo.to_markdown())
        
        # 注册到 Hash Index
        self.hash_mgr.register(hash_id, file_path, temp_id)
        
        # 准备提交的文件列表
        files_to_commit = [file_path]
        # 添加 hash_index.json（如果被修改）
        hash_index_file = self.repo_root / ".mf" / "hash_index.json"
        if hash_index_file.exists():
            files_to_commit.append(hash_index_file)
        
        # 自动提交
        try:
            self.git_engine.auto_commit(
                CommitType.FEAT,
                "new",
                f"capture {title}",
                files_to_commit
            )
        except Exception as e:
            logger.warning(f"Failed to auto-commit: {e}")
        
        return hash_id, file_path
    
    def read_file(self, hash: str) -> Memo:
        """通过哈希读取文件
        
        Args:
            hash: 文件哈希（支持部分匹配）
        
        Returns:
            Memo 对象
        
        Raises:
            FileNotFoundError: 如果文件不存在
            ValueError: 如果找到多个匹配
        """
        paths = self.hash_mgr.resolve(hash)
        if len(paths) > 1:
            raise ValueError(f"Ambiguous hash '{hash}': {len(paths)} matches found")
        
        if len(paths) == 0:
            raise FileNotFoundError(f"Hash '{hash}' not found")
        
        return Memo.from_file(paths[0])
    
    def move_file(
        self,
        hash_id: str,
        old_path: str,
        new_jd_id: str
    ) -> Path:
        """通过 Hash 移动文件到新的 JD 目录
        
        Args:
            hash_id: 文件哈希
            old_path: 旧路径（JD ID，用于验证）
            new_jd_id: 新的 JD ID
        
        Returns:
            新文件路径
        """
        # 解析文件
        old_paths = self.hash_mgr.resolve(hash_id)
        if len(old_paths) > 1:
            raise ValueError(f"Ambiguous hash: {len(old_paths)} matches found")
        if len(old_paths) == 0:
            raise FileNotFoundError(f"Hash '{hash_id}' not found")
        
        old_file_path = old_paths[0]
        
        # 验证 old_path 匹配
        memo = Memo.from_file(old_file_path)
        if memo.id != old_path:
            raise ValueError(f"Old path mismatch: expected {old_path}, got {memo.id}")
        
        # 验证新路径
        if not self.schema_mgr.validate_path(new_jd_id):
            raise ValueError(f"Invalid JD path: {new_jd_id}")
        
        # 更新 Frontmatter
        import frontmatter
        post = frontmatter.load(old_file_path)
        post.metadata['id'] = new_jd_id
        
        # 计算新路径
        new_dir = self.schema_mgr.get_directory_path(new_jd_id)
        new_dir.mkdir(parents=True, exist_ok=True)
        new_path = new_dir / old_file_path.name
        
        # 移动文件
        with open(new_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
        old_file_path.unlink()
        
        # 更新 Hash 索引
        self.hash_mgr.update_path(hash_id, new_path, new_jd_id)
        
        # 准备提交的文件列表
        files_to_commit = [new_path]
        # 添加 hash_index.json（如果被修改）
        hash_index_file = self.repo_root / ".mf" / "hash_index.json"
        if hash_index_file.exists():
            files_to_commit.append(hash_index_file)
        
        # 自动提交（包括旧文件删除和新文件添加）
        try:
            self.git_engine.auto_commit(
                CommitType.REFACTOR,
                hash_id,
                f"move from {old_path} to {new_jd_id}",
                files_to_commit,
                removed_files=[old_file_path]
            )
        except Exception as e:
            logger.warning(f"Failed to auto-commit: {e}")
        
        return new_path
    
    def update_file(
        self,
        hash_id: str,
        content: Optional[str] = None,
        frontmatter_updates: Optional[Dict[str, Any]] = None,
        commit_message: Optional[str] = None
    ) -> Memo:
        """更新文件内容或 frontmatter
        
        Args:
            hash_id: 文件哈希
            content: 新内容（可选）
            frontmatter_updates: frontmatter 更新字典（可选）
            commit_message: 提交消息（可选，如果不提供则根据更新内容自动生成）
        
        Returns:
            更新后的 Memo 对象
        """
        memo = self.read_file(hash_id)
        
        import frontmatter
        post = frontmatter.load(memo.file_path)
        
        if content is not None:
            post.content = content
        
        if frontmatter_updates:
            post.metadata.update(frontmatter_updates)
        
        with open(memo.file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
        
        # 生成 commit message
        if commit_message is None:
            if content is not None:
                commit_message = "update content"
            elif frontmatter_updates:
                # 根据更新的字段生成消息
                updates = []
                for key, value in frontmatter_updates.items():
                    if value is None:
                        updates.append(f"remove {key}")
                    else:
                        updates.append(f"set {key} to {value}")
                commit_message = ", ".join(updates)
            else:
                commit_message = "update file"
        
        # 准备提交的文件列表
        files_to_commit = [memo.file_path]
        # 检查 hash_index.json 是否被修改（通过 register 或 update_path）
        # 注意：update_file 本身不直接修改 hash_index，但为了完整性，我们检查一下
        hash_index_file = self.repo_root / ".mf" / "hash_index.json"
        if hash_index_file.exists():
            # 如果 hash_index 可能被修改（例如通过其他操作），也包含它
            # 但 update_file 本身不修改 hash_index，所以这里不添加
            pass
        
        # 自动提交
        try:
            self.git_engine.auto_commit(
                CommitType.DOCS,
                hash_id,
                commit_message,
                files_to_commit
            )
        except Exception as e:
            logger.warning(f"Failed to auto-commit: {e}")
        
        return Memo.from_file(memo.file_path)
    
    def query(
        self,
        status: Optional[str] = None,
        due_date: Optional[datetime] = None,
        file_type: Optional[str] = None
    ) -> List[Memo]:
        """查询文件
        
        Args:
            status: 状态过滤（open, done, archived）
            due_date: 到期日期过滤
            file_type: 文件类型过滤
        
        Returns:
            匹配的 Memo 列表
        """
        memos = []
        
        # 扫描所有 Markdown 文件
        for md_file in self.repo_root.rglob("*.md"):
            try:
                memo = Memo.from_file(md_file)
                
                # 应用过滤器
                if status and memo.status != status:
                    continue
                if due_date and memo.due_date:
                    if memo.due_date.date() != due_date.date():
                        continue
                elif due_date and not memo.due_date:
                    continue
                if file_type and memo.type != file_type:
                    continue
                
                memos.append(memo)
            except Exception as e:
                logger.debug(f"Failed to parse {md_file}: {e}")
        
        return memos
    
    def _sanitize_filename(self, title: str) -> str:
        """清理文件名，移除非法字符
        
        Args:
            title: 原始标题
        
        Returns:
            清理后的文件名
        """
        # 移除非法字符
        safe = re.sub(r'[^\w\s-]', '', title)
        # 替换多个空格/连字符为单个连字符
        safe = re.sub(r'[-\s]+', '-', safe)
        # 限制长度
        return safe[:50] if len(safe) > 50 else safe
