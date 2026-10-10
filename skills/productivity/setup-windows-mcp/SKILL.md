---
name: setup-windows-mcp
description: "在新 Windows 电脑上安装并注册 Windows-MCP（Windows 桌面自动化 MCP server：截屏、点击、UI 树、浏览器控制）。覆盖 codebuddy / claude-code / codex 三个 CLI 的一次性配置，含国内网络加速（uv 安装镜像 + PyPI 镜像）。首次在新机器配 windows-mcp、或 MCP 连接报 'uvx not found' / 超时时使用。"
---

# 安装 Windows-MCP（新机器配置指南）

## 这个 skill 解决什么

Windows-MCP（`windows-mcp` PyPI 包）让 agent 直接操作 Windows 桌面：截屏、鼠标点击、键盘输入、UI 元素树、窗口管理。它靠 `uvx` 运行——**不需要 clone 源码**，uvx 自动从 PyPI 拉包。

新机器上配它的坑不在 MCP 本身，而在三件事：

1. **uv 没装** → `uvx` 命令不存在，注册了也连不上。
2. **国内网络** → astral.sh 官方安装脚本可能超时；uvx 首次拉 windows-mcp 的 90+ 依赖包走 PyPI，国内同样可能超时。
3. **PATH 分裂** → Git Bash、PowerShell、cmd 的 PATH 可能不一致，agent 在 Git Bash 里找不到 uvx（本机经验：winget/uvx 都出现过这种情况）。**注册 MCP 时用 uvx.exe 全路径最稳**。

## 总原则

- **不需要 clone Windows-MCP 源码仓库**——uvx 直接从 PyPI 运行，clone 只在改源码时才需要。
- **注册用 uvx 全路径**，不要裸写 `uvx`——规避各终端 PATH 不一致。
- **镜像设成 Windows 用户级**，不要只写 `~/.bashrc`——uvx 是 Windows 程序，PowerShell/cmd 读不到 bash 配置。

---

## 步骤一：安装 uv（含国内加速）

优先官方脚本（PowerShell）：

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

超时则走国内备选（任选其一）：

```powershell
# 备选 A：winget（Windows 自带包管理器）
winget install --id=astral-sh.uv -e

# 备选 B：pip（有 Python 环境时）
pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple
```

装完验证：**开新终端**（PATH 才会刷新），运行 `uvx --version`。

找不到命令时，检查默认安装位置 `%USERPROFILE%\.local\bin\uvx.exe` 是否存在，存在就直接用全路径（后续步骤本来就要用全路径，不受影响）。

## 步骤二：配置 PyPI 国内镜像（uvx 拉包加速）

用 PowerShell 写进 Windows 用户级环境变量（.NET 写法，避免 git-bash 展开 `$`）：

```powershell
[Environment]::SetEnvironmentVariable("UV_DEFAULT_INDEX", "https://pypi.tuna.tsinghua.edu.cn/simple", "User")
```

> 不需要镜像（海外机器）就跳过这步。

## 步骤三：预拉包验证（一次性，强烈建议）

先手动跑一次，让 uvx 把 windows-mcp 及依赖全部下载到本地缓存：

```shell
uvx windows-mcp --help
```

看到 `Usage: windows-mcp [OPTIONS] COMMAND [ARGS]...` 即成功。这一步把网络问题提前暴露在「可控的命令行」里，而不是藏在 MCP 客户端连接超时里。之后 MCP 每次启动都走本地缓存，秒起。

## 步骤四：注册到各 CLI

> **偷懒方式**：直接跑本 skill 自带脚本 `bash scripts/register-all.sh`（自动探测 uvx 路径、三件套全注册、支持 `--mirror` 预配镜像）。下面是手动方式，适合只想注册其中一两个 CLI。

以下命令中把 `C:\Users\<user>\.local\bin\uvx.exe` 换成步骤一探测到的实际路径（可用 `where uvx` / `which uvx` 查）。

### CodeBuddy

```shell
codebuddy mcp add --scope user --transport stdio windows-mcp -- "C:\Users\<user>\.local\bin\uvx.exe" windows-mcp serve
```

> 注意：`codebuddy mcp add` 在**另一个 CodeBuddy 会话运行中**可能报 `EADDRINUSE`（端口被当前会话占用）。遇到就直接编辑配置文件 `~/.codebuddy/.mcp.json`：

```json
{
  "mcpServers": {
    "windows-mcp": {
      "type": "stdio",
      "command": "C:\\Users\\<user>\\.local\\bin\\uvx.exe",
      "args": ["windows-mcp", "serve"]
    }
  }
}
```

### Claude Code

```shell
claude mcp add --transport stdio windows-mcp -- "C:\Users\<user>\.local\bin\uvx.exe" windows-mcp serve
```

（Claude Code 配置在 `~/.claude.json` 的 `mcpServers`，也可直接编辑。）

### Codex CLI

Codex 用 TOML 配置，编辑 `~/.codex/config.toml` 追加：

```toml
[mcp_servers.windows-mcp]
command = 'C:\Users\<user>\.local\bin\uvx.exe'
args = ["windows-mcp", "serve"]
startup_timeout_sec = 120
```

> `startup_timeout_sec` 建议加大：首次启动若恰好碰到 uvx 补拉依赖更新，默认超时可能不够。

## 步骤五：验证

1. 重启对应 CLI（MCP 配置只在进程启动时加载，会话中途写配置不生效，`/clear` 也没用）。
2. 会话内输入 `/mcp`（codebuddy/claude）确认 `windows-mcp` 显示 connected。
3. 让 agent 截一张屏测试。

---

## 实战坑位（待补）

> 后续使用中踩到的坑往这里追加。已知线索：

- **USER_CONTROL 等待**：检测到用户正在操作键鼠时，工具调用会返回 `USER_CONTROL` 状态并延迟约 10 秒，属正常安全机制，等一下重试即可。
- **坐标缩放**：截屏返回的图像可能被降采样，文本里会给出 `Coordinate Scale`（如 1.666667）。图像上的像素坐标 × 缩放比 = 实际屏幕坐标，传给 Click/Move 前必须换算。
- **窗口枚举可能为空**：纯截屏正常，但 `Opened Windows` 可能误报 "No windows found"，需要窗口列表时改用 Snapshot。

## 参考来源

- Windows-MCP 仓库：https://github.com/CursorTouch/Windows-MCP
- uv 安装文档：https://docs.astral.sh/uv/getting-started/installation/
- PyPI 镜像（清华 TUNA）：https://pypi.tuna.tsinghua.edu.cn/simple
