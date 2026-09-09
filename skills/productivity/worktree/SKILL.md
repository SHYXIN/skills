---
name: worktree
description: 通用 Git worktree 隔离工作技能。帮 wangxin/wx 用 git worktree 做目录级任务隔离：从基线分支切 feature 分支到主仓库旁的 .wt-<短任务名> 目录、在 worktree 里开发提交、合并后清理 worktree 与分支。支持多 worktree 并行与归属盘点（不碰别人的工作现场）。分支命名、基线判断、提交规范沿用 branch-management 技能。一切删除动作执行前必须先向用户确认。
---

# Worktree 隔离工作

帮用户用 **git worktree** 做"目录级"任务隔离：同一仓库同时有多个独立工作目录，互不打扰。
典型场景：主仓库正在跑别的事（或有未提交改动），新任务需要干净工作区；或多条任务线并行。

本技能覆盖**全生命周期**：创建 → 开发 → 清理。
分支命名、基线判断、提交与 MR 规范**沿用 branch-management 技能**，本技能只写 worktree 特有部分。

默认用户身份（与 branch-management 一致）：
- 姓名：wangxin / 王鑫
- initials：`wx`

---

## 核心约定

### 目录位置与命名

worktree 放在**主仓库父目录**下的隐藏目录，名字 `.wt-<短任务名>`（取分支名的语义后缀）：

```text
C:/code_proj/<项目域>/<repo>/              ← 主仓库
C:/code_proj/<项目域>/.wt-<短任务名>/      ← worktree
```

示例：分支 `feature/wx-0909-fix-otel` → worktree 目录 `.wt-fix-otel`。

- 短任务名用 kebab-case 英文，2-4 个词，与分支语义对应
- 一个 worktree 只承载一件事（对应一个分支）

### 操作边界（重要）

可以直接执行的低风险操作：
- `git worktree list`
- `git worktree add <path> -b <branch> <base>`
- worktree 内的 `git status` / `git add` / `git commit` / `git push -u origin <branch>`
- `git fetch --all --prune`（只清理失效引用，不删真实数据）

**一切删除动作执行前必须先向用户确认**（无一例外）：
- `git worktree remove <path>`
- `git branch -d <branch>`（含已验证合并的本地分支——先确认，再删）
- `git branch -D <branch>`（强制删未合并分支，确认时必须说明"未合并"风险）
- `git push origin --delete <branch>`（删远端分支）
- 别人的 worktree / 分支：**一律不删，只报告**

---

## 进入技能后先做

1. 确认主仓库位置与状态：
   ```bash
   git rev-parse --show-toplevel
   git status --short
   git branch --show-current
   ```
2. 盘点现有 worktree（后面会讲归属判断）：
   ```bash
   git worktree list
   ```
3. 基线分支判断沿用 branch-management：优先 `develop`，其次问用户（常见 `main` / `master`）。

---

## 场景 1：创建 worktree

触发语义：
- "开个 worktree"
- "用 worktree 隔离做这个任务"
- "新任务，别动当前目录"

流程：

1. 提取任务名，按 branch-management 规则生成分支名 `feature/wx-<task>`（日期可省略，worktree 场景常用短格式）。
2. 从基线分支创建 worktree + 分支（一步完成）：
   ```bash
   git fetch --all --prune
   git worktree add ../.wt-<短任务名> -b feature/wx-<task> origin/develop
   ```
   路径按"主仓库父目录 + `.wt-<短任务名>`"拼出绝对路径更稳妥。
3. 进 worktree 工作：
   ```bash
   cd ../.wt-<短任务名>
   ```
4. 汇报：worktree 路径、分支名、基线。

主仓库有未提交改动时**不需要 stash**——这正是 worktree 的优势：当前目录原样保留，新任务在独立目录进行。

---

## 场景 2：在 worktree 里开发

与普通仓库无异，只提醒三点：

1. 提交、push、MR 前检查全部沿用 branch-management 技能（场景 3 / 场景 4）。
2. 注意当前 shell 的工作目录在 worktree 里，别和主仓库混淆；可用 `git rev-parse --show-toplevel` 随时确认。
3. 长任务中途离开没关系，worktree 状态独立保存，回来 `git worktree list` 能找回。

---

## 场景 3：合并后清理

触发语义：
- "MR 合了，清一下"
- "删 worktree"
- "收尾清理"

流程：

1. **验证已合并**（只读操作，可直接执行）：
   ```bash
   git fetch origin
   git merge-base --is-ancestor <分支头commit> origin/develop && echo MERGED || echo NOT_MERGED
   ```
   注意用 `origin/develop`（或对应远端基线）验证，本地基线可能落后。
2. **向用户确认**：报告将要删除的清单（worktree 目录、本地分支、远端分支），等用户点头。
3. 用户确认后，按顺序执行：
   ```bash
   git worktree remove ../.wt-<短任务名>
   git branch -d feature/wx-<task>
   git push origin --delete feature/wx-<task>
   ```
   远端分支若已被 GitLab/GitHub 在合并时自动删除，会报 `remote ref does not exist`——这是正常情况，不是错误。
4. 清理失效的远端引用：
   ```bash
   git fetch --prune origin
   ```
5. 完成报告：删了什么、保留了什么、主仓库当前分支与状态。

删除被拒绝时（`branch -d` 拒绝说明 Git 认为未合并）：
- **不要**改用 `-D` 绕过，先调查：`git log --oneline <branch> ^origin/develop` 看哪些 commit 未合。
- 若确认要放弃这些改动，向用户说明后，用户仍同意才用 `-D`。

---

## 进阶场景：多 worktree 并行与归属盘点

一个主仓库可同时挂多个 worktree（自己的、同事的）：

```bash
git worktree list
```

归属判断约定：**按分支名前缀**（`wx-` 是王鑫的，`mwn-` 等是同事的）。
worktree 目录名不一定能看出归属，分支名才可靠。

规则：
- 盘点时列出每个 worktree 的路径、分支、归属判断。
- **清理时只动自己的**（分支名含 `wx`）；别人的 worktree 与分支一律不碰、只报告。
- 发现可疑或长期不用的 worktree，报告给用户，由用户决定。

---

## 完成报告

每次操作结束后，用简短报告说明：
- 主仓库与 worktree 的路径、分支
- 已执行的关键命令
- 删除动作：删了什么、用户是否确认过
- 还需用户手动完成的事项（如创建 MR、通知同事）
