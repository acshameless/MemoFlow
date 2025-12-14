"""Schema Manager for MemoFlow"""

import logging
from pathlib import Path
from typing import Optional, List, Tuple
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
        """生成临时 ID（用于 Inbox，格式如 `HANK-00.01` 或 `HANK-00.001`）
        
        Args:
            counter: 临时计数器（用于生成唯一ID）
        
        Returns:
            临时 JD ID（使用两位小数格式以保持简洁和兼容性）
        """
        schema = self.load_schema()
        prefix = schema.user_prefix
        # 使用 00 作为 Inbox 区域
        # 临时 ID 使用两位小数格式（00.01, 00.02, ...）以保持简洁
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
    
    def get_available_areas(self) -> List[Tuple[int, str]]:
        """获取所有可用的区域列表
        
        Returns:
            [(area_id, area_name), ...] 列表
        """
        schema = self.load_schema()
        return [(area.id, area.name) for area in schema.areas]
    
    def get_available_categories(self, area_id: int) -> List[Tuple[int, str, Tuple[float, float]]]:
        """获取指定区域下的所有可用类别列表
        
        Args:
            area_id: 区域 ID
        
        Returns:
            [(category_id, category_name, (range_start, range_end)), ...] 列表
        """
        schema = self.load_schema()
        area = schema.get_area(area_id)
        if not area:
            return []
        return [(cat.id, cat.name, cat.range) for cat in area.categories]
    
    def generate_next_id(self, area_id: int, category_id: int, repo_root: Path) -> Optional[str]:
        """为指定区域和类别生成下一个可用的 ID
        
        Args:
            area_id: 区域 ID
            category_id: 类别 ID
            repo_root: 仓库根目录
        
        Returns:
            下一个可用的 JD ID，如果类别不存在则返回 None
        """
        schema = self.load_schema()
        area = schema.get_area(area_id)
        if not area:
            return None
        
        category = area.get_category(category_id)
        if not category:
            return None
        
        # 获取类别范围
        range_start, range_end = category.range
        
        # 确定格式（三位小数还是两位小数）
        range_start_str_3f = f"{range_start:.3f}"
        range_start_str_2f = f"{range_start:.2f}"
        use_three_decimal = (range_start_str_3f.rstrip('0').rstrip('.') != range_start_str_2f.rstrip('0').rstrip('.'))
        
        # 使用 range_start 构建测试 ID 来获取目录路径
        test_id = f"{schema.user_prefix}-{range_start_str_3f if use_three_decimal else range_start_str_2f}"
        category_dir = schema.get_directory_path(test_id, repo_root)
        
        used_ids = set()
        if category_dir.exists():
            for md_file in category_dir.glob("*.md"):
                try:
                    from mf.models.memo import Memo
                    memo = Memo.from_file(md_file)
                    # 解析 ID 获取 item_id
                    from mf.utils.jd import parse_jd_id
                    parsed = parse_jd_id(memo.id)
                    if parsed:
                        _, _, item_id = parsed
                        used_ids.add(item_id)
                except Exception:
                    pass
        
        # 从 range_start 开始查找第一个未使用的 ID
        # 根据格式决定步长
        if use_three_decimal:
            # 三位小数格式，步长为 0.001
            step = 0.001
            current = range_start
            max_iterations = int((range_end - range_start) / step) + 1
            iterations = 0
            while current <= range_end and iterations < max_iterations:
                # 使用 round 避免浮点数精度问题
                current_rounded = round(current, 3)
                if current_rounded not in used_ids:
                    from mf.utils.jd import format_jd_id
                    return format_jd_id(schema.user_prefix, area_id, current_rounded)
                current += step
                current = round(current, 3)
                iterations += 1
        else:
            # 两位小数格式，步长为 0.01
            step = 0.01
            current = range_start
            max_iterations = int((range_end - range_start) / step) + 1
            iterations = 0
            while current <= range_end and iterations < max_iterations:
                # 使用 round 避免浮点数精度问题
                current_rounded = round(current, 2)
                if current_rounded not in used_ids:
                    from mf.utils.jd import format_jd_id
                    return format_jd_id(schema.user_prefix, area_id, current_rounded)
                current += step
                current = round(current, 2)
                iterations += 1
        
        # 如果范围内所有 ID 都被使用，返回 None
        return None
