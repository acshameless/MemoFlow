# Changelog

All notable changes to MemoFlow will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-XX

### Added

#### 核心功能
- 双重索引系统：短哈希（UUID）+ Johnny.Decimal ID
- Markdown 文件管理：自动生成 frontmatter，支持必需和可选字段
- Schema 配置系统：通过 `schema.yaml` 自定义组织结构
- Git 自动集成：所有操作自动提交，遵循 Angular Commit Convention
- 配置管理系统：支持仓库级别配置（如默认编辑器）
- **命名空间管理（Namespace Management）**：全局仓库注册表，支持多仓库管理
  - 仓库自动注册：`mf init` 时自动将仓库注册到全局注册表（`~/.memoflow/repos.json`）
  - 命名空间隔离：每个仓库作为独立的命名空间，支持多仓库并行管理

#### CLI 命令
- `mf init` - 初始化 MemoFlow 仓库（支持 `--editor` 选项配置默认编辑器，自动注册到全局注册表）
- `mf capture` / `mf new` - 快速捕获内容（支持 meeting, note, task, email）
- `mf move` / `mf mv` - 使用短哈希移动文件
- `mf finish` - 标记任务为完成
- `mf type` - 修改文件类型
- `mf rebuild-index` - 重建哈希索引
- `mf migrate-prefix <old> <new>` - 批量更新所有文件的用户前缀
- `mf schema reload` - 重新加载 schema.yaml
- `mf schema validate` - 验证 schema.yaml 配置
- **仓库管理命令（`mf repo`）**：
  - `mf repo list` - 列出所有注册的 MemoFlow 仓库
  - `mf repo info [name]` - 查看指定仓库的详细信息（名称、路径、用户前缀等）
  - `mf repo rm [name|--repo PATH] --yes` - 删除仓库及其所有 MemoFlow 数据（危险操作）

#### 视图命令
- `mf` - 启动交互式 TUI 仪表板（无参数时默认启动）
- `mf list` - 列表视图（树形/扁平格式）
- `mf status` - 显示仓库统计数据和文件列表（静态输出，支持过滤选项）
- `mf timeline` - 时间轴视图（支持时间范围和类型过滤）
- `mf calendar` - 日历视图（显示到期任务，突出过期项）

#### 交互式 TUI（运行 `mf` 启动）
- 实时查看和操作文件
- **资源导航（k9s 风格）**：
  - Context Bar：顶部显示当前 Namespace / Area / Category / View 上下文
  - Area 过滤：`A` / `a` 键选择 Area，按 Area ID 过滤文件列表
  - Category 过滤：`G` / `g` 键选择 Category（需先选择 Area），按 Category 范围过滤文件列表
  - Schema 视图：`S` 键查看完整的 schema 配置（Area/Category 结构）
- 支持修改文件类型（`c` 键）
- 支持修改文件状态（`u` 键）
- 支持打开外部编辑器（`e` 键，可配置 vim/typora/vscode 等）
- 支持创建新文件（`n` 键）
- 支持移动文件（`m` 键）
- 支持重建索引（`R` 键）
- 支持查看列表/时间轴/日历视图（`l`/`T`/`C` 键）
- 支持过滤和搜索

#### 自动化
- `mf ci` - CI 命令（morning/evening 模式）
- GitHub Actions 工作流模板（晨间唤醒、晚间复盘）

#### 工具函数
- Johnny.Decimal 工具函数（解析、格式化、验证）
  - 支持两位和三位小数格式（如 `10.01` 和 `10.001`）
- Markdown 工具函数（frontmatter 处理、wikilink/hashtag 提取）

#### 错误处理
- 异常类定义（HashCollisionError, InvalidPathError 等）
- 日志系统配置
- 完善的错误消息和用户提示

### Changed

- 默认 Schema 使用三位小数格式（`10.001-10.099`）以支持更多文件
- **命令结构重构**：
  - `mf` 无参数时启动交互式 TUI 仪表板（原 `mf status` 的 TUI 功能）
  - `mf status` 改为显示统计数据和文件列表（静态输出）
- 所有修改操作都包含明确的 commit message

### Technical Details

- Python 3.9+ 支持
- 使用 Typer 作为 CLI 框架
- 使用 Textual 构建交互式 TUI
- 使用 Rich 美化终端输出
- 使用 GitPython 进行 Git 操作
- 使用 python-frontmatter 处理 Markdown
- 测试覆盖（74 个测试，新增 RepoRegistry 和 CLI 端到端测试）
