---
name: agent-config-lint
description: 自动检查智能体配置（AGENTS.md、soul.md、SKILL.md、agent yaml 及脚本）里混入的决策背景、会话说明、闲聊等多余内容。派子 agent 按 agent-config-tidy 的判定规则扫描目标目录，产出只读差异报告；不改任何文件、不等用户确认。用于流程收尾处的无人值守检查；发现的问题要落地修改时用 /agent-config-tidy。
version: 0.1.0
---

# Agent Config Lint（配置克制自动检查）

对一套 agent 配置做**只读检查**：派子 agent 按 `/agent-config-tidy` 的判定规则
扫描目标目录，输出带建议动作的差异报告。与 `/agent-config-tidy` 的分工：

| | agent-config-lint（本技能） | agent-config-tidy |
|---|---|---|
| 交互 | 无人值守，跑完即出报告 | 每步等用户确认 |
| 写文件 | 永不 | 确认后改写 |
| 用途 | 流程收尾处的自动检查档（如 wx-flow 阶段 4） | 实际清理配置 |

## 输入

一个**目录**（整套 agent 配置的所在），结构无关。缺省时用当前任务涉及的
配置目录；用户给了路径就用用户的。文件发现范围与 `/agent-config-tidy`
一致：配置文档（AGENTS.md / soul.md / SKILL.md，大小写不敏感）、agent
定义（带 `interface:` 结构的 yaml）、脚本（注释与运行时输出）。

## 流程

1. **定目标**：确定要检查的目录，回显「将检查 <目录>」。
2. **派子 agent**：用 Agent 工具（Explore 类只读子 agent）发起**一次**检查，
   prompt 必须包含：
   - 目标目录绝对路径；
   - 指令：按候选路径**依次 Read** `agent-config-tidy/SKILL.md`，获取
     「判定规则 / 必须留 / 不确定时」全部规则——规则以该文件为唯一真相源，
     不要凭记忆复述或另立标准。候选路径（主会话按自身环境展开成绝对路径，
     第 1 条优先写本技能兄弟目录）：
     1. `<本技能所在 skills 根>/agent-config-tidy/SKILL.md`（兄弟目录）
     2. `~/.agents/skills/agent-config-tidy/SKILL.md`
     3. `~/.codebuddy/skills/agent-config-tidy/SKILL.md`
     4. `~/.claude/skills/agent-config-tidy/SKILL.md`
     候选逐个试，命中即停；全部失败 → 向主会话报错终止，不要降级为凭
     感觉扫描；
   - 产出要求：按文件列出手 findings——文件:行号、原文片段、命中哪条
     判定规则、建议动作（删除 / 改写 / 保留）、每条附一句理由；最后给一行
     总计（N 个文件，M 处 finding，其中明显多余 X 处、灰区 Y 处）。只报告，
     不修改任何文件。500 字以内，灰区单独标注。
3. **转呈报告**：把子 agent 报告原样/轻整理呈现给用户，标注来源是自动
   检查。**本技能到此结束**——不改文件、不追问、不替用户执行建议。
4. **出口提示**（固定一句话）：「要落地修改任意一条，跑
   `/agent-config-tidy <目录>`，逐条确认后改写。」

## 护栏

- 只读：本技能及子 agent 均不得写、删、改目标目录任何文件。
- 规则单源：判定规则永远现场 Read agent-config-tidy 的 SKILL.md，不内嵌副本。
- 不阻塞：子 agent 不可用（工具受限等）时，明确报告「无法派发子 agent，
  请手动跑 /agent-config-tidy」，不要静默跳过或主会话代跑（主会话代跑会
  污染编排上下文）。
- 零 findings 也是有效结论：明确说「未检出多余内容」，不强行凑报告。
