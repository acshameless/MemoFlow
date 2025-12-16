# MemoFlow 实施计划

本文档将 MemoFlow 的设计转换为一系列可执行的编码任务。每个任务都是面向代码生成 LLM 的提示，采用测试驱动开发方法，确保增量式构建和早期验证。

---

## 1. 项目初始化和基础架构

### 1.1 创建项目结构和依赖配置

- [ ] 创建项目目录结构：`memoflow/mf/` 及其子目录（`core/`, `commands/`, `views/`, `models/`, `utils/`, `integrations/`）
- [ ] 创建 `pyproject.toml` 文件，配置项目元数据和依赖：
  - Python >= 3.9
  - typer（CLI 框架）
  - gitpython（Git 操作）
  - pyyaml（YAML 解析）
  - python-frontmatter（Markdown frontmatter 处理）
  - pytest（测试框架）
  - pytest-cov（代码覆盖率）
- [ ] 创建所有必要的 `__init__.py` 文件
- [ ] 创建 `README.md` 基础文档
- [ ] 创建 `.gitignore` 文件

**参考需求**：需求 8.1（平台要求）

---

## 2. 数据模型实现

### 2.1 实现 Memo 数据模型

- [ ] 在 `mf/models/memo.py` 中创建 `Memo` 数据类：
  - 字段：`uuid`, `id`, `type`, `title`, `status`, `created_at`, `due_date`, `tags`, `content`, `file_path`
  - 实现 `to_frontmatter()` 方法：将 Memo 转换为 frontmatter 字典
  - 实现 `from_file()` 类方法：从 Markdown 文件解析 Memo
  - 实现 `to_markdown()` 方法：将 Memo 转换为 Markdown 格式字符串
- [ ] 编写单元测试：测试 Memo 的创建、序列化和反序列化
- [ ] 编写测试：验证必需字段验证（需求 1.3）

**参考需求**：需求 1.3（Markdown 文件结构）

### 2.2 实现 Schema 数据模型

- [ ] 在 `mf/models/schema.py` 中创建数据类：
  - `Category`：包含 `id`, `name`, `range`
  - `Area`：包含 `id`, `name`, `categories`
  - `Schema`：包含 `user_prefix`, `areas`
- [ ] 实现 `Schema.validate_path()` 方法：验证 Johnny.Decimal 路径是否有效
- [ ] 实现 `Schema.get_directory_path()` 方法：根据 JD ID 获取目录路径
- [ ] 编写单元测试：测试 Schema 加载、验证和路径解析

**参考需求**：需求 1.2（Schema 配置）

---

## 3. 核心服务层实现

### 3.1 实现 Hash Manager（哈希管理器）

- [ ] 在 `mf/core/hash_manager.py` 中创建 `HashManager` 类：
  - `__init__()`：初始化，加载索引文件 `.mf/hash_index.json`
  - `_load_index()`：从文件加载索引，如不存在返回空字典
  - `_save_index()`：保存索引到文件
  - `generate_hash()`：生成唯一的 6 位十六进制哈希，处理冲突（需求 9.1）
  - `register()`：注册 Hash 到文件路径的映射
  - `resolve()`：支持部分匹配查找文件（Git-style）
  - `update_path()`：文件移动时更新索引
  - `rebuild_index()`：重建索引（扫描所有 Markdown 文件）
- [ ] 编写单元测试：
  - 测试哈希生成唯一性（需求 1.1）
  - 测试冲突检测和处理（需求 9.1）
  - 测试部分哈希匹配（需求 3.1）
  - 测试索引持久化
- [ ] 编写集成测试：测试索引文件读写

**参考需求**：需求 1.1（双重索引系统）、需求 3.1（基于哈希的文件移动）、需求 9.1（哈希冲突处理）

### 3.2 实现 Schema Manager（Schema 管理器）

- [ ] 在 `mf/core/schema_manager.py` 中创建 `SchemaManager` 类：
  - `load_schema()`：加载 `schema.yaml`，如不存在则创建默认 schema（需求 1.2）
  - `validate_path()`：验证 Johnny.Decimal 路径是否有效
  - `get_area_name()`：获取区域名称
  - `get_category_name()`：获取类别名称
  - `generate_temp_id()`：生成临时 ID（用于 Inbox，格式如 `HANK-00.01`）
  - `get_directory_path()`：根据 JD ID 获取目录路径
- [ ] 实现默认 schema 生成逻辑
- [ ] 编写单元测试：
  - 测试 schema 加载（需求 1.2）
  - 测试路径验证（需求 1.2）
  - 测试临时 ID 生成
- [ ] 编写集成测试：测试 schema 文件不存在时的默认创建

**参考需求**：需求 1.2（Schema 配置）

### 3.3 实现 Git Engine（Git 引擎）

- [ ] 在 `mf/core/git_engine.py` 中创建 `GitEngine` 类：
  - 定义 `CommitType` 枚举：`FEAT`, `REFACTOR`, `DOCS`, `CHORE`
  - `__init__()`：初始化，确保 Git 仓库存在（需求 2.2）
  - `_ensure_repo()`：如 Git 未初始化则自动初始化
  - `auto_commit()`：自动 Stage + Commit，遵循 Angular Convention（需求 2.2）
  - `parse_timeline()`：解析 Git Log 生成时间轴（需求 4.3）
  - `push()`：推送到远程仓库（可选，配置化）
- [ ] 编写单元测试：
  - 测试自动初始化 Git（需求 2.2）
  - 测试提交消息格式（需求 2.2）
  - 测试时间轴解析（需求 4.3）
- [ ] 编写集成测试：使用临时 Git 仓库测试完整流程

**参考需求**：需求 2.2（自动 Git 集成）、需求 4.3（时间轴视图）、需求 9.3（Git 集成边界情况）

### 3.4 实现 File Manager（文件管理器）

- [ ] 在 `mf/core/file_manager.py` 中创建 `FileManager` 类：
  - `__init__()`：初始化，创建 Inbox 目录
  - `create_file()`：创建新文件，生成哈希和临时ID，存入 Inbox（需求 2.1）
  - `read_file()`：通过哈希读取文件（需求 3.1）
  - `update_file()`：更新文件内容或 frontmatter（需求 2.2）
  - `move_file()`：移动文件到新位置，更新 frontmatter 中的 id（需求 3.1）
  - `_sanitize_filename()`：清理文件名，移除非法字符
- [ ] 编写单元测试：
  - 测试文件创建（需求 2.1）
  - 测试文件读取（需求 1.3）
  - 测试文件移动（需求 3.1）
  - 测试 frontmatter 更新（需求 1.3）
- [ ] 编写集成测试：测试文件创建、移动、更新的完整流程

**参考需求**：需求 2.1（快速捕获命令）、需求 3.1（基于哈希的文件移动）、需求 1.3（Markdown 文件结构）

---

## 4. CLI 命令实现

### 4.1 实现 CLI 框架和基础命令结构

- [ ] 在 `mf/cli.py` 中创建 Typer 应用：
  - 使用 Typer 创建主应用
  - 定义命令组结构
- [ ] 创建 `mf/commands/__init__.py` 和命令模块占位符
- [ ] 编写测试：测试 CLI 框架初始化

**参考需求**：需求 8.1（平台要求）

### 4.2 实现 capture 命令

- [ ] 在 `mf/commands/capture.py` 中实现 `handle_capture()` 函数：
  - 验证文件类型（`meeting`, `note`, `task`, `email`）（需求 2.1）
  - 调用 `FileManager.create_file()` 创建文件
  - 调用 `GitEngine.auto_commit()` 自动提交（需求 2.2）
  - 输出创建成功消息（包含哈希）
- [ ] 在 `mf/cli.py` 中注册 `capture` 命令
- [ ] 编写测试：
  - 测试有效类型捕获（需求 2.1）
  - 测试无效类型拒绝（需求 2.1）
  - 测试自动 Git 提交（需求 2.2）

**参考需求**：需求 2.1（快速捕获命令）、需求 2.2（自动 Git 集成）

### 4.3 实现 move 命令

- [ ] 在 `mf/commands/organize.py` 中实现 `handle_move()` 函数：
  - 使用 `HashManager.resolve()` 定位文件（支持部分匹配）（需求 3.1）
  - 验证 `old_path` 与文件实际路径匹配（需求 3.1）
  - 验证 `new_path` 有效性（需求 3.1）
  - 调用 `FileManager.move_file()` 移动文件
  - 调用 `GitEngine.auto_commit()` 自动提交（需求 2.2）
- [ ] 在 `mf/cli.py` 中注册 `move` 命令
- [ ] 编写测试：
  - 测试哈希定位（需求 3.1）
  - 测试路径验证（需求 3.1）
  - 测试多匹配处理（需求 3.1）
  - 测试自动 Git 提交（需求 2.2）

**参考需求**：需求 3.1（基于哈希的文件移动）、需求 2.2（自动 Git 集成）

### 4.4 实现 finish 命令

- [ ] 在 `mf/commands/engage.py` 中实现 `mark_finished()` 函数：
  - 使用 `HashManager.resolve()` 定位文件（需求 5.1）
  - 调用 `FileManager.update_file()` 更新 `status` 为 "done"（需求 5.1）
  - 调用 `GitEngine.auto_commit()` 自动提交（需求 2.2）
  - 处理已完成的文件（需求 5.1）
- [ ] 在 `mf/cli.py` 中注册 `finish` 命令
- [ ] 编写测试：
  - 测试任务完成（需求 5.1）
  - 测试已完成任务处理（需求 5.1）
  - 测试自动 Git 提交（需求 2.2）

**参考需求**：需求 5.1（任务完成）、需求 2.2（自动 Git 集成）

---

## 5. 视图层实现

### 5.1 实现 list 视图

- [ ] 在 `mf/views/list_view.py` 中实现列表视图：
  - 扫描目录结构，构建树形结构（需求 4.1）
  - 显示 Johnny.Decimal ID 和短哈希（需求 4.1）
  - 显示文件元数据（类型、状态、标题）（需求 4.1）
  - 支持树形格式输出
- [ ] 在 `mf/cli.py` 中注册 `list` 命令
- [ ] 编写测试：测试列表视图输出格式

**参考需求**：需求 4.1（列表视图）

### 5.2 实现 status 视图

- [ ] 在 `mf/views/status_view.py` 中实现状态视图：
  - 计算 Inbox 文件数量（需求 4.2）
  - 计算 `status: open` 文件数量（需求 4.2）
  - 构建哈希到文件映射表（需求 4.2）
  - 格式化输出
- [ ] 在 `mf/cli.py` 中注册 `status` 命令
- [ ] 编写测试：测试状态视图计算和输出

**参考需求**：需求 4.2（状态视图）

### 5.3 实现 timeline 视图

- [ ] 在 `mf/views/timeline_view.py` 中实现时间轴视图：
  - 调用 `GitEngine.parse_timeline()` 解析 Git 日志（需求 4.3）
  - 按时间顺序渲染条目（需求 4.3）
  - 显示提交消息、时间戳、文件哈希（需求 4.3）
  - 支持按日期范围、类型、哈希过滤（需求 4.3）
- [ ] 在 `mf/cli.py` 中注册 `timeline` 命令，支持 `--since`, `--type` 选项
- [ ] 编写测试：测试时间轴解析和过滤

**参考需求**：需求 4.3（时间轴视图）

### 5.4 实现 calendar 视图

- [ ] 在 `mf/views/calendar_view.py` 中实现日历视图：
  - 扫描所有文件的 `due_date` 字段（需求 4.4）
  - 按日期组织文件（需求 4.4）
  - 显示文件标题、哈希、状态（需求 4.4）
  - 突出显示过期项目（需求 4.4）
- [ ] 在 `mf/cli.py` 中注册 `calendar` 命令，支持 `--month` 选项
- [ ] 编写测试：测试日历视图生成

**参考需求**：需求 4.4（日历视图）

---

## 6. 任务聚合功能

### 6.1 实现任务聚合查询

- [ ] 在 `mf/core/file_manager.py` 中添加 `query()` 方法：
  - 支持按 `status` 查询（需求 5.2）
  - 支持按 `due_date` 查询（需求 6.2）
  - 支持按 `type` 查询
  - 返回符合条件的 Memo 列表
- [ ] 编写测试：测试各种查询条件

**参考需求**：需求 5.2（任务聚合）、需求 6.2（晨间唤醒工作流）

---

## 7. GitHub Actions 自动化

### 7.1 实现 CI 命令

- [ ] 在 `mf/commands/ci.py` 中实现 `handle_ci()` 函数：
  - 检测模式（morning/evening）（需求 6.4）
  - Morning 模式：扫描今日到期任务，生成 `Daily_Focus.md`（需求 6.2）
  - Evening 模式：分析今日 Git Log，生成 `Daily_Review.md`（需求 6.3）
  - 非交互模式运行（需求 6.4）
  - 适当的错误代码退出（需求 6.4）
- [ ] 在 `mf/cli.py` 中注册 `ci` 命令
- [ ] 编写测试：测试 CI 命令的两种模式

**参考需求**：需求 6.2（晨间唤醒工作流）、需求 6.3（晚间复盘工作流）、需求 6.4（CI 命令接口）

### 7.2 创建 GitHub Actions 工作流

- [ ] 创建 `.github/workflows/morning_wake.yml`：
  - 定时触发（每天 8:00，可配置时区）（需求 6.2）
  - 安装 Python 和 MemoFlow
  - 执行 `mf ci --mode morning`
  - 自动提交和推送 `Daily_Focus.md`（需求 6.2）
- [ ] 创建 `.github/workflows/evening_review.yml`：
  - 定时触发（每天 23:00，可配置时区）（需求 6.3）
  - 安装 Python 和 MemoFlow
  - 执行 `mf ci --mode evening`
  - 自动提交和推送 `Daily_Review.md`（需求 6.3）
- [ ] 编写文档：说明如何配置 GitHub Actions

**参考需求**：需求 6.1（GitHub Actions 集成）、需求 6.2（晨间唤醒工作流）、需求 6.3（晚间复盘工作流）

---

## 8. 错误处理和边界情况

### 8.1 实现错误处理框架

- [ ] 在 `mf/utils/exceptions.py` 中定义异常类：
  - `MemoFlowError`：基础异常类
  - `HashCollisionError`：哈希冲突异常（需求 9.1）
  - `InvalidPathError`：无效路径异常（需求 3.1）
  - `FileNotFoundError`：文件未找到异常（需求 3.1）
  - `SchemaValidationError`：Schema 验证异常（需求 1.2）
- [ ] 在关键位置添加错误处理逻辑
- [ ] 编写测试：测试各种错误场景

**参考需求**：需求 8.3（错误处理）、需求 9.1（哈希冲突处理）、需求 9.2（文件系统边界情况）

### 8.2 实现日志记录

- [ ] 在 `mf/utils/logger.py` 中配置日志系统：
  - 使用 Python `logging` 模块（需求 8.3）
  - 配置日志级别（DEBUG, INFO, WARNING, ERROR）
  - 控制台输出（INFO+）
  - 可选文件输出（`.mf/logs/`）
- [ ] 在关键操作点添加日志记录
- [ ] 编写测试：测试日志记录

**参考需求**：需求 8.3（错误处理）

---

## 9. 工具函数实现

### 9.1 实现 Johnny.Decimal 工具函数

- [ ] 在 `mf/utils/jd.py` 中实现工具函数：
  - `parse_jd_id()`：解析 JD ID（如 `HANK-12.04`）
  - `format_jd_id()`：格式化 JD ID
  - `validate_jd_id()`：验证 JD ID 格式
- [ ] 编写测试：测试 JD 工具函数

**参考需求**：需求 1.2（Schema 配置）

### 9.2 实现 Markdown 工具函数

- [ ] 在 `mf/utils/markdown.py` 中实现工具函数：
  - `parse_frontmatter()`：解析 frontmatter（使用 python-frontmatter）
  - `validate_frontmatter()`：验证必需字段（需求 1.3）
  - `format_frontmatter()`：格式化 frontmatter
- [ ] 编写测试：测试 Markdown 工具函数

**参考需求**：需求 1.3（Markdown 文件结构）

---

## 10. 初始化命令

### 10.1 实现 init 命令

- [ ] 在 `mf/commands/init.py` 中实现 `handle_init()` 函数：
  - 检查目录是否已初始化
  - 创建 `.mf/` 目录
  - 创建默认 `schema.yaml`（需求 1.2）
  - 初始化 Git 仓库（如不存在）（需求 2.2）
  - 创建 `00-Inbox` 目录
- [ ] 在 `mf/cli.py` 中注册 `init` 命令
- [ ] 编写测试：测试初始化流程

**参考需求**：需求 1.2（Schema 配置）、需求 2.2（自动 Git 集成）

---

## 11. 索引重建命令

### 11.1 实现 rebuild-index 命令

- [ ] 在 `mf/commands/organize.py` 中添加 `handle_rebuild_index()` 函数：
  - 调用 `HashManager.rebuild_index()` 重建索引
  - 显示重建结果统计
- [ ] 在 `mf/cli.py` 中注册 `rebuild-index` 命令
- [ ] 编写测试：测试索引重建

**参考需求**：需求 1.1（双重索引系统）

---

## 12. 图谱同步功能（可选，Phase 5）

### 12.1 实现 Nebula Graph 连接

- [ ] 在 `mf/integrations/nebula_sync.py` 中实现 `GraphSyncService` 类：
  - `connect()`：连接到 Nebula Graph（需求 7.1）
  - 使用 `nebula3-python` 客户端
  - 配置连接池
- [ ] 编写测试：测试连接功能（需要 Mock 或测试环境）

**参考需求**：需求 7.1（图谱同步）

### 12.2 实现图谱同步逻辑

- [ ] 实现 `sync_all()`：同步所有文件到图谱（需求 7.1）
- [ ] 实现 `sync_file()`：同步单个文件（需求 7.1）
- [ ] 实现 `extract_links()`：提取 `[[wikilink]]` 链接（需求 7.1）
- [ ] 实现 `extract_tags()`：提取 `#hashtag` 标签（需求 7.1）
- [ ] 创建节点（使用短哈希作为节点 ID）（需求 7.1）
- [ ] 创建边（LINKS_TO, TAGGED_WITH, PARENT_OF）（需求 7.1）
- [ ] 实现增量更新（需求 7.1）
- [ ] 在 `mf/cli.py` 中注册 `sync-graph` 命令
- [ ] 编写测试：测试同步逻辑

**参考需求**：需求 7.1（图谱同步）

---

## 13. 集成测试和端到端测试

### 13.1 编写端到端测试场景

- [ ] 测试完整工作流：初始化 → 捕获 → 移动 → 完成（需求 2.1, 3.1, 5.1）
- [ ] 测试 Git 提交消息格式（需求 2.2）
- [ ] 测试文件系统结构（需求 1.2）
- [ ] 测试视图命令输出（需求 4.1, 4.2, 4.3, 4.4）
- [ ] 测试 CI 命令（需求 6.2, 6.3）

**参考需求**：需求 8.2（数据完整性）

---

## 14. 文档和打包

### 14.1 完善文档

- [ ] 更新 `README.md`：安装说明、使用示例、命令参考
- [ ] 创建 `CONTRIBUTING.md`：贡献指南
- [ ] 创建 `CHANGELOG.md`：变更日志

### 14.2 配置打包

- [ ] 配置 `pyproject.toml` 的打包选项
- [ ] 配置入口点：`[project.scripts]` 中定义 `mf` 命令
- [ ] 测试安装：`pip install -e .`

---

## 15. Namespace & 资源视图（k9s 风格）

### 15.1 实现 Repo Registry 与命名空间命令

- [ ] **15.1.1 实现/完善 RepoRegistry（仓库注册表）**
  - 使用 `~/.memoflow/repos.json` 存储命名空间：
    - 结构：`{"repos": [{"name": "<name>", "path": "<abs_path>"}]}`。
  - 提供方法：
    - `list_repos() -> List[RegisteredRepo]`
    - `add_repo(name: str, path: Path)`（避免重复 name/path，处理冲突时记录日志）
    - `get_by_name(name: str) -> Optional[RegisteredRepo]`
    - `find_by_path(path: Path) -> Optional[RegisteredRepo]`
    - `remove_by_name(name: str) -> bool`
    - `remove_by_path(path: Path) -> bool`
  - **参考需求**：10.1（命名空间与仓库注册表）

- [ ] **15.1.2 在 init 流程中自动注册命名空间**
  - 更新 `mf/commands/init.py` 的 `handle_init()`：
    - 初始化成功后，使用目录名作为默认 `name`，仓库根目录作为 `path` 调用 `RepoRegistry.add_repo(...)`。
    - 记录日志（INFO）标明已注册。
  - 编写测试：
    - 在临时目录中执行 `handle_init()` 后，检查 `~/.memoflow/repos.json` 是否包含对应条目（可通过注入测试用 registry 文件路径实现）。
  - **参考需求**：10.1（在 init 时写入注册表）

- [ ] **15.1.3 实现 `mf repo list` 命令**
  - 在 `mf/cli.py` 中为 `repo_app` 添加 `repo list` 子命令：
    - 调用 `RepoRegistry.list_repos()`。
    - 无数据时输出友好提示（例如 `No repositories registered yet. Initialize one with 'mf init'.`）。
    - 有数据时按表格/行格式输出 `name` 和 `path`。
  - 编写 CLI 测试：
    - 使用 Typer 的 `CliRunner` 或等效工具验证输出格式和空列表行为。
  - **参考需求**：10.1（`mf repo list`）

- [ ] **15.1.4 实现 `mf repo info` 命令**
  - 在 `mf/cli.py` 中完善 `repo info` 子命令：
    - 支持 `mf repo info <name>`：
      - 从 `RepoRegistry.get_by_name(name)` 获取路径，若不存在则退出并报错。
    - 支持 `mf repo info`（无 name）：
      - 使用 `--repo/-r` 或全局 `_global_repo`，若都为空则使用当前目录，通过 `get_repo_root()` 解析仓库根。
      - 尝试在注册表中查找该路径；若不存在则使用目录名作为 name 自动注册一条新命名空间记录。
    - 加载 `schema.yaml` 和 `.mf/hash_index.json`，使用现有服务（`SchemaManager`、`FileManager`、`HashManager` 等）：
      - 计算 `user_prefix`、Areas 数、Categories 总数。
      - 查询所有 Memo，计算总数和 Inbox 文件数（与 `status` 视图定义保持一致）。
    - 以清晰的行格式输出信息（`Repo name / Path / User prefix / Areas / Categories / Files (Inbox: N)`）。
  - 编写 CLI 测试：
    - `mf repo info <name>` 正常路径；
    - 当前目录为 MemoFlow 仓库时的自动注册行为；
    - 错误路径 / 未找到 name 的错误提示。
  - **参考需求**：10.1（`mf repo info`）

- [ ] **15.1.5 实现 `mf repo rm` 命令并替代 `mf rm-repo`**
  - 在 `mf/cli.py` 的 `repo_app` 下实现 `repo rm` 子命令：
    - 接受参数：
      - `name`（可选）：命名空间名；
      - `--repo/-r`（可选）：路径或名称；
      - `--yes/-y`（必需）：确认删除。
    - 解析目标仓库：
      - 若提供 `name`：从注册表获取路径；
      - 否则使用 `--repo/-r` 或 `_global_repo` 或当前目录解析仓库根路径；
      - 若解析失败或路径下无 `.mf`/`schema.yaml`，则退出并提示“未检测到 MemoFlow 仓库”。
    - 调用现有 `handle_remove_repo(repo_root, force=True)` 删除 MemoFlow 相关资源：
      - `.mf/`、`schema.yaml`、`00-Inbox/`、JD 区间目录等。
    - 删除后更新注册表：
      - 若通过 name 调用，则使用 `remove_by_name(name)`；
      - 否则使用 `remove_by_path(repo_root)`。
    - 输出删除结果（包含删除的条目数量和目标路径）。
  - 移除或废弃旧的 `mf rm-repo` 命令入口，确保新规范只有 `mf repo rm`。
  - 编写 CLI 测试：
    - 删除存在的命名空间（含注册表项）；
    - 使用 `--repo` 路径删除；
    - 未提供 `--yes` 时的拒绝行为。
  - **参考需求**：10.2（命名空间删除与清理）

---

### 15.2 TUI 资源导航（Namespace / Area / Category / Item）

- [ ] **15.2.1 在 Status TUI 顶部增加资源上下文条**
  - 在 `mf/views/status_tui.py` 中：
    - 在布局中预留一行或一块区域，用于显示当前上下文信息：
      - `NS: <repo_name> | Area: <area_id or All> | Category: <category_id or All> | View: <Items/Tasks/Meetings/...>`。
    - 利用现有的 repo_root 和（未来的）RepoRegistry 解析当前命名空间名称（没有注册时可使用目录名）。
    - 确保在变更 Area/Category/视图时，该上下文条能即时刷新。
  - 编写 TUI 层测试（如已有 snapshot/结构测试），至少验证上下文条文本构造逻辑。
  - **参考需求**：11.1（资源分层模型）

- [ ] **15.2.2 Area 选择视图**
  - 在 `status_tui.py` 中新增一个用于选择 Area 的简单视图或对话框：
    - 通过 `SchemaManager` 读取当前 repo 的 `schema.areas`。
    - 显示所有 Areas：`id` + `name` + 类别数量。
  - 为 TUI 分配一个快捷键（例如 `a` 或 `A`），用于打开 Area 选择视图。
  - 当用户在 Area 列表中选择某个 Area 并确认时：
    - 更新内部状态（例如 `self.current_area_id`）。
    - 调用现有的过滤逻辑，基于 JD ID 范围过滤 `self.filtered_files`。
    - 更新上下文条中的 `Area` 显示。
  - 编写测试：
    - 给定一个包含多个 Area 的 schema，验证过滤后只剩下指定 Area 范围内的 Memo。
  - **参考需求**：11.1（Area 选择与过滤）

- [ ] **15.2.3 Category 选择视图**
  - 在 Area 已选定的前提下，为 Category 增加类似的选择视图：
    - 显示当前 Area 下的所有 Categories：`id` + `name` + `range`。
  - 为 TUI 分配一个快捷键（例如 `g` 或其它不冲突键），用于打开 Category 选择视图。
  - 当用户选择 Category 并确认时：
    - 更新内部状态（例如 `self.current_category_id`）。
    - 在已有 Area 过滤的基础上，进一步基于 Category.range 过滤 Memo。
    - 更新上下文条中的 `Category` 显示。
  - 编写测试：
    - 在给定 schema 和 Memo 列表的情况下，验证 Area+Category 双重过滤的正确性。
  - **参考需求**：11.1（Category 选择与过滤）

---

### 15.3 类型视图与 CLI 资源接口（规划阶段）

- [ ] **15.3.1 设计 Task/Meeting 类型视图的快捷键与过滤策略**
  - 在 `status_tui` 设计中预留：
    - Task 视图：显示所有 `type == "task"` 且 `status == "open"` 的 Memo，可继续按 Area/Category 过滤。
    - Meeting 视图：显示所有 `type == "meeting"` 的 Memo，按时间维度排序或高亮近期/未来会议。
  - 定义视图切换键（例如 `Shift+T` / `Shift+M`），并在上下文条的 `View` 字段中反映当前视角。
  - 确保在这些视图中，现有的操作键（`u`, `m`, `e`, `n`）语义与默认视图一致。
  - **参考需求**：11.2（类型视图与工作流视角）

- [ ] **15.3.2 草拟 CLI 资源视图命令的接口（不立即实现全部）**
  - 在设计层和 CLI 骨架中预留以下命令（可先加占位 help，不必立刻实现完整逻辑）：
    - `mf get areas`
    - `mf get categories --area <id>`
    - `mf get items [--type task|meeting|note|email] [--status open|done] [--area <id>] [--category <id>]`
    - `mf describe item <hash_or_id>`
  - 将这些命令与现有服务层（FileManager/SchemaManager/HashManager/GitEngine）对应好，避免未来实现时大幅重构。
  - **参考需求**：11.3（CLI 资源视图）

---

## 任务执行说明

每个任务都应该：

1. **先写测试**：采用 TDD 方法，先编写测试用例
2. **实现功能**：实现满足测试的代码
3. **运行测试**：确保所有测试通过
4. **重构优化**：在测试通过后优化代码
5. **集成验证**：确保新功能与现有功能集成良好

每个任务完成后，应该：

- 运行完整的测试套件
- 检查代码覆盖率
- 验证功能符合需求文档中的验收标准
- 更新相关文档（如需要）

---

## 依赖关系

任务执行顺序建议：

1. **阶段 1**：项目初始化 → 数据模型 → 核心服务（Hash, Schema, Git, File）
2. **阶段 2**：CLI 框架 → 基础命令（capture, move, finish）
3. **阶段 3**：视图层（list, status, timeline, calendar）
4. **阶段 4**：CI 命令 → GitHub Actions
5. **阶段 5**：错误处理 → 工具函数 → 图谱同步（可选）

每个阶段完成后，进行集成测试，确保功能正常工作。
