---
name: dp-agent-eval-local
description: 向本机 DeepWorks 工作区 agent 提一个问题并拿回答复（设备故障诊断专家等）。当用户说「问一下 DeepWorks 专家」「让本地 agent 看看这个问题」「调 agentDemo1 诊断」，或要在对话里直接调用本地 DeepWorks 工作区能力时触发。前置：DeepWorks 桌面端已打开目标工作区；agent-eval 仓库路径必填。过程日志全程打印，回答与日志落盘可回看。
---

# 调用本地 DeepWorks 工作区（单发问答）

**这不是测评工具**：没有 dataset、没有 judge、没有评分。它是把 agent-eval 仓库里已打通的
本地链路（DeepWorks 桌面 token → localhost API → opencode session）包成「一句话进、一份答复出」
的调用能力。批量评测是附带用法，见文末一行注。

## 用户看到什么

脚本全程打印进度（时间戳一行一步）：

```
[14:02:11] load config repo=agent-eval target=agent_demo1_deepworks
[14:02:12] prompt built case_id=single-20261010-140212 chars=37
[14:02:12] calling local DeepWorks workspace timeout=900s
[14:02:58] runner returned exit=0 latency=45.3s
[14:02:58] saved single-20261010-140212.answer.md, .log.json
===== ANSWER =====
（agent 的答复全文）
```

回答 + 步骤日志落盘在 `<repo>/outputs/single-shot/`（`.answer.md` 问答对、`.log.json`
含每步时间戳/exit code/session_id/stdout 尾部），用户事后可回看。

## 用法

```bash
uv run python <skill_dir>/scripts/ask_local_deepworks.py \
  --repo <agent-eval 仓库路径> \
  --message "燃气报警了怎么排查" \
  [--working-dir-note "现场情况说明"] \
  [--timeout 900] [--out-dir <目录>] [--dry-run]
```

- `--repo` 必填；`--message` 必填（就是问 agent 的问题）
- `--working-dir-note` 可选：现场背景，会和问题一起给 agent
- `--dry-run`：只渲染 prompt 不真调，用来先给用户确认要发什么
- 默认 target `agent_demo1_deepworks`；换被测工作区改 target 或其 yaml 的 `working_dir`

## 前置（脚本会检查，缺了报错即停）

1. DeepWorks 桌面端已打开目标工作区（本地 API 探活失败会明确提示）
2. agent-eval 仓库有 `.venv`（`uv sync` 过）

## 排查

- 「desktop API unreachable」→ 桌面端没开或工作区不对
- 超时 → 默认 900s，长问题可 `--timeout` 加大
- 回答为空 → 看 `.log.json` 的 `raw_stdout_tail` 定位

## 附：批量测评

要跑整个 XMind 测试集并评分出报告时，用仓库自带 `run_smoke.py --benchmark ... --target ...`
（见仓库 README），本 skill 不覆盖。
