---
name: oss-triage
description: GitHub 开源贡献第二步：选 issue + 读代码。给定目标仓库（用户指定或 oss-finder 选出的候选），用 gh CLI 拉取候选 issue（good first issue / help wanted），筛选出「未分配、无关联 PR、仍有效」的可接 issue，浅克隆到 ~/.oss 读代码，验证 issue 现状并给出「选题 + 改动方案」。触发词：「给 <repo> 挑个 issue」「这个项目能做什么」「看看这个 issue 能不能接」。
---

# OSS Triage

帮用户从目标仓库里挑出「能接、接得动」的 issue，读完相关代码，输出「选哪个 issue + 大致怎么改」的方案。本技能只读不写：不 fork、不改代码、不留言。

**入口**：目标仓库有两种来源——
- 用户指定：「我想给 facebook/react 贡献」「帮我看下 cli/cli 这个仓库」
- oss-finder 推荐：上一环节产出的候选清单里选一个

本技能工作目录约定：`~/.oss/<owner>/<repo>`（浅克隆，只读分析用）。**不污染当前工作区。**

---

## 沟通准则：让人看得懂、跟得上（每个技能都必须遵守）

本技能面向**会提需求、但不一定熟悉 GitHub 细节**的用户。严格按下面三条做，避免「看不懂 issue」「不知道在干啥」「还得反问我」：

1. **先翻译，再动手**。每次拿到 issue / PR 原文，先用 2-3 句大白话告诉用户：
   - 这是什么（bug 报告 / 功能请求 / 纯讨论？）
   - 报告人到底想要什么
   - 做完了长什么样（验收标准）
   
   不要直接把原始 issue body 丢给用户。若用户明显不熟悉 issue / PR / fork 等概念，顺带用一句话类比解释（例如：「issue 就像在公共笔记本上贴一张便利贴提需求；PR 是你写好代码请求合并」）。

2. **过程实时播报**。每个非闲鱼动作（拉 issue、克隆、跑测试、读代码）之前，用一句大白话说明「接下来做什么、为什么」；动作之后用一句说明「刚发生了什么、有什么变化（如：已克隆 / 已定位到某文件）」。让用户始终跟得上进度，不用反复问。

3. **主动给状态小结 + 下一步**。每完成一步，给一段极简总结：「当前状态」+「下一步是什么 / 在等什么（你 / maintainer / CI）」。需要用户拍板时，明确列出选项并给出**你的推荐**，不要留白等用户来问。本技能只读不写，任何 fork / 留言 / 建分支都交给 oss-contribute，但切换前要把「接下来要走哪一步」讲清楚。

## 操作边界

本技能全部是**只读**操作，可以自动执行：
- `gh issue list` / `gh issue view` / `gh api repos/<owner>/<repo>/issues`
- `gh search issues` / `gh search prs`
- `gh repo view`
- `git clone --depth 1`（浅克隆到 `~/.oss/<owner>/<repo>`）
- 工作区内的 `Grep` / `Read` / `Glob` 读代码

本技能**不**创建 fork、不写 issue 评论、不建分支、不 push。一切结果只输出给用户看。

---

## 进入技能后先做

1. 确认 gh CLI 已登录：
   ```bash
   gh auth status
   ```
2. 确定目标仓库 `<owner>/<repo>`：
   - 用户已指定 → 直接用
   - 未指定 → 提示用户先执行 oss-finder，或直接给一个仓库名
3. 看仓库基本信息与贡献指南：
   ```bash
   gh repo view <owner>/<repo>
   gh api repos/<owner>/<repo>/contents/CONTRIBUTING.md --jq .name 2>/dev/null
   ```

---

## 场景 1：给一个仓库挑可接的 issue

触发语义：
- "给 <repo> 挑个 issue"
- "这个项目有什么能做的"
- "看看 cli/cli 有没有适合我的任务"

流程：

1. **拉候选 issue**。分两路拉，合并去重：
   ```bash
   gh issue list --repo <owner>/<repo> --state open --label "good first issue" \
     --limit 50 --json number,title,labels,assignees,createdAt,commentsCount,url
   gh issue list --repo <owner>/<repo> --state open --label "help wanted" \
     --limit 50 --json number,title,labels,assignees,createdAt,url
   ```
   评论详情在下一步用 `gh issue view --comments` 看，列表阶段只拿基础字段。

2. **过滤掉不可接的**：
   - `assignees` 非空 → 已有人接，跳过
   - issue 是纯讨论 / 提问（标题含「how to」「question」，或 body 是问题不是任务）→ 跳过
   - 有未合 PR 在改同一件事（见第 3 步验证）→ 跳过
   - 最近评论里 maintainer 明确说「已修复 / 过期 / 不需要了」→ 跳过

3. **逐个深看候选 issue**（对 2-4 个最有希望的）：
   ```bash
   gh issue view <number> --repo <owner>/<repo> --comments \
     --json number,title,body,state,labels,assignees,createdAt,closedAt,comments
   ```
   **先给用户一句大白话翻译这个 issue 在说什么**（是什么 / 报告人想要什么 / 做完什么样），再展开下面的检查要点。
   检查要点：
   - **是否有人在做**：comments 里有没有人自告奋勇「I'll take this」；用 `gh search prs "repo:<owner>/<repo> is:open <标题关键词>"` 看有没有关联 PR
   - **是否仍然有效**：body 描述的 bug / 需求是否还成立
   - **描述是否清晰**：有没有复现步骤 / 期望行为 / 验收标准；描述模糊的要降低优先级
   - **maintainer 态度**：有没有 maintainer 回复过、有没有贴过相关代码位置

4. **浅克隆并读代码**，验证「接这个 issue 要动哪些文件、难度如何」：
   ```bash
   mkdir -p ~/.oss/<owner>
   git clone --depth 1 https://github.com/<owner>/<repo>.git ~/.oss/<owner>/<repo>
   ```
   已存在则更新：
   ```bash
   git -C ~/.oss/<owner>/<repo> fetch --depth 1 origin
   git -C ~/.oss/<owner>/<repo> reset --hard origin/HEAD
   ```
   然后在 `~/.oss/<owner>/<repo>` 里用 Grep / Read / Glob 定位 issue 涉及的代码：
   - 按 issue body 里的关键词（报错信息、函数名、模块名）搜索
   - 读相关文件确认改动面
   - 对 bug 类 issue：尽量在代码里走一遍问题路径，判断「问题是否真存在」

5. **输出选题建议**，对每个深入看过的 issue 给出：

```markdown
## 选题建议：<owner>/<repo>

### 候选 1：#<number> <issue 标题>
- 现状：3 天前创建，未分配，无关联 PR，maintainer 回复过
- 问题本质：<一句话>
- 改动面：涉及 `src/xxx.py`、`tests/test_xxx.py`，约 2 个文件
- 改动思路：<大致方案，含关键函数/位置>
- 风险：需要处理 XXX 边界情况
- 建议：✅ 适合接（理由） / ⚠️ 有风险（理由） / ❌ 不建议（理由）
```

最后明确给出推荐接哪个 issue，以及下一步走 oss-contribute。

---

## 场景 2：用户指定某个具体 issue

触发语义：
- "看看 #123 这个 issue 能不能接"
- "帮我评估一下这个任务"

流程：

1. 拉 issue 全文和评论：
   ```bash
   gh issue view <number> --repo <owner>/<repo> --comments \
     --json number,title,body,state,labels,assignees,createdAt,comments
   ```
   **拉到后先翻译**（见上方「沟通准则」第 1 条），再检查。
2. 按场景 1 第 3 步的要点逐项检查（是否被认领 / 是否有 PR / 是否仍有效）。
3. 浅克隆读代码，验证问题是否真实存在、改动面多大。
4. 输出结论：能接 / 不能接，及理由和改动思路。

---

## 场景 3：仓库里根本没有适合的 issue

触发语义：
- 场景 1 过滤后一个都不剩
- 仓库的 issue 全是讨论、全是已认领

流程：

1. 明确告知用户该仓库当前没有可接的任务，不要硬挑。
2. 给出三个选项：
   - **换仓库**：回 oss-finder 换下一个候选
   - **放宽标签**：去掉 good first issue 限制，看全部 open issue（`gh issue list --repo <owner>/<repo> --state open --limit 100`），但提醒用户这些可能门槛更高
   - **转向文档 / 测试贡献**：检查有没有「改进文档」类 issue，或 README 有没有过时的部分——这类贡献对新手最友好
3. 等用户决定后再继续。

---

## 异常处理

### gh 未登录

引导 `gh auth login`（需要 `repo` 权限），完成后重试。

### 浅克隆失败（网络 / 仓库过大）

- 先重试一次
- 仍失败：改用 `gh api` 读文件树和单个文件，不下全量代码：
  ```bash
  gh api repos/<owner>/<repo>/git/trees/main?recursive=1 --jq '.tree[].path' | grep -i <关键词>
  gh api repos/<owner>/<repo>/contents/<path> --jq .content | base64 -d
  ```
  并提示用户网络问题，可能需要代理。

### issue 描述含糊，无法判断改动面

不要猜。把「信息不足」作为结论之一写进选题建议，标记为 ⚠️，并列出需要 maintainer 澄清的问题。建议用户：要么换 issue，要么接受「先留言问清楚再动手」的路径（留言操作在 oss-contribute 中做）。

### 候选 issue 都指向同一块代码

说明该模块是热点，多个人可能在抢。优先选指向冷门模块的 issue，避免提交时撞车。

---

## 完成报告

- 目标仓库与基本信息
- 看过的 issue 数、过滤原因
- 每个深入 issue 的「现状 / 问题本质 / 改动面 / 思路 / 风险」
- 明确的选题结论 + 下一步（oss-contribute）
- 结尾必须给一句「下一步是什么 / 在等什么（你 / maintainer / CI）」，不要留白让用户来问。
