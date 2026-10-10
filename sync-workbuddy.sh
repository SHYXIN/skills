#!/usr/bin/env bash
# 把本仓库的技能同步（复制覆盖）到 WorkBuddy 的技能目录 ~/.workbuddy/skills/
#
# 背景：npx skills 暂不支持 workbuddy agent，故用本脚本直接复制 SKILL.md 目录。
# 只覆盖仓库里存在的技能，绝不删除目标目录里的其他内容（第三方/商店安装的技能不受影响）。
#
# 用法（新电脑 = 先 clone 本仓库，再跑一次）:
#   ./sync-workbuddy.sh
#
# 可选参数指定目标目录（默认 ~/.workbuddy/skills）:
#   ./sync-workbuddy.sh /path/to/workbuddy/skills
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$REPO_ROOT/skills"
DEST_DIR="${1:-$HOME/.workbuddy/skills}"

if [ ! -d "$SRC_DIR" ]; then
  echo "❌ 找不到技能目录: $SRC_DIR" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"

count=0
# 遍历任意嵌套层级下的 SKILL.md，取其所在目录整体复制
while IFS= read -r skill_md; do
  skill_dir="$(dirname "$skill_md")"
  skill_name="$(basename "$skill_dir")"
  mkdir -p "$DEST_DIR/$skill_name"
  cp -r "$skill_dir/." "$DEST_DIR/$skill_name/"
  echo "  ✓ $skill_name"
  count=$((count + 1))
done < <(find "$SRC_DIR" -name "SKILL.md" -not -path "*/node_modules/*" | sort)

echo ""
echo "✅ 已同步 $count 个技能 -> $DEST_DIR"
echo "   （目标目录中原有的其他技能未受影响；若仓库中改名/删除了技能，请手动删除目标目录中的旧副本）"
