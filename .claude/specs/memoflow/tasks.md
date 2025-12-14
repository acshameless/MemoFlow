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
