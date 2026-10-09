---
name: excalidraw-diagram
description: "手绘风 Excalidraw 图生成技能——把自然语言或结构化需求变成 .excalidraw 文件与可分享链接。基于 excalidraw-cli（npx 首次自动下载）生成流程图、关系图、思维导图、架构图、数据流图、泳道图、类图、时序图、ER 图共 9 类，内置「图要论证不是陈列」方法论与配色单一真源。仅显式调用 /excalidraw-diagram 时触发。"
level: 2
---

# Excalidraw Diagram（手绘风图生成）

把需求变成一份 `.excalidraw` 文件，需要时再上传成 excalidraw.com 可分享链接。图是**手绘风**的——粗糙线条、圆角、手写字体，适合架构图、流程说明、方案对比这类要"讲清楚一件事"的场合。

## 三个技能的分工（先认清产出物）

| 技能 | 产出物 | 用在哪 |
|------|--------|--------|
| `visualise` | 对话内联 SVG / HTML | GUI 宿主里即时渲染、可交互 |
| `tui-diagram` | 终端 Unicode 字符画 | 纯终端宿主，不依赖渲染器 |
| **本技能** | **`.excalidraw` 文件 + 分享链接** | 要一个能存进仓库、能发链接给别人打开编辑的文件 |

**只做第三件事。** 用户要的是"对话里看一眼"就用 `visualise`，要"终端里看"就用 `tui-diagram`，要"一个文件 / 一条链接"才用本技能。

## 触发规则

- **仅在本技能被显式调用（`/excalidraw-diagram`）时执行。** 不要在普通对话里主动画图——内联出图是 `visualise` 的活。
- 调用时可带主题（如 `/excalidraw-diagram 认证流程`），也可不带：不带时回顾当前对话，找出最该画的内容。
- 一次调用产出一份图。

## 首次使用：CLI 自动就绪（无需手动安装）

本技能依赖 [`excalidraw-cli`](https://github.com/ahmadawais/excalidraw-cli)。**不需要预先全局安装**——统一用 `npx` 调用，首次运行会自动下载并缓存，之后秒开：

```bash
npx -y excalidraw-cli@0.0.2 create --json '[...]' -o diagram.excalidraw
```

- **版本锁定 `@0.0.2`**：本技能只用这个已验证版本，避免上游早期版本（当前仅 `0.0.x`）行为漂移把出图弄挂。升级需手动改这里。
- 若 `npx` 不可用（无 Node ≥18），先提示用户安装 Node，再继续。
- 检查命令：`npx -y excalidraw-cli@0.0.2 --help`

## 工作流（三步）

1. **选图型**：分析需求，从 [references/diagram-types.md](./references/diagram-types.md) 的 9 类里选最合适的一类（依据见每类"何时用"）。
2. **排元素**：按 [references/methodology.md](./references/methodology.md) 的布局/字号/间距规则 + [references/color-palette.md](./references/color-palette.md) 的配色，产出元素 JSON。**先读配色调色板，它是颜色的单一真源。**
3. **出图**：用 [references/cli-usage.md](./references/cli-usage.md) 的命令生成文件；用户要链接时再 `export`。

```bash
# 1) 出文件
npx -y excalidraw-cli@0.0.2 create --json '[ {cameraUpdate}, {元素...} ]' -o diagram.excalidraw

# 2) 要分享链接时（会加密上传到 excalidraw.com）
npx -y excalidraw-cli@0.0.2 export diagram.excalidraw
# → https://excalidraw.com/#json=xxx,yyy
```

## 核心原则（一句话）

**图要"论证"，不是"陈列信息"。** 形状本身要承载含义——因果用箭头指向、层级用嵌套区域、对比用并列色块。不要只是把文字塞进方框。详见 [references/methodology.md](./references/methodology.md)。

## 参考文件

- [references/cli-usage.md](./references/cli-usage.md) — CLI 全部命令、元素格式、label 简写、默认值、checkpoint
- [references/diagram-types.md](./references/diagram-types.md) — 9 类图型的选型与骨架
- [references/methodology.md](./references/methodology.md) — 「图要论证」方法论、布局、字号、间距、明暗模式
- [references/color-palette.md](./references/color-palette.md) — 配色单一真源（浅色 + 深色）

## 注意事项

- **隐私**：`export` 会把图上传到 excalidraw.com。涉密图只 `create` 出本地 `.excalidraw` 文件，不要 `export`。
- 不要写 emoji 进图文字——Excalidraw 手写字体渲染不出来。
- JSON 里不要有注释、尾逗号，否则 `create` 会报 `Invalid JSON`。
