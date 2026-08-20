# CNB 主平台镜像设置 — 来源追溯 / Source Tracing

> 本文记录 `wangxin/skills` 以 **CNB（shy-xin/skills）** 为主平台、镜像到 GitHub + Gitee 的设置过程中，每一条技术断言（claim）的来源。
> 标记说明：
> - `对话里用过`：本会话中实际已抓取/读取的来源（WebFetch / WebSearch / API 探测 / 本地文件）。
> - `补查得到`：本会话未直接使用、本次补查的一手/二手来源。
> - `高信任一手来源`：官方文档 / 源码 / 接口规范 / 一手 API（可直信）。
> - `二手来源`：博客/论坛/聚合站（仅作线索，确认需回溯其引用的一手来源）。

---

## 一、对话里已用过的来源（已核实）

### 来源清单（对话中实际出现）
| 类型 | 标识 | 精确地址 / 路径 |
|------|------|----------------|
| WebFetch | CNB CLI 文档 | https://docs.cnb.cool/zh/plugin/public/cnbcool/cnb-cli.html |
| WebFetch | CNB 流水线语法 | https://docs.cnb.cool/zh/build/grammar.html |
| WebFetch | CNB 环境变量 | https://docs.cnb.cool/zh/build/env.html |
| WebSearch | 语法检索 | "cnb.cool .cnb.yml 流水线 语法 push 事件 stages image script 示例" |
| WebSearch | 密钥检索 | "cnb.cool .cnb.yml 使用 仓库 密钥 变量 imports 环境变量 流水线" |
| API 探测 | CNB OpenAPI | https://api.cnb.cool/swagger.json （OpenAPI 2.0，191 条 path） |
| 文件读取 | GitHub 兜底流水线 | `C:/code_proj/github-proj/wangxin/skills/.github/workflows/mirror-to-gitee.yml` |
| 文件读取 | cnb CLI 打包源码 | `C:/nvm4w/nodejs/node_modules/@cnbcool/cnb-cli/dist/index.js` |
| 文件读取 | 本地镜像说明 | `C:/code_proj/github-proj/wangxin/skills/MIRROR.md` |

### 断言追溯（对话里用过）

**C1. CNB API base 是 `https://api.cnb.cool`（不是 `https://cnb.cool/api/v1`）**
- 来源：`https://api.cnb.cool/swagger.json`（对话 API 探测，spec 本身即托管于该域名）；cnb-cli 源码 `index.js`：`process.env.CNB_API_ENDPOINT || "https://api.cnb.cool"`。
- 信任：`高信任一手来源`。
- 标签：`对话里用过`。

**C2. `cnb` CLI 的 token 取自 `CNB_TOKEN` 环境变量，回退到 `~/.cnb/token` 文件**
- 来源：cnb-cli 源码 `index.js`。`resolveToken()` 逻辑：`CNB_TOKEN_FOR_CODEBUDDY` → `CNB_TOKEN` → `loadToken()`；`loadToken()` 经 `xg()` 读取 `path.join(homedir(), ".cnb", "token")`。
- 信任：`高信任一手来源`（源码）。
- 标签：`对话里用过`（文件读取）。

**C3. CNB 不会把仓库设置里的「变量/密钥」自动注入 `.cnb.yml` 脚本；必须用 `imports:` 从密钥仓库引入**
- 来源：https://docs.cnb.cool/zh/build/env.html（「导入环境变量」一节：通过 `imports` 导入密钥仓库文件，将敏感信息注入为环境变量；文档未描述仓库设置的密钥会自动注入脚本）；https://docs.cnb.cool/zh/build/grammar.html（imports 章节）。
- 信任：`高信任一手来源`。
- 标签：`对话里用过`（WebFetch）。

**C4. `.cnb.yml` 层级为：分支(branch) → 事件(push) → 流水线(pipeline) → 阶段(stages) → 任务(jobs) → 脚本(script)**
- 来源：https://docs.cnb.cool/zh/build/grammar.html（完整示例 YAML 结构）。
- 信任：`高信任一手来源`。
- 标签：`对话里用过`（WebFetch）。

**C5. 流水线变量名仅允许 `[A-Za-z0-9_]`，不能以数字开头；变量值长度 ≤ 100KiB**
- 来源：https://docs.cnb.cool/zh/build/env.html（「限制说明」：变量名格式仅支持字母、数字和下划线，不能以数字开头；变量值长度不能超过 100KiB）。
- 信任：`高信任一手来源`。
- 标签：`对话里用过`（WebFetch）。

**C6. `imports:` 语法为 `imports: https://cnb.cool/<repo-slug>/-/blob/<branch>/file.yml`**
- 来源：https://docs.cnb.cool/zh/build/grammar.html 与 https://docs.cnb.cool/zh/build/env.html（示例：`imports: https://cnb.cool/<your-repo-slug>/-/blob/main/xxx/envs.yml`）。
- 信任：`高信任一手来源`。
- 标签：`对话里用过`（WebFetch）。

**C7. 创建仓库：`POST /{slug}/-/repos`，body 为 `{name, visibility, description}`；需权限 `group-resource:rw`**
- 来源：https://api.cnb.cool/swagger.json（paths 含 `POST /{slug}/-/repos`，描述「在指定组织下创建一个新仓库」，权限要求 `group-resource:rw`；请求体 schema 为 `dto.CreateRepoReq`，字段 `name`/`visibility`/`description`）。
- 信任：`高信任一手来源`（一手 API 规范）。
- 标签：`对话里用过`（API 探测）。

**C9. Gitee HTTPS 认证格式：`https://<token>@gitee.com` 报错 `Incorrect username or password`；`https://user:pass@gitee.com` 可用（本会话经验实测）**
- 来源：本会话对 Gitee 的经验性实测（用 `https://<token>@gitee.com` 推送失败，改用 `https://<用户名>:<私人令牌>@gitee.com` 成功）。交叉印证见下方「补查得到」的 Gitee 官方文档。
- 信任：`高信任一手来源`（一手实测）+ `补查得到` 官方交叉印证。
- 标签：`对话里用过`（经验实测）。

**C10. 将 GitHub 侧的 `mirror-to-cnb.yml` 改名 `.disabled` 可避免 CNB↔GitHub 死循环**
- 来源：本地项目配置 `MIRROR.md`（「GitHub 上的 `mirror-to-cnb.yml` 已改名 `.disabled`，避免 CNB↔GitHub 死循环」），以及 `.github/workflows/mirror-to-gitee.yml` 仅保留 Gitee 兜底。
- 信任：`高信任一手来源`（项目自身配置事实）。
- 标签：`对话里用过`（本地文件）。

**C11. GitHub PAT 需具备 `repo` 权限才能 push 镜像**
- 来源：本地 `MIRROR.md`（`GITHUB_TOKEN`：具备 `repo` 权限的 GitHub PAT）；官方文档见下方「补查得到」。
- 信任：`高信任一手来源`（项目配置）+ `补查得到`（GitHub 官方文档）。
- 标签：`对话里用过`（本地文件）。

---

## 二、补查得到的一手来源（对话未直接抓取，本次补足）

**C8. CNB 的 SSH/GPG 公钥仅用于提交/标签签名验证（commit signing），不能用于 push 认证；git 推送须用 HTTPS + PAT**
- 来源：https://docs.cnb.cool/zh/guide/commit-signature-verification.html（说明 GPG/SSH 公钥用于「对提交和标签进行签名」「CNB 会校验这些签名」，属签名验证机制，而非 git 传输层认证）。
- 佐证（代码层）：cnb-cli 源码 `index.js` 的 git/API 调用统一使用 `Authorization: Bearer ${resolveToken()}` 形式的 HTTPS 令牌；`.cnb.yml` 推送 GitHub/Gitee 亦采用 `https://$GITHUB_TOKEN@...` 的 HTTPS+PAT 模式。CNB 自身 push 走 `https://cnb:<PAT>@cnb.cool/...`。
- 信任：`高信任一手来源`（官方指南 + 源码）。
- 标签：`补查得到`。
- 备注：官方签名文档明确「签名验证」用途；「SSH 公钥不可用于 push 认证」由 CNB 整体采用 HTTPS Bearer 令牌的认证模型佐证。

**C7b. 创建仓库接口权限 `group-resource:rw` 的一手确认**
- 同 C7，swagger 原文权限字段即 `group-resource:rw`。不再单列。

**C9b. Gitee 私人令牌 over HTTPS 的官方格式**
- 来源：https://help.gitee.com/repository/settings/sync-between-gitee-github（Gitee 帮助中心「仓库镜像管理」，使用 `access_token=:personal access token` 调用 API）；Gitee 私人令牌配置文档 https://comate.baidu.com/zh/page/bflm7dpetny 引述 Gitee 自身界面：`git remote set-url origin https://<用户名>:<私人令牌>@gitee.com/<用户名>/<仓库名>...`（即「令牌放在密码字段、用户名为真实用户名」的格式）。
- 信任：Gitee 帮助中心 `help.gitee.com` 为 `高信任一手来源`；`comate.baidu.com` 为 `二手来源`（聚合站，但如实引述 Gitee 官方界面文案，可作为线索）。
- 标签：`补查得到`。
- 结论：Gitee HTTPS 凭据格式为 `https://<用户名>:<私人令牌>@gitee.com`，即「用户名 : 令牌」两段式；仅写 `https://<令牌>@gitee.com`（无用户名/未把令牌置于密码段）会被判 `Incorrect username or password`。这与本会话经验实测一致。

**C11b. GitHub PAT `repo` scope 官方说明**
- 来源：https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens（「To use your token to access repositories from the command line, select `repo`」；「You can use a personal access token in place of a password when authenticating to GitHub ... over HTTPS」）。
- 信任：`高信任一手来源`。
- 标签：`补查得到`。

---

## 三、参考来源汇总 / References

- CNB CLI 文档：https://docs.cnb.cool/zh/plugin/public/cnbcool/cnb-cli.html
- CNB 流水线语法（grammar）：https://docs.cnb.cool/zh/build/grammar.html
- CNB 环境变量（env）：https://docs.cnb.cool/zh/build/env.html
- CNB OpenAPI 规范（swagger.json）：https://api.cnb.cool/swagger.json
- CNB 提交签名验证指南：https://docs.cnb.cool/zh/guide/commit-signature-verification.html
- Gitee 帮助中心（仓库镜像 / 私人令牌）：https://help.gitee.com/repository/settings/sync-between-gitee-github
- Gitee 私人令牌配置（聚合站，引述官方界面，作线索）：https://comate.baidu.com/zh/page/bflm7dpetny
- GitHub 个人访问令牌文档：https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens

> 安全提示：任何文档与来源中均不得写入真实密钥值（GITHUB_TOKEN、GITEE_SSH_KEY、CNB PAT）。密钥仅经 `shy-xin/secrets` 仓库的 `skills/envs.yml` 通过 `imports:` 注入。
