---
name: modern-web-guidance-usage
description: Google 官方 Web 现代化指导工具（Chrome/Edge/Firefox/MDN 联合维护）的 agent 使用元工作流。何时用（写 Web UI/CSS/客户端 JS 前查最佳实践、扫描旧代码现代化机会）、CLI 三入口（search/retrieve/legacy-scan）、实测坑、与 astryx-usage/firecrawl-usage 的边界。触发词："modern-web-guidance"、"web 最佳实践"、"legacy-scan"、"现代化扫描"、"过时写法"。不搬运 262 条指南内容——运行时以 CLI 输出为准。
---

# Modern Web Guidance 使用元工作流

GoogleChrome/modern-web-guidance-src（本周 GitHub Trending +404%）= 把 Web 平台最新最佳实践做成 agent 可查的指南库：262 个现代功能 + 204 个用例指南，防止 LLM 写出训练数据里的过时代码。本技能只写「何时用 + 怎么用 + 坑」；指南内容一律运行时查 CLI。

## 何时启用

- **写 Web UI/CSS/客户端 JS 之前**：官方定位是 MANDATORY-first——modal/dialog/popover、暗色模式、表单校验、无障碍、View Transitions、容器查询、滚动动画等任务先 search 再动手
- **老项目现代化**：legacy-scan 扫描代码库里的过时模式（polyfill 手写、vendor 前缀滥用、缺 autocomplete 属性等），输出精确到 file:line
- **不用框架名查**：query 用 2-5 个英文动作词描述 UI 能力（`"light dismiss dialog"`），不要带 React/Vue/文件名
- **何时不启用**：后端（SQL/ORM/API 路由）、基础设施（CI/Docker）、纯工具链配置（Vite/tsconfig/ESLint）

## 接入

```bash
# 安装成 agent 技能（装进 ~/.agents/skills/ 并软链各 agent）
npx -y modern-web-guidance@latest install -y --agent '*'   # 非 TTY 必须带参数，见坑 1

# 也可不安装直接用（Node 22+）
npx -y modern-web-guidance@latest search "<query>"
```

## CLI 三入口（已实测）

```bash
npx -y modern-web-guidance@latest search "animate dialog backdrop"   # 搜指南，返回 [{id, description}]
npx -y modern-web-guidance@latest retrieve <guide-id>                # 读全文：Baseline 日期、浏览器支持、@supports 回退写法
npx -y modern-web-guidance@latest legacy-scan <path>                 # 扫描旧代码，file:line 级命中
npx -y modern-web-guidance@latest legacy-scan <path> --json          # 结构化输出（含 verifierRubric 判据），agent 消费用
npx -y modern-web-guidance@latest legacy-scan <path> --include-docs-and-tests  # 默认跳过 docs/test 文件
```

- legacy-scan 静态规则只覆盖 **38 条指南（约 20% 语料）**，扫描结果为 0 不代表没有现代化空间，其余靠 search
- 每条 finding 自带 **Keep/Drop 判据**（如 structuredClone 替换会提示「Vue reactive Proxy 包装时 Drop」）——改代码前先核对，防止 agent 傻改
- retrieve 出的指南含 WCAG 要求、Baseline 浏览器版本表、`@supports` 回退模板——「见到 vendor 前缀就删」前先读，Baseline 目标更早时应保留 fallback

## 实测坑（2026-11-20）

1. **install 非 TTY 必须带参**：裸 `install` 弹 agent 选择交互，agent 代跑报 `SKILLS_PROMPT_REQUIRES_TTY` 什么都不装；必须 `-y --agent '*'`（同 skills CLI 坑，skill-curator Step 5 有记）
2. **search query 要「动作+UI 对象」**：`"dialog"` 太短、`"responsive table dark mode"` 是复合任务要拆两次搜、带框架名/文件名的会污染结果；弱结果时用 HTML/CSS 具体名词（dialog/modal/popover）改搜一次再放弃
3. **遥测提示刷屏**：每次运行输出 Google 匿名统计提示，`DISABLE_TELEMETRY=1` 关掉；`NODE_TLS_REJECT_UNAUTHORIZED=0` 警告同 firecrawl（本机代理环境，无害）

## 与其他技能的边界

- **astryx-usage**：管「UI 组件从哪来」（Astryx 设计系统造组件）；本技能管「写出来的 Web 代码对不对」（平台 API 用法正确且现代）——互补不冲突
- **firecrawl-usage**：管抓网页取数；本技能管 Web 开发知识注入——一个取外部数据，一个查内部最佳实践
- **web-reader-wx**：读网页路由器，与本技能无交集

## 来源与更新

- 源码仓库：GoogleChrome/modern-web-guidance-src（指南发布仓库为 modern-web-guidance）
- 官方文档：developer.chrome.com/docs/modern-web-guidance
- 指南版本随 CLI 更新，search 命令里带 `--skill-version` 参数；运行时以 CLI 实际输出为准
