# 本机 / 公司环境附录

本文件收纳**本机（Windows + Git Bash）与公司 GitLab 实例特有**的信息，供 SKILL.md 按需引用。换机器 / 换实例时只需改这里，SKILL.md 主体保持通用。

---

## 1. glab 在本机会挂死 / 误报 422 → 改 curl 兜底

本机 glab CLI 配置了两个 host：`gitlab.com`（token 已失效）和 `gitlab.deepexi.com`（wangxi 账号）。已知问题：

- **默认 host 落在 `gitlab.com`**：直接 `glab api` 报 `Unauthenticated`。加前缀 `GITLAB_HOST=gitlab.deepexi.com` 可解。
- **加了前缀仍会挂死**：`glab mr view` / `glab api` 无输出、被 auto-background 后超时（非 401、非交互提示）。
- **`glab mr merge` 误报 422**：报 `{message: Branch cannot be merged}`，但同一 MR 用 curl 查是 `merge_status: can_be_merged`、`has_conflicts: false`，curl 直发 PUT .../merge 一次成功。**422 是 glab 自身路由问题，不是真冲突**，别据此去 rebase/解冲突。

**结论**：本机需要读 MR 状态、合并 MR 或调 GitLab API 时，**别先试 glab 子命令**（大概率挂死或误报 422），直接用 `curl + PRIVATE-TOKEN`。`glab mr create` 可照用（按 repo remote 识别 host，无需前缀）。

---

## 2. token 获取

**首选：`git credential fill`**（走 credential.helper=manager，一步直出，2026-10-17 实测）：

```bash
TOK=$(git credential fill <<'EOF' | sed -n 's/^password=//p'
protocol=https
host=gitlab.deepexi.com
EOF
)
```

- 输出是多行键值（`protocol=` / `host=` / `username=` / `password=`），只取 `password=` 行（`glpat-` 开头，26 位）。
- 如果 credential manager 里没存该 host，此命令会挂起等待输入——非交互环境下注意，改用下面的 glab config 方式。

**备选：glab 配置文件**：

```text
C:\Users\<用户>\AppData\Local\glab-cli\config.yml
```

取 `gitlab.deepexi.com` 段下的 `token:`。

**提取坑**：config 里 `gitlab.com` 段也有一个 `token:`（**空值**），`grep "token:"` 会先抓到那个空的。要取 `gitlab.deepexi.com` 段下那一行。

```bash
# 取当前 host 段下的 token（示例：gitlab.deepexi.com）
TOK=$(awk '/gitlab\.deepexi\.com:/{f=1} f&&/token:/{gsub(/.*token: */,"");print;exit}' \
  "$HOME/AppData/Local/glab-cli/config.yml")
```

> token 属敏感信息：只从配置读取使用，**绝不写入仓库、产物或回复**。

---

## 3. 公司 GitLab 实例

- host：`gitlab.deepexi.com`
- 常见 project 路径形如 `deepsense/<repo>`，curl 时 URL 编码为 `deepsense%2F<repo>`
- REST API 端点：`https://gitlab.deepexi.com/api/v4/`

## 3.5 中文内容写操作 → curl 400，用 python urllib JSON

**现象**（2026-10-17 实测，deepworks !1251 评论 / monorepo !136 建 MR 双双中招）：

- `curl --data-urlencode "body=<中文>"` POST notes → **400 Bad Request**，稳定复现
- `curl --data-urlencode "title=<中文>"` 建 MR → 同样 400；`--data-urlencode "body@/tmp/x.txt"` → curl 报读文件错误（Git Bash 的 /tmp 与原生 curl 路径不互通）
- 换英文 title 可过；中文 body 没得绕

**结论**：凡是 **POST/PUT 带中文内容**（评论、MR 标题/描述、issue 等），直接用 python `urllib` 发 JSON（`json.dumps(...).encode('utf-8')` + `Content-Type: application/json`），token 仍从 `git credential fill` 取。模板见 SKILL.md 场景 6。纯 ASCII 的表单字段（reviewer_ids、labels 等）curl 照常可用。

---

## 4. 分支策略约定（公司仓库）

- **只许 MR 进 `dev`**：所有 MR 的 target 指向 `dev`，禁止直开 target=`main` 的 MR；`dev` 永远最新。**只有用户明示时才把 `dev` 晋升到 `main`**。
- 例外：部分仓库（如 MES 相关）集成分支是 `master`，以仓库实际 remote / 历史为准，不要默认套用 `dev`。
