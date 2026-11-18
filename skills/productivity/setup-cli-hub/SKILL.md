---
name: setup-cli-hub
description: 在一台新机器上配置 CLI-Anything / CLI-Hub（HKUDS，agent-native CLI 市场：cli-hub 包管理器 + 79 个让 agent 操控真实软件的 CLI + matrix 能力矩阵）。覆盖 hub 安装（pyenv 多版本共存时 Scripts 目录不在 PATH 的坑）、cli-hub-meta-skill 安装（agent 自主发现/安装 CLI）、冒烟验证与三大安装坑（wheel 空包 bug、npm 版本断层、Python 壳≠真依赖）。手动调用（/setup-cli-hub）。
---

# CLI-Anything / CLI-Hub 环境配置

[CLI-Anything](https://github.com/HKUDS/CLI-Anything) 让 agent 通过 CLI 操控真实 GUI 软件（GIMP / Kdenlive / Blender / LibreOffice 等 79 个）。组成两层：

- **`cli-hub`**（pip 包 `cli-anything-hub`）：包管理器，`install/search/list` + `matrix`（能力×提供者矩阵，按需装单项能力）
- **`cli-hub-meta-skill`**：技能本体，装进 agent 目录后 agent 自己会查目录、装 CLI，用户不用记命令

**本技能只管装环境**；日常发现/安装 CLI 由 meta-skill 接管。

---

## Step 1 —— 探测现状（幂等）

```bash
# hub 是否已装、在哪个解释器
command -v cli-hub && cli-hub --version

# pyenv 有哪些版本（hub 要求 Python >=3.10，全局 shim 可能是旧版）
pyenv versions

# meta-skill 是否已装（任一 agent 目录有 SKILL.md 即可）
ls ~/.codebuddy/skills/cli-hub-meta-skill/SKILL.md 2>/dev/null || \
ls ~/.claude/skills/cli-hub-meta-skill/SKILL.md 2>/dev/null || \
ls ~/.agents/skills/cli-hub-meta-skill/SKILL.md 2>/dev/null
```

四种情况：

- **hub 在 + meta-skill 在** → 直接冒烟（Step 4）
- **hub 缺** → Step 2
- **meta-skill 缺** → Step 3
- **全新机器** → 从 Step 2 顺序走

`GREEN:` 现状已知。

---

## Step 2 —— hub 安装（关键：装对解释器 + Scripts 进 PATH）

hub 要求 **Python >=3.10**。pyenv-win 机器上全局 shim 往往停在旧版（本机 3.10.0 shim 可用但**不要**往里装——该版本常被其他工具占用；用 versions 下的新版独立装）：

```bash
# 用 pyenv versions 下的 3.13.3 的 python 直装（不切全局版本）
~/.pyenv/pyenv-win/versions/3.13.3/python.exe -m pip install cli-anything-hub
```

**坑：`cli-hub.exe` 落在该版本的 `Scripts/` 目录，不在 PATH 上。** 两处都加：

1. 用户 PATH（PowerShell）：
   ```powershell
   [Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path','User') + ';C:\Users\WX847\.pyenv\pyenv-win\versions\3.13.3\Scripts', 'User')
   ```
2. 当前 Git Bash 立即可用（`~/.bashrc`）：
   ```bash
   export PATH="$HOME/.pyenv/pyenv-win/versions/3.13.3/Scripts:$PATH"
   ```

`GREEN:` 新开 shell `cli-hub --version` 出版本号（本机 0.4.1）。

---

## Step 3 —— meta-skill 安装

```bash
npx skills add HKUDS/CLI-Anything --skill cli-hub-meta-skill -g -y
```

只装 meta-skill 这一个技能（`--skill` 过滤；不带会试图装仓库全部）。装完真身在 `~/.agents/skills/cli-hub-meta-skill/`，`~/.codebuddy/skills/`、`~/.claude/skills/` 出现软链。国内网络直连 GitHub 可能慢，重试即可。

`GREEN:` `ls ~/.codebuddy/skills/cli-hub-meta-skill/SKILL.md` 存在。

---

## Step 4 —— 冒烟验证

选**零依赖可跑**的 CLI 验证（registry 里推荐 `hacker-feeds-cli` / `cc-switch` / `pm2` / `clibrowser` / `mermaid`，均不拖真实 GUI 软件）：

```bash
cli-hub list                       # 79 个 CLI 目录可见
cli-hub search trending            # 关键词搜索
cli-hub install hacker-feeds-cli   # 装一个
cli-anything-hacker-feeds-cli github trending --json   # GitHub Trending JSON 输出
```

`GREEN:` JSON 有内容即全链路通。

要删干净：`pip uninstall cli-anything-hacker-feeds-cli`（Python 壳）+ `npm uninstall -g hacker-feeds-cli`（Node 层，如有）。

---

## 三大安装坑（按踩中概率排序）

1. **Python 包 wheel 空包 bug（上游）**：部分 `cli-anything-*` 包的仓库根目录缺 `__init__.py`，`find_packages()` 返回 `[]`，PyPI 装出的 wheel 只有 dist-info 没有模块 → `ModuleNotFoundError: No module named 'cli_anything'`。
   **修法**：clone 对应子目录源码，显式 `packages=["cli_anything", "cli_anything.<name>"]`（必要时补 `__init__.py`），`pip install .`
2. **npm 版本断层**：npm registry 上的 Node 层版本可能落后 repo（hacker-feeds-cli：registry 0.4.3 无 `--json`，repo 0.5.0 有但未发布）。需要 JSON 输出时从源码 `npm install --production && npm install -g .`。
3. **Python 壳 ≠ 真依赖**：不少 CLI 是 Python 薄壳 + Node/二进制真身。`cli-hub install` 成功只代表 Python 层就位；跑报错先读该 CLI harness 的 README 确认真实依赖（要不要 npm install、要不要下载外部二进制）。

## matrix 用法（跨多工具的任务才用）

单工具任务直接 `cli-hub install <name>`。任务横跨多个工具（如"做个视频"）走 matrix：

```bash
cli-hub can "transcribe audio"                          # 跨矩阵查能力
cli-hub matrix preflight video-creation --json          # 本机哪些可用（exit 3 = 有缺口）
cli-hub matrix install video-creation --capability text.transcribe   # 只装单项能力，别 bulk-install
```

## 本机事实（2026-11-18）

- hub 0.4.1 装在 pyenv 3.13.3；`cli-hub.exe` 在 `~/.pyenv/pyenv-win/versions/3.13.3/Scripts/`，用户 PATH + `~/.bashrc` 均已加
- meta-skill 已装：真身 `~/.agents/skills/cli-hub-meta-skill/`，软链 codebuddy + claude
- hacker-feeds-cli 曳光弹已跑通：Python 壳 0.4.x + Node 层 0.5.0（源码装）
