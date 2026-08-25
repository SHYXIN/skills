---
name: oss-finder
description: GitHub 开源贡献第一步：找项目。当用户想给开源做贡献但还没指定具体仓库时，用 gh CLI 按默认画像搜索候选仓库（近期活跃、中等规模、带 good first issue），逐项评估贡献友好度并打分，输出候选清单与推荐理由。触发词：「找开源项目」「有什么项目可以贡献」「帮我找个开源项目」；用户已经指定了仓库名时不要用本技能，直接走 oss-triage / oss-contribute。
---

# OSS Finder

帮用户在 GitHub 上找「值得贡献、接得住」的开源项目。本技能只做**发现和评估**，产出候选清单；选题和读代码交给 **oss-triage**，实际改动和提 PR 交给 **oss-contribute**。

默认用户身份：
- GitHub 账号：`SHYXIN`（登录状态通过 `gh auth status` 确认）

本技能是通用流程，不绑定具体项目。**如果用户已经指定了目标仓库（如「我想给 facebook/react 贡献」），不要执行本技能，直接进入 oss-triage。**

---

## 操作边界

本技能全部是**只读**操作，可以自动执行：
- `gh auth status`
- `gh search repos ...`
- `gh api repos/<owner>/<repo> ...`
- `gh api repos/<owner>/<repo>/contents/CONTRIBUTING.md`

本技能不产生任何 GitHub 共享状态变更，不做 fork、不建 issue、不留言。所有评估结果只输出给用户看。

---

## 进入技能后先做

1. 确认 gh CLI 已登录：
   ```bash
   gh auth status
   ```
   未登录则引导用户执行 `gh auth login`，说明需要 `repo` 权限，登录后继续。
2. 确认用户是否有偏好约束（语言 / 领域 / 话题），没有就用默认画像。

---

## 默认项目画像

无用户约束时按以下默认值搜索，目标是有社区但非巨头、适合第一次贡献的项目：

| 维度 | 默认阈值 |
|---|---|
| 活跃度 | 最近 30 天内有 push（`pushed:>30天前`） |
| 规模 | stars 200 ~ 50000（过滤掉个人玩具项目和巨型巨头） |
| 贡献友好 | `good first issue` 数量 >= 3 |
| 非归档 | `archived:false` |
| 健康度 | 有 license、有 README、issue 功能开启 |

---

## 场景 1：按默认画像找项目

触发语义：
- "找开源项目"
- "有什么项目可以贡献"
- "帮我找个开源项目"
- "想给开源做贡献，从哪里开始"

流程：

1. 计算 30 天前日期（Git Bash 用 GNU date，直接可用）：
   ```bash
   D30=$(date -d '30 days ago' +%Y-%m-%d)
   ```
2. 搜索候选仓库：
   ```bash
   gh search repos "pushed:>$D30 good-first-issues:>3 archived:false" \
     --sort stars --limit 30 \
     --json fullName,description,stargazersCount,forksCount,openIssuesCount,license,updatedAt
   ```
   说明：`--sort stars` 让搜索结果优先展示社区认可度更高的仓库；`--json` 一次拿到评估所需字段，避免逐仓多调 API。
3. 对上一步结果按语言 / 领域过滤（用户有偏好的话），取前 10 个做健康度体检。
4. 逐个体检，每个仓库检查：
   ```bash
   # 贡献指南是否存在（404 = 没有，说明贡献门槛不清晰）
   gh api repos/<owner>/<repo>/contents/CONTRIBUTING.md --jq .name
   # 仓库核心信息
   gh api repos/<owner>/<repo> --jq '{full_name, pushed_at, open_issues_count, default_branch, license: .license.spdx_id}'
   ```
5. 打分并排序。评分维度与权重如下。

### 评分细则（每项 0-5 分，满分 20）

| 维度 | 打分依据 |
|---|---|
| 活跃度（5） | `pushed_at` 距今 7 天内 = 5 分；7-30 天 = 3 分；30 天以上 = 1 分 |
| 社区健康（5） | 有 license（1 分）、有 CONTRIBUTING.md（2 分）、open issues 数在 50~1000 之间（2 分，太多说明没人清、太少说明没流量） |
| 贡献友好（5） | good first issue 数量 >= 20 得 5 分，>= 10 得 4 分，>= 3 得 3 分，否则 1 分 |
| 规模适中（5） | stars 在 1000 ~ 20000 = 5 分；200~1000 或 20000~50000 = 3 分；其余 1 分 |

6. 输出 **Top 5-8** 候选清单，格式：

```markdown
## 候选项目

| # | 仓库 | 一句话说明 | stars | 最近 push | GFI 数 | 得分 |
|---|------|-----------|-------|----------|--------|------|
| 1 | owner/repo | 描述 | 12k | 3 天前 | 15 | 18/20 |

### 推荐 1：owner/repo
- 为什么：3 天前还在发版、有贡献指南、good first issue 充足
- 谨慎点：issue 积压较多，选 issue 时要挑描述清晰的
- 下一步：用 oss-triage 给这个仓库挑一个可接的 issue
```

7. 询问用户选哪个（或直接告诉用户下一步走 oss-triage）。

---

## 场景 2：带语言 / 领域偏好找项目

触发语义：
- "找 Python 的开源项目"
- "想给前端框架做贡献"
- "找个做 AI 工具链的仓库"

流程：

在场景 1 的搜索命令上追加过滤条件：

```bash
# 指定语言
gh search repos "pushed:>$D30 good-first-issues:>3 archived:false" \
  --language python --sort stars --limit 30 --json fullName,description,stargazersCount,updatedAt

# 指定话题（可多个）
gh search repos "pushed:>$D30 good-first-issues:>3 archived:false" \
  --topic llm --topic cli --sort stars --limit 30 --json fullName,description,stargazersCount,updatedAt
```

其余流程与打分同场景 1。

---

## 异常处理

### gh 未登录

引导用户：
```bash
gh auth login
```
登录要求勾选 `repo`、`read:org` 权限。登录完成后重新执行本技能。

### 搜索结果为空或极少

说明默认画像太严，逐步放宽并说明原因：
1. 去掉 `good-first-issues:>3`，放宽到 `>0`
2. `pushed:>$D30` 放宽到 90 天
3. 去掉 stars 下界

每次放宽只动一个条件，让用户知道是哪个条件卡住了。

### 仓库的 CONTRIBUTING 在别的位置

部分仓库把贡献指南叫 `docs/CONTRIBUTING.md` 或写在 README 里。CONTRIBUTING 检查 404 时，不要直接判零分，改为检查：
```bash
gh api repos/<owner>/<repo>/contents/docs --jq '.[].name' 2>/dev/null | grep -i contributing
gh repo view <owner>/<repo> --json description 2>/dev/null
```

### 搜索结果全是超大项目

用户如果是第一次贡献，主动降权 stars > 50000 的巨型仓库，并在推荐里注明「这类仓库社区规范严、review 周期长，建议先用中小项目练手」。

---

## 完成报告

- 搜索条件（语言 / 话题 / 时间窗）
- 候选清单与得分
- 推荐 1-2 个的理由
- 下一步建议：对选中的仓库执行 oss-triage
