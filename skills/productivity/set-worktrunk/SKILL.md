---
name: set-worktrunk
description: "安装并配置 worktrunk（git worktree 管理 CLI，为并行 AI agent 工作流设计）。覆盖 Windows 本机安装全链路：winget 安装、PATH 验证、shell 集成（bash/powershell）、Windows Terminal wt.exe 撞名提醒（本机用 git-wt）、CoW 构建缓存不可用说明。装完即结束；日常 worktree 操作归 worktree skill。触发词：装 worktrunk / git-wt 找不到 / wt switch 不存在。"
---

# Set Worktrunk（一次性环境设置）

安装并配置 [worktrunk](https://worktrunk.dev)（Rust CLI，`git-wt` 命令），让 `worktree` skill 可以使用它做并行 agent 工作流。本技能只管**装好、能用**，不教日常操作。

## 安装步骤

### 1. winget 安装

```bash
winget install --id max-sixty.worktrunk --accept-source-agreements --accept-package-agreements --silent
```

winget 会自动把包目录加入用户 PATH（注册表），并注册 `wt` / `git-wt` 两个别名。

### 2. PATH 验证

winget 报「installed」后，**新开的 shell 才有新 PATH**。验证：

```bash
git-wt --version
```

找不到命令时（当前会话 PATH 陈旧是常态）：

- 快速解锁当前会话：把包目录临时加进 PATH——
  `export PATH="$LOCALAPPDATA/Microsoft/WinGet/Packages/max-sixty.worktrunk_Microsoft.Winget.Source_8wekyb3d8bbwe:$PATH"`（bash；路径以实际为准，`where git-wt` 或查注册表确认）
- 永久生效：重开终端即可；用户注册表 PATH 已由 winget 写入，无需手工改。

### 3. shell 集成（自动 cd + 补全）

```bash
echo y | git-wt config shell install
```

（交互式确认，管道 `echo y` 免输入；只装检测到的 shell。）

- bash：写入 `~/.bashrc` 一行 `eval "$(command git-wt config shell init bash)"`，**重开 shell 生效**。作用：`git-wt switch` 后自动 cd、交互式选择器。
- PowerShell：本机无 profile 文件时会跳过，属正常；不为此新建 profile。

### 4. 撞名提醒（Windows 特有）

- Windows Terminal 自带 `wt.exe` 优先于 worktrunk 的 `wt`——**本机一律用 `git-wt`** 调用，别用 `wt`。
- `worktree` skill 默认原生命令流程；装好后其「加速通道」一节可用 `git-wt`。

### 5. 已知缩水项（Windows）

- **写时复制构建缓存不可用**：worktrunk 的多 worktree 共享 `target/`、`node_modules/` 依赖 CoW 文件系统（APFS/btrfs/XFS），NTFS 不支持。10 个 worktree 各自全量构建，Rust/前端大仓库会占磁盘——worktree 数量适度。
- 其余功能（switch/list/merge/remove/hooks/LLM commit msg）在 Windows 完整可用。

## 验证收尾

在任意 git 仓库跑一次：

```bash
git-wt list
```

出表格（Branch/Status/Path 列）即安装完成。交给 `worktree` skill 接管日常使用。

## 卸载

```bash
winget uninstall max-sixty.worktrunk
```

残留：`~/.bashrc` 里的 eval 行需手工删除。
