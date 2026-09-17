---
name: dp-session-forensics
description: DeepWorks 会话取证。查询本机 opencode.db（SQLite，只读）还原 agent 实际收到的注入、思考与工具调用，定位「agent 行为和预期不符」类问题；支持 list / injections / reasoning 对比 / dump / 导出双格式（交互式 HTML + jsonl）五个子命令。当用户说「查会话」「会话取证」「agent 为什么没收到注入」「对比两个会话」时使用。
---

# dp-session-forensics — DeepWorks 会话取证

通过查询 DeepWorks 的会话库（`opencode.db`，SQLite）还原 agent 实际收到了什么、想了什么，用于定位「agent 行为和预期不符」类问题。

## 什么时候用

- agent 说「没收到 X」/「不能使用 X」，但你确定用户操作过 → 查注入是否真的存在
- 两个会话同一操作一个成功一个失败 → dump 两边对比 reasoning 分歧
- 需要确认平台某交互（如 @ 选择）实际下发了什么内容

## 会话库位置

```
C:/Users/DEEPEXI/AppData/Roaming/com.deepexi.deepworks/deepworks-engine-data/xdg/data/opencode/opencode.db
```

脚本已内置此默认路径，`--db` 可覆盖。只读模式打开（`mode=ro`），不会污染数据。

## 五个子命令

按取证流程排列：

```bash
# 1. 找到目标会话（按工作区目录过滤最常用）
python scripts/query_sessions.py list --dir deepsense-mes-ws --limit 10

# 2. 找带 Knowledge 注入的轮次（平台 @ 选择的落地形式）
python scripts/query_sessions.py injections <session_id>

# 3. 对比两个会话各轮 reasoning，定位行为分歧点
python scripts/query_sessions.py reasoning <session_id> --grep 知识

# 4. 全量导出单个会话（存档或细看）
python scripts/query_sessions.py dump <session_id> --roles user,assistant --out session.txt

# 5. 导出双格式到 tmp/：.html（浏览器交互浏览）+ .jsonl（机器分析）
python scripts/query_sessions.py export <session_id> --out tmp
```

## export 双格式说明

- `<sid>.html`：自包含暗色页面（无外部依赖，浏览器直接打开），仿 pi 导出布局：
  - 左侧导航栏：**按轮次折叠的树状索引**——每个 user 消息开一轮（青色「轮N」节点，▸ 点击折叠/展开，双击跳轮首），轮内 assistant/工具消息为其子节点（带树形连线），徽标 ⚡注入 / 🧠思考 / 🔧工具
  - 右侧滚动联动：滚入新一轮自动**展开该轮并折叠其他**（手风琴式），点击子项精确定位
  - 搜索框实时过滤（过滤/搜索时强制全展开）；档位：全部 / User / Assistant / 有注入
  - 左栏可拖拽调宽（260–560px），窄屏自动收纳为 ☰ 按钮
  - 右侧阅读区：消息卡片，system 注入 / 思考过程 / 工具调用在 `<details>` 折叠块
- `<sid>.jsonl`：一行一条消息，字段 `mid/time/role/agent/model/system/parts`，无损，可直接用 python/jq 分析
- 文件名：`日期_时间_会话标题.html/.jsonl`（如 `2026-09-16_1638_连接MES查看当前告警.html`），标题清洗掉路径分隔符与 Windows 非法字符，截断 60 字符；终端输出里会附带 session ID 供回查会话库
- 输出目录默认 `tmp/`（已在 .gitignore），导出产物不进仓库

注：pi 的左侧是「对话树」（entry 带 parentId，编辑/重试产生分支，点击节点沿路径回溯）；DeepWorks 会话数据是线性的（message 表无 parent 字段），本导出按「轮次」造树：user 消息为轮根，其后 assistant/工具消息挂为子节点，视觉与交互上接近树状。

## schema 的坑（脚本已封装，手敲 SQL 前必读）

- `role` / `agent` / `modelID` 都藏在 `message.data` 的 JSON 里，**表上没有这些列**——`SELECT role FROM message` 直接报 no such column
- **parts 在独立的 `part` 表**（按 `message_id` 关联），不在 `message.data` JSON 里——`message.data` 里没有 parts 字段
- `part.data` 是 JSON，`type` 分 `text`（正文）/ `reasoning`（思考）/ `tool` / `step-start` 等
- 必须整条 fetch 后 `json.loads`，用 `substr` 截断会产生断 JSON
- `session.time_created` 是毫秒时间戳

## 典型案例

2026-09-16 定位 @ 知识工作区选择失败：`injections` 证明平台注入存在且两会话逐字相同，`reasoning` 对比发现失败会话的 agent 把注入解读为「另一个 agent 的运行时上下文」而拒绝使用——根因是 deepsense.md 措辞歧义，不是环境问题。

## 局限

- 只能读 DeepWorks 本机会话库，跨机器/云端会话不适用
- 库 schema 随 DeepWorks 版本可能变化，报错时先重跑本文件开头验证 schema
