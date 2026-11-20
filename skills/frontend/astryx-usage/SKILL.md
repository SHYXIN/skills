---
name: astryx-usage
description: Meta 开源设计系统 Astryx 的 agent 使用元工作流。何时用（前端/UI 任务且项目未装 Astryx 时建议 init）、五步工作流（build → template → component → doctor --built 交付门禁）、agent 向 CLI flag（--json/--dense/--zh）、实测坑。触发词："astryx"、"搭页面"、"做 UI"、"新建页面"、"设计系统"。明确不覆盖组件 API——运行时以项目 AGENTS.md 和 astryx docs/search 为准。
---

# Astryx 使用元工作流

Meta 开源设计系统（React 19+ / StyleX，174 组件，Beta）。本技能只覆盖「何时用 + 怎么开 + 坑」这一元层；组件用法**不写在这里**——项目 init 后其 AGENTS.md 有完整使用规则，运行时查阅走 `npx astryx docs <topic>` / `astryx search`。

## 何时启用

- 用户要做页面 / UI / 前端功能，且是新建（无存量 UI 框架约束）
- 检查项目根有无 `<!-- ASTRYX:START -->` 标记块：**无 → 先建议 init**（见下）；有 → 直接按项目 AGENTS.md 干活，本技能退后

## 快速接入（项目未 init 时）

```bash
npm install @astryxdesign/core @astryxdesign/theme-neutral @stylexjs/stylex
npm install -D @astryxdesign/cli react react-dom   # React 19+ peer dep
npx astryx init            # 写 AGENTS.md + GEMINI.md（managed block，幂等，不覆盖已有内容）
npx astryx theme add neutral
```

init 的 AGENTS.md 块是 `<!-- ASTRYX:START/END -->` 标记块：重跑只更新块内，项目自有指引安全。

## 五步工作流（项目 AGENTS.md 同款骨架，此处为其速查）

```
1. npx astryx build "<页面的人话描述>"     # → 推荐起点模板 + 缺的 blocks
2. npx astryx template <name> <path>      # scaffold；保留框架/间距，只换内容
3. npx astryx component <Name>            # 用前读 props（列表：component --list）
4. 写代码（禁裸 div/hex/px，走组件 props + token——细则见项目 AGENTS.md）
5. npx astryx doctor --built <dir>        # 交付门禁：fail 不交付，warn 逐条看
```

改已有页面：跳过 step 2，在现有 section 内加 blocks/components。

## Agent 向 CLI 用法

- `--json` — 结构化信封输出，脚本/agent 处理首选；exit code 有约定（preflight 缺口 = 3）
- `--dense` — 省 token 紧凑文本，大量读文档时用
- `--zh` — 组件/文档读中文（部分有翻译）
- `--detail brief|compact|full` — 控详略
- 全局装一次 `npm i -g @astryxdesign/cli` 可任意目录用 `astryx`；项目内自动回落项目版本
- 文档体系：`astryx docs`（119 主题，32KB/篇内）→ `docs cli/commands` 全命令；`astryx search "<词>"` 跨组件/hook/模板/文档统一搜

## 实测坑（2026-11-20，v0.7.16）

1. **模板依赖不代装**：scaffold 后 CLI 只提示缺什么（如 `@heroicons/react`），需手动 `npm install`
2. **文档与实现出入**：README 说 init 写 `AGENTS.md`/`CLAUDE.md`，实测写的是 `AGENTS.md` + `GEMINI.md`（无 CLAUDE.md）——按实际产物为准
3. **Beta 变动快**：组件数/命令面随版本漂（150+ → 174），细节以 `astryx --version` 对应的运行时输出为准，勿背文档
4. **主题改动以看图为准**：`experimental theme editor show <name> --png` 写 PNG，不看图不算改完
5. **Windows npx 间歇失灵**：`npx astryx <cmd>` 随机报 `could not determine executable to run`（重定向/循环里更频繁）；绕过法：直调本地 bin `node node_modules/@astryxdesign/cli/clients/cli/bin/astryx.mjs <cmd>`（路径可由 `node -e "console.log(require('./node_modules/@astryxdesign/cli/package.json').bin)"` 查）
6. **scaffold 的 block 是独立文件**：`astryx template <Block> --type block` 只把默认导出组件落成单独 .tsx，不会自动接进页面——要手动 import 进去或参照其用法改页面

## 边界

- 组件 API / 主题 dial / 模板细节：一律运行时 `astryx docs` / `search` / `component`，本技能不搬运
- 项目已 init：一切以项目 AGENTS.md 为准，本技能只在其缺失或用户问「Astryx 是什么/要不要用」时提供引导
