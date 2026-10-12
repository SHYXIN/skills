---
name: dp-session-forensics-cloud
description: DeepWorks 会话取证，一个入口管本地+云端。--source teams 查 Agent Teams 云端会话（云 API 拉会话列表/消息明细，IAM token 自动从已登录桌面端同步）；--source local 转发本地版查本机 opencode.db。当用户说「查云端会话」「agent teams 那次跑的结果在哪」「云上会话取证」「本地+云端会话一起查」时使用。
---

# dp-session-forensics-cloud — 云端 + 本地会话取证

把本地版取证扩到云端：dp-ask-teams 发出去的每个云端任务，事后都能拉回完整消息链（谁说的、
什么内容、耗时多少）。与本地版共用一个参数风格，`--source` 切换数据面。

## 什么时候用

- 云端 agent / squad 跑完一个任务，要看它实际收发的内容和耗时
- 「上次 ask-teams 跑的那个问题，回答是什么来着」——list 按 title 搜，dump 拉全量
- 取证材料要落盘归档 —— export 出 jsonl + markdown
- 不确定会话在本地还是云端 —— 先 `--source teams list` 再 `--source local list` 各看一眼

## 用法

```bash
S=C:/code_proj/github-proj/wangxin/skills/skills/company/dp-session-forensics-cloud/scripts

# 云端（默认 source=teams, env=test）
python $S/query_cloud_sessions.py list --limit 20
python $S/query_cloud_sessions.py list --title 维修工单
python $S/query_cloud_sessions.py dump <session_id>
python $S/query_cloud_sessions.py export <session_id>   # 落 C:/code_proj/tmp/dp-forensics-cloud/

# 云端正式环境
python $S/query_cloud_sessions.py --env prod list

# 本地转发（查 opencode.db，env 默认 prod）
python $S/query_cloud_sessions.py --source local list --limit 20
python $S/query_cloud_sessions.py --source local dump <session_id>
```

## 参数矩阵

| 参数 | 值 | 数据面 |
|---|---|---|
| `--source` | `teams`（默认） | 云 API：test.deepworks.cn / agentteam.deepworks.cn |
| | `local` | 本机 opencode.db（转发 dp-session-forensics） |
| `--env` | `test` / `prod` | teams：云端双环境（默认 test）；local：本地桌面端双环境（默认 prod） |

本地版专属能力（injections / reasoning 对比）不在此复刻，`--source local` 只转发
list / dump / export；需要更深取证时直接用 `dp-session-forensics`。

## 前置条件

- **teams 源**：`.env`（默认 `C:/code_proj/gitlab-proj/agent-eval/.env`）里有
  `AGENT_TEAMS_TOKEN`（test）/ `AGENT_TEAMS_TOKEN_PROD`（prod）。token 过期时，
  已登录的对应桌面端在跑即可自动同步（test→9223 / prod→9222），无需手填。
- **local 源**：本机 opencode.db 存在（桌面端装过就有）。
- 纯 Python 标准库；认证直接 import dp-ask-teams 的 TeamsClient，不复制代码。

## 已知端点（实测 2026-10-12）

- `GET /api/chat/sessions` 会话列表
- `GET /api/chat/sessions/{id}/messages` 消息明细
- 桌面端 client.ts 还有 snapshot/stage-products/runs/artifacts 等，需要时在脚本里加子命令即可。
