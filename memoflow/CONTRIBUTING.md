# Contributing to MemoFlow

感谢您对 MemoFlow 的兴趣！我们欢迎所有形式的贡献。

## 开发环境设置

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/memoflow.git
cd memoflow
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -e ".[dev]"
```

### 4. 运行测试

```bash
pytest
```

## 开发流程

### 1. 创建分支

```bash
git checkout -b feature/your-feature-name
```

### 2. 编写代码

- 遵循 PEP 8 代码风格
- 为新功能编写测试
- 确保所有测试通过

### 3. 提交更改

提交消息遵循 [Angular Commit Convention](https://www.conventionalcommits.org/)：

```
feat: add new feature
fix: fix bug
docs: update documentation
refactor: refactor code
test: add tests
```

### 4. 运行测试和检查

```bash
# 运行所有测试
pytest

# 检查代码覆盖率
pytest --cov=mf --cov-report=html

# 检查代码风格（如果配置了）
flake8 mf/
```

### 5. 提交 Pull Request

- 描述您的更改
- 引用相关的 Issue（如果有）
- 确保 CI 通过

## 代码规范

### Python 代码风格

- 遵循 PEP 8
- 使用类型提示（Type Hints）
- 编写文档字符串（Docstrings）

### 测试

- 为新功能编写单元测试
- 编写集成测试验证功能完整性
- 目标覆盖率：80%+

### 提交消息

使用 Angular Commit Convention：

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

## 项目结构

```
memoflow/
├── mf/              # 核心包
│   ├── cli.py       # CLI 入口
│   ├── commands/    # 命令处理
│   ├── core/        # 核心服务
│   ├── models/      # 数据模型
│   ├── views/       # 视图层
│   └── utils/       # 工具函数
├── tests/           # 测试
└── pyproject.toml   # 项目配置
```

## 报告问题

如果发现 bug 或有功能建议，请：

1. 检查是否已有相关 Issue
2. 创建新 Issue，描述问题和复现步骤
3. 如果是 bug，请提供错误信息和环境信息

## 功能建议

欢迎提出新功能建议！请：

1. 在 Issue 中描述功能需求
2. 说明使用场景和预期行为
3. 讨论实现方案（可选）

## 许可证

贡献的代码将遵循项目的 MIT 许可证。
