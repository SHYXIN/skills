#!/usr/bin/env bash
# 国内一键安装 SHYXIN/skills + mattpocock/skills（均从 Gitee 拉取，免翻墙）
#
# 远程一键运行（从 Gitee 拉取本脚本，需先在 Gitee 上建好 theshyxin/skills 镜像）：
#   curl -fsSL https://gitee.com/theshyxin/skills/raw/master/install-cn.sh | bash
#   curl -fsSL https://gitee.com/theshyxin/skills/raw/master/install-cn.sh | bash -s -- "codebuddy,claude-code,codex"
#
# 本地运行：
#   ./install-cn.sh                          # 默认装到 codebuddy,claude-code,codex（全局）
#   ./install-cn.sh "codebuddy"              # 只装 codebuddy
#   ./install-cn.sh "codebuddy,codex"        # 自定义 agent 列表（逗号分隔）
set -euo pipefail

AGENTS="${1:-codebuddy,claude-code,codex}"

# 确保 cn-skills-cli 已安装（国内用 npmmirror 加速）
if ! command -v cn-skills >/dev/null 2>&1; then
  echo "📦 安装 cn-skills-cli（国内镜像）..."
  npm install -g cn-skills-cli --registry=https://registry.npmmirror.com
fi

echo "📦 安装 SHYXIN/skills (Gitee) -> $AGENTS"
cn-skills add SHYXIN/skills --yes --global --agent "$AGENTS"

echo "📦 安装 mattpocock/skills (Gitee 镜像) -> $AGENTS"
cn-skills add mattpocock/skills --yes --global --agent "$AGENTS"

echo "✅ 完成。运行 'cn-skills list' 查看已安装技能。"
