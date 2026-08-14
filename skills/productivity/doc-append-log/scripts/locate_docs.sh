#!/bin/sh
# 定位文档/日志目录：优先返回已有 INDEX.md 的目录；
# 否则返回第一个存在的常见候选目录；否则回退 "docs"。
# 用法：locate_docs.sh [显式目录]
#   - 传入显式目录时直接返回它（不校验是否存在）。
set -eu

if [ $# -ge 1 ] && [ -n "$1" ]; then
  printf '%s\n' "$1"
  exit 0
fi

CANDIDATES="docs doc document documentation log logs logs/docs wiki"

# 1) 已有 INDEX.md 的目录优先级最高
for d in $CANDIDATES; do
  if [ -f "$d/INDEX.md" ]; then
    printf '%s\n' "$d"
    exit 0
  fi
done

# 2) 否则取第一个存在的候选目录
for d in $CANDIDATES; do
  if [ -d "$d" ]; then
    printf '%s\n' "$d"
    exit 0
  fi
done

# 3) 回退默认（尚未建索引时）
printf '%s\n' "docs"
