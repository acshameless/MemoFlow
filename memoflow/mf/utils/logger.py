"""Logging configuration for MemoFlow"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    repo_root: Optional[Path] = None,
    level: int = logging.INFO,
    log_to_file: bool = False
) -> logging.Logger:
    """配置日志系统
    
    Args:
        repo_root: 仓库根目录（用于日志文件路径）
        level: 日志级别
        log_to_file: 是否输出到文件
    
    Returns:
        配置好的 logger
    """
    logger = logging.getLogger("mf")
    logger.setLevel(level)
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（可选）
    if log_to_file and repo_root:
        log_dir = repo_root / ".mf" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "memoflow.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # 文件记录更详细的日志
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger
