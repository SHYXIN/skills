#!/bin/sh
# 追加一篇新文档，并在 INDEX.md 中自动插入索引行（目录无关：先定位，再操作）。
# 同名文件已存在则跳过创建（不改写），但仍会补索引行（若缺失）。
# 用法：append_entry.sh [文档目录] <主题> [状态] [摘要]
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DIR=$(sh "$SCRIPT_DIR/locate_docs.sh" "${1:-}")
shift || true
TOPIC="${1:?用法: append_entry.sh [文档目录] <主题> [状态] [摘要]}"
STATUS="${2:-当前事实}"
SUMMARY="${3:-}"

TODAY=$(date +%Y-%m-%d)
FNAME="${TODAY}_${TOPIC}.md"
INDEX="$DIR/INDEX.md"

mkdir -p "$DIR"

if [ -f "$DIR/$FNAME" ]; then
  echo "文件已存在，跳过创建（不改写）: $DIR/$FNAME" >&2
else
  cat > "$DIR/$FNAME" <<EOF
# ${TOPIC}

> 创建日期：${TODAY} ｜ 状态：${STATUS}
> 本文件遵循"只追加、不改写"约定，创建后不回改内容。

（在此记录内容）

---
EOF
  echo "已创建文档: $DIR/$FNAME"
fi

if [ ! -f "$INDEX" ]; then
  echo "INDEX.md 不存在，请先运行: bash scripts/init_index.sh $DIR" >&2
  exit 1
fi

# 避免重复插入同一文件名的索引行
if grep -q "($FNAME)" "$INDEX"; then
  echo "索引行已存在，跳过追加: $FNAME" >&2
  exit 0
fi

ROW="| ${TODAY} | [${FNAME}](${FNAME}) | ${STATUS} | ${SUMMARY} |"
TMP=$(mktemp)
awk -v row="$ROW" '
  /<!-- APPEND_NEW_DOC_HERE -->/ { print row }
  { print }
' "$INDEX" > "$TMP" && mv "$TMP" "$INDEX"
echo "已在 INDEX.md 追加索引行: $ROW"
