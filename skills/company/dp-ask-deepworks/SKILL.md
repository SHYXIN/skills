---
name: dp-ask-deepworks
description: 向本机 DeepWorks 工作区 agent 提一个问题并拿回答复（专家能力由工作区决定，不限于诊断）。当用户说「问一下 DeepWorks 专家」「让本地 agent 看看这个问题」「调本地工作区 agent」，或要在对话里直接调用本地 DeepWorks 工作区能力时触发。前置：DeepWorks 桌面端已打开目标工作区。过程日志全程打印，回答与日志落盘可回看。
---

# 调用本地 DeepWorks 工作区（单发问答）

脚本**自包含**：纯 Python 标准库，无第三方依赖、不依赖 agent-eval 仓库、任意目录可跑。
链路：读桌面端端口/令牌文件 → 建会话 → 原样发送你的消息 → 轮询拿最终回答。
（历史版本曾依赖 agent-eval 的 runner，2026-10-12 起改为自包含。）

## 用户看到什么

脚本全程打印进度（时间戳一行一步）：

```
[11:24:09] read desktop port/token files
[11:24:09] creating session workspace_id=ws_xxx agent=deepworks
[11:24:10] prompt sent chars=13
[11:24:18] answer received latency=9.4s
===== ANSWER =====
（agent 的答复全文）
```

回答 + 步骤日志落盘在 `--out-dir`（默认 `C:/code_proj/tmp/dp-agent-eval-logs/`，
`.answer.md` 问答对、`.log.json` 含每步时间戳/session_id/消息尾部），用户事后可回看。

## 用法

```bash
python <skill_dir>/scripts/ask_local_deepworks.py \
  --message "帮我把这个目录里的报表整理成一页总结" \
  [--working-dir "C:/path/to/工作区"] \
  [--model "dth/DeepSeek-V4.1-Flash"] \
  [--working-dir-note "补充背景，会和问题一起给 agent"] \
  [--timeout 900] [--out-dir <目录>] [--dry-run]
```

- `--message` 必填（就是问 agent 的问题，原样发送）
- `--working-dir` 可选：目标工作区目录；只开了一个工作区时自动选中，多个时必填
- `--model` 可选：本次调用用的模型（provider 前缀可省，默认 dth）；不传则用工作区默认模型
- `--working-dir-note` 可选：附加背景说明，会和问题一起给 agent
- `--dry-run`：只打印要发的消息不真调，先给用户确认

## 前置（脚本会检查，缺了报错即停）

DeepWorks 桌面端已打开目标工作区（读不到端口/令牌文件会明确提示并列出已开工作区）。

## 排查

- 「服务繁忙」/「请求未完成」→ 多半是工作区默认模型所在供应商上游故障，`--model` 换一个（如 `dth/DeepSeek-V4.1-Flash`）重跑
- 「workspace not open」→ 桌面端没开或目录不对，报错里会列出已开工作区
- 超时 → 长问题 `--timeout` 加大
- 回答为空/卡住 → 看 `.log.json` 的 `messages_tail` 与本机 opencode 日志
  （`%APPDATA%/com.deepexi.deepworks/deepworks-engine-data/xdg/data/opencode/log/opencode.log`）
