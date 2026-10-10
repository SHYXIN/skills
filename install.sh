#!/usr/bin/env bash
# 一键安装 SHYXIN/skills + humanlayer/skills(show-me) + pstack + mattpocock/skills 到本地 agent
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

echo "📦 安装 humanlayer/skills show-me (推荐搭配) -> agents: $AGENTS"
npx skills@latest add humanlayer/skills --skill show-me -y -g -a $AGENTS

# pstack 整包（poteto-mode 路由 + 23 playbook + 24 principle，自带 unslop，故不再单独装 cursor/plugins）
echo "📦 安装 pstack (推荐搭配，整包) -> agents: $AGENTS"
npx skills@latest add backnotprop/pstack -y -g -a $AGENTS

# mattpocock/skills 放在 pstack 之后：同名技能 tdd/teach 后装者胜，这里让 matt 版覆盖 pstack 版
# （matt 的 tdd/teach 带额外参考文件且被其 /implement、/ask-matt 内部依赖，语义更完整）
echo "📦 安装 mattpocock/skills (推荐搭配) -> agents: $AGENTS"
npx skills@latest add mattpocock/skills -y -g -a $AGENTS

# opencli：让 agent 操控用户日常 Chrome（带登录态）。CLI 是本体，技能是说明书，两者都装
# 技能装全量（usage/browser/smart-search/autofix/adapter-author），它们成套互相引用
echo "📦 安装 opencli CLI + 全部 opencli 技能 -> agents: $AGENTS"
if ! command -v opencli >/dev/null 2>&1; then
  npm install -g @jackwener/opencli
fi
npx skills@latest add jackwener/opencli -y -g -a $AGENTS
echo "⚠️  opencli 还需 Chrome 扩展（无法静默安装）：https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk"
echo "    装好扩展后运行 'opencli doctor' 验证；完整引导见 setup-opencli 技能"

echo "✅ 完成。运行 'npx skills list' 查看已安装技能。"
