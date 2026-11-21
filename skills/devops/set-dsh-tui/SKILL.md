---
name: set-dsh-tui
description: "在本机安装 DSH CLI 并配置 TUI 终端界面的完整流程。覆盖：npm 装 dsh、profile 体系认知（web/headless/tui 各自独立）、credentials 凭据服务机制、自定义模型 patch（DTH + DTS 双路由实测配置）、danger-full-access 权限设置、安装 @deepseek-harness-tui/dsh-tui 插件（含 0.1.x 传递依赖豁免）。用户手动调用（/set-dsh-tui）。换新机器或帮别人配 DSH 时用。"
disable-model-invocation: true
---

# Set DSH TUI（DSH 安装 + TUI 配置引导）

把 DSH（DeepSeek Harness）CLI 装到一台 Windows 机器上，配好自定义模型路由和 TUI 终端界面，最终以「`dsh --profile tui` 打开全屏终端并能正常对话」作为验收。

本 skill 只管**安装、配置、装插件**；DSH 的日常使用、插件生态、SDK/ACP 集成不在范围内。

## 核心认知：profile 体系

DSH 用 profile 隔离不同入口的配置，**每个 profile 是独立的 Cordis 配置树**，互不继承：

| Profile | 用途 | 说明 |
| --- | --- | --- |
| `web` | 浏览器面板 | 最常用的交互入口 |
| `headless` | 命令行单发问答 | `dsh --profile headless "问题"` |
| `tui` | 全屏终端 UI | 需装 TUI 插件，本 skill 的目标 |
| `sdk` / `sdk-minimal` / `acp` | 程序化集成 | 不在本 skill 范围 |

关键推论：**Web 面板里配好的模型不会自动同步到其他 profile**。每个 profile 的自定义配置都要写进自己的 patch 文件（见 Step 3）。

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

## Step 2：理解凭据服务

API 密钥**不写进 profile 配置**，统一存在凭据服务里：

- 文件位置：`~/.dsh/.credentials.yaml`（明文 YAML，勿外传）
- 结构：`refs:` 下按环境变量名存值，如 `DTH_API_KEY: sk-xxx`
- 注入机制：**credentials 插件**（`@deepseek-ai/dsh-credentials-local`）启动时读取该文件，把键值注入进程环境变量；模型 provider 再按 `apiKeyEnv` 声明的变量名取值

填 key 的两种方式：

```bash
# 方式一：Web 面板「设置 → 模型」页填入（写进 .credentials.yaml）
# 方式二：启动前导出环境变量
export DTH_API_KEY=sk-xxx
```

首次运行 `dsh --profile web` 打开面板填 key 是最省事的初始化方式——key 会落进凭据服务，所有 profile 共享。

## Step 3：配置自定义模型（patch 模板）

新 profile 的 `cordis.patch.yml` 默认为空，模型回落到内置 `llm-deepseek`（DeepSeek 官方路由，需要 `DEEPSEEK_API_KEY`）——不配就会报 `MISSING_CREDENTIAL: llm-deepseek`。

把下面三段写进目标 profile 的 `cordis.patch.yml`（实测配置，dth + DTS 双路由）：

```yaml
# openai 槽位 = OpenAI 兼容协议（不是 OpenAI 官方），这里指向 Deepexi DTS 网关
- id: llm-pi-ai
  name: "@deepseek-ai/dsh-llm-pi-ai"
  config:
    providers:
      openai:                        # ← DTS 网关（https://dts.deepexi.com，OpenAI 兼容协议）
        baseURL: https://dts.deepexi.com/v1
        models:
          - id: glm-5.3
            name: GLM-5.3
            contextWindow: 200000
            maxTokens: 32768
          - id: glm-5.3-flash
            name: GLM-5.3 Flash
            contextWindow: 128000
            maxTokens: 16384
        apiKeyEnv: OPENAI_API_KEY    # ← 变量名只是槽位约定，key 值是 DTS 网关发的
        retryPolicy:
          mode: normal
          maxRetries: 5
          retryableCodes: [EMPTY_RESPONSE, RATE_LIMIT, SERVER, TIMEOUT, TRANSPORT, STREAM_CLOSED]
      dth:                           # ← DTH 路由（tokenhub 计费网关）
        apiKeyEnv: DTH_API_KEY
        api: openai-completions
        baseURL: https://tokenhub.deepexios.cn/gateway/api/v1
        models:
          - id: DeepSeek-V4.1-Flash
            name: DeepSeek-V4.1-Flash
          - id: GLM-5.3
            name: GLM-5.3
          - id: GLM-5.3-Flash
            name: GLM-5.3-Flash
        retryPolicy:
          mode: normal
          maxRetries: 5
          retryableCodes: [EMPTY_RESPONSE, RATE_LIMIT, SERVER, TIMEOUT, TRANSPORT, STREAM_CLOSED]
- id: agent-default-model
  name: "@deepseek-ai/dsh-agent-default-model"
  config:
    provider: dth                    # ← 默认走 dth；换默认模型改这两行
    model: GLM-5.3-Flash
- id: sandbox-policy
  name: "@deepseek-ai/dsh-sandbox-policy"
  config:
    mode: danger-full-access         # ← 权限默认全放开（不作沙箱限制、不弹审批）
    workspaceRoot: !!js process.cwd()
```

三段的作用：

1. `llm-pi-ai` — provider 定义。`openai` 是 DSH 内置的**协议槽位名**（OpenAI 兼容协议），DTS 网关说这套协议所以挂在它下面；`dth` 是自定义命名，`api: openai-completions` 声明同样走 OpenAI 兼容协议
2. `agent-default-model` — 默认模型
3. `sandbox-policy` — 权限策略。Windows 上 base 默认就是 `danger-full-access`（通过 `!!js` 平台条件），显式写死可以跨平台稳定生效

写完验证：

```bash
dsh --profile <name> --dump-config | grep -A4 "agent-default-model"
# 应看到 provider: dth, model: GLM-5.3-Flash
```

**headless profile 额外一步**：headless 模板默认**禁用** credentials 插件（`disabled: true`），导致读不到 `.credentials.yaml` 里的 key，报 `MISSING_CREDENTIAL` 即使 key 已存。在 patch 里加一段重新启用：

```yaml
- id: credentials
  name: "@deepseek-ai/dsh-credentials-local"
  disabled: false
```

（web / tui profile 无此问题，credentials 插件默认启用。）

## Step 4：安装 TUI 插件

TUI 不是内置的——`dsh --profile tui` 首次启动只有裸 base，界面出不来，必须装社区维护的 TUI 插件。

**选型（2026-11 实测）**：npm 上搜 `dsh-tui` 会撞到多个同名包，认准 `@deepseek-harness-tui/dsh-tui`（ccch1mneyyy 维护，peerDeps 明确支持 0.2.x，持续更新）。其他同名包（如 `@dsh-tui/dsh-tui`）锁死 0.1.x 且停更，装上会在 import 阶段报 `does not provide an export named ...` 的 API 断裂错误。

```bash
dsh plugin --profile tui add "@deepseek-harness-tui/dsh-tui"
```

**可能被拒：传递依赖是 0.1.x 旧包**。安装器对整棵依赖树做版本兼容检查，该插件的传递依赖里有两个 0.1.x 遗留包（`@deepseek-ai/dsh-code-runtime-worker-thread`、`@deepseek-ai/dsh-agent-presets`，均锁 `0.1.0-rc.6`）会被 0.2.x 运行时拒绝：

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
dsh --profile tui
```

预期：全屏 TUI 界面，模型走 dth/GLM-5.3-Flash。常用操作：

| 快捷键 | 功能 |
| --- | --- |
| `/model` | 切换模型 |
| `Ctrl+N` | 新会话 |
| `Ctrl+S` | 恢复会话 |
| `Ctrl+Q` | 退出 |
| `Shift+Tab` | 循环权限模式 |

headless 顺手验证：`dsh --profile headless "回复OK两个字母即可"`，正常返回即全链路通。

## 坑速查表

| 症状 | 原因 | 解法 |
| --- | --- | --- |
| `MISSING_CREDENTIAL: llm-deepseek` | patch 没配自定义模型，回落到内置 DeepSeek 官方路由 | Step 3 三段 patch |
| key 已存但报 MISSING_CREDENTIAL（headless） | headless 模板默认禁用 credentials 插件，凭据读不到 | Step 3 末尾的启用段 |
| `installation rejected: incompatible` | 依赖树里有 0.1.x 旧包 | Step 4 的 allow-version 豁免 |
| import 阶段 `does not provide an export named ...` | 装了锁死 0.1.x 的停更包（API 断裂，豁免救不了） | 认准 `@deepseek-harness-tui/dsh-tui` scope |
| Web 面板配好模型但 headless/tui 没用上 | profile 配置隔离，各 profile 的 patch 独立 | 每个 profile 单独写 Step 3 |
| TUI 启动报 `entry did not activate` | 插件与本机 dsh 版本 API 不匹配 | 查插件 peerDeps 是否覆盖你的 dsh 版本，不覆盖就换包 |

## 来源

- DSH 官方仓库：https://github.com/deepseek-ai/deepseek-harness（plugin-manager 文档在 `packages/boot/plugin-manager/README.zh.md`）
- TUI 插件：npm 包 `@deepseek-harness-tui/dsh-tui`（2026-11-21 实测 0.20.2 版兼容 0.2.2-rc.1）
- 本机已验证配置存档：`~/.dsh/profiles/{web,headless,tui}/cordis.patch.yml`
