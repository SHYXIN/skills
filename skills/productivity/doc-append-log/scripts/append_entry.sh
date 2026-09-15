#!/bin/sh
# 追加一篇新文档，并在 INDEX.md 中自动插入索引行（目录无关：先定位，再操作）。
# 同名文件已存在则跳过创建（不改写），但仍会补索引行（若缺失）。
# 用法：append_entry.sh [文档目录] <主题> [状态] [摘要]
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DIR=$(sh "$SCRIPT_DIR/locate_docs.sh" "${1:-}")
shift || true
TOPIC="${1:-}"
STATUS="${2:-当前事实}"
SUMMARY="${3:-}"

# 相对路径基于调用方 cwd 规范化为绝对路径；绝对路径保持不变。
# 否则 mkdir/写文件发生在当前 shell 的任意 cwd，同一相对参数会在不同位置落盘。
case "$DIR" in
  /*|[A-Za-z]:[\\/]*) ;;                       # 已是绝对路径（POSIX / Windows 盘符）
  *) DIR="$(pwd)/$DIR" ;;
esac

# 空主题时自动命名，不中断流程（原来的 ${1:?...} 会直接报用法错误退出）。
if [ -z "$TOPIC" ]; then
  TOPIC="untitled-entry"
fi

# 主题即文件名的一部分，拒绝路径穿越与分隔符，避免写到目标目录之外。
case "$TOPIC" in
  *..*|*/*|*"\\"*)
    echo "错误：主题不能包含 .. 、/ 或 \\\\（收到: \"$TOPIC\"）" >&2
    exit 1
    ;;
esac

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
