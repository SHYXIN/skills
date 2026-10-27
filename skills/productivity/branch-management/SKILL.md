---
name: branch-management
description: 通用 Git 分支管理操作技能。用于在当前仓库中新建 feature 分支、同步 develop、提交并 push、MR 前检查、合并后清理分支。分支名默认 feature/<initials>-YYYYMMDD-<task>，initials 从 git config 读取（skill.initials），不硬编码用户身份。提交前校验作者邮箱（skill.email），不一致则拒绝提交。会主动执行低风险 Git 操作；历史重写、远端删除、生产分支相关动作需明确确认。
---

# Branch Management

帮用户在**当前 Git 仓库**里执行日常分支管理闭环：新建 feature 分支、同步集成分支、提交并推送、MR 前检查、合并后清理分支。

本技能是通用流程，不绑定具体仓库、不绑定具体用户。除非当前仓库另有明确约定，否则按下面的默认规则执行。

**五个场景的完整流程、命令序列和异常处理见 [SCENARIOS.md](./SCENARIOS.md)**，按用户意图进入对应场景：

| 场景 | 触发语义示例 |
|---|---|
| 1. 新建 feature 分支 | "新建分支""开一个 feature""开始新任务" |
| 2. 同步集成分支 | "同步 develop""rebase develop" |
| 3. 提交并 push | "提交一下""commit""提交并推送" |
| 4. MR 前检查 | "MR 前检查""准备提 MR""检查能不能合" |
| 5. 合并后清理分支 | "清理分支""MR 合了，删分支" |

## 用户身份（每次进入技能先确认）

分支前缀和提交身份都从 git 配置读取，**不硬编码任何人**：

```bash
git config --get skill.initials   # 分支前缀，如 wx、zs
git config --get skill.email      # 提交邮箱，用于 commit 前身份校验
```

- `skill.initials` 未配置：提示用户执行一次性设置，例如 `git config --global skill.initials wx`；用户不想配置则询问本次分支前缀用什么，仅本次生效。
- `skill.email` 未配置：跳过提交身份校验，正常提交。

feature 分支格式：

```text
feature/<initials>-YYYYMMDD-<kebab-task-name>
```

## 分支归属防线

多人共用技能库、共用仓库时，feature 分支靠 `<initials>` 前缀区分归属。凡是对**不是本人前缀**的分支执行 rebase、删除、强推等写操作前，必须先向用户确认"这个分支是你本人的吗"，防止误操作同事的分支。

## 操作边界

可以直接执行的低风险操作：
- `git status`
- `git branch --show-current`
- `git remote -v`
- `git fetch --all --prune`
- `git checkout <branch>`
- `git pull origin <branch>`
- `git checkout -b feature/<initials>-YYYYMMDD-<task>`
- `git push -u origin feature/<initials>-YYYYMMDD-<task>`
- `git add <明确文件>`
- `git commit -m "<message>"`
- `git push`

必须先明确征得用户确认的操作：
- `git rebase ...` 后的 `git push --force-with-lease`
- 删除本地分支：`git branch -d ...`
- 删除远端分支：`git push origin --delete ...`
- 对 `main` / `master` / `release/*` / `hotfix/*` 的 checkout、merge、push、reset
- 任何 `reset --hard`、`clean -fd`、`checkout -- <file>` 等会丢弃改动的命令

以上两类边界是硬规则：生产分支操作、删除分支、强推、丢弃工作区改动，先确认后执行。

## 进入技能后先做

1. 确认当前位置是 Git 仓库：
   ```bash
   git rev-parse --show-toplevel
   ```
2. 查看状态：
   ```bash
   git status --short
   git branch --show-current
   git remote -v
   ```
3. 判断集成分支：
   - 优先使用 `develop`
   - 如果没有本地 `develop`，检查 `origin/develop`
   - 如果没有 `develop`，询问用户使用哪个基线分支，常见候选是 `main` 或 `master`

如果工作区有未提交改动：
- 新建分支前，如果当前分支不是目标基线，先提醒用户并建议 stash 或在当前分支直接建 feature。
- stash 在用户明确同意后执行。
