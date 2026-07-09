# SHYXIN Skills

个人 Claude Code 技能集。

## 安装

```bash
npx skills@latest add SHYXIN/skills
```

安装后，在 Claude Code 中即可使用以下技能。

## 更新

当技能有新版本时，运行以下命令更新：

```bash
# 更新指定技能
npx skills@latest update socratic-tutor
npx skills@latest update idea-alchemist
npx skills@latest update interview-coach
npx skills@latest update fastapi-starlette-admin
npx skills@latest update ssh-key-setup

# 或者同时更新多个
npx skills@latest update socratic-tutor idea-alchemist anysearch interview-coach fastapi-starlette-admin ssh-key-setup
```

## 技能列表

### 教学

- **socratic-tutor** — 自适应教学技能。通过对话探测学习者的理解水平，动态调整讲解深度（术语密度、抽象层级、前置知识假设、例子复杂度），支持任意领域知识。自动跟踪学习进度，持续校准层级。内置**面试模式**（复习第 3 次起自动升级），用挑战式问题做深度检验，支持用户主动发起。

### 面试

- **interview-coach** — 面试备战教练。通过知识梳理、问答练习和全真模拟三种模式，帮求职者系统准备面试。覆盖技术面试（算法、系统设计、编码）和行为面试（STAR、文化匹配）。内置 5 家公司情报（字节/阿里/Google/Amazon/腾讯），支持能力图谱追踪、错题本和艾宾浩斯复习计划。进度文件独立存储于 `~/.interview-coach/`，更新 skill 不丢数据。

### 产品

- **idea-alchemist** — 想法炼金师。通过引导式追问，帮普通人把模糊想法变成清晰的产品蓝图和技术规格。

### 验证

- **verify-manual** — 手动验证手册生成器。在 `/to-prd` 或 `/to-issues` 完成代码后，自动生成分层验证手册（冒烟测试→功能点→端到端场景），存放在 `docs/verify/issue-NNNN.md`。

### 搜索

- **anysearch** — 实时搜索引擎。支持通用网页搜索、垂直领域搜索（股票/学术/法律/代码等）、并行批量搜索和网页内容提取。已适配 Windows Clash 代理环境，开关代理均可自动连通。

### 效率

- **ssh-key-setup** — 新机器 SSH 密钥初始化。生成一对 ed25519 密钥（一机一钥），登记到任意多个远端 git 服务（gitLab / GitHub / Gitee 等），逐一 `ssh -T` 验证，清除旧 https/PAT 凭据残留。全中文引导，不自动上传密钥（由用户粘贴入库），含 4 条踩坑记录（CRLF、老 sshd、2FA 绕过、一机一钥）。

### 前端开发

- **miniprogram-iconfont** — 微信小程序 Iconfont 图标集成。从 iconfont.cn 挑选下载图标，自动替换字体文件、更新 CSS、扫描并替换 WXML/JS 中的 emoji 为 iconfont 类名。引导式交互 + 自动化脚本，覆盖完整的图标集成流程。

### 后端开发

- **fastapi-starlette-admin** — 给 FastAPI 项目快速集成 starlette-admin 管理面板。自动检测项目结构（从零开始 or 已有项目），处理 async/sync 引擎双轨制，生成完整的 admin 配置（含 AuthProvider、ModelView、batch actions、自定义 Dashboard、i18n 语言切换），标注 database.py 和 main.py 的修改点。基于真实项目经验，包含 11 条踩坑记录。

## 目录结构

```
skills/
├── teaching/          # 教学类技能
│   └── socratic-tutor/
├── productivity/      # 效率类技能
│   ├── idea-alchemist/
│   ├── anysearch/     # 搜索类技能（含代理适配）
│   ├── interview-coach/  # 面试备战教练
│   └── ssh-key-setup/ # 新机器 SSH 密钥初始化 + 多端登记
├── frontend/           # 前端开发类技能
│   └── miniprogram-iconfont/  # 小程序 Iconfont 图标更新
└── backend/           # 后端开发类技能
    └── fastapi-starlette-admin/  # FastAPI + starlette-admin 快速集成
```

## 后续计划

持续添加新技能，包括但不限于：

- 写作类
- 分析类
- 更多开发工作流类
