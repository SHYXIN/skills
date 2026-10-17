---
name: gitlab
description: GitLab 平台操作技能，覆盖任意 GitLab 实例的全部远端交互：MR 生命周期（创建/查看/合并/关闭/rebase）、reviewer/assignee、labels/milestone、approve 与评论讨论；以及 REST API 调用（curl + PRIVATE-TOKEN）、CI pipeline 查询、tag/发布操作、token/凭据获取。凡是涉及 GitLab 实例、GitLab API、MR、pipeline、tag、凭据的任务就用本技能。本地 git 流程（建分支 / commit / push）见 branch-management。
---

# GitLab 平台操作（gitlab）

在**任意 GitLab 实例**上完成两类事：一是"把 MR 从建到合、并把人和标签挂对"的闭环，二是 MR 之外的**平台层操作**——调 REST API、查 CI pipeline、打/验 tag、拿凭据。本技能只做 **GitLab 平台层**，不碰本地 git 流程。

## 定位与边界

| 事项 | 归属 |
| --- | --- |
| 建分支、commit、push、rebase 本地分支、合并后清理本地分支 | `branch-management` |
| **MR 创建/查看/合并/关闭/rebase、reviewer/assignee、labels/milestone、approve、评论讨论** | **本技能** |
| **REST API 调用、pipeline 查询、tag 操作、token/凭据获取** | **本技能** |

两者互补：本地流程走 `branch-management`，一旦要动 GitLab 平台层（MR、API、pipeline、tag、凭据），走本技能。

> 本机 / 公司特有的信息（glab 挂死兜底、token 位置、公司 host、分支策略约定）见 [references/local-environment.md](references/local-environment.md)。SKILL.md 主体保持通用。

---

## 前置：确认实例与认证

1. 确认远端与实例：
   ```bash
   git remote -v          # 从 URL 推断 host（ssh: git@<host>:<ns>/<proj>.git）
   ```
2. 确认 glab 已登录该 host：
   ```bash
   glab auth status
   ```
3. 记录 **project 路径**（`<namespace>/<project>`），curl 兜底时要用 URL 编码形式 `<namespace>%2F<project>`。

---

## 调用方式：glab 优先，curl 兜底

**默认用 `glab`**（按当前仓库 remote 自动识别 host，无需前缀）。`glab mr create` 在本机稳定可用。

**出现下列任一情况，立刻改 `curl + PRIVATE-TOKEN` 直连 API**，不要在 glab 上反复重试：

- `glab api` / `glab mr view` 无输出、挂死、超时
- `glab mr merge` 报 `422 {message: Branch cannot be merged}`，但 MR 实际可合

curl 通用形态：

```bash
TOK=$(git credential fill <<EOF | sed -n 's/^password=//p'
protocol=https
host=<host>
EOF
)   # 见 references/local-environment.md；备选 glab config 提取
PROJ="<namespace>%2F<project>"
API="https://<host>/api/v4"
curl -fsS -H "PRIVATE-TOKEN: $TOK" "$API/projects/$PROJ/merge_requests/<iid>"
```

> token 属敏感信息：只从配置读取使用，**绝不写入仓库、产物或回复**。

---

## 场景 1：创建 MR（含审核者 / 指派人）

```bash
glab mr create \
  --source-branch <feature-branch> \
  --target-branch <target> \
  --title "<Conventional Commits 风格标题>" \
  --description "<改动内容 / 相关 Issue / 测试方式 / Checklist>" \
  --reviewer <user1,user2> \
  --assignee <user> \
  --label <label> \
  --yes
```

要点：

- `--reviewer` / `--assignee` 用 **GitLab 用户名**（不是邮箱/显示名）；不确定用户名时先查。
- 目标分支默认取仓库集成分支（`develop` / `master` / `main`，以仓库约定为准）。
- 创建后回报 **MR 链接**给用户。

curl 兜底（创建）：

```bash
curl -fsS -X POST -H "PRIVATE-TOKEN: $TOK" \
  --data-urlencode "source_branch=<feature>" \
  --data-urlencode "target_branch=<target>" \
  --data-urlencode "title=<title>" \
  --data-urlencode "description=<desc>" \
  "$API/projects/$PROJ/merge_requests"
```

改人员/标签（对已存在的 MR）：

```bash
# 先拿用户 id
curl -fsS -H "PRIVATE-TOKEN: $TOK" "$API/users?username=<user>" | python -c "import sys,json;print(json.load(sys.stdin)[0]['id'])"
# 再更新
curl -fsS -X PUT -H "PRIVATE-TOKEN: $TOK" \
  -d "reviewer_ids[]=<id1>" -d "reviewer_ids[]=<id2>" \
  -d "assignee_id=<id>" -d "labels=<a,b>" \
  "$API/projects/$PROJ/merge_requests/<iid>"
```

---

## 场景 2：查看 MR 状态

```bash
glab mr view <iid>
```

curl 兜底时重点看这几个字段：

```bash
curl -fsS -H "PRIVATE-TOKEN: $TOK" "$API/projects/$PROJ/merge_requests/<iid>" \
  | python -c "import sys,json;d=json.load(sys.stdin);print('state:',d['state']);print('merge_status:',d.get('detailed_merge_status') or d.get('merge_status'));print('has_conflicts:',d.get('has_conflicts'));print('reviewers:',[u['username'] for u in d.get('reviewers',[])]);print('assignees:',[u['username'] for u in d.get('assignees',[])])"
```

- `detailed_merge_status: can_be_merged` 且 `has_conflicts: false` → 可合
- `state: opened` / `merged` / `closed` / `locked`

---

## 场景 3：合并前冲突预检

**合并前先做一次冲突预检**，一条命令即可，不要手写 diff 交集：

```bash
git fetch origin
git merge-tree --write-tree origin/<target> <feature-branch>
```

- 退出码 0、无冲突标记 → 可合
- 有冲突 → 停下汇报冲突文件，先解决再合（解决流程见 `branch-management`）

---

## 场景 4：合并 MR

```bash
glab mr merge <iid> --yes
```

- 合并策略：默认 `merge`（保留 merge commit，与仓库既有 `Merge branch ... into ...` 历史一致）；需要压成单提交时用 squash（`--squash` / API `squash=true`）。
- 是否删源分支：**先问用户**，确认后再加 `--remove-source-branch` / API `should_remove_source_branch=true`。
- 合并前必须满足：MR 可合、无冲突、用户已确认。

curl 兜底：

```bash
curl -fsS -X PUT -H "PRIVATE-TOKEN: $TOK" \
  -d "should_remove_source_branch=false" \
  "$API/projects/$PROJ/merge_requests/<iid>/merge"
```

---

## 场景 5：关闭 / rebase

```bash
glab mr close <iid>      # 关闭（不合并）
glab mr rebase <iid>     # 让 GitLab 侧把源分支 rebase 到目标分支
```

curl 兜底：

```bash
curl -fsS -X PUT  -H "PRIVATE-TOKEN: $TOK" "$API/projects/$PROJ/merge_requests/<iid>?state_event=close"
curl -fsS -X PUT  -H "PRIVATE-TOKEN: $TOK" "$API/projects/$PROJ/merge_requests/<iid>/rebase"
```

---

## 场景 6：approve 与评论讨论

```bash
glab mr approve <iid>                 # 批准
glab mr revoke <iid>                  # 取消批准
glab mr note <iid> -m "<评论内容>"     # 评论 / 讨论
```

curl 兜底：

```bash
curl -fsS -X POST -H "PRIVATE-TOKEN: $TOK" "$API/projects/$PROJ/merge_requests/<iid>/approve"
curl -fsS -X POST -H "PRIVATE-TOKEN: $TOK" --data-urlencode "body=<评论>" "$API/projects/$PROJ/merge_requests/<iid>/notes"
```

---

## 场景 7：MR 之外的 API 调用（pipeline / tag / 通用端点）

MR 生命周期外的平台操作直接用 curl 通用形态（见"调用方式"），常用端点：

```bash
# 查 pipeline（按 ref，如某分支或某 tag）
curl -fsS -H "PRIVATE-TOKEN: $TOK" "$API/projects/$PROJ/pipelines?ref=<ref>&per_page=3"
# 查单个 pipeline 的 jobs
curl -fsS -H "PRIVATE-TOKEN: $TOK" "$API/projects/$PROJ/pipelines/<pid>/jobs"
# 查 tag 及其指向
curl -fsS -H "PRIVATE-TOKEN: $TOK" "$API/projects/$PROJ/repository/tags/<tag>"
# 创建 tag（触发 tag 驱动的发布流水线时）
curl -fsS -X POST -H "PRIVATE-TOKEN: $TOK" \
  --data-urlencode "tag_name=v1.2.3" --data-urlencode "ref=<commit-or-branch>" \
  "$API/projects/$PROJ/repository/tags"
```

要点：

- project 路径一律 URL 编码（`<namespace>%2F<project>`）。
- 本地打 tag 也可以走 git（`git tag vX.Y.Z <ref> && git push origin vX.Y.Z`），走 API 的好处是可与后续验证在同一脚本里完成。
- tag 推送 / 删除、发布流水线触发属于发布动作，执行前须用户确认。

---

## 安全护栏（必须遵守）

以下动作**执行前必须获得用户明确确认**：

- 合并 MR（`merge`）
- 删除源分支 / 远端分支
- 关闭 MR
- 任何写操作（改 reviewer/assignee/labels、approve、评论）在用户未明确要求时不要擅自发起

只读查询（view / 查状态 / 列 MR）可直接执行。

---

## 常见坑

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `glab api` / `glab mr view` 挂死无输出 | 本机 glab 子命令问题 | 改 curl 直连 API（见 references） |
| `glab mr merge` 报 422 `Branch cannot be merged` | glab 路由误报，非真冲突 | 用 curl 查 `merge_status` 确认，再 curl 合并 |
| `--reviewer` 报找不到用户 | 传了邮箱/显示名 | 用 GitLab 用户名；curl 时先查 `/users?username=` 拿 id |
| curl 报 404 | project 路径未 URL 编码 | 用 `<namespace>%2F<project>` |
| curl 报 401 | token 取错（如抓到别的 host 的空值） | 取当前 host 段下的 token（见 references） |
| 合并后目标分支缺改动 | 合到了错误的目标分支 | 先确认 target 分支是仓库集成分支 |

---

## 完成报告

每次操作后简短汇报：

- 实例与 project
- MR iid 与链接
- 已执行的关键动作（创建/指派/合并/…）
- 当前 MR 状态（state / merge_status）
- 还需用户手动完成的事项
