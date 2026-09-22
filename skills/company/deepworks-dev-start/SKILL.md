---
name: deepworks-dev-start
description: 在 Windows Git Bash 或 PowerShell 中启动 DeepWorks 桌面开发环境。自动检查依赖、设置开发环境变量、运行桌面构建并报告启动状态；适用于本地 DeepWorks 开发启动。
metadata:
  author: "deepworks-user-pb6bxh"
---

# DeepWorks 本地开发启动

## 适用场景

每次需要在本地启动 `C:/code_proj/deepworks` 桌面开发环境时使用。不限定具体功能或入口；可用于普通 DeepWorks 功能开发、桌面 UI、会话/引擎调试、扩展、CLI、`@deepsense`、CAXA MES 等场景。

## 启动前检查

1. 确认仓库存在：`C:/code_proj/deepworks`。
2. 确认当前分支和工作区改动，不自动切换分支、不覆盖用户改动。
3. 检查 `node`、`pnpm`、`bun`；依赖缺失时先报告，不自行安装系统级工具。
4. 如依赖未安装，运行：

```bash
pnpm install --frozen-lockfile
```

## Git Bash 启动方式

不要在 Windows Git Bash 中直接运行根目录 `pnpm dev`：根脚本使用 Unix 内联环境变量，但 pnpm 在 Windows 下可能交给 `cmd.exe`，导致 `DEEPWORKS_DEV_MODE` 被识别为命令。

使用以下命令：

```bash
cd /c/code_proj/deepworks
export DEEPWORKS_DEV_MODE=1
export DEEPWORKS_ELECTRON_REMOTE_DEBUG_PORT=9228
export VITE_DEEPWORKS_CLI_ENABLED=1
pnpm --filter @deepworks/desktop dev
```

## PowerShell 启动方式

```powershell
Set-Location C:\code_proj\deepworks
$env:DEEPWORKS_DEV_MODE = "1"
$env:DEEPWORKS_ELECTRON_REMOTE_DEBUG_PORT = "9228"
$env:VITE_DEEPWORKS_CLI_ENABLED = "1"
pnpm --filter @deepworks/desktop dev
```

## 启动成功判定

重点确认输出包含：

- Server/Types 构建成功；
- Engine plugins bundle 成功；
- Vite 或 Electron 开发进程启动；
- Electron CDP 暴露在 `127.0.0.1:9228`；
- DeepWorks 桌面窗口打开。

开发环境下以下信息通常不是启动失败：

- YAML 未使用导入警告；
- stale generated release config 被忽略；
- updater candidate pointer schema 警告；
- SQLite experimental warning；
- Vite JSX duplicate attribute warning。

## 启动后可选验证

启动完成后按用户当前目标继续验证，不预设必须检查某个功能：

- 普通 DeepWorks UI、会话或引擎功能：确认桌面窗口和 workspace 可用；
- 扩展或 CLI：进入对应设置页检查入口；
- DeepSense/CAXA：选择本地 workspace，确认 `@deepsense` 和对应域卡片；
- CAXA 业务：由 Kit 的 CAXA Skills 调用真实 HTTP API；API03 IoT 尚未实现时必须显示未实现，不得伪造数据。

## 状态报告格式

启动完成时简洁报告：

```text
DeepWorks 开发模式已启动。
- 分支：<branch>
- Electron/CDP：127.0.0.1:9228
- CLI 灰度：已启用
- 构建：成功/失败
- 警告：仅列影响启动的错误
```

不要把凭据、Token、工作区私有认证文件内容写入输出。
