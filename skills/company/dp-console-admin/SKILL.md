---
name: dp-console-admin
description: DeepWorks 管理面 CLI：在管理控制台层面创建/发布/绑定 专家（agent）、Skill、专家团（squad），列出 runtime，删除测试资源。当用户说「建一个专家」「创建 skill 并发布」「给专家配 skill」「组个专家团」「清理测试专家」，或要在 DeepWorks 管理界面批量做资源管理时触发。走受控 Chrome + CDP 桥接（需 console 会话，不支持桌面端 token），首次运行自动登录。
---

# dp-console-admin — 管理面资源管理 CLI（CDP 桥接版）

直接操作 DeepWorks 管理控制台背后的 API（agent-teams-backend），等价于在
`https://agentteam-test.deepworks.cn/deepsense-workspace/agents` 界面上手工操作。

## 认证形态

管理面写操作要求 console 会话（Workbench OIDC 企业登录）；桌面端 token
无管理面权限，写操作会 403。

方案：脚本启动一个**受控 Chrome**（独立 profile `C:/code_proj/tmp/dp-console-chrome-profile`，
CDP 端口 9333），在管理页里 `Runtime.evaluate` 执行 fetch，cookie+CSRF 自动携带。
首次自动填企业账密登录（deepsense/deepsense，可用 `DP_CONSOLE_USER/_TENANT/_PASS`
环境变量覆盖），cookie 持久化，之后静默复用。

## 硬约束

1. **draft skill 绑不上**：skill 必须先 publish 才能绑定（draft → 404 `skill not found`）。
   加 `--publish-skills` 自动先发布。
2. **agent 发布需要 runtime**：脚本自动取 workspace 第一个 runtime。
3. **绑定是全量替换**：脚本默认 **merge**（现有+新增去重），`--replace` 才是真全量。
4. **已发布 skill 重复 publish → 400**：脚本先查状态自动跳过。

## 用法

```bash
S=<skill_dir>/scripts/dp_console_admin.py

# 首次/会话失效时：起受控 Chrome 并自动登录（也可手动 login 修复）
python $S login

# 列出资源
python $S list agents|skills|squads|runtimes

# 建 Skill（--publish 顺带发布）
python $S create-skill --name "数据质检" --instructions "检查数据质量…" [--description D] [--publish]

# 建专家：一键 建草稿→发布 skill→配 runtime→绑定→发布专家
python $S create-agent --name "质检专家" [--description D] \
  --skills "数据质检,文档处理" [--publish-skills] [--publish] [--release-note R]

# 绑定（默认合并；--replace 全量替换）
python $S bind --agent "质检专家" --skills "数据质检" [--publish-skills] [--replace]

# 单独发布
python $S publish skill --name "数据质检"
python $S publish agent --name "质检专家" [--release-note R]

# 组专家团（leader 必填）
python $S create-squad --name "质检团" --leader "质检专家"

# 删除（先 dry-run 看目标，加 --yes 才真删）
python $S delete agents|skills|squads --name "___probe_test" [--yes]
```

全局选项：`--cdp-port`（默认 9333）。

## 典型场景

- **一键造专家**：`create-agent --skills ... --publish-skills --publish`
- **清理测试资源**：先 `list agents` 找名字，再 `delete ... --yes`
- **给已有专家加 skill**：`bind`（默认合并，不打散已有配置）

## 排查

- `console tab not found` → 受控 Chrome 没开或没登过录，跑 `python $S login`
- `Workbench login page detected` 卡住 → 自动登录失败（改密了？），在受控 Chrome
  窗口里手动登一次即可（cookie 会记住）
- `skill not found: <id>`（绑定时报）→ skill 还是 draft，加 `--publish-skills`
- `Invalid CSRF token` → 会话过期，重跑 `login`
- 403 Permission denied → 当前登录账号没有管理面按钮权限（检查是否登对了企业账号）
- 重复建名 → 脚本默认拒绝重名，`--force` 才允许
- 受控 Chrome 与日常 Chrome 是两个独立窗口/profile，互不影响；关掉受控窗口
  不影响 cookie 持久化（下次自动重开）
