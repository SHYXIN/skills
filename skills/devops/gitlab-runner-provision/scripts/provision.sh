#!/usr/bin/env bash
# 远程准备：安装 Docker（如无）并创建/启动 gitlab-runner 容器。
# 用法: provision.sh <user@host> [gitlab_runner_version]
set -euo pipefail

TARGET="${1:?用法: provision.sh <user@host> [gitlab_runner_version]}"
RUNNER_VER="${2:-v15.11.1}"
RUNNER_CONFIG_DIR="${RUNNER_CONFIG_DIR:-/srv/gitlab-runner/config}"

echo "=== 检测/安装 Docker ==="
DOCKER_VERSION=$(ssh -o BatchMode=yes "$TARGET" 'command -v docker >/dev/null 2>&1 && docker --version 2>/dev/null || echo NO_DOCKER')
if [ "$DOCKER_VERSION" = "NO_DOCKER" ]; then
  echo "[docker] 未安装，开始安装（可能需要数分钟）..."
  ssh "$TARGET" 'curl -fsSL https://get.docker.com | sh && systemctl enable --now docker'
  echo "[docker] 安装完成"
else
  echo "[docker] 已安装: $DOCKER_VERSION"
fi

echo "=== 检测/创建 gitlab-runner 容器 ==="
RUNNER_EXISTS=$(ssh -o BatchMode=yes "$TARGET" 'docker ps -a --format "{{.Names}}" | grep -qx "gitlab-runner" && echo YES || echo NO')
if [ "$RUNNER_EXISTS" = "YES" ]; then
  echo "[runner] 容器已存在，确保运行中..."
  ssh "$TARGET" 'docker start gitlab-runner >/dev/null 2>&1 || true'
else
  echo "[runner] 创建 gitlab-runner 容器 ($RUNNER_VER) ..."
  # 挂载 docker.sock 供 docker executor 使用；config 目录持久化
  ssh "$TARGET" "mkdir -p $RUNNER_CONFIG_DIR && docker run -d \
    --name gitlab-runner \
    --restart always \
    -v $RUNNER_CONFIG_DIR:/etc/gitlab-runner \
    -v /var/run/docker.sock:/var/run/docker.sock \
    gitlab/gitlab-runner:$RUNNER_VER"
  echo "[runner] 容器已创建"
fi

echo ""
echo "完成。下一步运行 register_runner.sh 注册 runner。"
