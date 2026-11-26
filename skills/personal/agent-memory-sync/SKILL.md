---
name: agent-memory-sync
description: "把本机各 AI agent（codebuddy/Claude Code/Codex/DSH/WorkBuddy 等）的历史记忆扫描出来、增量导入 engram 持久记忆库，并生成用户级 AGENTS.md 记忆指引。覆盖：混合扫描（内置适配器 + 兜底特征扫描 + 人肉勾选）、按工作区分库（project 名自动推断）、增量同步（内容指纹对比只灌新增变更）、首跑对账已有条目、AGENTS.md 指引段幂等更新、跨项目纪律类记忆 global scope 约定。用户手动调用（/agent-memory-sync）。换新机器迁移记忆、定期同步、接入新 agent 记忆源时用。"
disable-model-invocation: true
---

# Agent Memory Sync（各 agent 历史记忆 → engram）

把散落在各 agent 私有目录里的历史记忆收拢进 engram，最终以「`engram search --all` 能查到全部已选源的记忆 + AGENTS.md 指引段生效」验收。

边界（三条纪律，先立后动）：

1. **md 记忆源只读**——原始记忆文件是原 agent 维护的真相源，本 skill 永不改写不删除
2. **写入只进 engram**——新结论、修正都存 engram 对应库，不回写 md
3. **入库前列清单人肉勾选**——扫描结果永远先给用户过目再动手

前置：engram 已安装且 doctor 全绿（没有先跑 `/set-engram`）。

## 核心认知：记忆源地图

| agent | 记忆位置 | 形态 |
| --- | --- | --- |
| codebuddy | `~\.codebuddy\memery\<uid>_memery.md` | 全局个人档案（单文件，frontmatter + 正文） |
| codebuddy | `~\.codebuddy\projects\<编码工作区路径>\memory\` | 项目记忆库：`MEMORY.md` 索引 + 每条记忆一个 md（frontmatter 含 name/description/type） |
| Claude Code | 项目根 `CLAUDE.md`、`~\.claude\` 下 memory 特征目录 | 探测点，存在才列 |
| Codex | `~\.codex\` 下 memory/AGENTS 特征文件 | 探测点，存在才列 |
| DSH | 用户级 `AGENTS.md` 已有指引段 | 只读参考，不重复导入 |
| 未知 agent | 兜底扫描：用户目录一层 dotdir 下找 `MEMORY.md` / `memory` / `memery` 目录 | 列出来等人裁决 |

**分库原则**：一个工作区一个 engram project，命名取工作区路径的特征段（本机先例：`C:\code_proj` → `code-proj`，`C:\Users\DEEPEXI` → `deepexi-home`）。已知库沿用已有名，新库默认取目录名，清单确认时可以改。

**type 映射**：md frontmatter 的 `type:` 字段直接透传（project/reference/feedback）；文件名前缀 `project_`/`reference_`/`feedback_` 是后备推断。

## 操作序列

全部通过脚本驱动（Python 3.8+，无第三方依赖）：

### Step 1：扫描

```bash
python scripts/agent_memory_sync.py scan
```

产出：按源分组的记忆文件清单（路径 / 条数 / 推断的 engram project / 是否已有导入记录）。完成标准：清单里每个条目都能回答「这是什么 agent、哪个工作区、多少条」。

### Step 2：勾选

把清单给用户，逐源确认：入哪个库、跳过哪些。**没有用户确认不进 Step 3**——兜底扫描可能拽进非记忆目录。

### Step 3：增量导入

```bash
python scripts/agent_memory_sync.py sync --source <源key> [--project <库>] [--dry-run]
```

- 每个文件的导入状态记在 `~\.engram\agent-memory-sync-state.json`（路径 → 内容 sha256 + engram obs_id）
- **只灌新增/变更**：指纹没变的跳过，变了的重新 save 并更新记录
- 首跑对账：库里已有但 state 没记的（比如手工灌过的），跑一次 `sync --source <源> --reconcile`——按标题在对应 project 里查重，命中即登记跳过，防重复灌库
- 完成标准：`synced=X skipped=Y fail=0`，抽一条新导的能 `engram search` 命中

### Step 4：生成 AGENTS.md 指引段

```bash
python scripts/agent_memory_sync.py agents-md
```

输出一段 Markdown（记忆源清单 + engram 分库 + 查询纪律），由 agent 插入用户级 `AGENTS.md` 的 `<!-- agent-memory-sync:start -->…<!-- agent-memory-sync:end -->` 标记对内——重复跑只更新标记内内容，不动文件其他部分。完成标准：AGENTS.md 里指引段与实际库状态一致。

## 查询与写入纪律（写给用这套库的 agent）

- 查询单库 `--project <库>`，跨库 `--all`；查询词用记忆标题里的词
- **跨项目的纪律/偏好**（工作习惯、通用踩坑）存 `--scope global`，查询 `--all` 可见；工作区专属事实不带 global
- 原始 md 有更新后重跑 sync 即可；重复跑幂等

## 坑速查表

| 症状 | 原因 | 解法 |
| --- | --- | --- |
| engram 命令每次慢 2-4 秒 | 更新检查 | `/set-engram` 坑速查表；脚本已内置 `ENGRAM_NO_UPDATE_CHECK=1` |
| 同标题记忆存出两份 | state 丢失后重灌 / 绕过脚本手工灌 | `sync --reconcile` 对账；`engram conflicts list` 兜底检出 |
| codebuddy 工作区目录名是 `c-code_proj-github-proj` 这类编码 | codebuddy 把工作区路径编码成了目录名 | 推断 project 名时取工作区特征段，清单确认环节人工把关 |
| frontmatter 解析失败 / type 推断成 reference | 文件没有 frontmatter 或字段缺失 | 文件名前缀后备推断；都没有就 reference，清单里注明 |
| 想重灌但怕重复 | 增量指纹判定"没变"跳过 | 删掉 state 里对应条目再跑，或 `engram delete <id>` 后重灌 |
| 用户级 AGENTS.md 里指引段越写越长 | 每次 agents-md 全量重写 | 标记对内幂等替换，只保留当前真实状态 |

## 来源

- 实战来源：2026-11-26 本机迁移（code-proj 166 条 + deepexi-home 17 条 + 7 条 global 纪律，全量对账通过）
- 配套：`/set-engram`（装与升级）；engram 自带 `conflicts` / `projects consolidate` 做兜底治理
