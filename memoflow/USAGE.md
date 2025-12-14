# MemoFlow 使用指南

## 安装和设置

### 1. 安装 MemoFlow

```bash
# 进入项目目录
cd memoflow

# 创建虚拟环境（如果还没有）
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装 MemoFlow
pip install -e .
```

### 2. 使用 `mf` 命令

#### 方法 1：激活虚拟环境（推荐）

```bash
# 激活虚拟环境
source venv/bin/activate

# 现在可以直接使用 mf 命令
mf version
mf init
mf capture -t task "My task"
```

#### 方法 2：使用绝对路径

```bash
# 不激活虚拟环境，使用绝对路径
/Users/shameless/Documents/github/code/gpt/venv/bin/mf version
```

#### 方法 3：创建别名（可选）

在你的 shell 配置文件中（`~/.zshrc` 或 `~/.bashrc`）添加：

```bash
# 对于 zsh
alias mf='/Users/shameless/Documents/github/code/gpt/venv/bin/mf'

# 或者更灵活的方式（自动检测虚拟环境）
alias mf='source /Users/shameless/Documents/github/code/gpt/venv/bin/activate && mf'
```

然后重新加载配置：
```bash
source ~/.zshrc  # 或 source ~/.bashrc
```

#### 方法 4：全局安装（不推荐）

```bash
# 全局安装（需要管理员权限）
pip install -e .

# 现在可以在任何地方使用 mf
mf version
```

## 为什么需要激活虚拟环境？

当你在虚拟环境中安装 Python 包时，可执行脚本（如 `mf`）会被安装到 `venv/bin/` 目录中。

- **未激活虚拟环境**：`venv/bin/` 不在 PATH 中，系统找不到 `mf` 命令，必须使用绝对路径
- **已激活虚拟环境**：`venv/bin/` 被添加到 PATH 前面，可以直接使用 `mf` 命令

## 验证虚拟环境是否激活

```bash
# 检查 Python 路径
which python
# 应该显示：/path/to/venv/bin/python

# 检查 mf 命令
which mf
# 应该显示：/path/to/venv/bin/mf

# 检查 PATH
echo $PATH | grep venv
# 应该包含 venv/bin
```

## 常见问题

### Q: 为什么每次打开终端都要激活虚拟环境？

A: 虚拟环境的激活只在当前 shell 会话中有效。每次打开新终端都需要重新激活。

**解决方案**：
1. 使用别名（见方法 3）
2. 使用 `direnv` 等工具自动激活
3. 在项目目录创建激活脚本

### Q: 可以在不激活虚拟环境的情况下使用吗？

A: 可以，使用绝对路径：
```bash
/path/to/venv/bin/mf --help
```

### Q: 如何让 mf 命令在所有地方都可用？

A: 有几种方式：
1. **全局安装**（不推荐，可能污染系统 Python）
2. **创建符号链接**：
   ```bash
   sudo ln -s /path/to/venv/bin/mf /usr/local/bin/mf
   ```
3. **使用 pipx**（推荐用于 CLI 工具）：
   ```bash
   pipx install -e /path/to/memoflow
   ```

## 推荐工作流

1. 进入项目目录
2. 激活虚拟环境：`source venv/bin/activate`
3. 使用 `mf` 命令
4. 工作完成后可以 `deactivate`（可选）

## 使用 pipx（推荐用于 CLI 工具）

`pipx` 是专门用于安装和运行 Python CLI 应用程序的工具：

```bash
# 安装 pipx
pip install pipx

# 使用 pipx 安装 MemoFlow
pipx install -e /path/to/memoflow

# 现在可以在任何地方使用 mf
mf version
```

pipx 会自动管理虚拟环境，你不需要手动激活。
