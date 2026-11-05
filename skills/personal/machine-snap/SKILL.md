---
name: machine-snap
description: agent 工具箱快照与还原：whitelist.json 记录有利于 agent 工作的 CLI 白名单（core = agent 直接用的 CLI 如 rg/jq/fzf/duckdb/sg/http，coreRuntimes = MCP/skills 依赖的 runtime），doctor 逐条对账本机在位情况，restore 照单还原 + 三客户端 MCP 配置 + PATH 增量，redact 出脱敏版。换新电脑快速给 agent 配齐工具箱时用。用户手动调用（/machine-snap）。
---

# Machine Snap

把「新电脑给 agent 配工具箱」压缩成三步：**改白名单 → doctor 对账 → restore 还原**。

与 dp-dev-bootstrap 的分工：那个管**单个仓库**为什么跑不起来，这个管**整台机器**上 agent 的工具集与配置。

## 定位

**只记有利于 agent 工作的东西**——不是整机快照。manifest 是**手工维护的白名单**：

- `core`：agent 直接调用的工作 CLI（rg/jq/fzf/duckdb/sg/http/gh/glab/cnb 等）
- `coreRuntimes`：MCP server 和 skills 依赖的 runtime（nvm/python/uv 等），restore 时**先装**
- MCP 三客户端配置 + PATH 增量：从本机实采（`snap-mcp` 命令），不进白名单

## 文件布局

| 文件 | 内容 | 性质 |
|---|---|---|
| `whitelist.json`（skill 包内） | core + coreRuntimes 白名单，手工维护 | 随 skill 走，可进 git |
| `~/.machine-snap/mcp-snapshot.json` | MCP 三客户端原样快照（含 token）+ PATH | 本机文件，`snap-mcp` 命令采集，**不进 git** |
| `~/.machine-snap/manifest.redacted.json` | redact 生成的可外传脱敏版 | 可备份/外传 |

## 用法

```bash
S=<skill目录>/scripts/snap.mjs

# 1. 日常机：采集 MCP + PATH 快照（含 token，只存本机）
node $S snap-mcp

# 2. 平时对账（白名单逐条核对 + MCP/PATH 差异）
node $S doctor

# 3. 新电脑还原（先 dry-run 看一遍）
node $S restore --dry-run
node $S restore

# 4. MCP/PATH 快照需要外传时出脱敏版
node $S redact
```

前提：新电脑需有 node（restore 脚本本身是 node 写的）。

## 白名单条目格式

```json
{ "manager": "winget|choco|pip|npm|manual", "packageId": "包管理器的包 ID",
  "command": "实际命令名", "version": "仅参考", "note": "备注/坑" }
```

- `command` 必填且必须真实可执行——**winget 包 ID ≠ 命令名**是最大坑源
- `manager: "manual"` = 不代装，restore 时打印 note 里的手工命令
- 加新工具 = 在 whitelist.json 里加一条，然后 doctor 验证

## restore 语义

- **coreRuntimes 先装 → tools → MCP → PATH**（runtime 铺好后面的才装得上）
- **包管理器缺失只提示不代装**（提权/重启状态/公司策略坑密度高；提示卡带安装命令）
- manual 条目只打印 note 不执行
- 默认装最新版，version 仅作 doctor 对账参考
- MCP 合并写入（同名 server 以快照为准，快照没有的不动），codex 是**追加 TOML 块**（同名块存在则跳过）
- PATH 追加前逐条去重
- 无 mcp-snapshot.json 时只还原 CLI 并提示（快照文件要人肉从旧机带过来）

## 已知坑

- **winget 的 HTTPie.HTTPie 是 Electron GUI 假货**，不带 `http` CLI；CLI 版来自 pip（whitelist 里 pip:httpie 已记 note）
- **node 走 nvm4w**（不是 winget 直装 NodeJS），restore 提示卡里是 choco install nvm 路径
- choco 在有 pending reboot 时会报错，restore 提示用管理员终端
- winget export 的包 ID 不带版本号，版本靠 doctor 逐条 `--version` 探测暴露
- claude 的 `~/.claude.json` 里还有 projects/历史等无关状态，snap-mcp 只取 `mcpServers` 键
- glab 在部分环境有挂死史，备选 curl 直连 API

## 通用化约束

脚本不绑定任何项目名/机器名；白名单按机器类型分文件扩展（如 whitelist.macos.json），doctor/restore 加 `--wl <文件>` 参数即可，schema 不变。
