---
name: set-engram
description: "给本机安装/升级 engram（AI coding agent 持久记忆系统：单 Go 二进制 + SQLite，MCP/CLI/TUI 三用）并把任意 AI coding agent 接入它。覆盖：Windows 安装两条路径（GitHub release zip 实测 / Go install）、doctor 体检、save/search/timeline/stats 常用命令、codebuddy mcp.json 注册模板、升级时 exe 被 agent 的 MCP 常驻进程占用的处理、实测坑（更新检查每次调用拖慢 2-4 秒、搜索偏关键词、scope 是枚举）。用户手动调用（/set-engram）。换新机器配记忆工具、升级 engram、给新 agent 接记忆时用。"
disable-model-invocation: true
---

# Set Engram（安装 + 升级 + 多 agent 接入）

在一台 Windows 机器上装好 engram 并通过 doctor 全绿，最终以「任意 agent 能通过 CLI 或 MCP 读写同一份记忆库」验收。

本 skill 只管**装、升级、接入**；记忆内容的迁移导入走 `/agent-memory-sync`，日常存查命令见 Step 3 速查。

## 核心认知：engram 的心智模型

- **是什么**：agent 持久记忆，单 Go 二进制 + SQLite（`~/.engram/engram.db`），策展式哲学——存结论/决策/坑，不存对话流水，写入靠 agent 主动 save
- **三层结构**：`project`（工作区隔离）→ `observation`（一条记忆，带 type）→ 可选 `scope` 标记适用范围
- **type 惯例**：`project`（工作区事实）/ `reference`（外部事实、路径、凭据位置）/ `feedback`（踩坑与纪律）
- **三个入口**：CLI（脚本化，agent 最好接）、MCP stdio（agent 内原生工具，27 个 `mem_*` 工具）、TUI（人肉翻库）

正主仓库：https://github.com/Gentleman-Programming/engram （认准这个；社区有同名 fork 版本线不同，如 nagisanzenin/engram 停在 v1.x，看源码别拿错）。

## Step 1：安装

**路径 A：release zip（推荐，无工具链依赖，实测路径）**

从 https://github.com/Gentleman-Programming/engram/releases/latest 拿 `engram_<ver>_windows_amd64.zip`，解出 `engram.exe` 放进 PATH 目录（本机惯例 `~\.local\bin\`）：

```powershell
$ver = "3.7.2"   # 换成 latest 页看到的版本
$tmp = "$env:TEMP\engram-setup"; New-Item $tmp -Force | Out-Null
Invoke-WebRequest -Uri "https://github.com/Gentleman-Programming/engram/releases/download/v$ver/engram_${ver}_windows_amd64.zip" -OutFile "$tmp\e.zip"
Expand-Archive "$tmp\e.zip" "$tmp\x" -Force
Copy-Item "$tmp\x\engram.exe" "$env:USERPROFILE\.local\bin\" -Force
engram --version   # 完成标准：输出版本号
```

release 附带 `checksums.txt`，较真就校验一下。

**路径 B：Go install（机器上有 Go 工具链时）**

```bash
go install github.com/Gentleman-Programming/engram/v3/cmd/engram@latest
```

装完把 `%USERPROFILE%\go\bin` 确认在 PATH 里。

## Step 2：doctor 验收

```powershell
engram doctor
```

完成标准：`Checks: 10 ok=10 warnings=0 blocked=0 errors=0`。有 blocked 再处理，别带病往下走。

## Step 3：CLI 速查（agent 接入的最小集）

```powershell
engram save "标题" "内容" --type feedback --project <库> --scope global   # 存；type 用 project/reference/feedback
engram search "<关键词>" --project <库>        # 查单库
engram search "<关键词>" --all                 # 跨库查；跨项目记忆优先用这个
engram timeline <obs_id>                       # 看某条记忆前后的上下文
engram stats --all                             # 全库统计（条数/项目列表）
engram tui                                     # 人肉翻库
engram delete <obs_id>                         # 软删；--hard 才真删
```

经验：**search 偏关键词而非纯语义**——查询词用记忆标题里出现过的词，命中率最高；同一条结论跨项目适用时存一份 `--scope global` 的，`--all` 一网打尽。

## Step 4：接入各 agent

**codebuddy（mcp.json，stdio）**：在 `~\.codebuddy\mcp.json` 加：

```json
"engram": {
  "command": "C:\\<用户目录>\\.local\\bin\\engram.exe",
  "args": ["mcp"]
}
```

`engram mcp` 支持 `--tools=agent|admin|all`（27 工具全量默认）和 `--project NAME`（进程级默认库）。重启 agent 会话后生效。

**Claude Code / Codex**：各自的 MCP 注册机制同型——command 指到同一个 `engram.exe`，`args: ["mcp"]`。注册后用一条 `mem_search` 实测握手。

**DSH / 其他没有 MCP 注册位的 agent**：CLI 就是兜底——agent 能跑命令就能 `engram save/search`，不依赖任何集成位。用 `--project` 或环境变量 `ENGRAM_PROJECT` 固定默认库。

## Step 5：升级

engram 常驻形态是各 agent 的 MCP server，**exe 被运行中的进程锁死**，直接覆盖会报 `being used by another process`：

```powershell
Get-Process engram | Stop-Process -Force        # 杀掉所有常驻实例（agent 空闲时无感知）
Start-Sleep -Milliseconds 800
Copy-Item "$env:USERPROFILE\.local\bin\engram.exe" "$env:USERPROFILE\.local\bin\engram.exe.bak-<旧版本>" -Force
Copy-Item "<新解压>\engram.exe" "$env:USERPROFILE\.local\bin\engram.exe" -Force
engram --version        # 完成标准：新版本号
engram doctor           # 完成标准：10/10 ok
engram search "<已知存在的关键词>" --all   # 抽查：老记忆还在
```

agent 侧无需重配：MCP 下次被调用时自动拉起新版二进制。

## 坑速查表

| 症状 | 原因 | 解法 |
| --- | --- | --- |
| 每次 save/search 多等 2-4 秒，偶尔刷 `Could not check for updates` | 启动时 GitHub 更新检查超时 | 设 `ENGRAM_NO_UPDATE_CHECK=1`；压不掉也无害，只是慢 |
| 覆盖 exe 报 `being used by another process` | agent 的 MCP 常驻进程锁着文件 | Step 5 先 `Stop-Process` 再换 |
| save 时提示 update available 并附 go install 命令 | 有新版本 | 按 Step 5 流程升级，别当场 go install（工具链未必在） |
| 搜得到英文/标题词，换口语描述就搜不到 | 检索偏关键词 | 用记忆标题里的词查；真语义需求走 TUI 人肉翻 |
| `--scope md-import-xxx` 存进去显示 `scope: project` | scope 是枚举（project/global 等），自由字符串被归一 | 想标自定义批次用 state 文件记，别指望 scope |
| 同一条记忆存出两份 | 重复 save（engram 有 conflicts 机制能检出） | `engram conflicts list` 查看；导入类操作前先查重 |
| 项目名起乱了想合并 | 多次入库用了不同 project 名 | `engram projects consolidate --all --dry-run` 先预览再合并 |

## 来源

- 仓库：https://github.com/Gentleman-Programming/engram （README / `engram --help`）
- 本机先例：`~\.codebuddy\mcp.json` 的 engram 条目；`~\.engram\engram.db`
- 记忆内容迁移：`/agent-memory-sync`
