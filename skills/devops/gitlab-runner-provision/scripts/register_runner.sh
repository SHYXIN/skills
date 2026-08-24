#!/usr/bin/env bash
# 在远程 gitlab-runner 容器中注册一个新 runner。
# 用法: register_runner.sh <user@host> <gitlab_url> <registration_token> [description] [tags]
set -euo pipefail

TARGET="${1:?用法: register_runner.sh <user@host> <gitlab_url> <registration_token> [description] [tags]}"
URL="${2:?需要 GitLab URL，如 https://<你的GitLab地址>/}"
TOKEN="${3:?需要 registration token（项目级或群组级）}"
DESC="${4:-runner-on-$TARGET}"
TAGS="${5:-docker}"

# 校验 token 非空且不以明文泄露到 shell 历史之外
[ -z "$TOKEN" ] && { echo "token 为空，中止"; exit 1; }

ssh -o BatchMode=yes "$TARGET" "docker exec gitlab-runner gitlab-runner register \\
  --non-interactive \\
  --url '$URL' \\
  --registration-token '$TOKEN' \\
  --executor docker \\
  --docker-image docker:24.0.7 \\
  --description '$DESC' \\
  --tag-list '$TAGS' \\
  --run-untagged=true \\
  --locked=false"

echo ""
echo "注册命令已执行。"
echo "请到 GitLab 对应项目/群组 Settings → CI/CD → Runners 确认新 runner 为 online。"
echo "若输出 401/403：项目级 token 需 Maintainer+；群组级 token 在 GitLab < 15.7 需 Owner。"
