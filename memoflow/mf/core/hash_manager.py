"""Hash Manager for MemoFlow"""

import uuid
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HashManager:
    """哈希管理器：生成、存储、查询 Short Hash"""
    
    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root).resolve()
        self.index_file = self.repo_root / ".mf" / "hash_index.json"
        self.index: Dict[str, dict] = self._load_index()
    
    def _load_index(self) -> Dict[str, dict]:
        """从文件加载索引，如不存在则返回空字典"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load index file: {e}. Starting with empty index.")
                return {}
        return {}
    
    def _save_index(self):
        """保存索引到文件"""
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Failed to save index file: {e}")
            raise
    
    def generate_hash(self) -> str:
        """生成唯一的 6 位十六进制哈希
        
        Returns:
            唯一的短哈希字符串（至少6位，如冲突则扩展）
        """
        full_uuid = uuid.uuid4().hex
        short_hash = full_uuid[:6]
        
        # 碰撞检测：如冲突则扩展长度
        length = 6
        max_length = 12  # 安全限制
        attempts = 0
        max_attempts = 100
        
        while short_hash in self.index and attempts < max_attempts:
            attempts += 1
            if length < max_length:
                length += 1
                short_hash = full_uuid[:length]
            else:
                # 重新生成 UUID
                full_uuid = uuid.uuid4().hex
                short_hash = full_uuid[:6]
                length = 6
        
        if short_hash in self.index:
            raise ValueError(f"Failed to generate unique hash after {max_attempts} attempts")
        
        return short_hash
    
    def register(self, hash_id: str, file_path: Path, jd_id: Optional[str] = None):
        """注册 Hash 到文件路径的映射
        
        Args:
            hash_id: 短哈希
            file_path: 文件路径
            jd_id: Johnny.Decimal ID（可选）
        """
        try:
            relative_path = file_path.relative_to(self.repo_root)
        except ValueError:
            # 如果文件不在仓库内，使用绝对路径
            relative_path = file_path
        
        self.index[hash_id] = {
            "path": str(relative_path),
            "id": jd_id,
            "last_updated": datetime.now().isoformat()
        }
        self._save_index()
    
    def resolve(self, partial_hash: str) -> List[Path]:
        """支持部分匹配 (Git-style)，返回匹配的文件路径列表
        
        Args:
            partial_hash: 部分哈希（如 "7f9" 可匹配 "7f9a2b"）
        
        Returns:
            匹配的文件路径列表
        
        Raises:
            FileNotFoundError: 如果没有找到匹配的文件
        """
        matches = [
            (h, self.repo_root / info["path"])
            for h, info in self.index.items()
            if h.startswith(partial_hash)
        ]
        
        if len(matches) == 0:
            raise FileNotFoundError(f"Hash '{partial_hash}' not found")
        
        return [path for _, path in matches]
    
    def get_exact(self, hash_id: str) -> Optional[Path]:
        """获取精确匹配的文件路径
        
        Args:
            hash_id: 完整的哈希
        
        Returns:
            文件路径，如果不存在则返回 None
        """
        if hash_id in self.index:
            return self.repo_root / self.index[hash_id]["path"]
        return None
    
    def update_path(self, hash_id: str, new_path: Path, new_jd_id: Optional[str] = None):
        """文件移动时更新映射
        
        Args:
            hash_id: 短哈希
            new_path: 新文件路径
            new_jd_id: 新的 Johnny.Decimal ID（可选）
        """
        if hash_id not in self.index:
            raise ValueError(f"Hash '{hash_id}' not found in index")
        
        try:
            relative_path = new_path.relative_to(self.repo_root)
        except ValueError:
            relative_path = new_path
        
        self.index[hash_id]["path"] = str(relative_path)
        if new_jd_id:
            self.index[hash_id]["id"] = new_jd_id
        self.index[hash_id]["last_updated"] = datetime.now().isoformat()
        self._save_index()
    
    def rebuild_index(self):
        """重建索引：扫描所有 Markdown 文件"""
        from mf.models.memo import Memo
        
        self.index = {}
        count = 0
        
        for md_file in self.repo_root.rglob("*.md"):
            try:
                memo = Memo.from_file(md_file)
                self.register(memo.uuid, md_file, memo.id)
                count += 1
            except Exception as e:
                # 跳过无法解析的文件
                logger.warning(f"Failed to parse {md_file}: {e}")
        
        self._save_index()
        logger.info(f"Rebuilt index with {count} files")
        return count
    
    def get_all_hashes(self) -> List[str]:
        """获取所有已注册的哈希"""
        return list(self.index.keys())
    
    def get_hash_info(self, hash_id: str) -> Optional[dict]:
        """获取哈希的详细信息"""
        return self.index.get(hash_id)
