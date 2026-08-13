#!/usr/bin/env bash
# 一键安装 SHYXIN/skills + mattpocock/skills 到本地 agent
#
# 用法:
#   ./install.sh                      # 默认装到 codebuddy claude-code codex（全局）
#   ./install.sh codebuddy            # 只装 codebuddy
#   ./install.sh "codebuddy codex"    # 自定义 agent 列表
set -euo pipefail

AGENTS="${1:-codebuddy claude-code codex}"

echo "📦 安装 SHYXIN/skills -> agents: $AGENTS"
# 未加引号以让空格分隔的 agent 列表展开为多个 -a 参数
npx skills@latest add SHYXIN/skills -y -g -a $AGENTS

echo "📦 安装 mattpocock/skills (推荐搭配) -> agents: $AGENTS"
npx skills@latest add mattpocock/skills -y -g -a $AGENTS

echo "✅ 完成。运行 'npx skills list' 查看已安装技能。"
