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
npx skills@latest update socratic-tutor idea-alchemist
```

## 技能列表

### 教学

- **socratic-tutor** — 自适应教学技能。通过对话探测学习者的理解水平，动态调整讲解深度（术语密度、抽象层级、前置知识假设、例子复杂度），支持任意领域知识。自动跟踪学习进度，持续校准层级。

### 产品

- **idea-alchemist** — 想法炼金师。通过引导式追问，帮普通人把模糊想法变成清晰的产品蓝图和技术规格。

## 目录结构

```
skills/
├── teaching/          # 教学类技能
│   └── socratic-tutor/
└── productivity/      # 效率类技能
    └── idea-alchemist/
```

## 后续计划

持续添加新技能，包括但不限于：

- 写作类
- 分析类
- 开发工作流类
