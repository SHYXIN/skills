# npx skills 使用说明

[`npx skills`](https://github.com/vercel-labs/skills) 是开放 Agent Skills 生态的官方 CLI，用来**安装、使用、更新、卸载、搜索、创建**各类 agent 技能，无需手动克隆仓库、复制文件。本仓库（`SHYXIN/skills`）的技能即通过它分发。

> 国内用户（免翻墙）请改用 [`cn-skills-cli`](https://github.com/SHYXIN/cn-skills-cli)，从 Gitee 镜像拉取，用法见仓库 README 的「国内安装」。本文档面向可直接访问 GitHub 的环境。

全文示例均基于本仓库 `SHYXIN/skills`，默认装到 `codebuddy claude-code codex`（全局）。把 `SHYXIN/skills` 换成任意 `owner/repo` 即可用于其他技能集。

## 命令总览

| 命令 | 说明 |
| --- | --- |
| `npx skills add <source>` | 安装技能（核心命令） |
| `npx skills use <source>` | 不安装即临时使用一个技能 |
| `npx skills list` | 列出已安装技能（别名 `ls`） |
| `npx skills find [query]` | 交互式或按关键词搜索技能 |
| `npx skills update [skills]` | 更新已安装技能到最新版本 |
| `npx skills remove [skills]` | 从 agent 中移除已安装技能（别名 `rm`） |
| `npx skills init [name]` | 新建一个 `SKILL.md` 模板 |

## 快速开始

```bash
# 安装本仓库全部技能（自动检测本机 agent，或装到默认 agent）
npx skills@latest add SHYXIN/skills

# 推荐：全局安装到指定 agent，跳过确认
npx skills@latest add SHYXIN/skills -y -g -a codebuddy claude-code codex

# 同时安装社区推荐搭配 mattpocock/skills
npx skills@latest add mattpocock/skills -y -g -a codebuddy claude-code codex
```

安装后，在对应 agent（CodeBuddy / Claude Code / Codex 等）中即可直接调用本仓库的技能，例如 `/socratic-tutor`、`/grill-one`。

## 安装 add

`add` 是最常用的命令，把一个来源里的技能安装到你的 agent。

```bash
# 安装全部技能
npx skills add SHYXIN/skills

# 只安装某个技能
npx skills add SHYXIN/skills --skill socratic-tutor

# 全局 + 指定 agent + 跳过确认
npx skills add mattpocock/skills -g -a codebuddy -y

# 也支持完整 URL
npx skills add https://github.com/SHYXIN/skills
```

### 来源格式（Source Formats）

`add` 的 `<source>` 支持多种写法，下面是结合本仓库的示例：

```bash
# 1) GitHub shorthand（owner/repo）
npx skills add SHYXIN/skills

# 2) 完整 GitHub URL
npx skills add https://github.com/SHYXIN/skills

# 3) 仓库内某个技能的直接路径（tree 链接）
npx skills add https://github.com/SHYXIN/skills/tree/main/skills/productivity/socratic-tutor

# 4) GitLab URL
npx skills add https://gitlab.com/org/repo

# 5) 任意 git URL
npx skills add git@github.com:SHYXIN/skills.git

# 6) 本地路径（克隆到本地后用，详见文末「本地克隆后安装」）
npx skills add ./skills

# 7) 直链下载（单个 SKILL.md 或 .zip/.tar/.tar.gz/.tgz，无需扩展名）
npx skills add https://example.com/download/my-skill
```

直链下载默认限制：下载 ≤ 10 MiB，解压内容 ≤ 25 MiB，归档 ≤ 1000 个文件。信任来源时可用 `SKILLS_DOWNLOAD_MAX_BYTES` / `SKILLS_EXTRACT_MAX_BYTES` / `SKILLS_EXTRACT_MAX_FILES` 调整。

### 私有仓库

公开仓库与私有仓库用**相同的命令**。CLI 会复用你已为该仓库 URL 配置好的认证：

```bash
# GitHub shorthand 或 HTTPS（依次尝试：Git 凭据 → GitHub CLI → SSH 回退）
npx skills add acme/private-skills

# SSH（GitHub / GitLab / 其他 Git 主机）
npx skills add git@github.com:acme/private-skills.git
npx skills add ssh://git@git.example.com/acme/private-skills.git

# HTTPS（使用已配置的 Git credential helper）
npx skills add https://git.example.com/acme/private-skills.git
```

- GitHub HTTPS / shorthand：先走普通 Git 凭据；失败且已登录 GitHub CLI 时尝试 `gh repo clone`，再回退 SSH。不会执行 `gh auth token`，也不会把 GitHub CLI 凭据拷进 Node 进程。
- GitHub tree 查询：先匿名 API，再显式环境变量 token，再 `gh api`。GitHub CLI 只返回 API 响应，凭据不会进入 `skills` 进程。
- `GITHUB_TOKEN` 或 `GH_TOKEN` 可显式提供，用于私有仓库下载与更新检查；当 Git / GitHub CLI / SSH 已配置时安装可不填。

### 选项（Options）

| 选项 | 说明 |
| --- | --- |
| `-g, --global` | 安装到用户目录（跨项目可用），而非项目目录 |
| `-a, --agent <agents...>` | 指定目标 agent（如 `claude-code`、`codex`），见下方「支持范围」 |
| `-s, --skill <skills...>` | 按名称安装指定技能（用 `'*'` 表示全部） |
| `-l, --list` | 仅列出仓库可用技能，不安装 |
| `--copy` | 复制文件而非软链到 agent 目录 |
| `-y, --yes` | 跳过所有确认提示 |
| `--all` | 安装全部技能到全部 agent，无需确认 |

更多示例：

```bash
# 列出仓库里的技能
npx skills add SHYXIN/skills --list

# 安装多个指定技能（名字含空格需加引号）
npx skills add SHYXIN/skills --skill socratic-tutor --skill "Convex Best Practices"

# 装到多个指定 agent
npx skills add SHYXIN/skills -a claude-code -a opencode

# 非交互安装（适合 CI/CD）
npx skills add SHYXIN/skills --skill socratic-tutor -g -a codebuddy -y

# 安装全部技能到全部 agent
npx skills add SHYXIN/skills --all

# 安装全部技能到指定 agent
npx skills add SHYXIN/skills --skill '*' -a claude-code
```

## 不安装即用 use

`skills use` 解析来源的方式与 `add` 相同，但只把所选技能写入临时目录，默认**只把生成的提示打印到 stdout**；加 `--agent` 则会用该提示启动对应 agent。

```bash
# 生成一个技能的提示并管道给 agent
npx skills use SHYXIN/skills@socratic-tutor | claude

# 指定技能 + 指定 agent，交互式启动
npx skills use SHYXIN/skills --skill socratic-tutor --agent codebuddy
```

## 查看已安装 list

```bash
# 列出全部已安装技能（项目 + 全局）
npx skills list

# 只看全局技能
npx skills ls -g

# 按 agent 过滤
npx skills ls -a codebuddy -a claude-code
```

## 搜索 find

```bash
# 交互式搜索（fzf 风格）
npx skills find

# 按关键词搜索
npx skills find typescript

# 跨某作者/组织下的所有仓库搜索
npx skills find react --owner mattpocock
```

## 更新 update

```bash
# 更新全部（交互选择范围）
npx skills update

# 只更新某个技能
npx skills update socratic-tutor

# 同时更新多个
npx skills update socratic-tutor idea-alchemist interview-coach

# 只更新全局 / 项目范围
npx skills update -g
npx skills update -p

# 非交互（自动判定范围：在项目中→项目，否则全局）
npx skills update -y
```

| 选项 | 说明 |
| --- | --- |
| `-g, --global` | 只更新全局技能 |
| `-p, --project` | 只更新项目技能 |
| `-y, --yes` | 跳过范围确认（自动判定） |
| `[skills...]` | 按名称更新指定技能，而非全部 |

## 卸载 remove

```bash
# 交互式选择已安装技能卸载
npx skills remove

# 按名称卸载某个技能
npx skills remove socratic-tutor

# 卸载多个
npx skills remove frontend-design web-design-guidelines

# 从全局范围卸载
npx skills remove --global socratic-tutor

# 只从指定 agent 卸载
npx skills remove --agent codebuddy claude-code socratic-tutor

# 全部卸载（无需确认）
npx skills remove --all

# 从某 agent 卸载全部技能
npx skills remove --skill '*' -a claude-code

# 从所有 agent 卸载某技能
npx skills remove socratic-tutor --agent '*'

# rm 是 remove 的别名
npx skills rm socratic-tutor
```

| 选项 | 说明 |
| --- | --- |
| `-g, --global` | 从全局（`~/`）而非项目卸载 |
| `-a, --agent` | 从指定 agent 卸载（用 `'*'` 表示全部） |
| `-s, --skill` | 指定要卸载的技能（用 `'*'` 表示全部） |
| `-y, --yes` | 跳过确认提示 |
| `--all` | 等价于 `--skill '*' --agent '*' -y` |

## 初始化新技能 init

```bash
# 在当前目录创建 SKILL.md
npx skills init

# 在子目录创建新技能
npx skills init my-skill
```

生成的 `SKILL.md` 带 YAML frontmatter（`name` + `description`），是编写自定义技能的起点。

## 本地克隆后安装

如果你已经把本仓库克隆到本地（例如想改完再装、或离线环境），可以用**本地路径**作为来源：

```bash
# 1) 克隆仓库
git clone https://github.com/SHYXIN/skills.git
cd skills

# 2) 直接用本地路径安装（无需再走网络）
npx skills@latest add ./skills -y -g -a codebuddy claude-code codex

# 只装某个本地技能
npx skills add ./skills --skill socratic-tutor -g -a codebuddy

# 装到项目目录（不写全局，随仓库提交、团队共享）
npx skills add ./skills --skill socratic-tutor -a codebuddy
```

> 本地路径来源同样支持 `-g` / `-a` / `-s` / `--copy` / `-y` 等全部选项。注意 `<source>` 指向的是**含 `skills/` 目录的仓库根**，CLI 会自动发现其中的 `SKILL.md`。

## 安装范围与方式

### 安装范围（Scope）

| 范围 | 标志 | 位置 | 适用场景 |
| --- | --- | --- | --- |
| **项目** | （默认） | `./<agent>/skills/` | 随项目提交，团队共享 |
| **全局** | `-g` | `~/<agent>/skills/` | 跨所有项目可用 |

### 安装方式（Method）

交互安装时可选：

| 方式 | 说明 |
| --- | --- |
| **软链（推荐）** | 从各 agent 软链到同一份权威副本，单一来源、易于更新 |
| **复制** | 为各 agent 创建独立副本，软链不支持时使用（`--copy`） |

## 环境变量

| 变量 | 说明 |
| --- | --- |
| `INSTALL_INTERNAL_SKILLS` | 设为 `1` 或 `true` 才显示/安装标记为 `internal: true` 的内部技能 |
| `DISABLE_TELEMETRY` | 禁用匿名使用统计 |
| `DO_NOT_TRACK` | 另一种禁用统计的方式 |
| `GITHUB_TOKEN` | 可选，显式提供 GitHub API 认证 token |
| `GH_TOKEN` | 同上，作为 `GITHUB_TOKEN` 的回退 |

```bash
# 安装内部技能
INSTALL_INTERNAL_SKILLS=1 npx skills add SHYXIN/skills --list
```

## 相关链接

- 完整命令与巨表（Supported Agents 全表、兼容性矩阵、Troubleshooting、Telemetry）：<https://github.com/vercel-labs/skills#readme>
- Agent Skills 规范：<https://agentskills.io>
- 技能发现目录：<https://skills.sh>
- 本仓库国内免翻墙安装（cn-skills-cli）：见 `README.md` 的「国内安装」
- 本仓库技能清单：见 `README.md` 的「技能列表」
