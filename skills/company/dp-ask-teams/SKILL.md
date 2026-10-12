---
name: dp-ask-teams
description: 向 Agent Teams 云端 agent 发起一个任务并等到完成拿结果，不限于特定领域专家。当用户说「发起云端任务」「让云端专家做这个」「调 Agent Teams 跑这个」「云端跑一下」，或要直接调用云端 agent-teams 能力时触发。不带 --agent-name 时列出全部可用专家。token 自动从已登录桌面端获取，零手填。轮询过程日志全程打印，结果与日志落盘可回看。
---

# 调用 Agent Teams 云端 agent（单发任务）

脚本**自包含**：纯 Python 标准库，无第三方依赖、不依赖 agent-eval 仓库、任意目录可跑。
链路：IAM 登录 → workspace/project/agent 解析（跨 project 搜索）→ 建 chat session →
原样发送你的消息 → SSE 流式等待（失败回退轮询）→ 收最终回答。
（历史版本曾依赖 agent-eval 的 runner，2026-10-12 起改为自包含。）

与本地版（`dp-ask-deepworks`）的区别：本版走云端 API、不依赖本机 DeepWorks 桌面端
（仅 token 刷新可选借桌面端）、单任务可能要跑几分钟。

## 用户看到什么

不带 `--agent-name` 先列出全部可选专家（按 project 分组、带简介）：

```
[12:02:19] login via IAM
workspace: deepsense-workspace

## DeepSense (11 agents)
- 设备故障诊断专家  # 设备故障诊断专家围绕"事实抽取 → 本体定位 → …"构建诊断闭环
- 维修执行专家  # 你好！我是「维修执行专家」
…

## 通用 (12 agents)
- 文档处理专家  # 面向 Word/DOCX、Excel/XLSX/CSV、PPTX、PDF 和 Markdown…
…

39 agents total. Re-run with --agent-name <名称> --message <任务> to send one task.
```

发送任务后全程打印进度（时间戳一行一步），轮询期间不沉默：

```
[14:05:04] login via IAM
[14:05:06] target resolved workspace=deepsense-workspace agent_id=7f3a…
[14:05:07] session created session_id=…
[14:05:08] message sent task_id=… run_id=…
[14:05:08] streaming run events (SSE)
[xx:xx:xx] answer received status=completed latency=…s
===== ANSWER =====
（agent 的结果全文）
```

结果 + 步骤日志落盘在 `--out-dir`（默认 `C:/code_proj/tmp/dp-agent-eval-logs/`，
`.answer.md` 任务/结果对、`.log.json` 含每步时间戳/session_id），用户事后可回看。

## 用法

```bash
python <skill_dir>/scripts/ask_teams_agent.py                # 不带参数：列出全部专家
python <skill_dir>/scripts/ask_teams_agent.py --list         # 同上

python <skill_dir>/scripts/ask_teams_agent.py \
  --agent-name "文档处理专家" \
  --message "把这个 Word 报告提炼成一页要点" \
  [--env test|prod] \
  [--env-file "C:/path/to/.env"] \
  [--note "背景"] \
  [--timeout 1200] [--out-dir <目录>] [--no-sync-token] [--dry-run]
```

- 不带 `--agent-name` 或 `--message`（或用 `--list`）→ 只列出专家名单后退出，不发送
- `--env` 可选：test（默认，test.deepworks.cn）/ prod（agentteam.deepworks.cn）；运行日志首行打印所连环境
- `--agent-name` 按名字精确匹配，会在**所有 project** 里搜（专家分布在不同 project）
- `--timeout` 单个等待窗口秒数（默认 1200）；窗口到期但任务还在云端跑（冷启动）会**自动续等**并打日志，不会失败退出
- `--max-wait` 总等待上限秒数（默认 2400）；冷启动实测 10–21 分钟，跑长任务建议加大到 3600
- `--dry-run`：只打印要发的消息不真调，先给用户确认
- `--no-sync-token`：跳过从桌面端刷新 IAM token（桌面端没开时自动跳过）

## 盘点 / 删除会话（清理云端历史）

每次运行（含超时/失败）都会在 out-dir 记录 session_id，之后可盘点与清理云端会话：

```bash
# 列出工作区最近的云端会话（id | 时间 | 标题），默认 20 条，删除前先盘点
python <skill_dir>/scripts/ask_teams_agent.py --list-sessions [N] [--env test]

# 删除最近一次运行建的会话（按 --env 匹配，已删的自动跳过）
python <skill_dir>/scripts/ask_teams_agent.py --delete-session last [--env test]

# 按 id 删指定会话
python <skill_dir>/scripts/ask_teams_agent.py --delete-session <uuid> [--env test]

# 批量删除本脚本记录在 out-dir 的所有存活会话（成功的打标记，失败的保留待重试）
python <skill_dir>/scripts/ask_teams_agent.py --delete-ask-sessions [--env test]
```

- 云端会话按环境隔离，`last` 与批量删除只匹配 `--env` 对应环境的记录
- 只清理本脚本记录的会话（`teams-*.log.json`），不会碰本地版 dp-ask-deepworks 的记录
- 删除成功的记录会打上 `session_deleted` 标记，`last` 与批量删除都不会再碰它们

## 首次准备（每台机器一次）

**通常零配置**：只要对应环境的 DeepWorks 桌面端开着且已登录，脚本会自动通过桌面端
调试端口（test=9223，prod=9228）拿 IAM token，无需手填。桌面端没开时回退用 .env 里
已有的 token。

.env（模板见 `.env.example`，默认读 `C:/code_proj/gitlab-proj/agent-eval/.env`，
可用 `--env-file` 换路径）两个环境的 token 各一行，均可留空由自动同步填充：

```
AGENT_TEAMS_TOKEN=       # test
AGENT_TEAMS_TOKEN_PROD=  # prod
```

## 前置（脚本会检查，缺了报错即停）

对应环境 token 可用：优先自动同步（桌面端开着+已登录），否则 .env 里对应键非空
（`--env test` 查 `AGENT_TEAMS_TOKEN`，`--env prod` 查 `AGENT_TEAMS_TOKEN_PROD`）。

## 排查

- 「TOKEN missing」且没开桌面端 → 开对应环境桌面端（已登录）重跑，或手填 .env
- 「token sync failed ... not logged in」→ 桌面端开着但未登录，先登录
- 「agent not found by name 'xx'」→ 报错里列出全部名字，抄一个重跑；或先不带参数跑一遍看名单
- 超时 → 窗口到期自动续等（日志可见 "extending wait #N"），直到 `--max-wait`（默认 2400s）才放弃；冷启动实测 10–21 分钟，任务在云端不会丢，放弃后也可去 UI 看结果或稍后重试
- 长时间 "streaming"/running 无进展 → 多半是 runtime 冷启动慢，耐心等或去 DeepWorks UI 看该 session 是否已出回复
