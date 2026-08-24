#!/usr/bin/env bash
# 校验远程机器状态：docker、gitlab-runner 容器、已注册 runner 列表。
# 用法: verify.sh <user@host>
set -euo pipefail

TARGET="${1:?用法: verify.sh <user@host>}"

echo "=== 远程 Docker ==="
ssh -o BatchMode=yes "$TARGET" 'docker --version 2>/dev/null || echo "docker 未安装"'

echo ""
echo "=== gitlab-runner 容器 ==="
ssh -o BatchMode=yes "$TARGET" 'docker ps --format "{{.Names}}  {{.Status}}" | grep gitlab-runner || echo "gitlab-runner 容器未运行"'

echo ""
echo "=== 已注册 Runner 列表（config.toml） ==="
ssh -o BatchMode=yes "$TARGET" 'docker exec gitlab-runner gitlab-runner list 2>/dev/null || docker exec gitlab-runner cat /etc/gitlab-runner/config.toml | grep -E "name|token" || echo "无法读取 runner 配置"'

echo ""
echo "=== 人工核对项 ==="
echo "1. GitLab: 项目或群组 Settings → CI/CD → Runners，确认新 runner 状态为 online。"
echo "2. 推送一个带 .gitlab-ci.yml 的最小流水线，确认 pipeline 变绿（参考 SKILL.md Step 5）。"
