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

# 或者同时更新多个
npx skills@latest update socratic-tutor idea-alchemist anysearch
```

## 技能列表

### 教学

- **socratic-tutor** — 自适应教学技能。通过对话探测学习者的理解水平，动态调整讲解深度（术语密度、抽象层级、前置知识假设、例子复杂度），支持任意领域知识。自动跟踪学习进度，持续校准层级。内置**面试模式**（复习第 3 次起自动升级），用挑战式问题做深度检验，支持用户主动发起。

### 产品

- **idea-alchemist** — 想法炼金师。通过引导式追问，帮普通人把模糊想法变成清晰的产品蓝图和技术规格。

### 搜索

- **anysearch** — 实时搜索引擎。支持通用网页搜索、垂直领域搜索（股票/学术/法律/代码等）、并行批量搜索和网页内容提取。已适配 Windows Clash 代理环境，开关代理均可自动连通。

## 目录结构

```
skills/
├── teaching/          # 教学类技能
│   └── socratic-tutor/
└── productivity/      # 效率类技能
    ├── idea-alchemist/
    └── anysearch/     # 搜索类技能（含代理适配）
```

## 后续计划

持续添加新技能，包括但不限于：

- 写作类
- 分析类
- 开发工作流类
