"""Init command for MemoFlow"""

import logging
from pathlib import Path
from typing import Optional
from mf.core.schema_manager import SchemaManager
from mf.core.git_engine import GitEngine
from mf.core.hash_manager import HashManager
from mf.core.config_manager import ConfigManager
from mf.core.file_manager import FileManager
from mf.core.repo_registry import RepoRegistry

logger = logging.getLogger(__name__)


def handle_init(
    repo_root: Path, 
    force: bool = False, 
    preserve_schema: bool = True,
    editor: Optional[str] = None
) -> bool:
    """处理 init 命令
    
    Args:
        repo_root: 仓库根目录（如果不存在会自动创建）
        force: 是否强制初始化（覆盖现有配置）
        preserve_schema: 如果为 True，在重新初始化时保留现有的 schema.yaml（如果格式正确）
        editor: 编辑器命令（如 'vim', 'typora', 'code', 'notepad'），None 表示自动检测
    
    Returns:
        True 如果初始化成功
    """
    repo_path = Path(repo_root).resolve()
    
    # 如果目录不存在，创建它
    if not repo_path.exists():
        repo_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {repo_path}")
    
    # 检查是否已初始化
    mf_dir = repo_path / ".mf"
    schema_file = repo_path / "schema.yaml"
    inbox_dir = repo_path / "00-Inbox"
    
    is_existing_repo = mf_dir.exists() or schema_file.exists() or inbox_dir.exists()
    
    if is_existing_repo:
        if not force:
            raise ValueError(
                f"Repository at {repo_path} appears to be already initialized. "
                "Use --force to reinitialize."
            )
        logger.warning(f"Reinitializing repository at {repo_path}")
        
        # 如果 preserve_schema 为 True，尝试保留现有的 schema.yaml
        if preserve_schema and schema_file.exists():
            try:
                # 尝试加载现有 schema 验证格式
                schema_mgr = SchemaManager(repo_path)
                existing_schema = schema_mgr.load_schema()
                logger.info(f"Preserving existing schema.yaml (user_prefix: {existing_schema.user_prefix}, {len(existing_schema.areas)} areas)")
                # Schema 已加载，后续不需要重新创建
            except Exception as e:
                logger.warning(f"Existing schema.yaml has invalid format: {e}. Will create default schema.")
                # Schema 格式错误，删除它以便创建新的
                schema_file.unlink()
    
    # 创建 .mf 目录
    mf_dir.mkdir(exist_ok=True)
    
    # 初始化 Schema Manager（如果 schema.yaml 不存在或已删除，会创建默认 schema.yaml）
    schema_mgr = SchemaManager(repo_path)
    schema_mgr.load_schema()
    
    # 初始化 Git（如果不存在）
    git_engine = GitEngine(repo_path)
    
    # 创建 Inbox 目录
    inbox_dir.mkdir(exist_ok=True)
    
    # 初始化 Hash Manager（创建索引文件）
    hash_mgr = HashManager(repo_path)
    hash_mgr._save_index()  # 创建空的索引文件
    
    # 初始化配置管理器并设置编辑器
    config_mgr = ConfigManager(repo_path)
    if editor is not None:
        config_mgr.set_editor(editor)
        logger.info(f"Configured editor: {editor}")
    
    # 检查是否需要迁移 user_prefix
    # 如果仓库中已有文件，且 schema 的 user_prefix 与现有文件的前缀不同，提示用户
    if not force:  # 只在非强制初始化时检查（避免在重新初始化时重复提示）
        try:
            hash_mgr = HashManager(repo_path)
            schema_mgr = SchemaManager(repo_path)
            git_engine = GitEngine(repo_path)
            file_mgr = FileManager(repo_path, hash_mgr, schema_mgr, git_engine)
            
            # 获取所有文件
            all_files = file_mgr.query()
            if all_files:
                schema = schema_mgr.get_schema()
                new_prefix = schema.user_prefix
                
                # 检查是否有文件使用不同的前缀
                prefixes_found = set()
                for memo in all_files:
                    if '-' in memo.id:
                        file_prefix = memo.id.split('-')[0]
                        prefixes_found.add(file_prefix)
                
                # 如果发现文件使用的前缀与 schema 中的前缀不同
                if new_prefix not in prefixes_found and prefixes_found:
                    old_prefix = list(prefixes_found)[0]  # 取第一个找到的前缀
                    logger.warning(
                        f"Found files with prefix '{old_prefix}' but schema uses '{new_prefix}'. "
                        f"Run 'mf migrate-prefix {old_prefix} {new_prefix}' to update all file IDs."
                    )
        except Exception as e:
            logger.debug(f"Could not check for prefix migration: {e}")
    
    logger.info(f"Initialized MemoFlow repository at {repo_path}")

    # 注册到全局仓库注册表（使用目录名作为默认名称）
    try:
        registry = RepoRegistry()
        repo_name = repo_path.name
        registry.add_repo(repo_name, repo_path)
        logger.info(f"Registered repo '{repo_name}' at {repo_path} in global registry")
    except Exception as e:
        logger.warning(f"Failed to register repo in global registry: {e}")

    return True
