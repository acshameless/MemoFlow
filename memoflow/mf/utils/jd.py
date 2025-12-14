"""Johnny.Decimal utility functions"""

import re
from typing import Optional, Tuple


def parse_jd_id(jd_id: str) -> Optional[Tuple[str, int, float]]:
    """解析 Johnny.Decimal ID
    
    Args:
        jd_id: JD ID 格式，如 'HANK-12.04' 或 'HANK-11.001'（支持两位或三位小数） 或 'HANK-11.001'（支持两位或三位小数）
    
    Returns:
        (prefix, area_id, item_id) 元组，如果格式无效则返回 None
    """
    match = re.match(r'^([A-Z]+)-(\d+)\.(\d{2,3})$', jd_id)
    if not match:
        return None
    
    prefix, area_id_str, item_id_str = match.groups()
    area_id = int(area_id_str)
    item_id = float(f"{area_id_str}.{item_id_str}")
    
    return (prefix, area_id, item_id)


def format_jd_id(prefix: str, area_id: int, item_id: float) -> str:
    """格式化 Johnny.Decimal ID
    
    Args:
        prefix: 用户前缀
        area_id: 区域 ID
        item_id: 项目 ID（如 12.04 或 11.001）
    
    Returns:
        格式化的 JD ID（自动选择两位或三位小数格式）
    """
    # 根据 item_id 的精度自动选择格式
    # 先格式化为三位小数，然后检查是否需要去除末尾的零
    item_id_str_3f = f"{item_id:.3f}"
    item_id_str_2f = f"{item_id:.2f}"
    
    # 如果三位小数格式去除末尾零后等于两位小数格式，使用两位小数
    # 否则使用三位小数
    if item_id_str_3f.rstrip('0').rstrip('.') == item_id_str_2f.rstrip('0').rstrip('.'):
        item_id_str = item_id_str_2f
    else:
        item_id_str = item_id_str_3f
    
    return f"{prefix}-{item_id_str}"


def validate_jd_id(jd_id: str) -> bool:
    """验证 Johnny.Decimal ID 格式
    
    Args:
        jd_id: 要验证的 JD ID
    
    Returns:
        True 如果格式有效
    """
    return parse_jd_id(jd_id) is not None


def extract_area_id(jd_id: str) -> Optional[int]:
    """从 JD ID 提取区域 ID"""
    parsed = parse_jd_id(jd_id)
    return parsed[1] if parsed else None


def extract_item_id(jd_id: str) -> Optional[float]:
    """从 JD ID 提取项目 ID"""
    parsed = parse_jd_id(jd_id)
    return parsed[2] if parsed else None
