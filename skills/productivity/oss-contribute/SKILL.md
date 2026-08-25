---
name: oss-contribute
description: GitHub 开源贡献第三步：fork → 改 → PR。在 ~/.oss/<owner>/<repo> 工作区建分支、实现 oss-triage 选出的 issue 改动、本地验证、push 到自己的 fork、按上游 CONTRIBUTING 开 PR，并在 review 后跟进。fork、push、开 PR、issue 留言等改动 GitHub 共享状态的操作一律先征得确认。触发词：「提 PR」「贡献到 <repo>」「把 #<n> 做掉」。
---

# OSS Contribute

帮用户把一个 issue 从「方案」变成「已合并的 PR」。承接 **oss-triage** 的产出：目标仓库 + issue + 改动方案。

默认用户身份：
- GitHub 账号：`SHYXIN`（fork 归到该账号下）

工作目录约定：`~/.oss/<owner>/<repo>`（与 oss-triage 共用，避免污染工作区）。

---

## 操作边界

**可以直接执行**（本地、可逆）：
- `gh repo view` / `gh api repos/<owner>/<repo>`
- `git clone` / `git fetch` / `git remote` / `git checkout` / `git branch`
- 工作区内的 `Read` / `Grep` / `Glob` 读代码
- `git add` / `git commit`（本地提交可回退）
- 本地构建与测试

**必须先征得用户明确确认**（改动 GitHub 共享状态、难撤销）：
- 创建 fork：`gh repo fork <owner>/<repo>`
- push 到自己的 fork：`git push -u fork <branch>`
- 开 PR：`gh pr create`
- 在 issue / PR 上留言（认领 issue、询问、回应 review）
- `git push --force-with-lease`（rebase 后重写远端历史）

不做任何需要 `--no-verify` 的事；PR 的检查项（DCO、测试）必须照上游规则来。

---

## 进入技能后先做

1. 确认 gh CLI 已登录：
   ```bash
   gh auth status
   ```
2. 确认三件事，缺一不可：
   - 目标仓库 `<owner>/<repo>`
   - 要做的 issue `<number>`（或明确的改动目标）
   - 改动方案（通常来自 oss-triage；没有就先做 oss-triage）
3. 读上游贡献约定：
   ```bash
   gh api repos/<owner>/<repo>/contents/CONTRIBUTING.md --jq .content | base64 -d
   ```
   重点看：branch 命名规范、commit 规范（Conventional Commits？）、是否要求 DCO / sign-off（`-s`）、测试要求、PR 模板。
4. 确定 PR 语言：跟随上游仓库惯例（默认英文；上游 issue/PR 用中文则用中文）。

---

## 场景 1：从零开始贡献一个 issue

触发语义：
- "把 #<n> 做掉"
- "提个 PR 修这个 bug"
- "开始贡献"

流程：

### 第 1 步：创建 fork（确认）

```bash
gh repo fork <owner>/<repo> --remote=false --clone=false
```
- 已 fork 过则跳过，检查自己的 fork 在不在：
  ```bash
  gh api repos/SHYXIN/<repo> --jq .full_name
  ```
- 创建前向用户说明：fork 是你账号下一个长期存在的仓库副本，删除需要手动处理。

### 第 2 步：准备工作区与分支

```bash
# 没有本地 clone 则浅克隆上游
git clone --depth 1 https://github.com/<owner>/<repo>.git ~/.oss/<owner>/<repo>
cd ~/.oss/<owner>/<repo>

# 挂两个远端：upstream = 上游，fork = 你的副本
git remote add upstream https://github.com/<owner>/<repo>.git 2>/dev/null || true
git remote add fork https://github.com/SHYXIN/<repo>.git 2>/dev/null || true

# 同步上游默认分支
git fetch upstream --depth 1

# 从上游默认分支切新分支（默认分支用 git symbolic-ref refs/remotes/upstream/HEAD 判断）
BRANCH=$(git symbolic-ref --short refs/remotes/upstream/HEAD 2>/dev/null || echo main)
git checkout -b fix/issue-<number>-<kebab-summary> upstream/$BRANCH
```

分支命名建议：`fix/issue-<number>-<kebab-summary>` 或 `feat/issue-<number>-<kebab-summary>`；若上游 CONTRIBUTING 有自己约定，优先跟上游。

### 第 3 步：实现 + 本地验证

1. 按 oss-triage 的方案改代码，只改与本次 issue 相关的文件。
2. 提交前本地验证：
   ```bash
   # 按上游 README/CONTRIBUTING 的测试命令，例如：
   # python -m pytest tests/ | npm test | cargo test
   ```
   至少跑通与改动相关的测试；跑全量太慢则说明「跑了哪部分、哪些没跑」。
3. 提交。遵循上游 commit 规范（默认 Conventional Commits，`type` 英文、摘要跟 PR 语言）：
   ```bash
   git add <明确文件>
   git commit -s -m "fix(<scope>): <摘要>

   Fixes #<number>"
   ```
   - `-s`：加上 DCO sign-off（若上游要求；不要求可省）
   - 若改动涉及多个逻辑点，拆成多个 commit，保持每个 commit 自洽

### 第 4 步：push 到自己的 fork（确认）

```bash
git push -u fork fix/issue-<number>-<kebab-summary>
```
- push 前向用户展示 `git log --oneline` 和 `git status`，说明要推的内容。
- push 后可用 `--dry-run` 先验证 PR 参数再真正创建（`gh pr create --dry-run`）。

### 第 5 步：开 PR（确认）

```bash
gh pr create --repo <owner>/<repo> \
  --head SHYXIN:<branch> \
  --base <默认分支> \
  --title "fix(<scope>): <摘要>" \
  --body-file <PR 描述文件>
```

PR 描述（跟上游语言，若上游有模板则用模板）：

```markdown
## 改动内容
<!-- 一两句话说清楚做了什么 -->

## 关联 Issue
Fixes #<number>

## 测试方式
- [ ] Step 1: 本地测试命令与结果
- [ ] Step 2: 手动验证路径

## Checklist
- [ ] 只改了与本次任务相关的文件
- [ ] 本地相关测试通过
- [ ] 已按 CONTRIBUTING 要求补齐（DCO / changelog / 格式化）
```

创建前把 PR 的 title / base / head / body 给用户过目，确认后再创建。

### 第 6 步：跟进

1. 汇报 PR 链接。
2. 盯 CI：
   ```bash
   gh pr checks --repo <owner>/<repo>
   ```
   CI 失败 → 读失败日志，修复后 `git commit --amend` / 追加 commit 并 push（需要 force push 时先确认）。
3. 若上游要求 rebase 保持线性历史：`git fetch upstream && git rebase upstream/<base>`，rebase 后 push 前先确认（`--force-with-lease`）。
4. review 意见进来后：逐条处理，回复或改代码；回复内容给用户过目后留言（留言需确认）。

---

## 场景 2：改动已经做完，只差 push + PR

触发语义：
- "改好了，帮我提 PR"
- "把我的改动推到 GitHub"
- "本地都测过了，开个 PR"

流程：

1. 确认当前分支不是上游默认分支，且改动已 commit：
   ```bash
   git status --short
   git log --oneline origin/HEAD..HEAD
   ```
2. 若工作区在别处而非 `~/.oss/<owner>/<repo>`：说明本技能默认在 `~/.oss/<owner>/<repo>` 工作；可把改动搬到该目录，或让用户确认在当前位置继续。
3. 从第 4 步（push）开始执行，前提是 fork / 远端已就绪（没有则按场景 1 补齐）。
4. 若改动对应的 issue 还没有方案记录，简单核对改动内容与 issue 是否匹配，不匹配先停下问用户。

---

## 场景 3：pr 被要求修改（review 跟进）

触发语义：
- "PR 被 review 了，怎么改"
- "CI 挂了"
- "maintainer 让我 rebase"

流程：

1. 拉最新 review 状态：
   ```bash
   gh pr view --repo <owner>/<repo>
   gh pr checks --repo <owner>/<repo>
   ```
2. 逐条处理 review 意见：
   - 每条意见给出「改 / 回复说明」的判断，改动执行；回复类内容给用户确认后留言
   - 改完 commit，push（rebase 后需 force push 时先确认）
3. CI 失败：读日志定位，修复后重新 push。
4. 全部处理完，在 PR 下留言 @ maintainer 说明已更新（留言需确认）。

---

## 异常处理

### fork 已存在但落后上游

```bash
git -C ~/.oss/<owner>/<repo> fetch upstream --depth 1
git -C ~/.oss/<owner>/<repo> push fork upstream/<base>:<base> 2>/dev/null || echo "同步 fork 失败，可手动：gh repo sync SHYXIN/<repo>"
```
简化做法：`gh repo sync SHYXIN/<repo>`（同步 fork 的默认分支）。

### 分支冲突（rebase 上游）

```bash
git fetch upstream
git rebase upstream/<base>
```
冲突时停下来，逐个文件解决，`git add` 后 `git rebase --continue`。解决不了就问用户，不要用 `--abort` 之外的方式粗暴处理（除非用户同意）。

### 上游要求 DCO（Developer Certificate of Origin）

未 sign-off 会被 CI 卡：
```bash
git commit --amend -s   # 给最近一个 commit 加 sign-off
```

### 测试跑不起来（环境依赖）

明确汇报：装了哪些依赖、跑了哪些测试、卡在哪。不要静默跳过验证；也不要在没有本地验证的情况下直接 PR。

### 用户在非 Git 目录发起

先 `git rev-parse --show-toplevel` 确认；不在仓库里就引导到 `~/.oss/<owner>/<repo>` 或克隆。

---

## 完成报告

- PR 链接
- 分支、commit 摘要
- 本地验证结果（跑了哪些测试）
- CI 状态
- 还需要的操作：等 review / 回复意见 / 同步 fork 等
