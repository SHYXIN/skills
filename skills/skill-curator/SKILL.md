---
name: skill-curator
description: 维护本技能市场的 plugin.json / README 与磁盘上 skills/ 目录三者一致。注册新 skill、移除旧 skill、重同步漂移的元数据。改动文件后自动 git commit（git push 由用户手动触发）。用户手动调用（/skill-curator）。
---

# Skill Curator

维护这个技能市场的 **三处真相源（three sources of truth）** 永远一致：

1. **磁盘上的 `skills/<category>/<skill-name>/`** — 技能的实体（SKILL.md + references/）
2. **`.claude-plugin/plugin.json`** — 市场的注册清单
3. **`README.md`** — 用户的技能目录（更新命令 + 技能列表 + 目录树）

任一源头变动，另外两个必须跟着同步。本 skill 把这套同步自动化。

**核心概念 — curate（策展）**：你是一位技能策展人。策展人的职责不是创作作品，而是确保每件作品被**正确登记、归类、上架 / 下架**。本 skill 不动 SKILL.md 内容本身（那是作者 / 其他 skill 的事），只管**登记 + 归类 + 上架**。

---

## 三处同步点

### plugin.json（注册清单）

`.claude-plugin/plugin.json` → `skills[]` 数组。每个条目是相对路径字符串：`"./skills/<category>/<skill-name>"`。

- **新增 skill**：追加一行。
- **移除 skill**：删除对应行。
- **迁移 category**：改路径字符串（先 `mkdir` 新 path、`mv` 文件夹、再改注册）。

`GREEN:` `cat .claude-plugin/plugin.json | jq -r '.skills[]'` 的每一行都对应磁盘上一个真实存在的 `skills/<path>/SKILL.md`，没有缺失、没有悬空。

### README.md（三处都要同步）

| 位置 | 同步什么 | 操作 |
|---|---|---|
| **更新命令区**（`## 更新` 下方代码块） | 单独 update 行 + 批量 update 行都加新 skill 名 | 改两行 |
| **技能列表区**（`## 技能列表` 下方各 `### 类别` | 标题行 `**skill-name** — 一句话描述`（描述从 SKILL.md frontmatter description 字段抄） | 增/删/改一条 |
| **目录树区**（`## 目录结构` 下方代码块） | `skill-name/ # 备注` 行 | 增/删一行 |

`GREEN:` README.md 里三处新 skill 的信息都齐全，缺任何一个都算 not-green。

---

## Step 1 — 探测现状（drift detection）

先把三处真相当前状态读出来：

```bash
# A. 磁盘上的技能清单（含 frontmatter 名）
find skills -name SKILL.md -maxdepth 3 | sort | while read f; do
  dir=$(dirname "$f")
  name=$(grep -m1 '^name:' "$f" | sed 's/name: *//')
  echo "$dir  name=$name"
done

# B. 已注册的清单
cat .claude-plugin/plugin.json | jq -r '.skills[]'

# C. README 里出现的 skill 名（快节奏扫描）
grep -oE '^\- \*\*[a-z-]+\*\*' README.md | sed 's/- \*\*//; s/\*\*//'
```

对比三份清单，得到一份 **diff**：
- **在磁盘、不在 plugin.json** → 未注册的孤儿
- **在 plugin.json、不在磁盘** → 已删除但没清理的悬空注册
- **在 plugin.json、不在 README** → 注册了但用户看不到
- **在 README、不在 plugin.json** → 文档里有但实际没登记

`GREEN:` diff 已算出，带着明确的增删改清单进 Step 2。

---

## Step 2 — 确认策展计划

把 diff 展示给用户，生成一份**策展计划**：待注册清单、待移除清单、待同步清单。问一次"按这个走？还是要手动增删？"

`GREEN:` 用户确认了最终 plan。

---

## Step 3 —— 执行同步

按类型逐个处理：

### 3a. 注册新 skill（磁盘有、plugin.json 没有）

```bash
# 1. 改 plugin.json —— 用 jq 追加，不要手写
tmp=$(mktemp)
jq --arg p "./skills/<category>/<new-skill>" '.skills += [$p]' .claude-plugin/plugin.json > "$tmp" && mv "$tmp" .claude-plugin/plugin.md

# 2. 改 README —— 三处同步
#    a) 更新命令区
#    b) 技能列表区（描述从 SKILL.md frontmatter 取）
#    c) 目录树区
```

`GREEN:` plugin.json 里新条目存在，对应 SKILL.md 也存在；README 三处都改完。

### 3b. 移除旧 skill（plugin.json 有、磁盘没有 或 用户要求下架）

```bash
# 1. 改 plugin.json —— jq 过滤掉
tmp=$(mktemp)
jq --arg p "./skills/<category>/<old-skill>" '.skills = [.skills[] | select(. != $p)]' .claude-plugin/plugin.json > "$tmp" && mv "$tmp" .claude-plugin/plugin.json

# 2. 改 README —— 三处同步删除
```

`GREEN:` plugin.json 不再含该 skill；README 三处都不再含 SKILL.md frontmatter 里的 `name:`。

### 3c. 重同步漂移（status 还在但 README 描述过时）

用 SKILL.md frontmatter 的 `description` 字段作权威值，覆盖 README 技能列表区的描述行。

`GREEN:` README 每条描述 = 对应 SKILL.md frontmatter `description` 字段。

---

## Step 4 — Git commit

同步全部落盘后，做一个语义化 commit：

```bash
git add -A
git status --short   # 给用户看一眼暂存了什么

# 根据操作类型生成 commit msg
#   新增: feat: add <skill-name>
#   移除: chore: remove <skill-name>
#   同步: chore: sync registry
git commit -m "..."
```

`GREEN:` `git log -1 --oneline` 输出新 commit，`git status --short` 干净（除 commit 外无新增改动）。

**不要推送（push）。** push 是用户决定何时"上市"的动作。告诉用户"本地 commit 完成，检查无误后 `git push` 发布"。

---

## Pitfalls

### 坑 1 —— README 三处同步漏改

最常见的"半同步"：改了 plugin.json + 技能列表，忘了改目录树。每次操作后**三处同时 grep** 验证：

```bash
grep -c "<skill-name>" .claude-plugin/plugin.json README.md    # 应都 > 0（注册状态一致）
```

### 坑 2 —— plugin.json 手工编辑引入语法错

plugin.json 是 JSON，手滑少个逗号 / 引号就废。**始终用 jq 改**，不要直接改字符串。如果 jq 报错，立刻停下。

### 坑 3 —— frontmatter description 提取失败

有些 SKILL.md 的 frontmatter 用的是 `description:` 单行、有的是多行。提取时遇到歧义，直接把原始 frontmatter 段展示给用户看，让用户确认哪句是描述。

### 坑 4 —— commit msg 自动生成的偏差

commit msg 类型判断（feat / chore / sync）靠 diff 推断，如果同一轮混了增删改，用 `chore: sync registry` 兜底。用户读过 `git log` 可以后改。

---

## Rollback

```bash
git log --oneline -5          # 重置最近一次 curator 同步
git reset HEAD~1 --mixed      # 取消 commit，改动保留在工作区
# 然后重度跑一次 curator 即可
```
