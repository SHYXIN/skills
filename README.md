# SHYXIN Skills

个人 Claude Code 技能集。

> 国内用户请走「国内安装」（从 Gitee 拉取，免翻墙）；国外用户走「国外安装」（GitHub + npx skills）。

## 国内安装（免翻墙，推荐）

本仓库已镜像到 Gitee（`theshyxin/skills`），配合 [cn-skills-cli](https://github.com/SHYXIN/cn-skills-cli) 可从 Gitee 拉取，**无需翻墙**。`cn-skills-cli` 已内置别名：`SHYXIN/skills` / `mattpocock/skills` 会自动路由到 Gitee 镜像（需 `cn-skills-cli >= 0.1.10`）。

**方式一 · 一键安装（推荐）**

```bash
git clone --depth 1 https://gitee.com/theshyxin/skills.git /tmp/skills-cn && bash /tmp/skills-cn/install-cn.sh; rm -rf /tmp/skills-cn
```

默认装到 `codebuddy,claude-code,codex`（全局）。

自定义 agent 列表（逗号分隔）：

```bash
git clone --depth 1 https://gitee.com/theshyxin/skills.git /tmp/skills-cn && bash /tmp/skills-cn/install-cn.sh "codebuddy,claude-code,codex"; rm -rf /tmp/skills-cn
```

**方式二 · 手动命令（最稳，零依赖）**

```bash
# 1) 安装 cn-skills-cli（国内镜像加速）
npm install -g cn-skills-cli --registry=https://registry.npmmirror.com

# 2) 安装本仓库技能（自动走 Gitee）
cn-skills add SHYXIN/skills --yes --global --agent codebuddy,claude-code,codex

# 3) 安装推荐搭配 mattpocock/skills（Gitee 镜像）
cn-skills add mattpocock/skills --yes --global --agent codebuddy,claude-code,codex
```

**更新（国内）**

```bash
cn-skills update            # 更新全部
cn-skills update socratic-tutor   # 只更新某个
```

## 国外安装（GitHub + npx skills）

本仓库技能通过 [vercel-labs/skills](https://github.com/vercel-labs/skills) 提供的 `npx skills` 工具安装，**无需克隆本仓库**。

**方式一 · 一键安装（推荐，免下载仓库）**

```bash
curl -fsSL https://raw.githubusercontent.com/SHYXIN/skills/master/install.sh | bash
```

脚本会远程拉取并直接运行，依次安装本仓库技能与下方「推荐搭配」（`mattpocock/skills`、`humanlayer/skills` 的 show-me、`cursor/plugins` 的 unslop），默认装到 `codebuddy claude-code codex hermes-agent`（全局）。

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
npx skills@latest add SHYXIN/skills -y -g -a codebuddy claude-code codex hermes-agent

# 同时安装推荐搭配
npx skills@latest add mattpocock/skills -y -g -a codebuddy claude-code codex hermes-agent
npx skills@latest add humanlayer/skills --skill show-me -y -g -a codebuddy claude-code codex hermes-agent
npx skills@latest add cursor/plugins --skill unslop -y -g -a codebuddy claude-code codex hermes-agent
```

安装后，在对应 agent 中即可使用以下技能。

## 推荐搭配

### mattpocock/skills

[mattpocock/skills](https://github.com/mattpocock/skills) 是社区高质量技能集（TypeScript / 工程实践向）。上面的一键脚本已默认一并安装；如需单独安装：

```bash
npx skills@latest add mattpocock/skills -y -g -a codebuddy claude-code codex hermes-agent
```

### humanlayer/skills (show-me)

[humanlayer/skills](https://github.com/humanlayer/skills) 中的 **show-me** 技能：讲解当前主题时自动配简洁图表、代码形状草图和聚焦的 HTML artifact。一键脚本已默认只安装 show-me；如需单独安装：

```bash
npx skills@latest add humanlayer/skills --skill show-me -y -g -a codebuddy claude-code codex hermes-agent
```

### cursor/plugins (unslop)

[cursor/plugins](https://github.com/cursor/plugins) 中的 **unslop** 技能：清除 AI 写作腔——检测并改写 AI 高频套话（"highlighting/ensuring" 型悬空分词、"not just X, but Y" 句式、滥用 em-dash/冒号/加粗、聊天机器人客套话、抽象隐喻名词等 30+ 条规则），保留原意、匹配语气。user-invoked，手动触发。一键脚本已默认安装；如需单独安装：

```bash
npx skills@latest add cursor/plugins --skill unslop -y -g -a codebuddy claude-code codex hermes-agent
```

## 更新

国内用户（cn-skills）直接用：

```bash
cn-skills update socratic-tutor
cn-skills update next-step
cn-skills update cn-brief-wx
cn-skills update research-wx
cn-skills update cnb-token
cn-skills update gitlab-runner-provision
cn-skills update weekly-report
cn-skills update skill-curator
cn-skills update agent-config-tidy
cn-skills update worktree
cn-skills update visualise
cn-skills update visual-verdict
cn-skills update tui-diagram
cn-skills update teach-wx
cn-skills update mental-map
cn-skills update learn-by-doing
cn-skills update            # 或一次性更新全部
```

国外用户（npx skills）运行以下命令更新：

```bash
# 更新指定技能
npx skills@latest update socratic-tutor
npx skills@latest update eli5-zh
npx skills@latest update learn-by-minimal
npx skills@latest update anysearch
npx skills@latest update guided-book-reader
npx skills@latest update interview-coach
npx skills@latest update fastapi-starlette-admin
npx skills@latest update miniprogram-iconfont
npx skills@latest update ssh-key-setup
npx skills@latest update branch-management
npx skills@latest update grill-one grill-one-with-docs
npx skills@latest update consensus-tech-research
npx skills@latest update upward-networking
npx skills@latest update dp-session-forensics
npx skills@latest update dp-dev-bootstrap
npx skills@latest update dp-deepworks-dev-start
npx skills@latest update dp-knowledge-compile
npx skills@latest update writing-for-agents-wx
npx skills@latest update wait-what-wx
npx skills@latest update where-am-i-wx
npx skills@latest update wizard-wx
npx skills@latest update ai-daily-brief
npx skills@latest update doc-append-log
npx skills@latest update next-step
npx skills@latest update cn-brief-wx
npx skills@latest update research-wx
npx skills@latest update source-trace-wx
npx skills@latest update cnb-token
npx skills@latest update rust-windows-setup
npx skills@latest update gitlab-runner-provision
npx skills@latest update weekly-report
npx skills@latest update skill-curator
npx skills@latest update agent-config-tidy
npx skills@latest update worktree
npx skills@latest update oss-finder
npx skills@latest update oss-triage
npx skills@latest update oss-contribute
npx skills@latest update visualise
npx skills@latest update visual-verdict
npx skills@latest update tui-diagram
npx skills@latest update verify-manual-after-implementation
npx skills@latest update teach-wx
npx skills@latest update mental-map
npx skills@latest update learn-by-doing

# 或者同时更新多个
npx skills@latest update socratic-tutor eli5-zh learn-by-minimal mental-map learn-by-doing anysearch guided-book-reader interview-coach fastapi-starlette-admin miniprogram-iconfont ssh-key-setup branch-management grill-one grill-one-with-docs consensus-tech-research upward-networking dp-session-forensics dp-dev-bootstrap dp-deepworks-dev-start dp-knowledge-compile writing-for-agents-wx wait-what-wx where-am-i-wx wizard-wx ai-daily-brief doc-append-log next-step cn-brief-wx research-wx source-trace-wx cnb-token rust-windows-setup gitlab-runner-provision weekly-report skill-curator visualise visual-verdict tui-diagram verify-manual-after-implementation teach-wx agent-config-tidy worktree oss-finder oss-triage oss-contribute
```

## npx skills 用法示例

> 完整命令参考（来源格式、私有仓库、选项表、安装范围/方式、环境变量、本地克隆后安装等）见 **[NPX-SKILLS.md](./NPX-SKILLS.md)**。

以下示例结合本仓库 `SHYXIN/skills` 与推荐搭配 `mattpocock/skills`，覆盖 `npx skills` 的常用子命令。

### 安装 add

```bash
npx skills add SHYXIN/skills                        # 安装全部技能
npx skills add SHYXIN/skills --skill socratic-tutor # 只装某个技能
npx skills add mattpocock/skills -g -a codebuddy -y # 全局 + 指定 agent + 跳过确认
npx skills add https://github.com/SHYXIN/skills     # 也支持完整 URL
```

### 查看已安装 list

```bash
npx skills list
npx skills ls -g                    # 只看全局安装的技能
npx skills ls -a codebuddy -a claude-code  # 按 agent 过滤
```

### 更新 update

```bash
npx skills update                    # 更新全部
npx skills update socratic-tutor     # 只更新指定技能
npx skills update -g                 # 只更新全局范围
npx skills update -y                 # 跳过范围确认
```

### 卸载 remove

```bash
npx skills remove socratic-tutor
npx skills rm mattpocock/skills      # rm 是 remove 的别名
npx skills remove --all              # 全部卸载（--skill '*' --agent '*' -y）
```

### 更多用法

<details>
<summary>use / find / init</summary>

**use — 不安装即用（写入临时目录并打印提示）**

```bash
npx skills use SHYXIN/skills --skill socratic-tutor --agent codebuddy
```

**find — 搜索技能**

```bash
npx skills find typescript
npx skills find react --owner mattpocock   # 跨某作者/组织下的所有仓库搜索
```

**init — 新建技能模板**

```bash
npx skills init my-skill
```

</details>

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

- **verify-manual-after-implementation** — 实现完成后的通用手动验收手册生成器。适用于 `to-spec -> to-tickets -> implement` 后，自动审计仓库、必要时补 `scripts/dev.sh`，并生成 `docs/verification/manual-test-guide.md`。

### 搜索

- **anysearch** — 实时搜索引擎。支持通用网页搜索、垂直领域搜索（股票/学术/法律/代码等）、并行批量搜索和网页内容提取。已适配 Windows Clash 代理环境，开关代理均可自动连通。

### 效率

- **consensus-tech-research** — 基于已达成的设计共识，调研并比较适合的技术库、包或框架，输出有证据支撑的技术选型报告与推荐结论。在 grilling、grill-me 或 grill-with-docs 达成共识后，需要技术调研、框架比较、依赖选型，或为 to-spec 准备技术决策时使用。

- **guided-book-reader** — 带读英文技术书 PDF 的工作流技能。用于认真阅读英文技术书、论文集或长篇 PDF：先读取和解析 PDF、转成 txt、按章节拆分，再用中文为主的 teach 风格逐小节讲解、出选择题检查理解，并把每节阅读总结追加到 notes markdown。

- **grill-one** — 单问版 grilling。用于把用户的计划、决策或想法通过追问打磨清楚，但每轮只问一个问题，避免一次抛出多个问题。适合用户明确要求“一次只问一个问题”或希望更慢、更聚焦的设计访谈。
- **grill-one-with-docs** — 单问版 grill-with-docs。边访谈边沉淀文档：调 grill-one 一轮一问打磨设计，调 domain-modeling 把成形的术语/决策随手写进术语表（CONTEXT.md）与 ADR。原版（grilling 多问版）来自 mattpocock/skills，install.sh 会配套安装。
- **rust-windows-setup** — Windows 上安装 Rust 工具链（含需要 C 编译器的项目，如 rusqlite）。覆盖 rustup 国内镜像加速、Missing manifest 修复、MinGW/MSVC 选择、dlltool/ld 的 PATH 坑。在 Windows 配 Rust 环境或遇到 'Missing manifest' / 'dlltool not found' 报错时使用。

- **ssh-key-setup** — 新机器 SSH 密钥初始化。生成一对 ed25519 密钥（一机一钥），登记到任意多个远端 git 服务（gitLab / GitHub / Gitee 等），逐一 `ssh -T` 验证，清除旧 https/PAT 凭据残留。全中文引导，不自动上传密钥（由用户粘贴入库），含 4 条踩坑记录（CRLF、老 sshd、2FA 绕过、一机一钥）。

- **branch-management** — 通用 Git 分支管理操作技能。默认以 wangxin/wx 身份从 `develop` 创建 `feature/wx-YYYYMMDD-<task>`，帮你执行新建 feature、同步基线、提交并 push、MR 前检查、合并后清理分支；历史重写、远端删除、生产分支相关动作会先确认。
- **worktree** — 通用 Git worktree 隔离工作技能。从基线分支切 feature 分支到主仓库旁的 `.wt-<短任务名>` 目录做目录级隔离，覆盖创建 → 开发 → 合并后清理全生命周期；支持多 worktree 并行与归属盘点（按分支名前缀判断，只动自己的）。分支命名/提交规范沿用 branch-management；一切删除动作（含 worktree、本地/远端分支）执行前必须先确认。
- **oss-finder** — GitHub 开源贡献第一步：找项目。用 gh CLI 按默认画像（近期活跃、中等规模、带 good first issue）搜索候选仓库，按活跃度 / 社区健康 / 贡献友好度打分，输出候选清单与推荐理由。
- **oss-triage** — GitHub 开源贡献第二步：选 issue + 读代码。给定目标仓库，拉取 good first issue / help wanted 候选，筛掉已认领、有关联 PR、已过期的，浅克隆到 `~/.oss/<owner>/<repo>` 读代码验证，输出「选题 + 改动方案」。
- **oss-contribute** — GitHub 开源贡献第三步：fork → 改 → PR。在 `~/.oss` 工作区建分支实现改动、本地验证、push 到自己的 fork、按上游 CONTRIBUTING 开 PR 并跟进 review；fork、push、PR、留言一律先确认。

- **writing-for-agents-wx** — 中文版写给 agent 的文档写作规范（skill / AGENTS.md / CLAUDE.md）：让 agent 每次走同一套过程，而非产出相同文本。覆盖 context pointer、信息层级、完成标准、引导词与删减等杠杆。

- **wait-what-wx** — 中文版「没懂就喊停」：agent 上一句没说清时，让你手动触发它重讲——补上下文、用更短更主动的句式（技术词保留英文原词）、并套 `CONTEXT.md` 的通用语言。user-invoked，模型不会自触发。

- **where-am-i-wx** — 中文版「迷路就喊地图」：任务/对话中不知道走到哪时，手动触发画一张纯文字决策地图——已定结论、📍当前位置、未决问题、被否决的选项（附否决原因），关键节点旁标注前置知识（名词+一句话解释，深挖交给 eli5-zh / learn-by-minimal）。与 wait-what-wx 成对：单点没懂→重讲那句；整体迷路→喊地图。user-invoked，模型不会自触发。

- **wizard-wx** — 中文版手把手向导生成器：生成一个互动式 bash 脚本，一步步带着人完成只有人能做的操作（配置凭据 / CI secret、走陌生第三方后台、跑一次性迁移）。带 `template.sh` 库（分阶段进度、确认闸门、跨平台开 URL、隐藏式 secret 输入、幂等 `.env` 更新、`gh secret` / `gh variable` 写入）。model-invoked。

- **ai-daily-brief** — AI 每日简报：把「AI HOT 当日精选新闻」与「GitHub 热门仓库」合并成一份中文简报，一次调用出完整结果。AI 新闻走 aihot.virxact.com 匿名只读 API，GitHub trending 走 github.com/trending（WebFetch），均免 API Key；支持「今天(24h)」「本周(7d)」「最热(hot-topics)」三种模式。model-invoked。

- **upward-networking** — 仅当用户明确调用 upward-networking 或要求使用本技能时使用。帮助用户设计真诚、克制、可执行的向上社交和高价值关系经营动作，支持邀约、请教、跟进、复盘，以及可选的 Obsidian 笔记草稿。

- **doc-append-log** — 只追加、不改写的文档/日志历史机制。每次变更新建 `YYYY-MM-DD_主题.md`，并用 `INDEX.md` 时间线索引（含"当前事实/当前参考/历史背景"状态）串联，供 CodeBuddy / Claude Code / Codex 等智能体阅读完整历史；目录无关（自动定位 docs/log/logs/ 等，也接受显式路径），附带 `init_index.sh` / `append_entry.sh` / `locate_docs.sh` 三个幂等脚本。model-invoked。
- **next-step** — 规划"下一步做什么"：用户做完一段事或卡住时，列出 3-5 个带价值/代价/何时选/可照做动作的下一步并标出性价比最高者。触发：用户说"下一步""接下来""还能做什么""给点建议""不知道该干嘛""帮我理一下"，或一段回答结束、用户流露犹豫。适用代码/学习/生活/通用。model-invoked。
- **cn-brief-wx** — 中文简报：agent 刚才的英文步骤/工具调用/输出看不懂时，用中文复述"做了什么、为什么、现在到哪"，不替你改方向。model-invoked。
- **research-wx** — 中文版 research：派后台 agent 调研一手来源，结论写成带出处的 Markdown 存进仓库。model-invoked。
- **skill-curator** — 技能市场策展人：维护 plugin.json / README 与磁盘上 skills/ 目录三者一致（注册新技能、移除旧技能、重同步漂移），改动后自动 git commit。

- **agent-config-tidy** — 整理/收尾智能体配置（AGENTS.md、soul.md、SKILL.md、agent yaml 及脚本）：扫描并移除混进配置里的决策背景、会话说明、闲聊等不必要内容，只留运行时需要的指令；先出差异确认再改写。用于每轮 grill 迭代改完配置后的克制收尾。

- **source-trace-wx** — 追踪 agent 回答的原始依据与来源。先列出对话里真实读过的来源，再对没有出处的 claim 去一手来源（官方文档/源码/规范/第一方 API）补查，写成注明出处、区分一手/二手信任级的 Markdown 文件。触发词如「查出处」「原始依据在哪」。model-invoked。

### DevOps

- **gitlab-runner-provision** — GitLab Runner 新机器部署全流程引导：SSH 免登录 → 安装 Docker → 安装/注册 GitLab Runner → 最小 CI/CD 流水线跑通。半自动（scripts/ 做检测/生成/校验），通用化不绑定具体机器，验收标准是 push hello-world 流水线变绿。

### 个人

- **weekly-report** — 周报生成器。把多人的例会全文（如钉钉/飞书导出的周会记录）整理成单人周报邮件正文，自动提取指定成员（默认 王鑫）的「本周内容/进度」与「下周计划」，并起草「新技术/个人思考」一段，输出带主题行的三段式邮件正文。调用：`/weekly-report [成员名]`。

### 前端开发

- **miniprogram-iconfont** — 微信小程序 Iconfont 图标集成。从 iconfont.cn 挑选下载图标，自动替换字体文件、更新 CSS、扫描并替换 WXML/JS 中的 emoji 为 iconfont 类名。引导式交互 + 自动化脚本，覆盖完整的图标集成流程。

### 后端开发

- **fastapi-starlette-admin** — 给 FastAPI 项目快速集成 starlette-admin 管理面板。自动检测项目结构（从零开始 or 已有项目），处理 async/sync 引擎双轨制，生成完整的 admin 配置（含 AuthProvider、ModelView、batch actions、自定义 Dashboard、i18n 语言切换），标注 database.py 和 main.py 的修改点。基于真实项目经验，包含 11 条踩坑记录。

### 公司

- **dp-session-forensics** — DeepWorks 会话取证。查询本机 opencode.db（SQLite，只读）还原 agent 实际收到的注入、思考与工具调用，定位「agent 行为和预期不符」类问题；支持 list / injections / reasoning 对比 / dump / 导出双格式（交互式 HTML + jsonl）五个子命令。
- **dp-deepworks-dev-start** — Windows 本地启动 DeepWorks 桌面开发环境：设置开发变量、启用 CLI 灰度、运行桌面构建并报告启动状态，适用于所有 DeepWorks 本地开发场景。
- **dp-dev-bootstrap** — monorepo dev 环境一键体检（preflight）+ 确定性修复。检测依赖缺失、types 未构建、sidecar 缺失、native 模块 ABI 不匹配、Build Tools 未装、镜像未配等启动前置问题；轻量项 `--fix` 自动修，重量级（数 GB 安装/提权）只提示命令。声明式 profile 驱动，内置 deepworks，新仓库加 JSON 即支持；换新电脑跑一次即可拉齐环境。
- **dp-knowledge-compile** — 把 xmind 诊断树/知识树一键编译成 deepworks 知识中心可加载的本地知识库。自动生成项目骨架、拉取线上 foil schema（或用本地基准）、编译实体与关系、三层校验（spec Zod / 实例 / list-outputs）全绿才交付。业务无关，换领域只改 mappings.yaml。手动调用（/dp-knowledge-compile）。

### 设计

- **visualise** — 内联可视化渲染技能。把 SVG 图表、HTML 交互组件、Chart.js 图表等直接渲染进对话（sandboxed iframe，token 流式输出），用于画流程图、架构图、数据可视化、UI mockup、对比布局等；内置 design-system / diagrams / components / charts 四套参考规范（位于 `references/`）。触发：用户说"画个图""visualize""diagram""show me""对比布局"。
- **visual-verdict** — 结构化视觉 QA 判定技能。把生成的 UI 截图与一张或多张参考图对比，返回严格 JSON 判定（`score` 0-100 / `verdict` pass·revise·fail / `category_match` / `differences` / `suggestions` / `reasoning`），用于截图还原度、布局/间距/字体/配色一致性验收；目标阈值 90+。源自 oh-my-claudecode，可直接作为"截图对比检查清单"使用。
- **tui-diagram** — TUI 终端字符画图技能。用 Unicode 盒线字符（┌─┐│└┘ → ▼）在 Claude Code / CodeBuddy 等纯终端 Agent 里直接画流程图、架构图、时序图、状态机、层级树、对比矩阵、数据条、UI 线框、时间线共 9 类图；被调用时按对话上下文自动选型，内置中英混排宽度对齐规则。说"存下来"时能转 Mermaid 的图转入工作目录根部 `diagrams.md`，转不了的以 text 块原样保留。触发：仅显式调用 /tui-diagram。

### CNB

- **cnb-token** — 引导用户创建或粘贴 CNB 访问令牌（PAT）并持久化，使 cnb CLI 与 git push/pull 到 cnb.cool 免密可用；仅负责拿 token，建仓/推送交给 cnb-api、cnb-code-commit 等技能。

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
│   ├── guided-book-reader/  # 英文技术书 PDF 带读
│   ├── interview-coach/  # 面试备战教练
│   ├── grill-one/  # 单问版 grilling
│   ├── grill-one-with-docs/  # 单问版 grill-with-docs（访谈+ADR/术语表沉淀）
│   ├── ssh-key-setup/ # 新机器 SSH 密钥初始化 + 多端登记
│   ├── branch-management/ # 通用 Git 分支管理操作
│   ├── worktree/  # Git worktree 隔离工作：.wt- 目录隔离、全生命周期、归属盘点
│   ├── consensus-tech-research/ # 基于共识的技术选型调研
│   ├── writing-for-agents-wx/  # 写给 agent 的文档（中文版写作规范）
│   ├── wait-what-wx/  # 没懂就喊停（中文版）
│   ├── where-am-i-wx/  # 迷路就喊地图：当前任务/对话的决策定位图（中文版）
│   ├── wizard-wx/  # 生成手把手 bash 向导（中文版）
│   ├── ai-daily-brief/  # AI 每日简报（AI HOT 新闻 + GitHub trending 合并）
│   ├── upward-networking/ # 向上社交和高价值关系经营
│   ├── doc-append-log/  # 只追加文档/日志历史机制（INDEX.md + 脚本，目录无关）
│   ├── next-step/  # 下一步规划：复盘现状 + 3-5 个带价值/代价/何时选的下一步，标出性价比最高
│   ├── cn-brief-wx/  # 中文简报：把 agent 的英文步骤/工具调用/输出翻译成中文复述
│   ├── research-wx/  # 中文版研究：后台 agent 调研一手来源，结论带出处存进仓库
│   ├── rust-windows-setup/  # Windows 上稳健安装 Rust 工具链（含 C 编译器依赖，如 rusqlite）
│   └── agent-config-tidy/  # 配置克制收尾：移除混进 agent 配置的决策背景/闲聊
├── frontend/           # 前端开发类技能
│   └── miniprogram-iconfont/  # 小程序 Iconfont 图标更新
├── design/            # 设计 / 可视化类技能
│   ├── visualise/      # 内联可视化渲染（SVG/HTML/Chart.js，含 references/ 规范）
│   ├── visual-verdict/ # 截图 vs 参考图 结构化视觉 QA 判定
│   └── tui-diagram/    # TUI 终端字符画图（Unicode 盒线，9 类图型路由）
├── backend/           # 后端开发类技能
│   └── fastapi-starlette-admin/  # FastAPI + starlette-admin 快速集成
├── cnb/               # CNB 平台相关技能（建仓/提交/PR/流水线入口）
│   └── cnb-token/  # CNB 访问令牌初始化（PAT 创建+持久化，建仓前置）
├── company/           # 公司内部工作流技能
│   ├── dp-session-forensics/  # DeepWorks 会话取证（查 opencode.db 定位 agent 行为分歧）
│   ├── dp-dev-bootstrap/  # monorepo dev 环境体检+修复（preflight 引擎 + 声明式 profile）
│   ├── dp-deepworks-dev-start/  # DeepWorks 本地桌面开发启动
│   └── dp-knowledge-compile/  # xmind 一键编译 deepworks 本地知识库（三层校验）
├── devops/            # 运维 / CI-CD 类技能
│   └── gitlab-runner-provision/  # GitLab Runner 新机器部署（SSH→Docker→Runner→CI 跑通）
├── personal/          # 个人效率类技能
│   └── weekly-report/  # 周报生成器（例会全文 → 单人周报邮件正文）
└── skill-curator/     # 技能市场策展（plugin.json / README / 磁盘三者一致）
```

## 后续计划

持续添加新技能，包括但不限于：

- 写作类
- 分析类
- 更多开发工作流类
