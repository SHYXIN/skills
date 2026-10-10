---
name: setup-opencli
description: 在一台新机器上配置 OpenCLI——让 AI agent 通过 Chrome 扩展桥接操控用户日常 Chrome（带登录态）。覆盖前置检查、npm 安装 CLI、引导安装 Chrome 扩展、opencli doctor 验证、冒烟测试与常见排障（扩展 Reconnecting、daemon 未启动等）。用户手动调用（/setup-opencli）。
---

# OpenCLI 浏览器桥接配置

让 agent 能操控用户**日常使用的真实 Chrome**（带全部登录态），走的是「扩展桥接」路线：Chrome 扩展 + 本地 daemon + `opencli` CLI。

**组件关系**（前三者缺一不可）：

| 组件 | 角色 | 本技能是否安装 |
|------|------|--------------|
| `opencli` CLI | 命令入口，daemon 按需自启 | 是（npm） |
| Chrome 扩展 | 跑在用户 Chrome 里，桥接页面操作 | 引导用户手动装 |
| opencli 技能套件（5 个） | agent 的使用说明书 | 否，`npx skills@latest add jackwener/opencli -y -g -a <agents>` 安装 |

**opencli 技能套件**（成套设计、互相引用，建议全量安装）：

| 技能 | 定位 |
|------|------|
| `opencli-usage` | 入口地图：opencli 能做什么、怎么发现 adapter、该加载哪个技能 |
| `opencli-browser` | 核心驾驶：navigate / click / type / fill / extract / network 等页面操作 |
| `smart-search` | 搜索路由：把查询路由到最佳 opencli 数据源（100+ 站点 adapter） |
| `opencli-autofix` | 站点改版导致命令失败时，自动诊断并修复 adapter |
| `opencli-adapter-author` | 给新站点编写 adapter（recon → 解码 → verify 全流程） |

上游项目：<https://github.com/jackwener/opencli>

---

## Step 1 —— 探测现状（幂等）

依次检查三项，跳过已完成项：

```bash
opencli --version        # CLI 是否已装（>= 1.8.x）
node --version           # 是否 >= 20.18.1（npm 安装要求）
```

Chrome 扩展是否已装：直接跑 Step 4 的 `opencli doctor`，若报 Extension 未连接则视为未装。

三种情况：

- **CLI 已装且 doctor 全绿** → 无需配置，可直接冒烟测试（Step 5）确认
- **部分缺失** → 从对应 Step 继续
- **全新机器** → 从 Step 2 开始

`GREEN:` 三项现状已知。

---

## Step 2 —— 安装 CLI

```bash
npm install -g @jackwener/opencli
opencli --version
```

`GREEN:` `opencli --version` 输出 1.8.x 及以上。

若 Node 版本低于 20.18.1，先用 nvm 升级 Node，再执行本步。

---

## Step 3 —— 安装 Chrome 扩展（引导用户手动操作）

扩展无法命令行静默安装，二选一：

**方式 A — Chrome Web Store（推荐）：**
让用户在 Chrome 里打开 <https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk> 点击安装。

**方式 B — 手动加载（离线/商店不可用）：**
1. 从 <https://github.com/jackwener/opencli/releases> 下载最新 `opencli-extension-v{version}.zip`
2. 解压，打开 `chrome://extensions`，开启右上角「开发者模式」
3. 点「加载已解压的扩展程序」，选解压后的文件夹

`GREEN:` 用户确认扩展已出现在 Chrome 扩展列表中。

---

## Step 4 —— doctor 验证

```bash
opencli doctor
```

期望输出：`[OK] Daemon: running`、`[OK] Extension: connected`、`[OK] Connectivity: connected`、`Everything looks good!`

`GREEN:` doctor 全绿。

---

## Step 5 —— 冒烟测试

```bash
opencli browser smoke-test open "https://example.com"
opencli browser smoke-test close
```

`GREEN:` `open` 返回含 `"page": "<targetId>"` 的 JSON，`close` 输出 tab lease released。让用户确认 Chrome 里闪现过 example.com 页面。

---

## 排障

| 症状 | 原因与处理 |
|------|-----------|
| 扩展弹窗一直 Reconnecting | CLI/daemon 未装或未启动 → 先完成 Step 2，再跑 `opencli doctor` |
| doctor 报 Chrome not running | 启动 Chrome 后重试；扩展只在 Chrome 运行时连接 |
| doctor 报 Extension not connected | 扩展未装（回 Step 3）或刚装完未刷新 → 重开 Chrome 扩展弹窗 |
| debug port 被拦截 | 1Password 等安全类扩展可能拦截调试端口，按 doctor 提示临时禁用 |
| 多 Profile 混乱 | `opencli profile list` 查看，`opencli profile rename/use` 指定默认 |
| 命令超时 | `OPENCLI_BROWSER_CONNECT_TIMEOUT` / `OPENCLI_BROWSER_COMMAND_TIMEOUT` 环境变量调大（默认 45s / 60s） |

---

## 完成后

告诉用户：直接用自然语言说「帮我看看 B 站热门」「把我开着的这个页面提取成文本」即可；操作已开登录页时 agent 会用 `bind` 模式，不接管用户标签页生命周期。
