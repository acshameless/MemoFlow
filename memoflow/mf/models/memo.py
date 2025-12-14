"""Memo data model for MemoFlow"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import frontmatter
from dateutil.parser import parse as parse_date


@dataclass
class Memo:
    """MemoFlow 文件数据模型"""
    uuid: str                    # 短哈希（不可变）
    id: str                      # Johnny.Decimal ID（可变）
    title: str
    status: str                  # open, done, archived
    created_at: datetime
    type: Optional[str] = None   # meeting, note, task, email, 或 None（未分类）
    due_date: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    content: str = ""            # Markdown 正文
    file_path: Optional[Path] = None
    
    def to_frontmatter(self) -> dict:
        """转换为 frontmatter 字典"""
        metadata = {
            "uuid": self.uuid,
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }
        # 只有当 type 不为 None 且不为空时才添加 type 字段
        if self.type:
            metadata["type"] = self.type
        
        if self.due_date:
            metadata["due_date"] = self.due_date.isoformat()
        
        if self.tags:
            metadata["tags"] = self.tags
        
        return metadata
    
    @classmethod
    def from_file(cls, file_path: Path) -> 'Memo':
        """从文件解析 Memo"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        # 验证必需字段（type 是可选的）
        required_fields = ['uuid', 'id', 'title', 'status', 'created_at']
        missing_fields = [field for field in required_fields if field not in post.metadata]
        if missing_fields:
            raise ValueError(f"Missing required fields in frontmatter: {missing_fields}")
        
        # 解析日期字段
        created_at = post.metadata['created_at']
        if isinstance(created_at, str):
            created_at = parse_date(created_at)
        
        due_date = post.metadata.get('due_date')
        if due_date and isinstance(due_date, str):
            due_date = parse_date(due_date)
        
        # 获取标签
        tags = post.metadata.get('tags', [])
        if not isinstance(tags, list):
            tags = []
        
        return cls(
            uuid=post.metadata['uuid'],
            id=post.metadata['id'],
            type=post.metadata.get('type'),  # type 是可选的
            title=post.metadata['title'],
            status=post.metadata['status'],
            created_at=created_at,
            due_date=due_date,
            tags=tags,
            content=post.content,
            file_path=file_path,
        )
    
    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        post = frontmatter.Post(self.content, **self.to_frontmatter())
        return frontmatter.dumps(post)
    
    def validate(self) -> List[str]:
        """验证 Memo 数据的有效性，返回错误列表"""
        errors = []
        
        # 验证类型（如果提供）
        if self.type:
            valid_types = ['meeting', 'note', 'task', 'email']
            if self.type not in valid_types:
                errors.append(f"Invalid type: {self.type}. Must be one of {valid_types}")
        
        # 验证状态
        valid_statuses = ['open', 'done', 'archived']
        if self.status not in valid_statuses:
            errors.append(f"Invalid status: {self.status}. Must be one of {valid_statuses}")
        
        # 验证 UUID 格式（6位十六进制）
        if not self.uuid or len(self.uuid) < 6:
            errors.append(f"Invalid UUID: {self.uuid}. Must be at least 6 characters")
        
        # 验证 ID 格式（Johnny.Decimal，支持 XX.XX 或 XX.XXX）
        if not self.id or '-' not in self.id:
            errors.append(f"Invalid ID format: {self.id}. Must be in format PREFIX-XX.XX or PREFIX-XX.XXX")
        else:
            # 检查格式是否符合 JD ID 规范
            import re
            if not re.match(r'^[A-Z]+-\d+\.\d{2,3}$', self.id):
                errors.append(f"Invalid ID format: {self.id}. Must be in format PREFIX-XX.XX or PREFIX-XX.XXX")
        
        return errors
