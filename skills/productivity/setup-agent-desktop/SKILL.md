---
name: setup-agent-desktop
description: "在新 Windows 电脑上安装并配置 agent-desktop（Vercel Labs 跨平台桌面 GUI 自动化 CLI：无障碍树快照 + headless 语义操作 + @ref 寻址，Rust 实现、npm 分发）。覆盖 npm 安装与 postinstall 修复、status 验证、内置版本匹配指南加载、MCP 注册探针（正式版可能无 mcp 子命令）、记事本无头冒烟测试与排障。首次配 agent-desktop、或遇到 '走 Node launcher' / SNAPSHOT_NOT_FOUND / headless type 被 POLICY_DENIED / 快照带出隐私内容时使用。手动调用（/setup-agent-desktop）。"
---

# 安装 agent-desktop（新机器配置指南）

## 这个 skill 解决什么

agent-desktop（npm 包 `agent-desktop`）是 Vercel Labs 出的桌面 computer-use CLI：读 OS 无障碍树（Windows 走 UIA）让 agent 看见并操作桌面 GUI，默认 headless 语义操作，不抢焦点、不动鼠标。**Rust 实现、npm 分发**——包里是各平台预编译原生二进制 + 一个 JS 启动器，npm 只是渠道。

新机器上配它的坑不在 CLI 本身，而在五件事：

1. **postinstall 链接只对 PowerShell/cmd 生效**：npm 装好后 `agent-desktop.cmd` 垫片已被重写直指 .exe，但 Git Bash 优先命中不带扩展名的 JS wrapper，每次调用多约 125ms 并打印一次 launcher 警告。
2. **README（main 分支）超前于正式发布**：README 写了 `agent-desktop mcp`（MCP server 模式），但 npm 最新正式版可能还没有这个子命令（2026-11 实测 1.1.0 即无）。照着 README 注册 MCP 会得到一个启动即失败的坏 server。
3. **快照活不久**：`find` 产出的 ref 稍后用就 `SNAPSHOT_NOT_FOUND`；拍完照要立即行动，失败重拍即可（`retry: safe`）。
4. **Windows 上无头 `type` 会被拒**：`type` 是 SendInput 键盘合成，headless 返回 `POLICY_DENIED`；无头写入用 `set-value`（UIA ValuePattern，语义化且带读回验证）。
5. **快照会带出隐私内容**：`snapshot`/`get` 返回元素 value——冒烟只用新标签/空文档；能只取 ref 就不全量快照，输出严禁进日志/仓库/提交。

## 总原则

- **装完先 `status`**：一条命令同时验证安装、平台、权限（Windows 上 accessibility 默认 granted，没有授权弹窗）。
- **注册 MCP 前先探针**：`agent-desktop mcp --help` 能识别再注册，unrecognized 就跳过等发版。
- **ref 必须带快照 id**（`@s8f3k2p9:e1`）；PowerShell 里每个 ref 加单引号（裸 `@token` 是 splatting 操作符，参数会被悄悄吃掉），bash/cmd 不用。
- **无头优先，别用 `--headed` 救无头失败**；headed 只在用户明确允许物理输入时用。
- **内置指南比网上 README 可靠**：`agent-desktop skills get desktop` / `skills get platform` 是二进制里版本匹配的一手文档（README main 可能超前，见坑 2）。

---

## Step 1 —— 探测现状（幂等）

```bash
agent-desktop --version 2>/dev/null && agent-desktop status
```

三种情况：

- **已装且 `"ok":true`** → 跳 Step 4（冒烟）
- **已装但有 launcher 警告** → Step 3 修复
- **未装** → Step 2

`GREEN:` 现状已知。

---

## Step 2 —— npm 安装

```bash
npm install -g agent-desktop
```

装完立刻验证（**Git Bash 里留意有没有 launcher 警告**）：

```bash
agent-desktop status
```

看到 `this command runs through the Node launcher...` 说明 postinstall 的链接步骤没生效（每版本只警告一次）。原生二进制已随包带上，手动补跑即可，PowerShell/cmd 用户本就不受影响：

```bash
node "$(npm root -g)/agent-desktop/scripts/postinstall.js"
```

`GREEN:` `agent-desktop status` 返回 `"ok":true`，`platform` 为本机平台，`permissions.accessibility.state` 为 `granted`。

---

## Step 3 —— 加载内置指南（版本匹配的一手文档）

```bash
agent-desktop skills get desktop     # 通用循环：refs、验证、重试、headless 纪律
agent-desktop skills get platform    # 当前 OS 的差异（Windows：PowerShell 引用规则、headed-only 命令清单、最小化窗口不可驱动等）
```

按需再取参考（清单在 desktop 指南末尾表格里）：

```bash
agent-desktop skills get desktop commands-interaction
agent-desktop skills get agent-desktop-windows references/troubleshooting.md
```

`GREEN:` 两份指南内容已读，Windows 特差异点已知。

---

## Step 4 —— MCP 注册（先探针，正式版可能不支持）

```bash
agent-desktop mcp --help
```

- **能识别**（打印 mcp 的帮助）→ 在 `~/.codebuddy/.mcp.json` 注册。**命令用 .exe 全路径**（规避 PATH 分裂）：

  ```json
  "agent-desktop": {
    "type": "stdio",
    "command": "C:\\nvm4w\\nodejs\\node_modules\\agent-desktop\\bin\\agent-desktop-win32-x64.exe",
    "args": ["mcp"]
  }
  ```

  （路径用 `npm root -g` 定位，nvm 用户走 `C:\\nvm4w\\nodejs\\...` 符号链接，切 node 版本不失配；ARM 机是 `agent-desktop-win32-arm64.exe`。）注册后**重开客户端会话**生效。

- **`unrecognized subcommand 'mcp'`** → 正式版还没发这个功能（README main 超前），**跳过注册**，CLI 照常可用；等 npm 版本带上 mcp 再补注册。

`GREEN:` 探针有结果：要么注册完成，要么明确跳过并记录原因。

---

## Step 5 —— 冒烟测试（记事本无头闭环）

**在全新的空标签里做，别往用户已开着的文档里写。** `launch notepad` 在记事本已运行时会激活旧窗口（Win11 记事本是单实例多标签），先 `list-windows` 看当前开的是什么，快照可能带出隐私内容。

```bash
agent-desktop launch notepad
agent-desktop snapshot --app notepad -i                  # 观察：拿 textfield 的 ref
# 点"添加新标签页"拿到干净的空文档后再继续：
agent-desktop set-value @<snapshot_id>:e1 "smoke test"   # 行动：语义写入（type 无头会被拒）
agent-desktop get @<snapshot_id>:e1 --property text      # 验证：读回一致即成功
```

判定标准：`set-value` 返回 `disposition.delivery: "delivered_verified"`，且 `get` 读回文本与写入一致。

清理：关掉测试标签即可，关闭弹窗选**"不保存"**。测试标签页可留给用户手动关。

`GREEN:` 读回文本一致，闭环成立。

---

## 排障

| 症状 | 原因 | 处理 |
|---|---|---|
| 每次调用多约 125ms + launcher 警告 | Git Bash 命中 JS wrapper（postinstall 只重写了 .cmd/.ps1 垫片） | 手动补跑 `node "$(npm root -g)/agent-desktop/scripts/postinstall.js"`；或在 bash 里直接调 .exe |
| `SNAPSHOT_NOT_FOUND` | ref 所属快照已失效（UI 变化或快照过期） | 重拍 snapshot 用新 ref，原动作可安全重试（`retry: safe`） |
| 无头 `type` 返回 `POLICY_DENIED` | Windows 上 `type` = SendInput 键盘合成，需物理输入 | 改用 `set-value`；用户明确允许时加 `--headed` |
| `mcp` 子命令 unrecognized | 正式版未发 MCP 模式，README main 超前 | 跳过注册等发版；注册前永远先探针 |
| snapshot 树不全/为空 | 窗口最小化（元素全 offscreen）；Chromium/Electron 未 settle | `restore --app <name>` 后重拍；`--timeout-ms` 调大 |
| 快照输出带出敏感内容 | `snapshot`/`get` 返回元素 value | 用 `find --role textfield` 只取 ref；输出严禁进日志/仓库/提交 |
| `press` 到非前台应用失败 closed | press 写前台队列、无按进程定向 | 先 `focus-window`（会抢用户焦点，慎用） |
| 未签名二进制警告 | Windows SmartScreen 对无签名 .exe 的预期行为 | 预期内；GitHub Releases 提供 checksums.txt 与 gh attestation 校验 |
| `press` 某组合键被拒 | alt+f4 / win 系列等 shell 快捷键默认拒绝 | 确认确有必要后加 `--force` |
