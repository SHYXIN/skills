---
name: dp-agent-eval-teams
description: 向 Agent Teams 云端长程 agent（发现→AI员工→DeepSense→设备故障诊断专家链路）发起一个任务并等到完成拿结果。当用户说「发起长程任务」「让云端专家诊断」「调 Agent Teams 跑这个」「远程诊断一下」，或要直接调用云端 agent-teams 能力时触发。前置：agent-eval 仓库 .env 有 AGENT_TEAMS_TOKEN。轮询过程日志全程打印，结果与日志落盘可回看。
---

# 调用 Agent Teams 云端长程 agent（单发任务）

**这不是测评工具**：没有 dataset、没有 judge、没有评分。它是把 agent-eval 仓库里已打通的
云端链路（IAM token → workspace/project/agent 解析 → chat session → task → 轮询
`task.messages`）包成「一个任务进、一份结果出」的调用能力。

与本地版（`dp-agent-eval-local`）的区别：本版走云端 API、不依赖本机 DeepWorks 桌面端
（仅 token 刷新可选借桌面端）、单任务可能要跑几分钟。

## 用户看到什么

脚本全程打印进度（时间戳一行一步），轮询期间不沉默：

```
[14:05:01] load config repo=agent-eval target=agent_teams_device_diagnosis
[14:05:02] prompt built case_id=single-20261010-140502
[14:05:02] refreshing IAM token from desktop app
[14:05:04] calling Agent Teams cloud agent timeout=1200s (this can take minutes)
[14:07:31] runner returned exit=0 latency=149.8s
[14:07:31] saved single-20261010-140502.answer.md, .log.json
===== ANSWER =====
（agent 的结果全文）
```

结果 + 步骤日志落盘在 `<repo>/outputs/single-shot/`（`.answer.md` 任务/结果对、
`.log.json` 含每步时间戳/session_id/stdout 尾部/事件行数），用户事后可回看。

## 用法

```bash
uv run python <skill_dir>/scripts/ask_teams_agent.py \
  --repo <agent-eval 仓库路径> \
  --message "3号机床主轴异响，转速不稳" \
  [--note "现场背景"] \
  [--timeout 1200] [--no-sync-token] [--out-dir <目录>] [--dry-run]
```

- `--repo` 必填；`--message` 必填（就是发给云端 agent 的任务描述）
- `--dry-run`：只渲染 prompt 不真调，先给用户确认
- `--no-sync-token`：跳过从桌面端刷新 IAM token（桌面端没开时自动跳过）

## 首次准备（每台机器一次）

```bash
cd <agent-eval 仓库>
cp .env.example .env    # 填 AGENT_TEAMS_TOKEN；真实 token 不提交仓库
```

## 前置（脚本会检查，缺了报错即停）

1. `.env` 存在且含非空 `AGENT_TEAMS_TOKEN`
2. agent-eval 仓库有 `.venv`（`uv sync` 过）

## 排查

- 「AGENT_TEAMS_TOKEN missing」→ 登录 DeepWorks 桌面端后重跑（自动同步），或手填 `.env`
- 超时 → 默认 1200s，复杂任务 `--timeout` 加大；中断重跑即可，任务在云端已各自独立
- 任务无响应 → 看 `.log.json` 的 `raw_stderr_lines` 与 stdout 尾部定位卡在解析还是轮询

## 附：批量测评

要跑整个 XMind 测试集并评分出报告时，用仓库自带
`run_smoke.py --benchmark xmind_chain_agent_teams_file --target agent_teams_device_diagnosis`
（详见仓库 `docs/agent-teams-eval-guide.md`），本 skill 不覆盖。
