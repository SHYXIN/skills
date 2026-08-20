# 镜像同步说明（Mirror）

主平台：**CNB**（`shy-xin/skills`）。

## 同步流向

```
CNB (shy-xin/skills)  ← 主平台
   └─ .cnb.yml 触发 → GitHub (SHYXIN/skills)  +  Gitee (theshyxin/skills)
```

- GitHub 上的 `mirror-to-gitee.yml` 保留作兜底（Gitee 为终点，不回推）。
- GitHub 上的 `mirror-to-cnb.yml` 已改名 `.disabled`，避免 CNB↔GitHub 死循环。

## 密钥来源（imports）

CNB 不会把仓库设置里的密钥注入 `.cnb.yml`，需用「密钥仓库」+ `imports`：

- 密钥仓库：`shy-xin/secrets`（私有）
- 文件：`skills/envs.yml`，经 `.cnb.yml` 顶部 `imports:` 注入为环境变量：
  - `GITHUB_TOKEN`：具备 `repo` 权限的 GitHub PAT
  - `GITEE_SSH_KEY`：本机 `~/.ssh/id_rsa` 私钥全文（Gitee SSH 认证；可选，未配置时跳过 Gitee 同步）

## 改代码走 CNB

在 CNB 上 push `master` 即自动镜像到 GitHub 与 Gitee。直接推 GitHub 也行，会经 `mirror-to-gitee.yml` 兜底到 Gitee（不回推 CNB）。

## 参考来源 / References

> 每条技术断言的来源与信任等级见 `sources/cnb-mirror-setup.md`。下面仅列关键一手链接。

- CNB CLI 文档：https://docs.cnb.cool/zh/plugin/public/cnbcool/cnb-cli.html
- CNB 流水线语法（grammar）：https://docs.cnb.cool/zh/build/grammar.html
- CNB 环境变量（env）：https://docs.cnb.cool/zh/build/env.html
- CNB OpenAPI 规范（swagger.json）：https://api.cnb.cool/swagger.json
- CNB 提交签名验证指南：https://docs.cnb.cool/zh/guide/commit-signature-verification.html
- Gitee 帮助中心（仓库镜像 / 私人令牌）：https://help.gitee.com/repository/settings/sync-between-gitee-github
- GitHub 个人访问令牌文档：https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens

> 安全提示：文档中不得出现真实密钥值（GITHUB_TOKEN、GITEE_SSH_KEY、CNB PAT）。密钥仅经 `shy-xin/secrets` 仓库的 `skills/envs.yml` 通过 `imports:` 注入。
