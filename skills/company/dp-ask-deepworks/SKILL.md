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
  [--env prod|test] \
  [--working-dir "C:/path/to/工作区"] \
  [--model "dth/DeepSeek-V4.1-Flash"] \
  [--working-dir-note "补充背景，会和问题一起给 agent"] \
  [--timeout 900] [--out-dir <目录>] [--dry-run]
```

- `--message` 发给 agent 的问题（原样发送）；删除模式下可省
- `--env` 可选：prod=正式桌面端（默认）、test=测试桌面端；对应 AppData 目录 `com.deepexi.deepworks` / `com.deepexi.deepworks.test`，目标桌面端必须已打开
- `--working-dir` 可选：目标工作区目录；只开了一个工作区时自动选中，多个时必填
- `--model` 可选：本次调用用的模型（provider 前缀可省，默认 dth）；不传则用工作区默认模型
- `--working-dir-note` 可选：附加背景说明，会和问题一起给 agent
- `--dry-run`：只打印要发的消息不真调，先给用户确认

## 盘点 / 删除会话（清理历史）

每次运行（含超时/失败）都会在 out-dir 记录 session_id，之后可盘点与清理：

```bash
# 列出工作区里最近的会话（id | 标题），默认 20 条，删除前先盘点
python <skill_dir>/scripts/ask_local_deepworks.py --list-sessions [N] \
  --env prod --working-dir "C:/path/to/工作区"

# 删除最近一次运行建的会话（按 --env 匹配，已删的自动跳过）
python <skill_dir>/scripts/ask_local_deepworks.py --delete-session last \
  [--env prod] [--working-dir "C:/path/to/工作区"]

# 按 id 删指定会话
python <skill_dir>/scripts/ask_local_deepworks.py --delete-session ses_xxx [--env prod] [...]

# 批量删除本脚本记录在 out-dir 的所有存活会话（成功的打标记，失败的保留待重试）
python <skill_dir>/scripts/ask_local_deepworks.py --delete-ask-sessions [--env prod] [...]
```

- 只清理本脚本记录的会话（本地脚本的 `{stamp}.log.json`），不会碰 dp-ask-teams 的 `teams-*.log.json`
- 删除成功的记录会打上 `session_deleted` 标记，`last` 与批量删除都不会再碰它们

## 前置（脚本会检查，缺了报错即停）

对应环境的 DeepWorks 桌面端已打开目标工作区（读不到端口/令牌文件或工作区未开会明确提示并列出该环境已开工作区）。

## 排查

- 「服务繁忙」/「请求未完成」→ 多半是工作区默认模型所在供应商上游故障，`--model` 换一个（如 `dth/DeepSeek-V4.1-Flash`）重跑
- 「workspace not open」→ 对应环境的桌面端没开或目录不对，报错里会列出该环境已开工作区；确认要连的环境与 `--env` 一致
- 超时 → 长问题 `--timeout` 加大
- 回答为空/卡住 → 看 `.log.json` 的 `messages_tail` 与本机 opencode 日志
  （`%APPDATA%/com.deepexi.deepworks/deepworks-engine-data/xdg/data/opencode/log/opencode.log`）
