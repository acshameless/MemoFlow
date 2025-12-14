"""Schema Manager for MemoFlow"""

import logging
from pathlib import Path
from typing import Optional
from mf.models.schema import Schema

logger = logging.getLogger(__name__)


class SchemaManager:
    """Schema 管理器：加载和验证 Johnny.Decimal Schema 配置"""
    
    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root).resolve()
        self.schema_file = self.repo_root / "schema.yaml"
        self._schema: Optional[Schema] = None
    
    def load_schema(self) -> Schema:
        """加载 schema.yaml，如不存在则创建默认"""
        if self._schema is not None:
            return self._schema
        
        if self.schema_file.exists():
            try:
                self._schema = Schema.from_yaml(self.schema_file)
                logger.info(f"Loaded schema from {self.schema_file}")
            except Exception as e:
                logger.error(f"Failed to load schema: {e}. Using default schema.")
                self._schema = Schema.default()
                self._save_default_schema()
        else:
            logger.info("Schema file not found, creating default schema")
            self._schema = Schema.default()
            self._save_default_schema()
        
        return self._schema
    
    def _save_default_schema(self):
        """保存默认 schema 到文件"""
        try:
            with open(self.schema_file, 'w', encoding='utf-8') as f:
                f.write(self._schema.to_yaml())
            logger.info(f"Created default schema at {self.schema_file}")
        except IOError as e:
            logger.error(f"Failed to save default schema: {e}")
    
    def validate_path(self, path: str) -> bool:
        """验证 Johnny.Decimal 路径是否有效"""
        schema = self.load_schema()
        return schema.validate_path(path)
    
    def get_area_name(self, area_id: int) -> Optional[str]:
        """获取区域名称"""
        schema = self.load_schema()
        area = schema.get_area(area_id)
        return area.name if area else None
    
    def get_category_name(self, area_id: int, category_id: int) -> Optional[str]:
        """获取类别名称"""
        schema = self.load_schema()
        area = schema.get_area(area_id)
        if not area:
            return None
        category = area.get_category(category_id)
        return category.name if category else None
    
    def generate_temp_id(self, counter: int = 1) -> str:
        """生成临时 ID（用于 Inbox，格式如 `HANK-00.01`）
        
        Args:
            counter: 临时计数器（用于生成唯一ID）
        
        Returns:
            临时 JD ID
        """
        schema = self.load_schema()
        prefix = schema.user_prefix
        # 使用 00 作为 Inbox 区域
        item_id = f"{counter:02d}"
        return f"{prefix}-00.{item_id}"
    
    def get_directory_path(self, jd_id: str) -> Path:
        """根据 Johnny.Decimal ID 获取目录路径"""
        schema = self.load_schema()
        return schema.get_directory_path(jd_id, self.repo_root)
    
    def get_schema(self) -> Schema:
        """获取当前 Schema 对象"""
        return self.load_schema()
    
    def reload_schema(self):
        """重新加载 Schema（用于 schema.yaml 更新后）"""
        self._schema = None
        return self.load_schema()
