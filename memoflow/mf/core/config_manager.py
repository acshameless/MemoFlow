"""Config Manager for MemoFlow"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器：管理 MemoFlow 仓库配置"""
    
    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root).resolve()
        self.config_file = self.repo_root / ".mf" / "config.json"
        self.config: Dict[str, Any] = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """从文件加载配置，如不存在则返回默认配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.debug(f"Loaded config from {self.config_file}")
                    return config
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load config file: {e}. Using default config.")
                return self._default_config()
        return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """返回默认配置"""
        return {
            "editor": None  # None 表示自动检测
        }
    
    def _save_config(self):
        """保存配置到文件"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved config to {self.config_file}")
        except IOError as e:
            logger.error(f"Failed to save config file: {e}")
            raise
    
    def get_editor(self) -> Optional[str]:
        """获取配置的编辑器"""
        return self.config.get("editor")
    
    def set_editor(self, editor: Optional[str]):
        """设置编辑器配置
        
        Args:
            editor: 编辑器命令（如 'vim', 'typora', 'code', 'notepad'），None 表示自动检测
        """
        self.config["editor"] = editor
        self._save_config()
        logger.info(f"Set editor to: {editor if editor else 'auto-detect'}")
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self.config.copy()
    
    def update_config(self, updates: Dict[str, Any]):
        """更新配置
        
        Args:
            updates: 要更新的配置项字典
        """
        self.config.update(updates)
        self._save_config()
        logger.info(f"Updated config: {updates}")
