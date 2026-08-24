#!/usr/bin/env bash
# 检测 SSH 免登录是否可用。
# 用法: check_ssh.sh <user@host> [port]
set -euo pipefail

TARGET="${1:?用法: check_ssh.sh <user@host> [port]}"
PORT="${2:-22}"

if ssh -o BatchMode=yes -o ConnectTimeout=6 -p "$PORT" "$TARGET" 'echo SSH_OK' 2>/dev/null | grep -q SSH_OK; then
  echo "SSH 免登录已可用: $TARGET"
  exit 0
else
  echo "SSH 免登录不可用: $TARGET（请运行 ensure_ssh.sh 配置，或检查网络/密钥）"
  exit 1
fi
