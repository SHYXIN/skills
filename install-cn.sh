#!/usr/bin/env bash
# 国内一键安装 SHYXIN/skills + pstack + mattpocock/skills（均从 Gitee 拉取，免翻墙）
#
# 远程一键运行（Gitee 对 raw 文件有反爬拦截，curl 直接拉 /raw/ 会 403，请用 clone 方式）：
#   git clone --depth 1 https://gitee.com/theshyxin/skills.git /tmp/skills-cn && bash /tmp/skills-cn/install-cn.sh; rm -rf /tmp/skills-cn
#   git clone --depth 1 https://gitee.com/theshyxin/skills.git /tmp/skills-cn && bash /tmp/skills-cn/install-cn.sh "codebuddy,claude-code,codex,workbuddy"; rm -rf /tmp/skills-cn
#
# 本地运行：
#   ./install-cn.sh                          # 默认装到 codebuddy,claude-code,codex,workbuddy（全局）
#   ./install-cn.sh "codebuddy"              # 只装 codebuddy
#   ./install-cn.sh "codebuddy,codex"        # 自定义 agent 列表（逗号分隔）
set -euo pipefail

AGENTS="${1:-codebuddy,claude-code,codex,workbuddy}"

# 确保 cn-skills-cli 已安装（国内用 npmmirror 加速）
if ! command -v cn-skills >/dev/null 2>&1; then
  echo "📦 安装 cn-skills-cli（国内镜像）..."
  npm install -g cn-skills-cli --registry=https://registry.npmmirror.com
fi

echo "📦 安装 SHYXIN/skills (Gitee) -> $AGENTS"
cn-skills add SHYXIN/skills --yes --global --agent "$AGENTS"

# pstack 整包，从 Gitee 镜像仓拉取（默认分支当前对应冻结版 v0.15.15；冻结 tag 见仓内 refs/tags）
# 用完整 gitee URL：cn-skills 的 owner/repo 简写会解析到 GitHub，而 npx skills 从 Gitee 拉取会被反爬 403
echo "📦 安装 pstack 整包 (Gitee 镜像 theshyxin/pstack) -> $AGENTS"
cn-skills add https://gitee.com/theshyxin/pstack --yes --global --agent "$AGENTS"

# mattpocock/skills 放在 pstack 之后：同名技能 tdd/teach 后装者胜，这里让 matt 版覆盖 pstack 版
# （matt 的 tdd/teach 带额外参考文件且被其 /implement、/ask-matt 内部依赖，语义更完整）
echo "📦 安装 mattpocock/skills (Gitee 镜像) -> $AGENTS"
cn-skills add mattpocock/skills --yes --global --agent "$AGENTS"

# opencli：让 agent 操控用户日常 Chrome（带登录态）。CLI 是本体，技能是说明书，两者都装
# 技能装全量（usage/browser/smart-search/autofix/adapter-author），它们成套互相引用
# 注意：@jackwener/opencli 与 jackwener/opencli 均来自 GitHub/npm 官方源，国内直连可能慢或失败
echo "📦 安装 opencli CLI + 全部 opencli 技能 -> $AGENTS"
if ! command -v opencli >/dev/null 2>&1; then
  npm install -g @jackwener/opencli --registry=https://registry.npmmirror.com
fi
cn-skills add jackwener/opencli --yes --global --agent "$AGENTS"
echo "⚠️  opencli 还需 Chrome 扩展（无法静默安装）：https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk"
echo "    装好扩展后运行 'opencli doctor' 验证；完整引导见 setup-opencli 技能"

# asd-ste100：ASD-STE100 受控英语规则，改写给 agent 消费的英文文本（工具描述/错误消息/提示词），防误读
# 无 Gitee 镜像，直连 GitHub（国内可能慢）
echo "📦 安装 asd-ste100-skill (推荐搭配，GitHub 直连) -> $AGENTS"
cn-skills add danyuchn/asd-ste100-skill --yes --global --agent "$AGENTS"

# book-to-skill：把书/文档蒸馏成结构化技能，章节按需加载省 token
# 无 Gitee 镜像，直连 GitHub（国内可能慢）；PDF 等格式转换时按需补 Python 依赖
echo "📦 安装 book-to-skill (推荐搭配，GitHub 直连) -> $AGENTS"
cn-skills add virgiliojr94/book-to-skill --yes --global --agent "$AGENTS"

# rea（Reverse Engineer Anything）：全栈逆向 MCP 的技能说明书，轻量无依赖
# 无 Gitee 镜像，直连 GitHub；MCP server 本体（npx rea-agents setup）要用时再装
echo "📦 安装 rea (推荐搭配，GitHub 直连) -> $AGENTS"
cn-skills add morluto/rea --yes --global --agent "$AGENTS"

echo "✅ 完成。运行 'cn-skills list' 查看已安装技能。"
