# SHYXIN Skills

个人 Claude Code 技能集。

> 国内用户请走「国内安装」（从 Gitee 拉取，免翻墙）；国外用户走「国外安装」（GitHub + npx skills）。

## 国内安装（免翻墙，推荐）

本仓库已镜像到 Gitee（`theshyxin/skills`），配合 [cn-skills-cli](https://github.com/SHYXIN/cn-skills-cli) 可从 Gitee 拉取，**无需翻墙**。`cn-skills-cli` 已内置别名：`SHYXIN/skills` / `mattpocock/skills` 会自动路由到 Gitee 镜像（需 `cn-skills-cli >= 0.1.10`；`cn-skills update` 需 `>= 0.1.15`）。

> **Windows 用户请直接看「方式一 · 手动命令」**——纯 npm + cn-skills 命令，PowerShell / CMD / Git Bash 通吃，无需 bash。下面的「一键脚本」是 bash 脚本，仅适用于 macOS / Linux / 装了 Git Bash 的 Windows。

**方式一 · 手动命令（推荐，全平台通用）**

在任意终端（PowerShell / CMD / bash）逐条执行：

```bash
# 1) 安装 cn-skills-cli（国内镜像加速）
npm install -g cn-skills-cli --registry=https://registry.npmmirror.com

# 2) 安装本仓库技能（自动走 Gitee）
cn-skills add SHYXIN/skills --copy --yes --global --agent codebuddy,claude-code,codex,workbuddy

# 3) 安装推荐搭配 pstack 整包（Gitee 镜像仓 theshyxin/pstack，用完整 URL；当前冻结版 v0.15.15）
cn-skills add https://gitee.com/theshyxin/pstack --copy --yes --global --agent codebuddy,claude-code,codex,workbuddy

# 4) 安装推荐搭配 mattpocock/skills（Gitee 镜像；放最后，使 tdd/teach 采用 matt 版，见下「同名技能」）
cn-skills add mattpocock/skills --copy --yes --global --agent codebuddy,claude-code,codex,workbuddy

# 5) 安装 opencli CLI + 全部 opencli 技能（让 agent 操控日常 Chrome；CLI 已装则跳过 npm 那步）
npm install -g @jackwener/opencli --registry=https://registry.npmmirror.com
cn-skills add jackwener/opencli --copy --yes --global --agent codebuddy,claude-code,codex,workbuddy

# 注意：还需手动装 Chrome 扩展（无法静默安装）：
# https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk
# 装好后 opencli doctor 验证，完整引导见 setup-opencli 技能

# 6) asd-ste100：受控英语规则，改写给 agent 消费的英文文本，防误读（无 Gitee 镜像，直连 GitHub）
cn-skills add danyuchn/asd-ste100-skill --copy --yes --global --agent codebuddy,claude-code,codex,workbuddy

# 7) 公司内部 dp-* 技能（DeepWorks 工具链，从公司 GitLab 拉取，需内网权限；装完见 ask-dp 路由器说明）
cn-skills add deepexi/skills/wangxin --copy --yes --global --agent codebuddy,claude-code,codex,workbuddy
```

> 说明：`--agent` 逗号分隔列表在 PowerShell / CMD / Git Bash 下均可直接使用（`cn-skills-cli >= 0.1.16`）。装完可用 `cn-skills update` 随时更新（详见下方「更新（国内）」）。

**方式二 · 一键脚本（macOS / Linux / Git Bash）**

适合 bash 环境，一条命令拉取并安装全部：

```bash
git clone --depth 1 https://gitee.com/theshyxin/skills.git /tmp/skills-cn && bash /tmp/skills-cn/install-cn.sh; rm -rf /tmp/skills-cn
```

默认装到 `codebuddy,claude-code,codex,workbuddy`（全局）。

自定义 agent 列表（逗号分隔）：

```bash
git clone --depth 1 https://gitee.com/theshyxin/skills.git /tmp/skills-cn && bash /tmp/skills-cn/install-cn.sh "codebuddy,claude-code,codex"; rm -rf /tmp/skills-cn
```

> ⚠️ Windows 注意：原生 cmd / PowerShell **没有 bash**，直接跑会报 `execvpe(/bin/bash) failed`（落到 WSL 且 WSL 未装 bash 时）。Windows 用户请用上面的「方式一 · 手动命令」。

**更新（国内）**

```bash
cn-skills update            # 更新全部（lock 记录里的 skills）
cn-skills update socratic-tutor   # 只更新某个
```

> 需 `cn-skills-cli >= 0.1.15`。通过 `cn-skills add` 安装的技能会自动记录 lock；`npx skills add` 装的也能更新（兼容读取同一份 `~/skills-lock.json`）。

## 国外安装（GitHub + npx skills）

本仓库技能通过 [vercel-labs/skills](https://github.com/vercel-labs/skills) 提供的 `npx skills` 工具安装，**无需克隆本仓库**。

> Windows 用户：这里的 `curl … | bash` 同样需要 bash 环境（macOS / Linux / Git Bash）。原生 cmd / PowerShell 下可参照「国内安装 · 方式一」的手动命令，把 `cn-skills` 换成 `npx skills@latest` 逐条执行即可。

**方式一 · 一键安装（推荐，免下载仓库）**

```bash
curl -fsSL https://raw.githubusercontent.com/SHYXIN/skills/master/install.sh | bash
```

脚本会远程拉取并直接运行，依次安装本仓库技能与下方「推荐搭配」（`mattpocock/skills`、`humanlayer/skills` 的 show-me、`pstack` 整包；**matt 置于最后**，以便 `tdd`/`teach` 采用 matt 版——见「同名技能」一节），默认装到 `codebuddy claude-code codex hermes-agent`（全局）。

自定义 agent 列表：

```bash
curl -fsSL https://raw.githubusercontent.com/SHYXIN/skills/master/install.sh | bash -s -- "codebuddy claude-code codex hermes-agent"
```

如需固定到某个稳定版本（推荐生产环境使用），把 URL 中的 `master` 换成 release tag，例如 `v1.0.0`：

```bash
curl -fsSL https://raw.githubusercontent.com/SHYXIN/skills/v1.0.0/install.sh | bash
```

**方式二 · 克隆后本地运行**

```bash
git clone https://github.com/SHYXIN/skills.git
cd skills
./install.sh                      # 默认装到 codebuddy claude-code codex hermes-agent（全局）
./install.sh codebuddy           # 只装 codebuddy
./install.sh "codebuddy codex"   # 自定义 agent 列表
```

**方式三 · 手动命令**

```bash
# 安装本仓库技能
npx skills@latest add SHYXIN/skills -y --copy -g -a codebuddy claude-code codex hermes-agent

# 同时安装推荐搭配（顺序有意义：matt 放最后，让 tdd/teach 采用 matt 版）
npx skills@latest add humanlayer/skills --skill show-me -y --copy -g -a codebuddy claude-code codex hermes-agent
npx skills@latest add backnotprop/pstack -y --copy -g -a codebuddy claude-code codex hermes-agent
npx skills@latest add mattpocock/skills -y --copy -g -a codebuddy claude-code codex hermes-agent

# opencli：让 agent 操控日常 Chrome（CLI 已装则跳过 npm 那步；技能装全量，成套互相引用）
npm install -g @jackwener/opencli
npx skills@latest add jackwener/opencli -y --copy -g -a codebuddy claude-code codex hermes-agent

# asd-ste100：受控英语规则，改写给 agent 消费的英文文本，防误读
npx skills@latest add danyuchn/asd-ste100-skill -y --copy -g -a codebuddy claude-code codex hermes-agent

# book-to-skill：把书/文档蒸馏成结构化技能（PDF/EPUB/DOCX/MD 等，Python 依赖按格式可选装）
npx skills@latest add virgiliojr94/book-to-skill -y --copy -g -a codebuddy claude-code codex hermes-agent

# 注意：还需手动装 Chrome 扩展（无法静默安装）：
# https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk
# 装好后 opencli doctor 验证，完整引导见 setup-opencli 技能
```

安装后，在对应 agent 中即可使用以下技能。

## 推荐搭配

### mattpocock/skills

[mattpocock/skills](https://github.com/mattpocock/skills) 是社区高质量技能集（TypeScript / 工程实践向）。上面的一键脚本已默认一并安装；如需单独安装：

```bash
npx skills@latest add mattpocock/skills -y --copy -g -a codebuddy claude-code codex hermes-agent
```

### humanlayer/skills (show-me)

[humanlayer/skills](https://github.com/humanlayer/skills) 中的 **show-me** 技能：讲解当前主题时自动配简洁图表、代码形状草图和聚焦的 HTML artifact。一键脚本已默认只安装 show-me；如需单独安装：

```bash
npx skills@latest add humanlayer/skills --skill show-me -y --copy -g -a codebuddy claude-code codex hermes-agent
```

### pstack

[backnotprop/pstack](https://github.com/backnotprop/pstack) 是 [cursor/plugins](https://github.com/cursor/plugins) 的独立镜像，作者 Lauren Tan（poteto）。它是一套**方法论底座**：入口技能 `/poteto-mode` 会按任务匹配 playbook（bug fix / perf / feature / refactoring / prototype / shipping / 无人值守等 23 个），再按步骤调 `/how`、`/why`、`/architect`、`/arena`、`/swarm`、`/interrogate`、`/tdd`、`/unslop` 等技能，并用 24 条 principle 作为判断标准。核心主张是"走得快先扎得深"，写更少但更高质量的代码，用可验证的工作换取自如的并行。

本仓库按**整包**安装。pstack 自带 `unslop`，因此不再单独安装 `cursor/plugins` 的 unslop（两者同源，独立安装会导致同名技能双副本、更新/卸载互相打架）。一键脚本已默认安装；如需单独安装：

```bash
npx skills@latest add backnotprop/pstack -y --copy -g -a codebuddy claude-code codex hermes-agent
```

pstack 还随附 `poteto-agent` 与 `Comment Sicko` 两个子代理定义（在 `agents/` 下），但 `npx skills` 只安装 `skills/` 里的技能，**子代理不会自动落地**。缺失时 poteto-mode 会降级为"普通子代理 + 固定前缀"运行（pstack 的 Harness 章节写明此路径），功能可用，只是不复用 `poteto-agent` 的完整读取流程。国内安装走 Gitee 镜像仓 `theshyxin/pstack`（默认分支当前对应冻结版 `v0.15.15`，每周自动同步上游，冻结 tag 见仓内 `refs/tags`）。注意用**完整 Gitee URL**：`cn-skills` 的 `owner/repo` 简写会解析到 GitHub，而 `npx skills` 从 Gitee 拉取会被反爬 403：

```bash
cn-skills add https://gitee.com/theshyxin/pstack --copy --yes --global --agent codebuddy,claude-code,codex
```

### opencli

[jackwener/opencli](https://github.com/jackwener/opencli) 让 agent 操控你的日常 Chrome（带全部登录态）。一键脚本已默认安装（CLI + 全部 opencli 技能）；如需单独安装：

```bash
npx skills@latest add jackwener/opencli -y --copy -g -a codebuddy claude-code codex hermes-agent
```

> 注意：还需手动装 Chrome 扩展（无法静默安装）：<https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk>，装好后 `opencli doctor` 验证。完整引导见 setup-opencli 技能。

### asd-ste100-skill

[danyuchn/asd-ste100-skill](https://github.com/danyuchn/asd-ste100-skill) 把航空航天受控英语标准 ASD-STE100 改造成 Claude Code 技能：改写给 agent 消费的英文文本（工具描述、错误消息、系统提示词、跨 agent 指令），消除歧义防止下游误读。与 [writing-for-agents-wx](#技能列表)（中文写作规范）是英文侧的天然搭档。一键脚本已默认安装；如需单独安装：

```bash
npx skills@latest add danyuchn/asd-ste100-skill -y --copy -g -a codebuddy claude-code codex hermes-agent
```

### ppt-master

[hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 从任意文档生成可编辑的原生 PPTX：幻灯片生成、页面视觉重构、品牌/风格/版式工作区、原生模板填充、成品增强，支持讲解词与动画。**不随一键脚本安装**——子目录 64MB 且带 Python 依赖（`requirements.txt`），属"要用时再装"的重型工具，需要 PPT 能力时单独安装：

```bash
npx skills@latest add hugohe3/ppt-master -y --copy -g -a codebuddy claude-code codex hermes-agent
```

### book-to-skill

[virgiliojr94/book-to-skill](https://github.com/virgiliojr94/book-to-skill) 把技术书、文档夹或一组资料蒸馏成**结构化技能**（不是摘要）：框架、决策规则、反模式、术语表、速查表，章节文件按需加载，回答基于原文不幻觉——官方实测比整本塞上下文省 24–51 倍 token。输入不限书籍：内部文档、品牌手册、论文集、RFC 都行。一键脚本已默认安装；如需单独安装：

```bash
npx skills@latest add virgiliojr94/book-to-skill -y --copy -g -a codebuddy claude-code codex hermes-agent
```

> 注意：转换 PDF/EPUB/DOCX 等格式时按需安装 Python 依赖（`pip install "book-to-skill[pdf]"` 等，纯 Markdown 免依赖）；对 Python 3.9+。

### rea（Reverse Engineer Anything）

[morluto/rea](https://github.com/morluto/rea) 一个 MCP 覆盖全栈逆向：原生二进制（配合 Hopper/Ghidra/IDA）、Electron/JavaScript、.NET 程序集、网站行为——看中某个应用的特性，让 agent 拆解它怎么实现、出示证据、指导复刻。分析全程本地运行。一键脚本只装**技能本体**（`reverse-engineer-anything`，纯说明书，轻量无依赖）；**MCP server 本体**（`npx rea-agents setup`，仓库 50MB）与原生分析引擎属"要用时再装"的重型件，需要逆向能力时单独安装：

```bash
npx skills@latest add morluto/rea -y --copy -g -a codebuddy claude-code codex hermes-agent   # 技能（一键脚本已含）
npx rea-agents setup                                                                  # MCP server（要用时再装）
```

### 同名技能：tdd / teach

推荐搭配之间只有两个技能重名，都发生在 pstack 与 mattpocock/skills 之间：

| 技能 | pstack 版 | matt 版 |
|------|-----------|---------|
| `tdd` | 精简版「TDD Bug Fix」，仅在明确要求或存在便宜测试点时触发 | 完整 red-green-refactor 参考（含 tests/mocking 指南），被 matt 的 `/implement`、`/ask-matt` 内部依赖 |
| `teach` | 一次性讲清某段代码/变更（内部跑 `/how`、`/why`） | 有状态、跨多次会话的学习工作区 |

`npx skills` / `cn-skills` 把技能平铺到同一目录（`~/.agents/skills/<name>`），**同名后装者胜、无冲突提示**。因此本仓库的安装顺序**特意把 mattpocock/skills 放在 pstack 之后**，让 matt 版的 `tdd`/`teach` 覆盖 pstack 版（matt 版语义更完整且被其工作流内部引用）。pstack 的这两个是单文件，会被 matt 的多文件版本干净覆盖，不留残渣。

若你更想要 pstack 版，把 `install.sh` / `install-cn.sh` 里的 pstack 块移到 matt 块**之后**即可（后装者胜）。

## npx skills 用法

完整命令参考（来源格式、私有仓库、选项表、安装范围/方式、环境变量、本地克隆后安装等）见 **[NPX-SKILLS.md](./NPX-SKILLS.md)**。

## 技能列表

### 教学

- **socratic-tutor** — 自适应教学技能。通过对话探测学习者的理解水平，动态调整讲解深度（术语密度、抽象层级、前置知识假设、例子复杂度），支持任意领域知识。自动跟踪学习进度，持续校准层级。内置**面试模式**（复习第 3 次起自动升级），用挑战式问题做深度检验，支持用户主动发起。

- **eli5-zh** — 像给五岁小孩一样解释（ELI5）中文版。按受众的年龄、学历、职业角色或关系，自动调整讲解的词汇、类比、语气、深度与切入角度，把任意主题、代码、概念或报错讲得任何人都能听懂。触发词如「用五岁小孩能懂的话说」「给我经理解释一下」「给我妈解释这个报错」「给设计师简化一下」。改编自 DreambigOu/ELI5，全中文化并做了适度本地化。

- **learn-by-minimal** — 从最小实例学起。用「最小可运行/可体验实例 → 逐部件点亮 → 全景可视化」的方法，带用户学会任何可拆解的知识或系统（代码框架、算法、协议、业务流程…）。先生成最小 demo 与一张 Mermaid 组件学习地图（按依赖排序），再逐个点亮部件、扩展 demo、高亮地图节点，每步用有深度的选择题/判断题校验理解，最终地图长成完整结构图即全景可视化。进度按主题存于 `~/.learn-by-minimal/<主题>/`，支持跨会话续学。

- **teach-wx** — 中文优先的技术学习 skill。用于快速了解技术概念、阅读 GitHub 仓库/代码库、系统学习某个主题、澄清技术问题，或生成可复习的 HTML lesson。默认初始化学习区、主线讲课产出 HTML，节奏可调；可运行示例按主题性质判定：实操型（学库/API）配 examples/，概念型（原理/架构）用「架构观察」章节（tui-diagram 风格字符图 + 值得读的资料清单）替代；专业名词保留英文或常用缩写，但必须用中文解释其作用和边界。

- **mental-map** — 领域地图师。攻克概念型学科（有理论体系、有学术争议的领域）的三阶段 skill：全量灌料（候选材料清单确认制）→ 画地图（提取专家共享的 5 个心智模型 + 3 处根本性分歧 + 共识/开放问题，产出独立可复习的 map.md）→ 自测陪练（10 道区分"真懂与背书"的鉴别题，一次一题，答错触发追问纠错）。产物按主题落盘 `learning/<主题>/`。不适用于实操型技能（学 Rust/K8s 靠动手）和单点概念澄清。user-invoked。

- **learn-by-doing** — 项目驱动式技能学习。通过做出一个真实项目习得实操技能（学 Rust、学 K8s、学框架）：Agent 设计项目并写码、逐段讲解，用户带「看懂每个动作」的目标旁观学习（阶段前置小卡 + 随手提问），每阶段以一个亲手小改动验收（可查资料，代码自己敲，跑通才过关）。项目与学习文件一体落盘（`learning/` 内 plan / cards / reviews）。与 learn-by-minimal 成系列：minimal 管理解，doing 管上手。user-invoked。

### 面试

- **interview-coach** — 面试备战教练。通过知识梳理、问答练习和全真模拟三种模式，帮求职者系统准备面试。覆盖技术面试（算法、系统设计、编码）和行为面试（STAR、文化匹配）。内置 5 家公司情报（字节/阿里/Google/Amazon/腾讯），支持能力图谱追踪、错题本和艾宾浩斯复习计划。进度文件独立存储于 `~/.interview-coach/`，更新 skill 不丢数据。

### 验证

- **verify-manual-after-implementation** — 实现完成后的通用手动验收手册生成器。适用于 `to-spec -> to-tickets -> implement-spec` 后，自动审计仓库、必要时补 `scripts/dev.sh`，并生成 `docs/verification/manual-test-guide.md`；验收步骤采用结构化「操作」约定（open/click/fill/curl/wait 动词 + 预期），可被 verify-run 照单自动执行。
- **verify-run** — opencli 驱动的通用自动验证执行器。三档输入自动探测：有验收手册照单执行、有仓库无手册轻量审计现场推导、只有 URL 探索式驱动；每步 pass/fail 带证据（截图/响应），产出 `docs/verification/verify-run-report.md`。与 verify-manual-after-implementation / verify-replay 成系列。
- **verify-replay** — 验证全绿后的回放清单固化。把 verify-run 跑通的执行过程固化为 YAML 步骤清单（`docs/verification/replay.yml`），重放由 agent+opencli 逐条执行、agent 判定断言；报告有 fail 时拒绝固化（YAML 是执行产物，不是预生成物）。

### 搜索

- **anysearch** — 实时搜索引擎。支持通用网页搜索、垂直领域搜索（股票/学术/法律/代码等）、并行批量搜索和网页内容提取。已适配 Windows Clash 代理环境，开关代理均可自动连通。

### 效率

- **consensus-tech-research** — 基于已达成的设计共识，调研并比较适合的技术库、包或框架，输出有证据支撑的技术选型报告与推荐结论。在 grilling、grill-me 或 grill-with-docs 达成共识后，需要技术调研、框架比较、依赖选型，或为 to-spec 准备技术决策时使用。

- **guided-book-reader** — 带读英文技术书 PDF 的工作流技能。用于认真阅读英文技术书、论文集或长篇 PDF：先读取和解析 PDF、转成 txt、按章节拆分，再用中文为主的 teach 风格逐小节讲解、出选择题检查理解，并把每节阅读总结追加到 notes markdown。

- **bookpipe** — forcoder.net → suufun.com 加速 → book-to-skill 的每日书籍流水线，下载到 skill 闭环。带 URL 跑单本全链路（下载+解压+即记账）；不带参数抓今日书目并分级预勾选（AI/编程默认勾选，MP4 永不自动）；status 三态查漏单，转换默认值已固化不再问。浏览器操作走 opencli（认证零凭据进脚本），hCaptcha 暂停等人工。

- **handoff-wx** — 把当前对话压缩成交接文档，供下一个 agent 会话无缝接手。适用于任何场景（开发/调研/写作/协作），不限代码。存储按序探测当前目录的 `temp/handoffs/` → `tmp/handoffs/`，都没有则退回 OS 临时目录；文件名 `YYYY-MM-DD_HHMM_主题.md`。保留原版纪律：不复制已有工件（只给路径/URL 指针）、脱敏、参数=下个会话重点。改编自 mattpocock/skills 的 handoff，与其存取策略不同。user-invoked。
- **domain-modeling-wx** — 构建并打磨项目的领域模型：讨论代码库术语、写/改 GLOSSARY.md（术语层，与 matt 上游完全兼容）、CONTEXT.md（关系/对话/歧义 wx 扩展层）或记录 ADR 时使用。

- **agent-tdd** — agent 开发的 TDD 闭环。改 agent 的 md/skill（系统提示词、工作流规则、技能文档）时用「行为案例」当测试：新行为先写案例跑红再改跑绿（案例先行轨），存量改动跑两轮 diff 防退步（回归护栏轨）；案例写法纪律治 LLM 抖动，diff 红绿复跑仲裁。user-invoked。

- **grill-one** — 单问版 grilling。用于把用户的计划、决策或想法通过追问打磨清楚，但每轮只问一个问题，避免一次抛出多个问题。适合用户明确要求“一次只问一个问题”或希望更慢、更聚焦的设计访谈。
- **grill-one-with-docs** — 单问版 grill-with-docs。边访谈边沉淀文档：调 grill-one 一轮一问打磨设计，调 domain-modeling-wx 把术语写进 GLOSSARY.md（与 matt 上游兼容）、术语关系/歧义写进 CONTEXT.md、决策写进 ADR。原版（grilling 多问版）来自 mattpocock/skills，install.sh 会配套安装。
- **retro-wx** — 复盘一次编码会话，向 agent 的环境提出改进建议（改环境不改代码，只提议不执行）。按导航/自动检查/编码标准/steering 瘦身/工具经济/no-op/信息可达七类扫描痛点，按严重度排序；默认复盘当前会话，也可直接 grep 本机五源会话日志（codebuddy/claude/codex/copilot/pi 的 jsonl，无需服务）复盘任意 harness 的历史会话，落点含个人 skills 仓库新 skill 提议与 auto-memory。改编自 mattpocock/skills 的 retro（主体同构），与 matt 版共存。user-invoked。
- **ask-wx** — 工作流主线路由器：问该用哪个技能。入口裁决区默认 `/grill-one-with-docs`（有工作目录即起步：单问快磨 + GLOSSARY/CONTEXT/ADR 沉淀），无工作目录退 `/grill-one`，确定走 matt 全流程想多问深挖才用 matt 的 grill-with-docs；共识已定走 consensus-tech-research 选型。主流含原型绕行（handoff 出 → prototype → handoff 回）与 matt 系中后段（spec/tickets/implement/review），验证层（代码产物 verify-run 系 / agent 行为载体 agent-tdd）与复盘（retro vs retro-wx）用自有技能；附纠错层（where-am-i-wx/wait-what-wx/source-trace-wx/next-step）与支线（triage/diagnosing-bugs/wayfinder/research-wx）。推荐前必读目标技能的 SKILL.md。user-invoked。
- **step-card-wx** — 生成保姆级测试/操作步骤卡，让不看代码的人也能照着走并把结果交回判定。基础档=通用操作指引（分步+命令原文+说明）；验收档=叠加排雷第0步+每步预期结果+测试者/判定者分离闭环。用于"给我测试步骤""怎么测""写个操作指引""验收步骤卡"等场景。
- **rust-windows-setup** — Windows 上安装 Rust 工具链（含需要 C 编译器的项目，如 rusqlite）。覆盖 rustup 国内镜像加速、Missing manifest 修复、MinGW/MSVC 选择、dlltool/ld 的 PATH 坑。在 Windows 配 Rust 环境或遇到 'Missing manifest' / 'dlltool not found' 报错时使用。

- **setup-windows-mcp** — 在新 Windows 电脑上安装并注册 Windows-MCP（Windows 桌面自动化 MCP server：截屏、点击、UI 树、浏览器控制）。覆盖 codebuddy / claude / codex 三 CLI 的一次性配置，含国内网络加速（uv 安装镜像 + PyPI 镜像）与 register-all.sh 一键注册脚本。不需要 clone 源码，uvx 直接从 PyPI 拉包。

- **ssh-key-setup** — 新机器 SSH 密钥初始化。生成一对 ed25519 密钥（一机一钥），登记到任意多个远端 git 服务（gitLab / GitHub / Gitee 等），逐一 `ssh -T` 验证，清除旧 https/PAT 凭据残留。全中文引导，不自动上传密钥（由用户粘贴入库），含 4 条踩坑记录（CRLF、老 sshd、2FA 绕过、一机一钥）。
- **sync-workbuddy** — 把技能仓库的本地克隆同步（复制覆盖）到 WorkBuddy 的 `~/.workbuddy/skills/`。WorkBuddy 不在 `npx skills` 支持的 agent 列表里，故用脚本直接复制；只增改、永不删除目标目录中已有技能（第三方/商店安装的不受影响）。适用于改完 skill 后同步到本机 WorkBuddy、新电脑初始化 WorkBuddy 环境。

- **branch-management** — 通用 Git 分支管理操作技能。用于在当前仓库中新建 feature 分支、同步 develop、提交并 push、MR 前检查、合并后清理分支。分支名默认 `feature/<initials>-YYYYMMDD-<task>`，initials 从 git config 读取（`skill.initials`），不硬编码用户身份。提交前校验作者邮箱（`skill.email`），不一致则拒绝提交。会主动执行低风险 Git 操作；历史重写、远端删除、生产分支相关动作需明确确认。
- **worktree** — 通用 Git worktree 隔离工作技能。从基线分支切 feature 分支到主仓库旁的 `.wt-<短任务名>` 目录做目录级隔离，覆盖创建 → 开发 → 合并后清理全生命周期；支持多 worktree 并行与归属盘点（按分支名前缀判断，只动自己的）。分支命名/提交规范沿用 branch-management；一切删除动作（含 worktree、本地/远端分支）执行前必须先确认。
- **oss-finder** — GitHub 开源贡献第一步：找项目。用 gh CLI 按默认画像（近期活跃、中等规模、带 good first issue）搜索候选仓库，按活跃度 / 社区健康 / 贡献友好度打分，输出候选清单与推荐理由。
- **oss-triage** — GitHub 开源贡献第二步：选 issue + 读代码。给定目标仓库，拉取 good first issue / help wanted 候选，筛掉已认领、有关联 PR、已过期的，浅克隆到 `~/.oss/<owner>/<repo>` 读代码验证，输出「选题 + 改动方案」。
- **oss-contribute** — GitHub 开源贡献第三步：fork → 改 → PR。在 `~/.oss` 工作区建分支实现改动、本地验证、push 到自己的 fork、按上游 CONTRIBUTING 开 PR 并跟进 review；fork、push、PR、留言一律先确认。

- **writing-for-agents-wx** — 中文版写给 agent 的文档写作规范（skill / AGENTS.md / CLAUDE.md）：让 agent 每次走同一套过程，而非产出相同文本。覆盖 context pointer、信息层级、完成标准、引导词与删减等杠杆。

- **wait-what-wx** — 中文版「没懂就喊停」：agent 上一句没说清时，让你手动触发它重讲——补上下文、用更短更主动的句式（技术词保留英文原词）、用词遵循 `GLOSSARY.md` 的通用语言（多 context 跟 `GLOSSARY-MAP.md`）、表达方式参考 `CONTEXT.md` 的 `## Example dialogue` 示范对话。双层承接 domain-modeling-wx。user-invoked，模型不会自触发。

- **where-am-i-wx** — 中文版「迷路就喊地图」：任务/对话中不知道走到哪时，手动触发画一张纯文字决策地图——已定结论、📍当前位置、未决问题、被否决的选项（附否决原因），关键节点旁标注前置知识（名词+一句话解释，深挖交给 eli5-zh / learn-by-minimal）。与 wait-what-wx 成对：单点没懂→重讲那句；整体迷路→喊地图。user-invoked，模型不会自触发。

- **wizard-wx** — 中文版手把手向导生成器：生成一个互动式 bash 脚本，一步步带着人完成只有人能做的操作（配置凭据 / CI secret、走陌生第三方后台、跑一次性迁移）。带 `template.sh` 库（分阶段进度、确认闸门、跨平台开 URL、隐藏式 secret 输入、幂等 `.env` 更新、`gh secret` / `gh variable` 写入）。model-invoked。

- **ai-daily-brief** — AI 每日简报：把「AI HOT 当日精选新闻」与「GitHub 热门仓库」合并成一份中文简报，一次调用出完整结果。AI 新闻走 aihot.virxact.com 匿名只读 API，GitHub trending 走 github.com/trending（WebFetch），均免 API Key；支持「今天(24h)」「本周(7d)」「最热(hot-topics)」三种模式。model-invoked。

- **upward-networking** — 设计真诚、克制、可执行的向上社交和高价值关系经营动作，支持邀约、请教、跟进、复盘，以及可选的 Obsidian 笔记草稿。想走向上社交流程时手动调用（/upward-networking）。

- **doc-append-log** — 只追加、不改写的文档/日志历史机制。每次变更新建 `YYYY-MM-DD_主题.md`，并用 `INDEX.md` 时间线索引（含"当前事实/当前参考/历史背景"状态）串联，供 CodeBuddy / Claude Code / Codex 等智能体阅读完整历史；目录无关（自动定位 docs/log/logs/ 等，也接受显式路径），附带 `init_index.sh` / `append_entry.sh` / `locate_docs.sh` 三个幂等脚本。model-invoked。
- **next-step** — 规划"下一步做什么"：用户做完一段事或卡住时，列出 3-5 个带价值/代价/何时选/可照做动作的下一步并标出性价比最高者。适用代码/学习/生活/通用。用户手动调用（/next-step）。
- **closed-loop** — 把一件事逼到真正闭环：动态体检差距清单（排序 + 指定首选）、每一步带推荐推进、曳光弹端到端拿证据。约束 AI——宣布完成必须附证据。用户手动调用（/closed-loop），当你要确认「这事真的完成了吗」时用。
- **playbook** — 领域专家路线：调用即扮演该领域行家，按行家手册给当前局面一条带顺序、完成标准、坑位预警的推荐路线；复杂权衡可升级多专家会诊。方向已定、想知道「行家会怎么走」时手动调用（/playbook）。
- **consensus-check** — 共识审计：grill、访谈或长讨论结束后，把双方达成的共识逐条罗列并具体化到可检验细节，标出 ✅ 已对齐 / ⚠️ 有出入 / ❓ AI 补全，暴露隐藏的模糊点。想确认「我们真的对齐了吗」时手动调用（/consensus-check）。
- **skill-iterate** — 迭代打磨一个已存在的 skill：把一次使用中的摩擦（误触发、抢跑、粒度不对、步骤缺失）变成小步修改。一次只改一类行为（±10 行），先要一手摩擦证据不猜失败模式；行为修改只动 SKILL.md，plugin.json/README 按条件同步；只提议 commit 不主动 git。纯删杂质（背景/闲聊/重复自述）转给 agent-config-tidy，行为校准才归本 skill。user-invoked。
- **loop-driver** — 环式自进化调度器。把任务逼成一个自我改进的循环：收集目标 → 按经验选 skill 组合 → 执行 → 用闭环信号记分 → 沉淀到 ledger 并调权重 → 等下一个目标，一圈比一圈选得准。人只在无共识决策和红线处被拍板。说"转起来""跑一整个循环""让 loop 转一圈"时手动调用（/loop-driver）。
- **cn-brief-wx** — 中文简报：agent 刚才的英文步骤/工具调用/输出看不懂时，用中文复述"做了什么、为什么、现在到哪"，不替你改方向。model-invoked。
- **research-wx** — 中文版 research：派后台 agent 调研一手来源，结论写成带出处的 Markdown 存进仓库。model-invoked。
- **skill-curator** — 技能市场策展人：维护 plugin.json / README 与磁盘上 skills/ 目录三者一致（注册新技能、移除旧技能、重同步漂移），改动后自动 git commit。

- **agent-config-tidy** — 整理/收尾智能体配置（AGENTS.md、soul.md、SKILL.md、agent yaml 及脚本）：扫描并移除混进配置里的决策背景、会话说明、闲聊等不必要内容，只留运行时需要的指令；并交叉检查同一件事在多个配置文件间的描述是否一致（同步缺失/互相矛盾/各说各话）；先出差异确认再改写。用于每轮 grill 迭代改完配置后的克制收尾。交互档：每步等用户确认，确认后才改写。

- **agent-config-lint** — 配置克制自动检查：派只读子 agent 按 agent-config-tidy 的判定规则扫描目标目录（含跨文件描述一致性），产出带建议动作的差异报告，跨文件问题成对列出；无人值守、永不改文件。与 agent-config-tidy 成对——lint 是自动检查档（如 wx-flow 阶段 4 配置类改动收尾），要落地修改再走 tidy 逐条确认。

- **source-trace-wx** — 追踪 agent 回答的原始依据与来源。先列出对话里真实读过的来源，再对没有出处的 claim 去一手来源（官方文档/源码/规范/第一方 API）补查，写成注明出处、区分一手/二手信任级的 Markdown 文件。触发词如「查出处」「原始依据在哪」。model-invoked。

- **setup-opencli** — 在一台新机器上配置 OpenCLI 浏览器桥接：让 agent 通过 Chrome 扩展操控用户日常 Chrome（带全部登录态）。覆盖前置检查、npm 安装 CLI、引导安装 Chrome 扩展、opencli doctor 验证、冒烟测试与常见排障（扩展 Reconnecting、daemon 未启动等）。手动调用（/setup-opencli）。

- **setup-dws** — 在一台新机器上配置 dws CLI（钉钉 Workspace CLI，npm 包 dingtalk-workspace-cli）：让 agent 操作钉钉消息/日历/文档/待办等 25+ 服务。覆盖 npm 安装、OAuth 扫码登录（认证 dws 自管，无需配环境变量）、auth status 验证与排障。手动调用（/setup-dws）。

- **setup-tapd** — 在一台新机器上配置 tapd-cli（TAPD OpenAPI CLI）：覆盖从官方 cnb.cool 发版页获取 exe、用户级环境变量三件套（TAPD_API_ENDPOINT / TAPD_TOKEN / TAPD_WORKSPACE_IDS，个人访问令牌不进仓库）、只读命令验证与排障。手动调用（/setup-tapd）。

- **setup-tencent-docs** — 在一台新机器上配置腾讯文档访问：安装官方 tencent-docs 技能、配置 TENCENT_DOCS_TOKEN 用户级环境变量（tokenUrl 页面自助获取）、API 连通性验证与排障。无本地 CLI，纯 token 认证。手动调用（/setup-tencent-docs）。

- **setup-claude-code** — 在新机器上初始化 Claude Code 关键设置：`skipWebFetchPreflight`（跳过 WebFetch 域名预检，解决国内网络 "Unable to verify if domain is safe to fetch" 报错）、`permissions.defaultMode: bypassPermissions`（完全权限免确认框），以及可选的 windows-mcp 注册探测（已装跳过、未装转交 setup-windows-mcp）。幂等改写 `~/.claude/settings.json`，含 JSON 校验、生效条件说明与 5 条踩坑记录。手动调用（/setup-claude-code）。

### DevOps

- **gitlab-runner-provision** — GitLab Runner 新机器部署全流程引导：SSH 免登录 → 安装 Docker → 安装/注册 GitLab Runner → 最小 CI/CD 流水线跑通。半自动（scripts/ 做检测/生成/校验），通用化不绑定具体机器，验收标准是 push hello-world 流水线变绿。

- **gitlab** — GitLab 平台操作技能（只做平台层，本地 git 流程归 branch-management）：MR 创建/查看/合并/关闭/rebase、指定审核者(reviewer)与指派人(assignee)、labels/milestone、approve 与评论讨论；MR 之外的 REST API 调用、CI pipeline 查询、tag/发布操作、token/凭据获取；内置 glab 优先 + 挂死/误报 422 时改 curl + PRIVATE-TOKEN 直连 API 的兜底，以及合并前 merge-tree 冲突预检。通用化不绑定实例，本机/公司特有信息隔离在 references/。凡是涉及 GitLab 实例、GitLab API、MR、pipeline、tag、凭据的任务触发。

- **repo-init** — 仓库初始化引导器（一次性仪式）。两条路径：新仓库从 0 到 1（git init → 远程建仓 GitLab/GitHub → dev→main|master 分支模型 → 脚手架落盘 → push 点亮 → 设分支保护）；存量仓库只补缺、不改既有，不一致仅标注。GLOSSARY/CONTEXT 遵 domain-modeling-wx 纪律，GitLab 平台操作引用 gitlab skill。手动调用（/repo-init）。

### 个人

- **weekly-report** — 周报生成器。把多人的例会全文（如钉钉/飞书导出的周会记录）整理成单人周报邮件正文，自动提取指定成员（默认 王鑫）的「本周内容/进度」与「下周计划」，并起草「新技术/个人思考」一段，输出带主题行的三段式邮件正文。调用：`/weekly-report [成员名]`。

- **wx-flow** — 个人全任务流程驱动器（适用于所有代码任务，不限仓库）。五个阶段：需求澄清（grill）→ 隔离判断（worktree 硬裁决）→ 开发 → 收尾验证（按改动类型分流提示）→ 提交 + 清理（三档停靠：只提交 / 提交+push / 完整 MR，兜底只提交，升级由用户触发）。AI 领路，每个阶段收口处停下等用户拍板后再进下一阶段。调用：`/wx-flow`。

### 前端开发

- **miniprogram-iconfont** — 微信小程序 Iconfont 图标集成。从 iconfont.cn 挑选下载图标，自动替换字体文件、更新 CSS、扫描并替换 WXML/JS 中的 emoji 为 iconfont 类名。引导式交互 + 自动化脚本，覆盖完整的图标集成流程。

### 后端开发

- **fastapi-starlette-admin** — 给 FastAPI 项目快速集成 starlette-admin 管理面板。自动检测项目结构（从零开始 or 已有项目），处理 async/sync 引擎双轨制，生成完整的 admin 配置（含 AuthProvider、ModelView、batch actions、自定义 Dashboard、i18n 语言切换），标注 database.py 和 main.py 的修改点。基于真实项目经验，包含 11 条踩坑记录。

### pstack（同名技能副本）

> 从 pstack 挑选、改名后与 `mattpocock/skills` 的同名技能**并存**。安装后 `tdd`/`teach` 仍是 matt 版，这两个是 pstack 版。详见 [skills/pstack/README.md](./skills/pstack/README.md)。

- **tdd-pstack** — pstack 版 TDD Bug Fix：只在有明确、便宜的测试落点时，把 bug 先写成失败测试再改产品代码；测试难写/昂贵/依赖端到端时明确跳过，用最接近的可执行回归检查替代。与 matt 版 `tdd`（完整 red-green-refactor 参考）并存。
- **teach-pstack** — pstack 版 Teach：把一段工作讲清楚让人真正理解。内部运行 pstack 自有的 `how` / `why` 技能，把结果揉成一段平实讲解；只在用户想被「讲明白」时触发，不改动任何东西。与 matt 版 `teach`（跨会话有状态学习区）并存。

### 公司（已迁出）

公司内部 dp-* 技能（DeepWorks 工具链：ask-dp / dp-ask-deepworks / dp-ask-teams / dp-eval-run / dp-session-forensics(-cloud) / dp-dev-bootstrap / dp-deepworks-dev-start / dp-knowledge-compile / dp-dth-key-setup / dp-console-admin）**已迁移到公司 GitLab [deepsense/skills](https://gitlab.deepexi.com/deepsense/skills) 的 `wangxin/` 目录**，本仓库不再维护。一键安装：`cn-skills add deepexi/skills/wangxin --copy --yes --global`（需内网权限，见上方「国内安装」第 7 步）。

### 设计

- **visualise** — 内联可视化渲染技能。把 SVG 图表、HTML 交互组件、Chart.js 图表等直接渲染进对话（sandboxed iframe，token 流式输出），用于画流程图、架构图、数据可视化、UI mockup、对比布局等；内置 design-system / diagrams / components / charts 四套参考规范（位于 `references/`）。触发：用户说"画个图""visualize""diagram""show me""对比布局"。
- **visual-verdict** — 结构化视觉 QA 判定技能。把生成的 UI 截图与一张或多张参考图对比，返回严格 JSON 判定（`score` 0-100 / `verdict` pass·revise·fail / `category_match` / `differences` / `suggestions` / `reasoning`），用于截图还原度、布局/间距/字体/配色一致性验收；目标阈值 90+。源自 oh-my-claudecode，可直接作为"截图对比检查清单"使用。
- **tui-diagram** — TUI 终端字符画图技能。用 Unicode 盒线字符（┌─┐│└┘ → ▼）在 Claude Code / CodeBuddy 等纯终端 Agent 里直接画流程图、架构图、时序图、状态机、层级树、对比矩阵、数据条、UI 线框、时间线共 9 类图；被调用时按对话上下文自动选型，内置中英混排宽度对齐规则。说"存下来"时能转 Mermaid 的图转入工作目录根部 `diagrams.md`，转不了的以 text 块原样保留。触发：仅显式调用 /tui-diagram。
- **excalidraw-diagram** — 手绘风 Excalidraw 图生成技能。基于 `excalidraw-cli`（统一 `npx -y excalidraw-cli@0.0.2`，首次运行自动下载，无需全局安装）把需求变成 `.excalidraw` 文件，需要时再 `export` 成 excalidraw.com 可分享链接。内置「图要论证不是陈列」方法论、9 类图型选型（流程/关系/思维导图/架构/数据流/泳道/类图/时序/ER）与配色单一真源（浅色 + 深色）。与 `visualise`（对话内联）、`tui-diagram`（终端字符）三线分离。触发：仅显式调用 /excalidraw-diagram。

### CNB

- **cnb-token** — 引导用户创建或粘贴 CNB 访问令牌（PAT）并持久化，安装 cnb CLI 并配置 git 凭据，使 cnb 命令行与 git push/pull 到 cnb.cool 免密可用。首次配置 CNB 工具链、cnb 命令报 401/403、或 git 推拉 cnb.cool 要求认证时使用。

## 目录结构

```
skills/
├── teaching/          # 教学类技能
│   ├── socratic-tutor/
│   ├── teach-wx/
│   ├── eli5-zh/
│   ├── learn-by-minimal/
│   ├── mental-map/
│   └── learn-by-doing/
├── productivity/      # 效率类技能
│   ├── anysearch/     # 搜索类技能（含代理适配）
│   ├── bookpipe/  # forcoder 每日书籍流水线（suufun 加速 + book-to-skill 闭环转换 + 防漏单）
│   ├── guided-book-reader/  # 英文技术书 PDF 带读
│   ├── interview-coach/  # 面试备战教练
│   ├── grill-one/  # 单问版 grilling
│   ├── grill-one-with-docs/  # 单问版 grill-with-docs（访谈+ADR/术语表沉淀）
│   ├── domain-modeling-wx/  # 领域建模 wx 版（GLOSSARY 术语层 + CONTEXT 关系层 + ADR）
│   ├── agent-tdd/  # agent 开发的 TDD 闭环：行为案例双轨（先行轨红绿 + 护栏轨 diff 回归）
│   ├── retro-wx/  # 会话复盘：七类扫描改环境，支持 grep 五源历史会话，只提议不执行
│   ├── ask-wx/  # 工作流主线路由器：默认 grill-one-with-docs 入口，中后段指向 matt 系
│   ├── step-card-wx/  # 保姆级测试/操作步骤卡（基础档+验收档）
│   ├── verify-manual-after-implementation/  # 实现后手动验收手册生成（含结构化操作约定）
│   ├── verify-run/  # opencli 通用自动验证执行器（手册/仓库/URL 三档输入）
│   ├── verify-replay/  # 验证全绿后固化 YAML 回放清单
│   ├── ssh-key-setup/ # 新机器 SSH 密钥初始化 + 多端登记
│   ├── sync-workbuddy/ # 技能仓库克隆 → WorkBuddy 技能目录复制同步（含脚本）
│   ├── branch-management/ # 通用 Git 分支管理操作
│   ├── worktree/  # Git worktree 隔离工作：.wt- 目录隔离、全生命周期、归属盘点
│   ├── consensus-tech-research/ # 基于共识的技术选型调研
│   ├── writing-for-agents-wx/  # 写给 agent 的文档（中文版写作规范）
│   ├── wait-what-wx/  # 没懂就喊停（中文版）
│   ├── where-am-i-wx/  # 迷路就喊地图：当前任务/对话的决策定位图（中文版）
│   ├── source-trace-wx/  # 追踪回答的原始依据与来源（一手来源补查）
│   ├── wizard-wx/  # 生成手把手 bash 向导（中文版）
│   ├── ai-daily-brief/  # AI 每日简报（AI HOT 新闻 + GitHub trending 合并）
│   ├── upward-networking/ # 向上社交和高价值关系经营
│   ├── doc-append-log/  # 只追加文档/日志历史机制（INDEX.md + 脚本，目录无关）
│   ├── next-step/  # 下一步规划：复盘现状 + 3-5 个带价值/代价/何时选的下一步，标出性价比最高
│   ├── oss-finder/  # GitHub 开源贡献第一步：找项目（gh CLI 搜索打分）
│   ├── oss-triage/  # GitHub 开源贡献第二步：选 issue + 读代码
│   ├── oss-contribute/  # GitHub 开源贡献第三步：fork → 改 → PR（全确认制）
│   ├── closed-loop/  # 广义闭环驱动器：动态闭环体检 + 可选陪跑 + 曳光弹验证硬门槛
│   ├── playbook/  # 领域专家路线：行家视角给带顺序/完成标准/坑位预警的推荐路线，可多专家会诊
│   ├── consensus-check/  # 共识审计：共识清单具体化对账，标 ✅/⚠️/❓ 暴露隐藏模糊点
│   ├── skill-iterate/  # skill 迭代打磨：摩擦→小步修改（±10 行），同步真相源，只提议 commit
│   ├── loop-driver/  # 环式自进化调度器：收目标→选组合→执行→记分→沉淀调权重，skill 内容不污染
│   ├── cn-brief-wx/  # 中文简报：把 agent 的英文步骤/工具调用/输出翻译成中文复述
│   ├── research-wx/  # 中文版研究：后台 agent 调研一手来源，结论带出处存进仓库
│   ├── rust-windows-setup/  # Windows 上稳健安装 Rust 工具链（含 C 编译器依赖，如 rusqlite）
│   ├── setup-windows-mcp/  # 新机器安装注册 Windows-MCP 桌面自动化（codebuddy/claude/codex 三件套）
│   ├── setup-opencli/  # OpenCLI 浏览器桥接配置：CLI + Chrome 扩展 + doctor 验证
│   ├── setup-dws/  # 钉钉 dws CLI：npm 安装 + OAuth 扫码登录（认证自管，零环境变量）
│   ├── setup-tapd/  # TAPD tapd-cli：官方发版页 exe + 用户级 env 三件套（endpoint/token/workspace）
│   ├── setup-tencent-docs/  # 腾讯文档：官方技能安装 + TENCENT_DOCS_TOKEN 用户级 env（无本地 CLI）
│   ├── setup-claude-code/  # 新机器 Claude Code 关键设置：跳过 WebFetch 预检 + 完全权限 + windows-mcp 探测
│   ├── agent-config-tidy/  # 配置克制收尾：移除混进 agent 配置的决策背景/闲聊 + 跨文件描述一致性（交互确认档）
│   ├── agent-config-lint/  # 配置克制自动检查：子 agent 只读扫描出报告（含跨文件一致性），不改文件（自动档）
│   └── handoff-wx/  # 泛化交接文档：压缩当前对话供下个 agent 接手（temp/tmp handoffs 存储，不限代码）
├── frontend/           # 前端开发类技能
│   └── miniprogram-iconfont/  # 小程序 Iconfont 图标更新
├── design/            # 设计 / 可视化类技能
│   ├── visualise/      # 内联可视化渲染（SVG/HTML/Chart.js，含 references/ 规范）
│   ├── visual-verdict/ # 截图 vs 参考图 结构化视觉 QA 判定
│   ├── tui-diagram/    # TUI 终端字符画图（Unicode 盒线，9 类图型路由）
│   └── excalidraw-diagram/ # 手绘风 Excalidraw 图生成（.excalidraw 文件 + 分享链接）
├── backend/           # 后端开发类技能
│   └── fastapi-starlette-admin/  # FastAPI + starlette-admin 快速集成
├── pstack/            # pstack 同名技能副本（改名后与 matt 版并存）
│   ├── tdd-pstack/    # pstack 版 TDD Bug Fix（与 matt 的 tdd 并存）
│   └── teach-pstack/  # pstack 版 Teach（与 matt 的 teach 并存）
├── cnb/               # CNB 平台相关技能（建仓/提交/PR/流水线入口）
│   └── cnb-token/  # CNB 访问令牌初始化（PAT 创建+持久化，建仓前置）
├── devops/            # 运维 / CI-CD 类技能
│   ├── gitlab-runner-provision/  # GitLab Runner 新机器部署（SSH→Docker→Runner→CI 跑通）
│   ├── gitlab/  # GitLab 平台操作（MR 生命周期 / API·pipeline·tag·凭据 / reviewer·assignee / glab→curl 兜底）
│   └── repo-init/  # 仓库初始化引导器（新仓 0→1 / 存量补缺 / 分支保护）
├── personal/          # 个人效率类技能
│   ├── weekly-report/  # 周报生成器（例会全文 → 单人周报邮件正文）
│   └── wx-flow/        # 个人全任务流程驱动器（grill → 隔离 → 开发 → 验证 → 三档停靠提交）
└── skill-curator/     # 技能市场策展（plugin.json / README / 磁盘三者一致）
```

## 后续计划

持续添加新技能，包括但不限于：

- 写作类
- 分析类
- 更多开发工作流类
