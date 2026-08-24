#!/usr/bin/env bash
# 配置 SSH 免登录：生成密钥（如无）→ 追加 ~/.ssh/config → 推送公钥。
# 用法: ensure_ssh.sh <user@host> [port]
set -euo pipefail

TARGET="${1:?用法: ensure_ssh.sh <user@host> [port]}"
PORT="${2:-22}"
USER="${TARGET%@*}"
HOST="${TARGET#*@}"
CONFIG_FILE="$HOME/.ssh/config"

echo "=== 1/3 检查密钥 ==="
if [ -f "$HOME/.ssh/id_ed25519" ]; then
  KEY="$HOME/.ssh/id_ed25519"
  echo "使用已有密钥: $KEY"
elif [ -f "$HOME/.ssh/id_rsa" ]; then
  KEY="$HOME/.ssh/id_rsa"
  echo "使用已有密钥: $KEY"
else
  KEY="$HOME/.ssh/id_ed25519"
  echo "生成 ed25519 密钥: $KEY"
  ssh-keygen -t ed25519 -N "" -f "$KEY"
fi

echo "=== 2/3 追加 ~/.ssh/config 条目 ==="
if [ ! -f "$CONFIG_FILE" ]; then
  touch "$CONFIG_FILE"
  chmod 600 "$CONFIG_FILE"
fi
if grep -q "Host $HOST$" "$CONFIG_FILE" 2>/dev/null; then
  echo "config 已存在 $HOST 条目，跳过"
else
  {
    echo ""
    echo "Host $HOST"
    echo "  HostName $HOST"
    echo "  User $USER"
    echo "  Port $PORT"
    echo "  IdentityFile $KEY"
    echo "  IdentitiesOnly yes"
  } >> "$CONFIG_FILE"
  echo "已追加条目到 $CONFIG_FILE"
fi

echo "=== 3/3 推送公钥（需要输入目标机器密码一次） ==="
ssh-copy-id -i "$KEY.pub" -o IdentitiesOnly=yes -p "$PORT" "$TARGET"

echo ""
echo "完成。运行 check_ssh.sh 验证免登录是否可用。"
