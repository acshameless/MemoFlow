"""Schema data model for MemoFlow"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from pathlib import Path
import yaml
import re


@dataclass
class Category:
    """Johnny.Decimal Category"""
    id: int
    name: str
    range: Tuple[float, float]  # (start, end)
    
    def contains(self, item_id: float) -> bool:
        """检查 item_id 是否在此类别范围内"""
        return self.range[0] <= item_id <= self.range[1]


@dataclass
class Area:
    """Johnny.Decimal Area"""
    id: int
    name: str
    categories: List[Category] = field(default_factory=list)
    
    def get_category(self, category_id: int) -> Optional[Category]:
        """根据 category_id 获取类别"""
        for cat in self.categories:
            if cat.id == category_id:
                return cat
        return None


@dataclass
class Schema:
    """Johnny.Decimal Schema"""
    user_prefix: str
    areas: List[Area] = field(default_factory=list)
    
    def validate_path(self, path: str) -> bool:
        """验证 Johnny.Decimal 路径是否有效
        
        Args:
            path: JD ID 格式，如 'HANK-12.04' 或 'HANK-11.001'（支持两位或三位小数）
        
        Returns:
            True 如果路径有效，False 否则
        """
        # 解析路径格式: PREFIX-XX.XX 或 PREFIX-XX.XXX
        match = re.match(r'^([A-Z]+)-(\d+)\.(\d{2,3})$', path)
        if not match:
            return False
        
        prefix, area_id_str, item_id_str = match.groups()
        
        # 检查前缀
        if prefix != self.user_prefix:
            return False
        
        # 检查区域
        area_id = int(area_id_str)
        area = self.get_area(area_id)
        if not area:
            return False
        
        # 检查类别和项目ID
        item_id = float(f"{area_id_str}.{item_id_str}")
        for category in area.categories:
            if category.contains(item_id):
                return True
        
        return False
    
    def get_area(self, area_id: int) -> Optional[Area]:
        """根据 area_id 获取区域"""
        for area in self.areas:
            if area.id == area_id:
                return area
        return None
    
    def get_directory_path(self, jd_id: str, repo_root: Path) -> Path:
        """根据 Johnny.Decimal ID 获取目录路径
        
        Args:
            jd_id: JD ID 格式，如 'HANK-12.04' 或 'HANK-11.001'（支持两位或三位小数）
            repo_root: 仓库根目录
        
        Returns:
            文件应该存放的目录路径
        """
        # 解析 JD ID (支持两位或三位小数: XX.XX 或 XX.XXX)
        match = re.match(r'^([A-Z]+)-(\d+)\.(\d{2,3})$', jd_id)
        if not match:
            raise ValueError(f"Invalid JD ID format: {jd_id}")
        
        prefix, area_id_str, item_id_str = match.groups()
        area_id = int(area_id_str)
        item_id = float(f"{area_id_str}.{item_id_str}")
        
        # 获取区域
        area = self.get_area(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found in schema")
        
        # 查找包含此 item_id 的类别
        category = None
        for cat in area.categories:
            if cat.contains(item_id):
                category = cat
                break
        
        if not category:
            raise ValueError(f"Item ID {item_id} not found in any category of area {area_id}")
        
        # 构建目录路径: XX-XX/XX.XXX-XX.XXX/
        area_range = f"{area_id}-{area_id + 10}"
        # 根据 range 的精度自动选择格式（支持 .XX 和 .XXX）
        range_start = category.range[0]
        range_end = category.range[1]
        # 检查是否需要三位小数（如果 range 包含三位小数部分）
        if range_start % 0.01 >= 0.001 or range_end % 0.01 >= 0.001:
            category_range = f"{range_start:.3f}-{range_end:.3f}"
        else:
            category_range = f"{range_start:.2f}-{range_end:.2f}"
        
        return repo_root / area_range / category_range
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'Schema':
        """从 YAML 文件加载 Schema"""
        if not yaml_path.exists():
            raise FileNotFoundError(f"Schema file not found: {yaml_path}")
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            raise ValueError("Schema file is empty")
        
        user_prefix = data.get('user_prefix', 'HANK')
        areas_data = data.get('areas', [])
        
        areas = []
        for area_data in areas_data:
            area_id = area_data['id']
            area_name = area_data['name']
            categories_data = area_data.get('categories', [])
            
            categories = []
            for cat_data in categories_data:
                cat_id = cat_data['id']
                cat_name = cat_data['name']
                cat_range = tuple(cat_data['range'])
                categories.append(Category(id=cat_id, name=cat_name, range=cat_range))
            
            areas.append(Area(id=area_id, name=area_name, categories=categories))
        
        return cls(user_prefix=user_prefix, areas=areas)
    
    def to_yaml(self) -> str:
        """转换为 YAML 格式"""
        data = {
            'user_prefix': self.user_prefix,
            'areas': []
        }
        
        for area in self.areas:
            area_data = {
                'id': area.id,
                'name': area.name,
                'categories': []
            }
            
            for category in area.categories:
                cat_data = {
                    'id': category.id,
                    'name': category.name,
                    'range': list(category.range)
                }
                area_data['categories'].append(cat_data)
            
            data['areas'].append(area_data)
        
        return yaml.dump(data, allow_unicode=True, default_flow_style=False)
    
    @classmethod
    def default(cls) -> 'Schema':
        """创建默认 Schema"""
        return cls(
            user_prefix="HANK",
            areas=[
                Area(
                    id=10,
                    name="项目",
                    categories=[
                        Category(id=1, name="规划", range=(10.001, 10.099)),
                        Category(id=2, name="执行", range=(10.100, 10.199)),
                    ]
                ),
                Area(
                    id=20,
                    name="学习",
                    categories=[
                        Category(id=1, name="阅读", range=(20.001, 20.099)),
                        Category(id=2, name="实践", range=(20.100, 20.199)),
                    ]
                ),
            ]
        )
