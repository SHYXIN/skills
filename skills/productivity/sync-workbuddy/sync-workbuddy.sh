#!/usr/bin/env bash
# 把技能仓库克隆里的技能同步（复制覆盖）到 WorkBuddy 的技能目录 ~/.workbuddy/skills/
# 只覆盖源仓库里存在的技能，绝不删除目标目录里的其他内容（第三方/商店安装的技能不受影响）。
#
# 用法:
#   sync-workbuddy.sh <源技能仓库克隆路径> [目标目录]
#
# 示例:
#   sync-workbuddy.sh ~/code/skills
#   sync-workbuddy.sh ~/code/skills /path/to/workbuddy/skills
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "用法: $(basename "$0") <源技能仓库克隆路径> [目标目录（默认 ~/.workbuddy/skills）]" >&2
  exit 1
fi

SRC_DIR="$1/skills"
DEST_DIR="${2:-$HOME/.workbuddy/skills}"

if [ ! -d "$SRC_DIR" ]; then
  echo "❌ 找不到技能目录: $SRC_DIR（请确认第一个参数是技能仓库的克隆路径）" >&2
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
echo "   （目标目录中原有的其他技能未受影响；若源仓库中改名/删除了技能，请手动删除目标目录中的旧副本）"
