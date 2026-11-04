---
name: machine-snap
description: 机器级环境快照与还原：capture 扫描本机 CLI（winget/choco/pip/npm）+ 三客户端 MCP 配置（codebuddy/claude/codex）+ 用户 PATH 增量，生成可修剪的 manifest；doctor 对账；restore 在新电脑照单还原；redact 出脱敏版。换新电脑想快速配成跟旧电脑一致时用。用户手动调用（/machine-snap）。
---

# Machine Snap

把「新电脑配环境」从半天回忆压缩成 capture → 修剪 → restore 三步。与 dp-dev-bootstrap 的分工：那个管**单个仓库**为什么跑不起来，这个管**整台机器**的工具集与配置。

## 概念

- **manifest**：快照清单，存 `~/.machine-snap/`（本机用户目录，MCP 里的 token **原样保留**，安全边界与 `.env` 相同）
- `manifest.draft.json` = capture 的自动采集草稿；人工修剪后另存为 `manifest.json` 定稿
- `manifest.redacted.json` = redact 生成的可外传脱敏版

## 用法

```bash
S=<skill目录>/scripts/snap.mjs

# 1. 采集（生成草稿）
node $S capture

# 2. 人工修剪草稿：删不要的条目、给容易装错的包补 note —— 然后定稿
cp ~/.machine-snap/manifest.draft.json ~/.machine-snap/manifest.json

# 3. 平时对账（清单 vs 实际装机，双向差异 + 版本差异）
node $S doctor

# 4. 新电脑还原（先 dry-run 看一遍）
node $S restore --dry-run
node $S restore

# 5. 需要外传时出脱敏版
node $S redact
```

restore 可指定别的清单：`node $S restore D:/backup/manifest.json`。

## 采集范围（三层，故意不多采）

1. **CLI**：winget（export JSON，自动剔除 `ARP\`/`MSIX\` 系统噪音）、choco、pip（`--user` 与全局都在 pip list 里）、npm 全局
2. **MCP**：按客户端分组原样快照——codebuddy `~/.codebuddy/mcp.json`、claude `~/.claude.json`（只取 `mcpServers`）、codex `~/.codex/config.toml`（只取 `mcp_servers.*` 块，保留原始 TOML 文本）
3. **PATH**：用户级 PATH 的全量条目，restore 时只补缺失的

**不采集**（各有成熟方案，不塞进来）：VS Code 插件、字体、系统设置、npm 全包快照。

## restore 语义（设计共识，勿改）

- **包管理器缺失只提示不代装**（提权/重启状态/公司策略坑密度高；提示卡里带安装命令）
- **默认装最新版**，manifest 里的版本仅作参考——restore 收尾自动跑一遍 doctor 打印版本差异表，要不要降级用户自决
- MCP 合并写入（已有的 server 不覆盖），codex 是**追加 TOML 块**（同名块存在则跳过）
- PATH 追加前逐条去重

## 已知坑（capture/restore 时注意）

- **winget 的 HTTPie.HTTPie 是 Electron GUI 假货**，不带 `http` CLI；CLI 版来自 pip。修剪草稿时删掉 GUI 条目、保留 pip 的 httpie，并在 note 里记一句
- choco 在有 pending reboot 时会报错，restore 提示用户用管理员终端
- choco list 的提示行（"Validation Warnings" 等）会被包名正则误命中——capture 已过滤，新增管理器解析时留意同类噪音
- winget export 的包 ID 不带版本号（官方导出格式如此），版本靠 doctor 的收尾对账暴露
- claude 的 `~/.claude.json` 里还有 projects/历史等无关状态，capture 只取 `mcpServers` 键

## 实测基线（2026-11-04，本机）

capture ≈240 条（winget 68 / pip ~150 / npm 17 / choco 3），MCP 4+2+2，PATH 36 条；doctor 本机 MISSING=0；redact 后 secret 键全部为 `[REDACTED]` 占位符。

## 通用化约束

脚本不绑定任何项目名/机器名；新机器类型（mac/linux）扩展方式 = 在 capture*/restore* 各函数里加分支，manifest schema 不变。
