"""Markdown utility functions"""

import re
from typing import List, Dict, Any
import frontmatter


def parse_frontmatter(file_path: str) -> tuple[Dict[str, Any], str]:
    """解析 Markdown 文件的 frontmatter
    
    Args:
        file_path: 文件路径
    
    Returns:
        (frontmatter_dict, content) 元组
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
    
    return post.metadata, post.content


def validate_frontmatter(metadata: Dict[str, Any]) -> List[str]:
    """验证 frontmatter 必需字段
    
    Args:
        metadata: frontmatter 字典
    
    Returns:
        错误列表（空列表表示无错误）
    """
    required_fields = ['uuid', 'id', 'type', 'title', 'status', 'created_at']
    errors = []
    
    for field in required_fields:
        if field not in metadata:
            errors.append(f"Missing required field: {field}")
    
    # 验证类型
    if 'type' in metadata:
        valid_types = ['meeting', 'note', 'task', 'email']
        if metadata['type'] not in valid_types:
            errors.append(f"Invalid type: {metadata['type']}. Must be one of {valid_types}")
    
    # 验证状态
    if 'status' in metadata:
        valid_statuses = ['open', 'done', 'archived']
        if metadata['status'] not in valid_statuses:
            errors.append(f"Invalid status: {metadata['status']}. Must be one of {valid_statuses}")
    
    return errors


def format_frontmatter(metadata: Dict[str, Any], content: str = "") -> str:
    """格式化 frontmatter 和内容为 Markdown
    
    Args:
        metadata: frontmatter 字典
        content: 内容正文
    
    Returns:
        Markdown 格式字符串
    """
    post = frontmatter.Post(content, **metadata)
    return frontmatter.dumps(post)


def extract_wikilinks(content: str) -> List[str]:
    """提取 [[wikilink]] 链接
    
    Args:
        content: Markdown 内容
    
    Returns:
        链接列表
    """
    pattern = r'\[\[([^\]]+)\]\]'
    matches = re.findall(pattern, content)
    return matches


def extract_hashtags(content: str, metadata: Dict[str, Any] = None) -> List[str]:
    """提取 #hashtag 标签
    
    Args:
        content: Markdown 内容
        metadata: frontmatter（可能包含 tags 字段）
    
    Returns:
        标签列表
    """
    tags = []
    
    # 从 frontmatter 获取
    if metadata and 'tags' in metadata:
        if isinstance(metadata['tags'], list):
            tags.extend(metadata['tags'])
    
    # 从内容中提取
    pattern = r'#(\w+)'
    content_tags = re.findall(pattern, content)
    tags.extend(content_tags)
    
    # 去重
    return list(set(tags))
