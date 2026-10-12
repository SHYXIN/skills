---
name: dp-ask-teams
description: 向 Agent Teams 云端 agent 发起一个任务并等到完成拿结果，不限于特定领域专家。当用户说「发起云端任务」「让云端专家做这个」「调 Agent Teams 跑这个」「云端跑一下」，或要直接调用云端 agent-teams 能力时触发。不带 --agent-name 时列出全部可用专家。前置：.env 有 AGENT_TEAMS_TOKEN。轮询过程日志全程打印，结果与日志落盘可回看。
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
  [--env-file "C:/path/to/.env"] \
  [--note "背景"] \
  [--timeout 1200] [--out-dir <目录>] [--no-sync-token] [--dry-run]
```

- 不带 `--agent-name` 或 `--message`（或用 `--list`）→ 只列出专家名单后退出，不发送
- `--agent-name` 按名字精确匹配，会在**所有 project** 里搜（专家分布在不同 project）
- `--message` 必填（就是发给云端 agent 的任务描述，原样发送）
- `--timeout` 默认 1200s；云端 runtime 首跑冷启动可能 10–21 分钟，给足余量
- `--dry-run`：只打印要发的消息不真调，先给用户确认
- `--no-sync-token`：跳过从桌面端刷新 IAM token（桌面端没开时自动跳过）

## 首次准备（每台机器一次）

```bash
cp .env.example .env    # 填 AGENT_TEAMS_TOKEN；真实 token 不提交仓库
```

默认读 `C:/code_proj/gitlab-proj/agent-eval/.env`，换机器时用 `--env-file` 指定路径即可。

## 前置（脚本会检查，缺了报错即停）

`.env` 存在且含非空 `AGENT_TEAMS_TOKEN`。

## 排查

- 「AGENT_TEAMS_TOKEN missing」→ 登录 DeepWorks 桌面端后重跑（自动同步），或手填 `.env`
- 「agent not found by name 'xx'」→ 报错里列出全部名字，抄一个重跑；或先不带参数跑一遍看名单
- 超时 → 云端 runtime 首跑可能极慢（实测冷启动 10–21 分钟才出回复，任务在云端不会丢，UI 里最终会出结果）；复杂任务 `--timeout` 给足（如 1800），中断重跑亦可
- 长时间 "streaming"/running 无进展 → 多半是 runtime 冷启动慢，耐心等或去 DeepWorks UI 看该 session 是否已出回复
