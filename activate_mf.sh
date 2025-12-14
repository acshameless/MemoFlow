#!/bin/bash
# MemoFlow 快速激活脚本
# 使用方法: source activate_mf.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PATH="$SCRIPT_DIR/venv"

if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    echo "✓ MemoFlow 虚拟环境已激活"
    echo "  使用 'mf --help' 查看帮助"
    echo "  使用 'deactivate' 退出虚拟环境"
else
    echo "✗ 虚拟环境不存在: $VENV_PATH"
    echo "  请先运行: python3 -m venv venv && pip install -e memoflow/"
fi
