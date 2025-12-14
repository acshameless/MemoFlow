# MemoFlow

MemoFlow（记忆流）是一个基于 Python 3 构建的命令行工作流管理工具，为会议、笔记、任务和邮件提供统一管理。

## 核心理念

**"快速捕获、清晰组织、经常回顾、有效执行"**

## 特性

- 📝 **Markdown 存储**：所有数据以 Markdown 文件形式存储，人类可读且机器可解析
- 🔄 **Git 版本控制**：所有操作自动提交到 Git，提供完整的历史追踪，遵循 Angular Commit Convention
- 🏷️ **双重索引**：短哈希（永久引用，不可变）+ Johnny.Decimal ID（逻辑组织，可变）
- ⚙️ **配置驱动**：通过 `schema.yaml` 自定义组织结构（柜子/抽屉）
- 🤖 **自动化**：GitHub Actions 集成，实现云端自动化（晨间唤醒、晚间复盘）
- 🎨 **美观输出**：使用 Rich 库提供美观的终端输出

## 安装

### 从源码安装

```bash
git clone https://github.com/yourusername/memoflow.git
cd memoflow
pip install -e .
```

### 从 PyPI 安装（发布后）

```bash
pip install memoflow
```

## 快速开始

### 1. 初始化仓库

```bash
# 在新目录初始化
mf init ~/my-second-brain
cd ~/my-second-brain

# 或在当前目录初始化
mf init
```

### 2. 快速捕获

```bash
# 捕获任务
mf capture -t task "Review PR #123"

# 捕获笔记
mf capture -t note "Meeting with Alice: discussed Q4 goals"

# 捕获会议记录
mf capture -t meeting "Weekly sync - discussed project timeline"
```

### 3. 查看状态

```bash
# 查看工作流状态
mf status

# 查看文件列表（树形）
mf list

# 查看文件列表（扁平）
mf list --flat
```

### 4. 组织文件

```bash
# 移动文件（使用短哈希）
mf move 7f9a HANK-00.01 HANK-12.04

# 查看时间轴
mf timeline --since "1 week ago"

# 查看日历
mf calendar
```

### 5. 完成任务

```bash
# 标记任务为完成
mf finish 7f9a
```

## 命令参考

### 基础命令

- `mf init [path]` - 初始化 MemoFlow 仓库
- `mf version` - 显示版本信息

### 捕获和组织

- `mf capture -t <type> "content"` - 快速捕获内容
  - 类型：`meeting`, `note`, `task`, `email`
- `mf move <hash> <old_path> <new_path>` - 移动文件
- `mf finish <hash>` - 标记任务为完成
- `mf type <hash> <new_type>` - 修改文件类型
- `mf rebuild-index` - 重建哈希索引
- `mf migrate-prefix <old_prefix> <new_prefix>` - 批量更新所有文件的用户前缀（如：`mf migrate-prefix HANK AC`）

### 查看和回顾

- `mf list [--tree/--flat]` - 列表视图
- `mf status` - 状态视图（交互式 TUI 模式或静态输出）
  - 交互模式：支持实时操作（修改类型、状态、移动文件等）
  - 静态模式：使用 `--no-interactive` 选项
- `mf timeline [--since <time>] [--type <type>]` - 时间轴视图
- `mf calendar [--month <month>] [--year <year>]` - 日历视图

### 自动化

- `mf ci --mode morning` - 生成晨间焦点文档（供 GitHub Actions 使用）
- `mf ci --mode evening` - 生成晚间复盘文档（供 GitHub Actions 使用）

### Schema 管理

- `mf schema reload` - 重新加载 schema.yaml
- `mf schema validate` - 验证 schema.yaml 配置

## 配置

### Schema 配置

编辑 `schema.yaml` 自定义组织结构：

```yaml
user_prefix: "HANK"
areas:
  - id: 10
    name: "项目"
    categories:
      - id: 1
        name: "规划"
        range: [10.01, 10.09]
```

### GitHub Actions

将 `.github/workflows/` 目录中的工作流文件复制到你的仓库，配置定时任务：

- `morning_wake.yml` - 每天 8:00 生成每日焦点
- `evening_review.yml` - 每天 23:00 生成每日复盘

## 文件结构

```
my-second-brain/
├── .mf/
│   ├── hash_index.json    # 哈希索引
│   └── logs/              # 日志目录（可选）
├── .github/
│   └── workflows/         # GitHub Actions
├── 00-Inbox/             # 收件箱
├── 10-20/                # Area 1
│   ├── 10.01-10.09/
│   └── 10.10-10.19/
├── schema.yaml           # Schema 配置
└── *.md                  # Markdown 文件
```

## 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_file_manager.py

# 查看覆盖率
pytest --cov=mf --cov-report=html
```

### 项目结构

```
memoflow/
├── mf/                   # 核心包
│   ├── cli.py            # CLI 入口
│   ├── commands/         # 命令处理
│   ├── core/             # 核心服务
│   ├── models/           # 数据模型
│   ├── views/            # 视图层
│   └── utils/            # 工具函数
├── tests/                # 测试
└── pyproject.toml        # 项目配置
```

## 工作原理

### 双重索引系统

- **短哈希（UUID）**：6 位十六进制，永久不变，用于快速引用
- **Johnny.Decimal ID**：如 `HANK-12.04`，随文件位置变化

### 记忆即代码

所有操作自动提交到 Git，提交消息遵循 Angular Commit Convention：
- `feat(new): capture ...` - 新建文件
- `feat(<hash>): mark as done` - 完成任务
- `refactor(<hash>): move from ... to ...` - 移动文件
- `docs(<hash>): update content` - 更新内容

### 自动化工作流

GitHub Actions 每天自动运行：
- **晨间**：扫描今日到期任务，生成 `Daily_Focus.md`
- **晚间**：分析今日 Git 日志，生成 `Daily_Review.md`

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
