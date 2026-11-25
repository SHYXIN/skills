---
name: set-dsh-tui
description: "在本机安装 DSH CLI 并配置 TUI 终端界面的完整流程。覆盖：npm 装 dsh（选型警告：用 rc 别用 alpha）、profile 体系认知（web/headless/tui 各自独立）、credentials 凭据服务机制、自定义模型 patch（dts + tokenhub 双网关实测配置，含 baseURL/模型名大小写/多模态声明三坑）、TUI 插件两条安装路径（A：全局启动器 dsh-tui 自动自举；B：plugin-manager 手动装 + 版本豁免）、win32 自带全权限说明。用户手动调用（/set-dsh-tui）。换新机器或帮别人配 DSH 时用。"
disable-model-invocation: true
---

# Set DSH TUI（DSH 安装 + TUI 配置引导）

把 DSH（DeepSeek Harness）CLI 装到一台 Windows 机器上，配好自定义模型路由和 TUI 终端界面，最终以「`dsh --profile dsh-tui` 打开全屏终端并能正常对话」作为验收。

本 skill 只管**安装、配置、装插件**；DSH 的日常使用、插件生态、SDK/ACP 集成不在范围内。

## 核心认知：profile 体系

DSH 用 profile 隔离不同入口的配置，**每个 profile 是独立的 Cordis 配置树**，互不继承：

| Profile | 用途 | 说明 |
| --- | --- | --- |
| `web` | 浏览器面板 | 最常用的交互入口 |
| `headless` | 命令行单发问答 | `dsh --profile headless "问题"` |
| `dsh-tui` | 全屏终端 UI | TUI 插件自建的 profile（路径 A 自举），本 skill 的目标 |
| `tui` | 全屏终端 UI | 路径 B 手动装插件时用的 profile，与 `dsh-tui`（路径 A 自举）是**两个不同的 profile**，配置互不相通 |
| `sdk` / `sdk-minimal` / `acp` | 程序化集成 | 不在本 skill 范围 |

关键推论：**Web 面板里配好的模型不会自动同步到其他 profile**。每个 profile 的自定义配置都要写进自己的 patch 文件（见 Step 3；web profile 自己的配法见 Step 6）。

每个 profile 的目录结构（`~/.dsh/profiles/<name>/`）：

- `cordis.yml` — 基础配置（首次启动自动生成，一般不动）
- `cordis.patch.yml` — patch 层，用户自定义配置写这里（每项以 `- id:` 定位要覆盖的条目）
- `package.json` — 已装 bundle 清单（plugin-manager 维护）
- `node_modules/` — 实际安装的插件包

## Step 1：安装 dsh CLI

```bash
npm install -g @deepseek-ai/dsh
dsh --version   # 确认版本
```

**版本选型警告（2026-11-25 实测）**：**用 rc 版，避开 alpha 版**。npm 上的 `0.2.2-alpha.2` 包在 node 24 下实测是坏的——web 和 tui 同时报 `agent-preset/invalid: Cannot read properties of undefined (reading 'parent')`（新建会话必崩），同一版本号的源码构建却正常，是发布包自身的问题。装的时候明确指定 rc 版本：

```bash
npm install -g @deepseek-ai/dsh@0.2.2-rc.5   # 或当时的最新 rc
```

## Step 2：理解凭据服务

API 密钥**不写进 profile 配置**，统一存在凭据服务里：

- 文件位置：`~/.dsh/.credentials.yaml`（明文 YAML，勿外传）
- 结构：`refs:` 下按环境变量名存值，如 `DEEPSEEK_API_KEY: sk-xxx`
- 注入机制：**credentials 插件**（`@deepseek-ai/dsh-credentials-local`）启动时读取该文件，把键值注入进程环境变量；模型 provider 再按 `apiKeyEnv` 声明的变量名取值
- 取值优先级：`apiKeyEnv` 声明的变量**先查进程环境**（已设则跳过凭据库），没设才读 `.credentials.yaml`——`/provider` 添加时提示「进程环境已提供同名变量，跳过写入」就是这个语义

填 key 的两种方式：

```bash
# 方式一：Web 面板「设置 → 模型」页填入（写进 .credentials.yaml）
# 方式二：启动前导出环境变量
export DEEPSEEK_API_KEY=sk-xxx
```

首次运行 `dsh --profile web` 打开面板填 key 是最省事的初始化方式——key 会落进凭据服务，所有 profile 共享。

## Step 3：配置自定义模型（patch 模板）

新 profile 的 `cordis.patch.yml` 默认为空，模型回落到内置 `llm-deepseek`（DeepSeek 官方路由，需要 `DEEPSEEK_API_KEY`）——不配就会报 `MISSING_CREDENTIAL: llm-deepseek`。

### 两个 LLM 行，两套 schema，别混

| 行 | 协议 | 底层 | 模型条目的多模态 key |
| --- | --- | --- | --- |
| `llm-deepseek`（provider=deepseek-official） | Anthropic Messages 兼容 | dsh 内置 deepseek 客户端 | `inputModalities:` |
| `llm-pi-ai` | OpenAI 兼容 | 内置 `@earendil-works/pi-ai` 库（行名由此来） | `input:` |

在 pi-ai 的模型条目里写 `inputModalities` 会被 schema **静默丢弃**（不报错），之后贴图就报「当前模型不支持图片」。

### 三条铁律（2026-11-25 实测）

1. **baseURL 不带 `/chat/completions`**——pi-ai 底层用 OpenAI SDK，SDK 自己拼 `/chat/completions`；写全路径会请求 `.../chat/completions/chat/completions` → 404。只写到 `/v1`
2. **模型名按网关实测，别发明**——`/provider` 添加时随手填的模型名（如 `dst`）DTS 上不存在，发消息报 404 或 `no configured model "dst"`。用 key 查 `GET {baseURL}/models` 实测
3. **模型名大小写按网关**——DTS 按账号组定，同一批 key 实测是全小写（`glm-5.3`，大写 `GLM-5.3` 404）；tokenhub 大小写敏感且是大写驼峰（`DeepSeek-V4.1-Flash`）。两网关规则不同，各测各的

### patch 模板（dts + tokenhub 双网关，实测可用）

```yaml
# llm-pi-ai = OpenAI 兼容协议行。dts 是自定义 provider 名
- id: llm-pi-ai
  name: "@deepseek-ai/dsh-llm-pi-ai"
  config:
    providers:
      dts:                            # ← Deepexi DTS 网关
        apiKeyEnv: DTS_API_KEY
        baseURL: https://dts.deepexi.com/v1    # ← 只到 /v1，不带 /chat/completions
        api: openai-completions
        models:                       # ← 名字全小写（按 key 实测；你的账号组可能不同）
          - id: glm-5.3
          - id: glm-5.3-flash
            input: [ "text", "image" ]         # ← pi-ai 行的多模态 key 是 input
          - id: glm-5.4
        retryPolicy:
          mode: normal
          maxRetries: 5
          retryableCodes: [EMPTY_RESPONSE, RATE_LIMIT, SERVER, TIMEOUT, TRANSPORT, STREAM_CLOSED]
      tokenhub:                       # ← tokenhub 计费网关（Anthropic Messages 兼容也通，但走 pi-ai 的 openai-completions 即可用）
        apiKeyEnv: DEEPSEEK_API_KEY
        baseURL: https://tokenhub.deepexios.cn/gateway/api/v1
        api: openai-completions
        models:                       # ← 大写驼峰（按 tokenhub /v1/models 实测）
          - id: DeepSeek-V4.1-Flash
            input: [ "text", "image" ]
          - id: DeepSeek-V4-Pro
          - id: GLM-5.3
          - id: GLM-5.3-Flash
            input: [ "text", "image" ]
          - id: Qwen-3.8-Max
            input: [ "text", "image" ]
        retryPolicy:
          mode: normal
          maxRetries: 5
          retryableCodes: [EMPTY_RESPONSE, RATE_LIMIT, SERVER, TIMEOUT, TRANSPORT, STREAM_CLOSED]
- id: agent-default-model
  name: "@deepseek-ai/dsh-agent-default-model"
  config:
    provider: dts                     # ← 默认路由；换默认模型改这两行
    model: glm-5.3
```

写完验证：

```bash
dsh --profile <name> --dump-config | grep -A4 "agent-default-model"
# 应看到 provider: dts, model: glm-5.3
```

### 权限（全访问）

**dsh-tui profile 不用写**：TUI 插件自带的 patch 在 Windows 上已硬编码 `sandbox-policy: danger-full-access` + `approval: never`（Windows 没有沙箱后端，终端即信任模型），装完即全权限、不弹审批；非 Windows 回落 `workspace-write` + ask。环境变量 `DSH_PERMISSION_MODE` 和记忆的 `/permission` 选择可覆盖。

**web / headless profile 要全放开才需手工写**：

```yaml
- id: sandbox-policy
  name: "@deepseek-ai/dsh-sandbox-policy"
  config:
    mode: danger-full-access
    workspaceRoot: !!js process.cwd()
- id: permission
  config:
    defaultPreset: danger-full-access
```

**headless profile 额外一步**：headless 模板默认**禁用** credentials 插件（`disabled: true`），导致读不到 `.credentials.yaml` 里的 key，报 `MISSING_CREDENTIAL` 即使 key 已存。在 patch 里加一段重新启用：

```yaml
- id: credentials
  name: "@deepseek-ai/dsh-credentials-local"
  disabled: false
```

（web / tui profile 无此问题，credentials 插件默认启用。）

## Step 4：安装 TUI（两条路径二选一）

TUI 不是内置的，必须装社区维护的 TUI 插件。**选型**：npm 上搜 `dsh-tui` 会撞到多个同名包，认准 `@deepseek-harness-tui/dsh-tui`（peerDeps 明确支持 0.2.x）。其他同名包（如 `@dsh-tui/dsh-tui`）锁死 0.1.x 且停更，装上会在 import 阶段报 `does not provide an export named ...` 的 API 断裂错误。

**版本兼容注意（2026-11-25 实测）**：TUI 0.20.2 的兼容列表只声明到 `0.2.2-rc.5`，**不含 alpha 版**——dsh 是 alpha（如 0.2.2-alpha.2）时启动被版本闸拦截：

```
dsh: skipping profile bundle "@deepseek-harness-tui/dsh-tui": Error: Plugin ... is incompatible with dsh 0.2.2-alpha.2 ...
```

解法（确认风险后授予精确版本豁免）：

```bash
dsh plugin --profile dsh-tui allow-version "@deepseek-harness-tui/dsh-tui@0.20.2" --dsh-version 0.2.2-alpha.2 --accept-risk
```

（避开 alpha、按 Step 1 用 rc 版则不需要这一步。）

### 路径 A：全局启动器（推荐）

```bash
npm install -g @deepseek-harness-tui/dsh-tui
dsh-tui doctor        # 环境预检（node/dsh/pnpm/密钥/profile）
dsh-tui               # 首次运行自动自举独立 profile：~/.dsh/profiles/dsh-tui/
```

- 启动器提供 `dsh-tui` / `dst` 两个命令，独立于官方 dsh 的 profile 体系（自建 `dsh-tui` profile，不碰 web/headless/tui）
- **首跑自举可能撞版本闸**：自举内部调的还是 plugin-manager（`dsh plugin --profile dsh-tui add -w ...`）。被拦时启动器会打印修复命令，照跑 allow-version 后重跑 `dsh-tui` 即可（豁免包自带条件守卫不会实际加载，同路径 B 的说明）
- 自动化引擎 `dsh-tui run` 有独立验证基线，**不含 0.2.2-alpha**——alpha 上 `run` 报 `ADAPTER_UNAVAILABLE`，只影响无界面自动化，不影响交互式 TUI
- 后续维护：`dsh-tui update` 一键对齐 TUI + dsh 引擎 + 启动器；`dsh-tui safe --rescue` 可建干净救援 profile；`dsh-tui doctor` 全绿（profile ✓ / config ✓）即自举完成
- 自举出的 profile 同样默认 `llm-deepseek`——**Step 3 的模型 patch 仍要写**进 `~/.dsh/profiles/dsh-tui/cordis.patch.yml`
- 验证注意：TUI profile 没有 headless 模式——`dsh --profile dsh-tui "提示词"` 会挂起（TUI 应用在非 TTY 下不退出），验证配置用 `--dump-config`，验证对话要在真终端里跑 `dsh-tui`

### 路径 B：plugin-manager 手动装（dsh 版本较旧时的兜底）

```bash
dsh plugin --profile tui add "@deepseek-harness-tui/dsh-tui"
```

装进官方 dsh 的 profile，启动用 `dsh --profile tui`。走 plugin-manager 会对整棵依赖树做版本兼容检查，**可能被拒：传递依赖是 0.1.x 旧包**——该插件的传递依赖里有两个 0.1.x 遗留包（`@deepseek-ai/dsh-code-runtime-worker-thread`、`@deepseek-ai/dsh-agent-presets`，均锁 `0.1.0-rc.6`）会被 0.2.x 早期版本拒绝：

```
dsh: installation rejected: Plugin ... is incompatible with dsh 0.2.2-rc.1
```

解法：对这两个包做**精确版本豁免**后重装：

```bash
dsh plugin --profile tui allow-version "@deepseek-ai/dsh-code-runtime-worker-thread@0.1.0-rc.6" --dsh-version 0.2.2-rc.1 --accept-risk
dsh plugin --profile tui allow-version "@deepseek-ai/dsh-agent-presets@0.1.0-rc.6" --dsh-version 0.2.2-rc.1 --accept-risk
dsh plugin --profile tui add "@deepseek-harness-tui/dsh-tui"
```

豁免的包**不会实际加载**：它们自带 `disabled: !!js` 条件守卫，检测到新版等价组件（`dsh-ptc-runtime-node` / `agent-preset-registry`）存在时自动禁用。0.2.x 运行时这两个组件都有，旧包被守卫挡住，风险可控。装完可验证：

```bash
dsh --profile tui --dump-config | grep -A3 "sandbox-policy\|agent-default-model"
```

TUI 会有两条无害警告（`tool-ralph` / `tool-subagent-list-agents` entry not found）——插件想增强 base 里两个可选工具，base 版本没有就跳过，不用管。

## Step 5：验收

```bash
# 路径 A
dsh-tui
# 路径 B
dsh --profile tui
```

预期：全屏 TUI 界面，默认模型走 Step 3 的 `agent-default-model`。常用操作：

| 快捷键 | 功能 |
| --- | --- |
| `/model` | 切换模型（**旧会话记得选**——配置改版前建的会话残留旧路由，发消息报 `no configured model "xxx"`，/model 重选或 /new 即愈） |
| `Ctrl+N` | 新会话 |
| `Ctrl+S` | 恢复会话 |
| `Ctrl+Q` | 退出 |
| `Shift+Tab` | 循环权限模式 |

headless 顺手验证：`dsh --profile headless "回复OK两个字母即可"`，正常返回即全链路通。

## Step 6：web profile 同款配置

web 的模型配置写进 `~/.dsh/profiles/web/cordis.patch.yml`，结构与 tui 同源，两处差异：

1. **tokenhub 挂在 `llm-deepseek` 行**（provider=deepseek-official，Anthropic Messages 协议）——web 内置模型选择器直接列出；多模态 key 用 `inputModalities:`：

```yaml
- id: llm-deepseek
  config:
    baseURL: https://tokenhub.deepexios.cn/gateway/api/v1
    reasoningEffort: off
    models:
      - id: DeepSeek-V4.1-Flash
        name: DeepSeek V4.1 Flash (tokenhub)
        contextWindow: 128000
        maxTokens: 32000
        inputModalities: [ "text", "image" ]   # ← 这行的 key 是 inputModalities
        systemPromptUpdate: in-history
        toolUpdate: addition-only
      # ...其余模型同结构
- id: agent-default-model
  config:
    provider: deepseek-official
    model: DeepSeek-V4.1-Flash
    reasoningEffort: off
```

2. **dts 走 `llm-pi-ai` 行**，与 Step 3 模板完全一致（key `input:`）。

改完重启 web 进程（配置只在启动时加载），浏览器刷新即可在「请选择模型」里看到两个网关的模型。

## 坑速查表

| 症状 | 原因 | 解法 |
| --- | --- | --- |
| `MISSING_CREDENTIAL: llm-deepseek` | patch 没配自定义模型，回落到内置 DeepSeek 官方路由 | Step 3 patch（两条路径都要写） |
| key 已存但报 MISSING_CREDENTIAL（headless） | headless 模板默认禁用 credentials 插件，凭据读不到 | Step 3 末尾的启用段 |
| TUI 启动被版本闸拦截（`skipping profile bundle ... incompatible`） | TUI 0.20.2 兼容列表只到 rc.5，dsh 是 alpha | 用 rc 版 dsh；或对 TUI 做精确版本豁免（Step 4） |
| web/tui 同时报 `agent-preset/invalid: reading 'parent'`，新建会话必崩 | npm 发布的 alpha 包自身构建问题（node 24 实测） | 卸掉换 rc 版；同版本源码构建正常（Step 1 选型警告） |
| 改了 patch 但模型列表/行为没变 | 配置只在进程启动时加载 | 重启 dsh web / 重开 dsh-tui |
| 旧会话发消息报 `no configured model "xxx"` | 会话残留配置改版前的旧路由 | 会话内 `/model` 重选，或 `/new` 开新会话 |
| 路径 B `installation rejected: incompatible` | 依赖树里有 0.1.x 旧包 | Step 4 路径 B 的 allow-version 豁免 |
| import 阶段 `does not provide an export named ...` | 装了锁死 0.1.x 的停更包（API 断裂，豁免救不了） | 认准 `@deepseek-harness-tui/dsh-tui` scope |
| 路径 A 自举被拦（`installation rejected`） | 自举内部也走 plugin-manager，0.1.x 传递依赖被拒 | 按启动器打印的命令跑 allow-version（对 `dsh-tui` profile），重跑 `dsh-tui` |
| 路径 A `ADAPTER_UNAVAILABLE`（仅 `dsh-tui run`） | 自动化引擎验证基线不含 0.2.2-alpha/rc.x 新版 | 不影响交互式 TUI；无界面自动化改用 `dsh --profile headless` 或路径 B 的 profile |
| Web 面板配好模型但 headless/tui 没用上 | profile 配置隔离，各 profile 的 patch 独立 | 每个 profile 单独写 Step 3 / Step 6 |
| TUI 启动报 `entry did not activate` | 插件与本机 dsh 版本 API 不匹配 | 查插件 peerDeps 是否覆盖你的 dsh 版本，不覆盖就换包 |

## 来源

- DSH 官方仓库：https://github.com/deepseek-ai/deepseek-harness（plugin-manager 文档在 `packages/boot/plugin-manager/README.zh.md`）
- TUI 插件：npm 包 `@deepseek-harness-tui/dsh-tui`，仓库 https://github.com/ccch1mneyyy/dsh-TUI
- 现成配置参考：`~/.dsh/profiles/*/cordis.patch.yml`
