---
name: setup-last30days
description: 在一台新机器上配置 last30days 研究技能（mvanhorn/last30days-skill，话题深挖：过去 30 天 Reddit/X/HN/YouTube/Polymarket 社区讨论，ai-daily-brief 的深挖搭档）。覆盖 Python 3.12+ 解析（LAST30DAYS_PYTHON 用户级环境变量，含 pyenv 版本过旧/shim 损坏等坑）、~/.config/last30days/.env 最小配置（SETUP_COMPLETE=true 跳过 setup wizard）、--diagnose 免费源健康检查与 --quick 冒烟、国内网络下 Reddit/网页搜索不可用的替代策略。手动调用（/setup-last30days）。
---

# last30days 研究技能环境配置

[last30days](https://github.com/mvanhorn/last30days-skill) 让 agent 研究任意话题在过去 30 天的真实社区讨论（Reddit / X / YouTube / HN / Polymarket / GitHub），合成带引用的报告。技能本体由 `cn-skills add mvanhorn/last30days-skill` / `npx skills add mvanhorn/last30days-skill` 安装（无 Gitee 镜像），**本技能只管装完后的环境配置**：Python 解释器解析、最小配置、健康检查与冒烟。

与 ai-daily-brief 分工：daily-brief 管每日固定简报（编辑精选 + 趋势榜），last30days 管单话题深挖。

---

## Step 1 —— 探测现状（幂等）

```bash
# 技能本体是否已装（任一 agent 目录里有 SKILL.md 即可）
ls ~/.codebuddy/skills/last30days/SKILL.md 2>/dev/null || ls ~/.claude/skills/last30days/SKILL.md 2>/dev/null

# 解释器与配置现状
echo "PY=${LAST30DAYS_PYTHON:-unset}"
cat ~/.config/last30days/.env 2>/dev/null
```

四种情况：

- **技能在 + PY set + .env 在** → 直接冒烟（Step 4）
- **技能在、PY 或 .env 缺** → 按缺什么跳 Step 2 / Step 3
- **技能不在** → 先装本体（见上），再回本流程
- **全新机器** → 从 Step 2 开始

`GREEN:` 现状已知。

---

## Step 2 —— Python 3.12+ 解析（版本门禁）

last30days v4 引擎硬性要求 **Python 3.12+**，运行前会做版本门禁。解析优先级（照 upstream `references/runtime.md`）：

1. 环境变量 `LAST30DAYS_PYTHON`（显式指定，最高优先）
2. `LOCALAPPDATA/Programs/Python` 与 `Program Files` 下的 `python.exe`
3. `python3.14` / `python3.13` / `python3.12` / `python3` / `python` 命令
4. `uv python find '>=3.12'`（有 uv 时自动装托管 CPython 3.12）

验证候选解释器过门禁：

```bash
"$candidate" -I -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' && echo PASS
```

找到后**持久化为用户级环境变量**（Windows，所有新进程可见；macOS/Linux 写 shell rc）：

```powershell
[Environment]::SetEnvironmentVariable('LAST30DAYS_PYTHON', 'C:\解释器完整路径\python.exe', 'User')
```

Git Bash 另加 `~/.bashrc`：`export LAST30DAYS_PYTHON="/c/解释器完整路径/python.exe"`。

`GREEN:` 新终端里 `"$LAST30DAYS_PYTHON" --version` ≥ 3.12。

### 已知坑（2026-11-18 实测）

| 坑 | 现象 | 处理 |
|---|---|---|
| pyenv 全局版本过旧 | `python`/`python3` 都解析到 3.10，门禁报 `requires Python 3.12+` | 不要动 pyenv 全局版本（影响别的项目）；找机器上真实的 3.12+ 解释器写进 `LAST30DAYS_PYTHON` |
| pyenv 版本 shim 损坏 | `python3.13 --version` 报 `not recognized`（shim 文件在但执行失败） | 绕过 shim，直接用 `~/.pyenv/pyenv-win/versions/<ver>/python.exe` 完整路径 |
| 残缺的 Python 安装目录 | `LOCALAPPDATA/Programs/Python/Python312/` 存在但没有 python.exe | preflight 的 find 会跳过（找不到 python.exe），继续找下一个候选 |

---

## Step 3 —— 最小配置（跳过 setup wizard）

```bash
mkdir -p ~/.config/last30days
printf 'SETUP_COMPLETE=true\n' > ~/.config/last30days/.env
```

`SETUP_COMPLETE=true` 跳过引擎的 first-run setup wizard，全部走免费源。**不把任何 API key 写进仓库文件**；将来要解锁更多源时再往这个 .env 加（可选：`SCRAPECREATORS_API_KEY` 解锁 X/TikTok/Instagram，1 万次免费；`X_BEARER_TOKEN` 解锁官方 X API；HN / Polymarket / GitHub / YouTube / Reddit 永远免 key）。

`GREEN:` `cat ~/.config/last30days/.env` 输出 `SETUP_COMPLETE=true`。

---

## Step 4 —— 健康检查 + 冒烟

```bash
"$LAST30DAYS_PYTHON" <技能目录>/scripts/last30days.py --diagnose
```

期望 `available_sources` 至少含 `hackernews`、`polymarket`、`github`、`grounding`（`youtube` 需 yt-dlp，`reddit` 视网络而定）。

冒烟（换成当下真实话题）：

```bash
"$LAST30DAYS_PYTHON" <技能目录>/scripts/last30days.py "<话题>" --quick --emit compact
```

`GREEN:` 输出 canonical report（HN 命中也算成功，哪怕只有 1 条）。

---

## 国内网络现实（重要预期管理）

2026-11-18 实测：**Reddit 直连超时；走本机代理（Clash 系出口）也是 403（出口 IP 被 Reddit 拉黑）**。keyless 网页搜索（brave / ddg / startpage 三个 HTML 引擎）直连与代理均被反爬墙拦（DDG 返回 202 challenge 页）。即引擎的网页层在国内网络环境下基本指望不上。

替代策略：SKILL.md 的 allowed-tools 本就含 WebSearch——跑 last30days 时用**宿主的 WebSearch/WebFetch 补网页层证据**，引擎负责 HN / Polymarket / GitHub 等可达源。这不是缺陷规避，是该网络环境下的正常用法。

---

## 排障

| 症状 | 原因与处理 |
|------|-----------|
| `ERROR: last30days v4 requires Python 3.12+` | 没设 `LAST30DAYS_PYTHON` 且所有候选 < 3.12 → 按 Step 2 找/装解释器 |
| `LAST30DAYS_PYTHON must point to Python 3.12+` | 变量指向了旧解释器 → 重新验证并改写 |
| 报告里 `Reddit unreachable: no path served; search blocked` | 首次 403 把健康缓存写成了 blocked → 删 `~/.config/last30days/reddit-health.json` 后重跑一次 |
| `brave/ddg/startpage throttled` | keyless 网页搜索被反爬墙拦（国内常态）→ 宿主 WebSearch 补证据 |
| 首跑弹出 setup wizard 引导 | `.env` 缺 `SETUP_COMPLETE=true` → 补 Step 3 |
| X/TikTok/Instagram 源缺失 | 需要 ScrapeCreators key → 用户自注册后写进 `~/.config/last30days/.env` |

---

## 完成后

告诉用户：日常直接说 `/last30days <话题>` 深挖（报告落盘 `~/Documents/Last30Days`）；每日固定简报继续走 `/ai-daily-brief`。本技能只在换机器时才需要。
