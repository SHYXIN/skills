#!/usr/bin/env bash
# 国内一键安装 SHYXIN/skills + mattpocock/skills（均从 Gitee 拉取，免翻墙）
#
# 远程一键运行（Gitee 对 raw 文件有反爬拦截，curl 直接拉 /raw/ 会 403，请用 clone 方式）：
#   git clone --depth 1 https://gitee.com/theshyxin/skills.git /tmp/skills-cn && bash /tmp/skills-cn/install-cn.sh; rm -rf /tmp/skills-cn
#   git clone --depth 1 https://gitee.com/theshyxin/skills.git /tmp/skills-cn && bash /tmp/skills-cn/install-cn.sh "codebuddy,claude-code,codex"; rm -rf /tmp/skills-cn
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
