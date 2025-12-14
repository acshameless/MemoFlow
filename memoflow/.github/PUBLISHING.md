# 发布到 PyPI

本文档说明如何将 MemoFlow 发布到 PyPI。

## 前置条件

1. **PyPI 账户**：确保你有一个 PyPI 账户（https://pypi.org/account/register/）
2. **配置 Trusted Publishing**：
   - 登录 PyPI 账户
   - 进入项目设置（https://pypi.org/manage/projects/）
   - 选择或创建 `memoflow` 项目
   - 在 "Publishing" 部分配置 Trusted Publishing
   - 添加 GitHub 仓库和 `pypi` 环境

## 发布流程

### 1. 准备发布

确保以下内容已更新：
- [ ] `pyproject.toml` 中的版本号已更新
- [ ] `CHANGELOG.md` 已更新
- [ ] 所有测试通过
- [ ] 文档完整

### 2. 创建 GitHub Release

1. 在 GitHub 仓库中，点击 "Releases" → "Create a new release"
2. 选择或创建新的标签（如 `v0.1.0`）
3. 填写发布标题和描述（可以从 CHANGELOG.md 复制）
4. 点击 "Publish release"

### 3. 自动发布

GitHub Actions 会自动：
1. 构建 Python 包（wheel 和 source distribution）
2. 上传到 PyPI
3. 发布完成后，可以在 https://pypi.org/project/memoflow/ 查看

## 验证发布

发布完成后，可以验证：

```bash
# 安装发布的版本
pip install memoflow==0.1.0

# 验证安装
mf version
```

## 故障排除

### 发布失败

如果发布失败，检查：
1. PyPI Trusted Publishing 配置是否正确
2. GitHub Actions 日志中的错误信息
3. 版本号是否已存在于 PyPI（不能重复发布相同版本）

### 手动发布（备用方案）

如果自动发布失败，可以手动发布：

```bash
# 安装构建工具
pip install build twine

# 构建包
python -m build

# 上传到 PyPI（需要 PyPI API token）
twine upload dist/*
```

## 注意事项

- **版本号**：遵循语义化版本控制（Semantic Versioning）
- **测试**：发布前确保所有测试通过
- **文档**：确保 README.md 和文档是最新的
- **依赖**：确保所有依赖在 `pyproject.toml` 中正确声明
