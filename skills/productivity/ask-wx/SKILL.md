---
name: ask-wx
description: "问该用哪个技能或流程。A router over the skills in this repo's main flow. 当用户说「该用哪个」「ask-wx」「从哪开始」「这个情况用什么技能」，或面对多个相似技能拿不准时触发。"
disable-model-invocation: true
---

# Ask WX

你不会记得每一个技能，所以问。

在陈述某个技能做什么、或建议跳过某步之前，先读那个技能的 SKILL.md：这里的摘要只用于定位。

一个 **flow** 是穿过这些技能的一条路径。大多数工作走一条**主流**（idea → ship）；**支线**喂料给它；**纠错层**在流程里任何时刻可喊；其余是独立技能。主流中后段直接沿用 mattpocock/skills 的技能（本仓库与它配套安装），本仓库自有技能接管入口打磨、验证与复盘。

## 主流：想法 → 交付

大多数工作走的路线。你有一个想法，想把它做出来。

1. **入口：打磨想法**。这是本图与 ask-matt 分叉的地方，也是路由的核心裁决区。按三条判据裁决，一轮问一条（遵循 grill-one 风格）：
   - **要沉淀吗？**——要把术语/决策落盘（ADR、术语表）→ with-docs 系；不要，临时打磨 → `/grill-one`。
   - **跟谁家走？**——这次工作将继续走 matt 的 spec/tickets 主线，且希望他的下游技能读到他的文档格式 → matt 的 `/grill-with-docs`；自己的小项目或独立打磨 → 本仓库的 grill-one 系。
   - **认知负载要多大？**——要快、单问 → grill-one 系；可以慢、多问深挖 → matt 的多问版。

   裁决结果：

   - **`/grill-one`**：快、单问、无文档沉淀。对自己已经比较清楚的需求，最快的入口。
   - **`/grill-one-with-docs`**：同样单问，边问边把术语与决策写进术语表和 ADR。要纸面痕迹时的最轻选择。
   - matt 的 **`/grill-with-docs`**：多问、有状态、GLOSSARY + ADR 齐全，且他的 `/to-spec` 等下游原生读它的产物。确定走 matt 全流程时用这个。
   - **共识已定、进入技术选型** → **`/consensus-tech-research`**：比较库/框架，产出有证据的选型报告，喂给 `/to-spec`。

2. **主流中后段（matt 系原样）**：`/to-spec` → `/to-tickets` → `/implement`（每票间 `/clear`）→ `/tdd` → `/code-review` → `/pr`。分支逻辑（多会话构建与否、`/implement-spec` 编排）见 ask-matt 的地图，此处不重复。

### Context hygiene

与 matt 版相同：入口打磨与 spec/tickets 保持在一个不间断的上下文窗口里（`/to-tickets` 之前不要 compact 或 clear），每个 `/implement` 从票据重新开始。上限同样是 **smart zone**（~150k tokens）。

## 验证层（本仓库自有，matt 版没有）

实现完成后，闭环前多一步 matt 没有的验证：

- **`/verify-manual-after-implementation`**：生成可人工打开网站/API/CLI 执行的验收手册。
- **`/verify-run`**：opencli 驱动的自动验证执行器。三档输入自动探测：有验收手册照单执行、有仓库无手册轻量审计现场推导、只有 URL 探索式驱动。
- **`/verify-replay`**：verify-run 全绿后，把执行过程固化为 YAML 回放清单，供后续快速重放。

顺序：生成手册（或直接给仓库）→ verify-run → 全绿后可选 verify-replay。

## 复盘（收尾）

- **`/retro`**（matt）：绑定他的 code-review 链，直接读当前 harness 的会话记录。
- **`/retro-wx`**（本仓库）：数据层走 agent-sessions（跨五源检索历史会话），落点含个人 skills 仓库提议与 auto-memory。

默认用 `/retro`（当前会话、matt 主线收尾）；要跨 harness 翻历史会话、或想把发现沉淀成自己的 skill / memory 时用 `/retro-wx`。

## 纠错层（任何时刻可喊）

流程里卡住时的急救出口。路由器不主动推荐，但地图上要能看见：

- **`/where-am-i-wx`**：迷路了，画出当前任务/对话的决策地图——走到哪了、还有什么路、每步该懂什么。
- **`/wait-what-wx`**：上一句没听懂，重讲一遍。用在工作中间、任何其他技能内部。
- **`/source-trace-wx`**：追这条回答的原始依据与出处，先挖对话里真实用过的来源，再对无出处的 claim 补查一手来源。
- **`/next-step`**：做完一段或卡住时，列出带价值/代价/何时选的下一步并标出性价比最高者。

## 支线（喂料给入口，不是主线）

一个会生成工作、然后汇入主流的起点情形：

- **要调研一个问题** → **`/research-wx`**：后台 agent 针对一手来源调研，产出带出处的 Markdown 存进仓库。它产出的是带进入口打磨的材料，不是替代品。
- **上下文丢了/在别的会话里** → **`/find-session`**：跨五源找历史会话并给出 resume 命令；找回上下文后回到入口打磨。

## 不在本图内

teaching（学习类）、design（图表类）、oss 系（开源贡献）、setup 系（环境配置）、cn-brief-wx / ai-daily-brief（简报类）等与工程主线无关的技能，不在路由范围。需要时直接按名调用。
