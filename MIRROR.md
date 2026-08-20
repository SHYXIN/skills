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
  - `GITEE_PASS`：Gitee 账号密码（HTTPS 认证；可选，未配置时跳过 Gitee 同步）

## 改代码走 CNB

在 CNB 上 push `master` 即自动镜像到 GitHub 与 Gitee。直接推 GitHub 也行，会经 `mirror-to-gitee.yml` 兜底到 Gitee（不回推 CNB）。
