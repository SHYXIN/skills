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

「推荐搭配」里的 pstack 走独立仓库镜像，不随本仓库同步：

```
backnotprop/pstack (GitHub, 上游)  ← 来源
   └─ 手工/定时同步 → Gitee (theshyxin/pstack)  ← 国内安装源
```

- 上游 `backnotprop/pstack` **没有任何 tag/release**（`git tag` 与 GitHub API 均为空），且 `npx skills add` 不支持 `@tag`/`--ref`，所以国外安装只能跟默认分支。
- 国内源是我们自己掌控的 `theshyxin/pstack` 快照，可享受「冻结版本」：同步时一并打 tag（如 `v0.15.9`），安装脚本与文档引用该 ref。
- 同步沿用本仓库的 upstream/main 分支法：`upstream` 分支存上游原样，`main` 分支叠加镜像改动，避免直接覆盖抹掉改动。
- pstack 迭代快且有过破坏性改版（其 README 记有 0.15.3 锁旧模型配置的先例），升级应为一次显式动作：同步 → 本地验一遍 → 改 tag。

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
