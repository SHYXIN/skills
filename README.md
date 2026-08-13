# SHYXIN Skills

个人 Claude Code 技能集。

## 安装

本仓库的技能通过 [vercel-labs/skills](https://github.com/vercel-labs/skills) 提供的 `npx skills` 工具安装。

**方式一 · 一键脚本（推荐）**

克隆本仓库后运行：

```bash
./install.sh                      # 默认装到 codebuddy claude-code codex（全局）
./install.sh codebuddy           # 只装 codebuddy
./install.sh "codebuddy codex"   # 自定义 agent 列表
```

脚本会同时安装本仓库技能与下方「推荐搭配」的 `mattpocock/skills`。

**方式二 · 手动命令**

```bash
# 安装本仓库技能
npx skills@latest add SHYXIN/skills -y -g -a codebuddy claude-code codex

# 同时安装推荐搭配（mattpocock/skills）
npx skills@latest add mattpocock/skills -y -g -a codebuddy claude-code codex
```

安装后，在对应 agent 中即可使用以下技能。

## 推荐搭配：mattpocock/skills

[mattpocock/skills](https://github.com/mattpocock/skills) 是社区高质量技能集（TypeScript / 工程实践向）。上面的一键脚本已默认一并安装；如需单独安装：

```bash
npx skills@latest add mattpocock/skills -y -g -a codebuddy claude-code codex
```

## 更新

当技能有新版本时，运行以下命令更新：

```bash
# 更新指定技能
npx skills@latest update socratic-tutor
npx skills@latest update idea-alchemist
npx skills@latest update guided-book-reader
npx skills@latest update interview-coach
npx skills@latest update fastapi-starlette-admin
npx skills@latest update ssh-key-setup
npx skills@latest update branch-management
npx skills@latest update grill-one
npx skills@latest update consensus-tech-research
npx skills@latest update upward-networking
npx skills@latest update agent-package-sync
npx skills@latest update writing-for-agents-wx
npx skills@latest update wait-what-wx
npx skills@latest update wizard-wx
npx skills@latest update skill-bundler
npx skills@latest update ai-daily-brief

# 或者同时更新多个
npx skills@latest update socratic-tutor idea-alchemist anysearch guided-book-reader interview-coach fastapi-starlette-admin ssh-key-setup branch-management grill-one consensus-tech-research upward-networking agent-package-sync writing-for-agents-wx wait-what-wx wizard-wx skill-bundler ai-daily-brief
```

## npx skills 用法示例

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

### 面试

- **interview-coach** — 面试备战教练。通过知识梳理、问答练习和全真模拟三种模式，帮求职者系统准备面试。覆盖技术面试（算法、系统设计、编码）和行为面试（STAR、文化匹配）。内置 5 家公司情报（字节/阿里/Google/Amazon/腾讯），支持能力图谱追踪、错题本和艾宾浩斯复习计划。进度文件独立存储于 `~/.interview-coach/`，更新 skill 不丢数据。

### 产品

- **idea-alchemist** — 想法炼金师。通过引导式追问，帮普通人把模糊想法变成清晰的产品蓝图和技术规格。

### 验证

- **verify-manual-after-implementation** — 实现完成后的通用手动验收手册生成器。适用于 `to-spec -> to-tickets -> implement` 后，自动审计仓库、必要时补 `scripts/dev.sh`，并生成 `docs/verification/manual-test-guide.md`。

### 搜索

- **anysearch** — 实时搜索引擎。支持通用网页搜索、垂直领域搜索（股票/学术/法律/代码等）、并行批量搜索和网页内容提取。已适配 Windows Clash 代理环境，开关代理均可自动连通。

### 效率

- **consensus-tech-research** — 基于已达成的设计共识，调研并比较适合的技术库、包或框架，输出有证据支撑的技术选型报告与推荐结论。在 grilling、grill-me 或 grill-with-docs 达成共识后，需要技术调研、框架比较、依赖选型，或为 to-spec 准备技术决策时使用。

- **guided-book-reader** — 带读英文技术书 PDF 的工作流技能。用于认真阅读英文技术书、论文集或长篇 PDF：先读取和解析 PDF、转成 txt、按章节拆分，再用中文为主的 teach 风格逐小节讲解、出选择题检查理解，并把每节阅读总结追加到 notes markdown。

- **grill-one** — 单问版 grilling。用于把用户的计划、决策或想法通过追问打磨清楚，但每轮只问一个问题，适合更慢、更聚焦的设计访谈。

- **ssh-key-setup** — 新机器 SSH 密钥初始化。生成一对 ed25519 密钥（一机一钥），登记到任意多个远端 git 服务（gitLab / GitHub / Gitee 等），逐一 `ssh -T` 验证，清除旧 https/PAT 凭据残留。全中文引导，不自动上传密钥（由用户粘贴入库），含 4 条踩坑记录（CRLF、老 sshd、2FA 绕过、一机一钥）。

- **branch-management** — 通用 Git 分支管理操作技能。默认以 wangxin/wx 身份从 `develop` 创建 `feature/wx-YYYYMMDD-<task>`，帮你执行新建 feature、同步基线、提交并 push、MR 前检查、合并后清理分支；历史重写、远端删除、生产分支相关动作会先确认。

- **writing-for-agents-wx** — 中文版写给 agent 的文档写作规范（skill / AGENTS.md / CLAUDE.md）：让 agent 每次走同一套过程，而非产出相同文本。覆盖 context pointer、信息层级、完成标准、引导词与删减等杠杆。

- **wait-what-wx** — 中文版「没懂就喊停」：agent 上一句没说清时，让你手动触发它重讲——补上下文、用更短更主动的句式（技术词保留英文原词）、并套 `CONTEXT.md` 的通用语言。user-invoked，模型不会自触发。

- **wizard-wx** — 中文版手把手向导生成器：生成一个互动式 bash 脚本，一步步带着人完成只有人能做的操作（配置凭据 / CI secret、走陌生第三方后台、跑一次性迁移）。带 `template.sh` 库（分阶段进度、确认闸门、跨平台开 URL、隐藏式 secret 输入、幂等 `.env` 更新、`gh secret` / `gh variable` 写入）。model-invoked。

- **skill-bundler** — 中文版技能打包上传器：把 `~/.agents/skills` 下的 skill 批量打成一个 zip，保留 `skills/<name>/` 目录树并附 `MANIFEST.txt`，方便上传到平台。支持按名字筛选 / 排除，自动剔除 `__pycache__`/`node_modules`/`.git`/`*.zip` 等缓存与旧包。user-invoked。

- **ai-daily-brief** — AI 每日简报：把「AI HOT 当日精选新闻」与「GitHub 热门仓库」合并成一份中文简报，一次调用出完整结果。AI 新闻走 aihot.virxact.com 匿名只读 API，GitHub trending 走 github.com/trending（WebFetch），均免 API Key；支持「今天(24h)」「本周(7d)」「最热(hot-topics)」三种模式。model-invoked。

- **upward-networking** — 仅当用户明确调用 upward-networking 或要求使用本技能时使用。帮助用户设计真诚、克制、可执行的向上社交和高价值关系经营动作，支持邀约、请教、跟进、复盘，以及可选的 Obsidian 笔记草稿。

### 前端开发

- **miniprogram-iconfont** — 微信小程序 Iconfont 图标集成。从 iconfont.cn 挑选下载图标，自动替换字体文件、更新 CSS、扫描并替换 WXML/JS 中的 emoji 为 iconfont 类名。引导式交互 + 自动化脚本，覆盖完整的图标集成流程。

### 后端开发

- **fastapi-starlette-admin** — 给 FastAPI 项目快速集成 starlette-admin 管理面板。自动检测项目结构（从零开始 or 已有项目），处理 async/sync 引擎双轨制，生成完整的 admin 配置（含 AuthProvider、ModelView、batch actions、自定义 Dashboard、i18n 语言切换），标注 database.py 和 main.py 的修改点。基于真实项目经验，包含 11 条踩坑记录。

### 公司

- **agent-package-sync** — 公司内部 agent/专家结果包上传前同步工作流。用于检查 result 包改动、同步 AGENTS.md 命名、按实际 skills 目录重打 zip、排除缓存并输出上传清单；不执行 git commit 或 push。

## 目录结构

```
skills/
├── teaching/          # 教学类技能
│   └── socratic-tutor/
├── productivity/      # 效率类技能
│   ├── idea-alchemist/
│   ├── anysearch/     # 搜索类技能（含代理适配）
│   ├── guided-book-reader/  # 英文技术书 PDF 带读
│   ├── interview-coach/  # 面试备战教练
│   ├── grill-one/  # 单问版 grilling
│   ├── ssh-key-setup/ # 新机器 SSH 密钥初始化 + 多端登记
│   ├── branch-management/ # 通用 Git 分支管理操作
│   ├── consensus-tech-research/ # 基于共识的技术选型调研
│   ├── writing-for-agents-wx/  # 写给 agent 的文档（中文版写作规范）
│   ├── wait-what-wx/  # 没懂就喊停（中文版）
│   ├── wizard-wx/  # 生成手把手 bash 向导（中文版）
│   ├── skill-bundler/  # 把用户 skills 批量打包成 zip 上传（中文版）
│   ├── ai-daily-brief/  # AI 每日简报（AI HOT 新闻 + GitHub trending 合并）
│   └── upward-networking/ # 向上社交和高价值关系经营
├── frontend/           # 前端开发类技能
│   └── miniprogram-iconfont/  # 小程序 Iconfont 图标更新
├── backend/           # 后端开发类技能
│   └── fastapi-starlette-admin/  # FastAPI + starlette-admin 快速集成
└── company/           # 公司内部工作流技能
    └── agent-package-sync/  # agent/专家结果包上传前同步
```

## 后续计划

持续添加新技能，包括但不限于：

- 写作类
- 分析类
- 更多开发工作流类
