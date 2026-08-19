#!/usr/bin/env bash
# 一键安装 SHYXIN/skills + mattpocock/skills + cathrynlavery/diagram-design + tt-a1i/archify 到本地 agent
#
# 远程一键运行（无需克隆仓库）:
#   curl -fsSL https://raw.githubusercontent.com/SHYXIN/skills/master/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/SHYXIN/skills/master/install.sh | bash -s -- "codebuddy codex"
#
# 本地运行:
#   ./install.sh                                          # 默认装到 codebuddy claude-code codex hermes-agent（全局）
#   ./install.sh codebuddy                               # 只装 codebuddy
#   ./install.sh "codebuddy codex"                       # 自定义 agent 列表
set -euo pipefail

AGENTS="${1:-codebuddy claude-code codex hermes-agent}"

echo "📦 安装 SHYXIN/skills -> agents: $AGENTS"
# 未加引号以让空格分隔的 agent 列表展开为多个 -a 参数
npx skills@latest add SHYXIN/skills -y -g -a $AGENTS

echo "📦 安装 mattpocock/skills (推荐搭配) -> agents: $AGENTS"
npx skills@latest add mattpocock/skills -y -g -a $AGENTS

echo "📦 安装 cathrynlavery/diagram-design (推荐搭配) -> agents: $AGENTS"
npx skills@latest add cathrynlavery/diagram-design -y -g -a $AGENTS

echo "📦 安装 tt-a1i/archify (推荐搭配) -> agents: $AGENTS"
npx skills@latest add tt-a1i/archify -y -g -a $AGENTS

echo "✅ 完成。运行 'npx skills list' 查看已安装技能。"
