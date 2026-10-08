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

## 推荐搭配 pstack 的国内镜像

「推荐搭配」里的 pstack 走独立仓库镜像，不随本仓库同步。链路是**镜像的镜像**：

```
cursor/plugins/pstack (Cursor 原始)          ← 真·上游
   └─ 由 backnotprop 维护 → backnotprop/pstack (GitHub)
         main     = 叠加 harness 中立化改动
         upstream = 上游原样快照
      └─ 本仓 GHA 定时同步（sync-pstack.yml）→ Gitee theshyxin/pstack  ← 国内安装源
```

- `backnotprop/pstack` 本身就是 cursor/plugins/pstack 的镜像，其 `main` 已叠了 harness 中立化改动、`upstream` 分支存上游原样。我们只做**二级镜像**（backnotprop → Gitee），不直接对接 cursor 原始仓。
- 上游 `backnotprop/pstack` **没有任何 tag/release**，且 `npx skills add` 不支持 `@tag`/`--ref`，所以国外安装只能跟默认分支（`main`）。
- 国内源是我们自己掌控的 `theshyxin/pstack`，可享受「冻结版本」：本地验证后手工打 tag（当前冻结版 `v0.15.15` → `3a60467`）；因工具不支持 ref，安装脚本与文档引用的是默认分支（当前即指向 `v0.15.15`）。
- **自动同步**：`.github/workflows/sync-pstack.yml` 每周一（UTC 03:00）自动拉 `backnotprop/pstack` 的 `main`+`upstream` 两个分支、`--force` 推到 Gitee，也可在 Actions 页手动 `workflow_dispatch` 触发。复用本仓已有的 `GITEE_SSH_KEY` 密钥（与 `mirror-to-gitee.yml` 同一把），无需新配置。
- 同步**只动分支、不搬 tag**：`git clone --bare` 不带 `--tags`，冻结版本 tag 不会被上游覆盖或前移。
- pstack 迭代快且有过破坏性改版（其 README 记有 0.15.3 锁旧模型配置的先例），**升级应为一次显式动作**：等自动同步拉下新分支 → 本地验一遍 → 再手工打新 tag 并改脚本文档引用。

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
