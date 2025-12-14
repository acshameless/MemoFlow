"""Schema management commands for MemoFlow"""

import logging
from pathlib import Path
from mf.core.schema_manager import SchemaManager

logger = logging.getLogger(__name__)


def handle_schema_reload(repo_root: Path) -> bool:
    """重新加载 schema.yaml（用于 schema.yaml 更新后）
    
    Args:
        repo_root: 仓库根目录
    
    Returns:
        True 如果成功
    """
    schema_mgr = SchemaManager(repo_root)
    
    try:
        schema = schema_mgr.reload_schema()
        logger.info(f"Reloaded schema: user_prefix={schema.user_prefix}, {len(schema.areas)} areas")
        return True
    except Exception as e:
        logger.error(f"Failed to reload schema: {e}")
        raise


def handle_schema_validate(repo_root: Path) -> bool:
    """验证 schema.yaml 格式是否正确
    
    Args:
        repo_root: 仓库根目录
    
    Returns:
        True 如果格式正确
    """
    schema_mgr = SchemaManager(repo_root)
    
    try:
        schema = schema_mgr.load_schema()
        logger.info(f"Schema is valid: user_prefix={schema.user_prefix}, {len(schema.areas)} areas")
        
        # 打印详细信息
        for area in schema.areas:
            logger.info(f"  Area {area.id}: {area.name} ({len(area.categories)} categories)")
            for category in area.categories:
                logger.info(f"    Category {category.id}: {category.name} (range: {category.range[0]}-{category.range[1]})")
        
        return True
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        raise
