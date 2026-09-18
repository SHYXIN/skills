---
name: grill-one-with-docs
description: 单问版 grill-with-docs。把计划/设计通过一问一答打磨清楚，同时随手沉淀文档（ADR 与术语表）。每轮只问一个问题（调 grill-one），文档沉淀（调 domain-modeling）。用户手动调用（/grill-one-with-docs）。
disable-model-invocation: true
---

依次调用两次 Skill 工具：

1. **`grill-one`** — 单问版设计访谈：一轮只问一个问题，把模糊想法磨成共享理解
2. **`domain-modeling`** — 访谈中术语、边界场景、决策一但成形，立刻写进术语表（CONTEXT.md）与 ADR

与原版 `grill-with-docs`（grilling 多问版）的差异只在节奏：这里一轮一问、更慢更聚焦；文档沉淀职责完全一致。两个被调用的 skill 需已安装（本市场 `productivity/grill-one` + domain-modeling，见仓库 install.sh 说明）。
