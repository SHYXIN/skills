---
name: dingtalk-brief
description: 钉钉每日简报。聚合未读邮件、近期收件箱、@我消息、未读会话、今日日程、今日待办，生成一份 Markdown 摘要。触发词：「看下钉钉」「今日简报」「钉钉简报」「我有什么未读」「@我有什么」「今天有什么日程/待办」。支持只拉单个数据源的定制请求。依赖 dws CLI（已装并登录，`dws auth status` 可验证）。
---

# DingTalk Brief

基于 `dws` CLI（DingTalk Workspace CLI）的钉钉信息聚合简报。

## 何时用

- 用户要"每日简报""看下钉钉""有什么未读/@我/日程/待办"
- 用户想自定义组合钉钉数据源（只要邮件、只要 @我、指定时间段日程等）

## 前置检查

1. 确认 dws 可用且已登录：

```bash
dws auth status
```

未安装或 token 失效时，提示用户先完成 dws 登录，不要继续执行其余命令。

## 默认场景：生成完整简报

执行本技能自带的脚本（与本 SKILL.md 同目录的 `scripts/dingtalk_daily_brief.ps1`）：

```powershell
pwsh -NoProfile -File "<技能目录>/scripts/dingtalk_daily_brief.ps1"
```

- 无 pwsh 时用 `powershell` 亦可。
- 脚本输出 Markdown 文件路径（`%TEMP%\dingtalk-brief\brief_<时间戳>.md`）。
- 生成后**读取该文件，用自然语言向用户摘要重点**（未读数、@我要点、今日安排），不要只丢一个文件路径。

脚本聚合六个数据源：未读邮件、近期收件箱、@我消息、未读会话、今日日程、今日待办。

### 定时自动运行（可选）

脚本可注册为 Windows 计划任务，工作日早上自动生成简报：

```powershell
$pw = (Get-Command pwsh -ErrorAction SilentlyContinue).Source; if (-not $pw) { $pw = (Get-Command powershell).Source }
$action  = New-ScheduledTaskAction -Execute $pw -Argument "-NoProfile -ExecutionPolicy Bypass -File `"<脚本绝对路径>`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 09:00
Register-ScheduledTask -TaskName "DingTalkDailyBrief" -Action $action -Trigger $trigger -Force
```

注册属共享状态变更，先向用户确认任务名和执行时间再动手。

## 按需定制数据源（dws 速查）

以下命令均已在真实环境验证过输出格式。用户只要单一数据源时直接调用，不必跑全量脚本：

| 需求 | 命令 | 关键输出字段 |
|---|---|---|
| 未读邮件 | `dws mail +unread-mail` | `.mails[]`（date/from/subject/threadId） |
| 近期收件箱 | `dws mail +recent-mail` | `.mails[]`（默认 20 封） |
| @我的消息 | `dws chat +at-me` | `.items[]`（conversation.name/sender/text/time） |
| 有未读的会话 | `dws chat +unread-chats` | `.conversations[]`（name/conversationId） |
| 今日日程 | `dws calendar +agenda` | `.data.events[]` |
| 今日到期待办 | `dws todo +due-today` | `.data.tasks[]` |

更多能力（发消息、发邮件、文档读写、日历预订等 25 个服务）用 `dws <service> --help` 探索；优先用 `+shortcut` 形式的快捷命令。

## 注意

- dws 输出是 UTF-8 JSON。在 PowerShell 里解析前必须设置 `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`，否则中文乱码且 JSON 解析失败（踩过坑）。
- 计划任务静默运行时同样受此约束——自带的脚本已内置该设置。
- 邮件/消息数据涉敏感内容，摘要时保守转述，不要把完整正文贴进不可信的输出渠道。
