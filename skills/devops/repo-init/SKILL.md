---
name: repo-init
description: >
  仓库初始化引导器（一次性仪式）。两条路径：新仓库从 0 到 1
  （init → 远程 → 分支模型 → 脚手架 → 点亮 → 保护）；存量仓库只补缺。
  说「初始化仓库 / 新建仓库」或「给这个仓库补规范」时手动调用（/repo-init）。
disable-model-invocation: true
---

# repo-init — 仓库初始化引导器

把一个仓库从 0 到 1 建成规范形态，或把存量仓库按同一规范补齐。这是
**prompt 驱动的引导技能，不是脚本**：探测 → 汇报 → 征得同意 → 再动手。

关联技能（引用，不复制）：
- `/gitlab` — GitLab 平台操作：glab 优先、curl+PRIVATE-TOKEN 兜底、
  token 走 `git credential fill`（绝不入库、不回显）
- `/domain-modeling-wx` — GLOSSARY/CONTEXT 的格式与惰性创建纪律
- `/wx-flow` — 初始化完成后跑第一个任务的推荐入口

---

## 阶段 0：探测现状（只读，直接执行）

```bash
git rev-parse --is-inside-work-tree 2>/dev/null   # 是不是 git 仓库
git remote -v                                      # 有没有远程、什么平台
git branch -a                                      # 分支现状（dev? main? master?）
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null   # default 分支真相（≠ 当前所在分支）
```

再看根目录：`README.md`、`AGENTS.md`、`.gitignore`、`GLOSSARY.md`、`CONTEXT.md`
各存在与否；技术栈信号（`package.json` / `pyproject.toml` / `go.mod` …，给
.gitignore 用）；`glab auth status` / `gh auth status`（凭据可用性）。

输出一句结论：**新仓库**（路径 A）或**存量仓库**（路径 B），附盘点摘要。
用户确认后进对应路径。

---

## 路径 A：新仓库（从 0 到 1）

### A1 分支模型（问一句）

> ❓ 分支模型用哪种？**a. dev→main**（推荐，业界默认） b. dev→master

- default 分支 = main 或 master；开发主线 = dev；MR 一律进 dev。
- 结果落盘进 AGENTS.md 的「仓库约定」节，保护规则按它配。

### A2 本地 init

```bash
git init -b <default>          # default = A1 选定值
# （脚手架文件在 A4 落盘后）
git add -A && git commit       # 首个提交 = 脚手架
git branch dev                 # 建开发主线
```

### A3 远程建仓（按平台分流）

| 平台 | 动作 | 凭据不可用时 |
|---|---|---|
| GitLab | `glab repo create <ns>/<name> --private`；挂死按 `/gitlab` 切 curl 兜底（`POST /projects`） | 用户网页建仓，本技能只 `git remote add` |
| GitHub | `gh repo create <name> --private`（空仓） | 同上 |

降级时向用户要 remote URL（或从网页复制），本技能负责检测并挂载。
建仓属远程写操作，**执行前报出将创建的 `<ns>/<name>` 和可见级别，等用户点头**。

### A4 脚手架落盘

| 文件 | 内容 | 已存在时 |
|---|---|---|
| `README.md` | 项目名 + 一句话说明 + 「怎么跑」占位节 | 不动 |
| `AGENTS.md` | 含「仓库约定」节（见下） | 存在则就地补/更新该节，不覆盖其他内容 |
| `.gitignore` | 按探测到的技术栈给最小集 | 不动 |
| `GLOSSARY.md` | **引导式最小出生**：问用户「这个项目最核心的 2-3 个术语是什么」，每条一句定义；格式遵 `/domain-modeling-wx` 的 GLOSSARY-FORMAT | 不动 |
| `CONTEXT.md` | 惰性：没有真实关系/歧义可记就**不建** | 不动 |

「仓库约定」节固定字段（设完保护后回填状态）：

```markdown
## 仓库约定
- 平台：GitLab（自托管）/ GitHub；remote：<URL>
- Issue tracker：跟随平台（GitLab Issues / GitHub Issues）
- 分支模型：dev → <main|master>；MR 目标 = dev
- MR-only：禁直推 dev 与 default 分支
- 分支保护：<未设 | 已设（dev + default 禁直推、必须 MR）>
```

### A5 提交 + 点亮远程

本地 commit 完成后，**推荐 push 并等用户点头**：

> 脚手架已就绪。推荐 push `dev` 和 `<default>` 两个分支点亮远程仓，推吗？

用户点头 → push 两分支 → 把远程 default 分支设为 A1 选定值
（GitLab：`PUT /projects/:id` 改 `default_branch`；GitHub：`gh repo edit --default-branch`）。

### A6 分支保护（必须在 push 之后）

顺序不可倒：先 push 后保护——反过来的话，保护规则会拦住 init 自己的推送。

推荐配置：**dev 与 default 均禁直推（push access = No one）、必须 MR**。
报出配置要点，用户点头后执行：

- GitLab：`POST /projects/:id/protected_branches`
  （`push_access_level=0`、`merge_access_level=30`，dev 和 default 各一条）
- GitHub：`gh api -X PUT repos/{owner}/{repo}/branches/<b>/protection`
  （require PR、禁直推）

设完回填 AGENTS.md「分支保护」字段并补一次 commit + push（同确认律）。

---

## 路径 B：存量仓库（只补缺，不改既有）

1. 对照规范出**差距清单**，每项标注动作：
   - **补缺**（缺 AGENTS.md/约定节、缺 .gitignore、缺保护规则、缺 dev 分支…）
   - **仅标注**（default 是 master 而非 main、已有不同分支习惯、已有 CI 绑定…
     —— 属于既成事实，**不动**，报告里写明「与推荐规范不一致，按现状保留」）
2. 用户对清单拍板（可逐项可整体）后，只执行「补缺」项。
3. 缺 dev 分支时提议 `git branch dev`（补缺，但建分支仍要点头）。
4. 保护规则缺失时按 A6 流程补设（同样先确认）。

红线：已有分支名、remote、文件内容一律**原样保留**，本技能在存量仓库只做
「补缺 + 约定落盘」；AGENTS.md 只就地追加/更新「仓库约定」节。

---

## 收尾报告

- 创建/补齐了什么（文件清单、分支、保护规则）
- remote 链接 + issue tracker 入口
- 用户否决/跳过/仅标注的事项
- 提示：可以开始第一个任务了，建议走 `/wx-flow`

---

## 红线

- push、远程建仓、保护设置一律**先报后做**，用户点头才执行
- 先 push 后保护，顺序不可倒
- token 只从凭据链读（`git credential fill`），绝不写进仓库、产物或回复
- 存量仓库不改既有约定，不一致只标注
- GLOSSARY/CONTEXT 格式纪律全遵 `/domain-modeling-wx`，本技能不定义格式
