---
name: domain-modeling-wx
description: 构建并打磨项目的领域模型。讨论代码库术语、写/改 GLOSSARY.md（术语）、CONTEXT.md（关系/对话/歧义）或记录 ADR 时使用。GLOSSARY.md 与 matt 的 domain-modeling 完全兼容；CONTEXT.md 是 wx 扩展层。
---

# Domain Modeling WX

在设计过程中主动构建并打磨项目的领域模型。这是*主动*纪律：挑战术语、发明边界场景、在结论成形的那一刻写下来。（只是*读* `GLOSSARY.md` 查词汇不算本技能：那是一行习惯，任何 skill 都会做。本技能用于你*正在修改*模型而非消费它的时候。）

## 文件分工（唯一写入点原则）

| 文件 | 内容 | 规则 |
|---|---|---|
| `GLOSSARY.md` | 纯术语：一句定义 + `_Avoid_` 别名 | 术语**唯一**写入点。格式与上游 domain-modeling 完全一致，见 [GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md) |
| `CONTEXT.md` | 关系层：`## Relationships`（术语间关系）、`## Example dialogue`（示范对话）、`## Flagged ambiguities`（歧义及裁决） | **永不写术语定义**。开头引用 `GLOSSARY.md`。格式见 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md) |
| `docs/adr/` | 决策记录 | 三条件全满足才建，见 [ADR-FORMAT.md](./ADR-FORMAT.md) |

核心纪律：**一个事实只写在一个文件里**。术语定义写 GLOSSARY.md 后，CONTEXT.md 里提到该术语只加粗引用、不重复定义；两文件间不复制内容，杜绝漂移。

## 文件结构

单 context 仓库（最常见）：

```
/
├── GLOSSARY.md          ← 术语层（有术语才建）
├── CONTEXT.md           ← 关系层（有关系/歧义/对话才记；可不存在）
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

多 context 仓库：根目录 `GLOSSARY-MAP.md` 指向各 context 的 `GLOSSARY.md`（结构见 GLOSSARY-FORMAT.md 末节）。每个 context 目录内可有自己的 `CONTEXT.md`。

**惰性创建**：有东西可写才建文件。第一个术语敲定 → 建 `GLOSSARY.md`；第一条关系/歧义/对话值得记 → 建 `CONTEXT.md`。小的讨论不该留下空壳文件。若项目已有旧版富格式 `CONTEXT.md`（含 Language 节），续写时把 Language 节迁入 `GLOSSARY.md`，CONTEXT.md 只留关系层。

## 会话中

### 对照 glossary 挑战

用户用的术语与 `GLOSSARY.md` 既有定义冲突时，立即指出："你的 glossary 里 'cancellation' 定义是 X，但你现在像是 Y 的意思。到底是哪个？"

### 打磨模糊语言

用户用词含糊或一词多义时，提出精确的规范术语："你说 'account'：是指 Customer 还是 User？这是两个东西。"

### 用具体场景压测

讨论到领域关系时，用具体场景压测：发明探边界的场景，逼用户把概念间界限说清楚。压测中确认的关系 → 写入 CONTEXT.md 的 Relationships。

### 与代码交叉验证

用户陈述某机制如何工作时，查代码是否同意。发现矛盾就摆出来："代码是整单取消，你刚说可以部分取消。哪个对？"

### 就地更新 GLOSSARY.md

术语敲定立即更新 `GLOSSARY.md`，不要攒批。格式见 [GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md)。

`GLOSSARY.md` 里不得出现任何实现细节。不把它当 spec、草稿纸或实现决策仓库——它是词汇表，仅此而已。

### 就地更新 CONTEXT.md

压测确认了一条术语间关系、裁决了一处歧义、或对话本身澄清了概念边界 → 立即写入 `CONTEXT.md` 对应节，同样不攒批。格式见 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)。

### 节制地提供 ADR

三条全中才提议建 ADR：

1. **难逆转**：日后改主意的代价实打实
2. **没上下文会费解**：未来读者会问"为什么这么做？"
3. **真实权衡的结果**：确有备选项，且因具体理由选了其一

缺任何一条就不建。格式见 [ADR-FORMAT.md](./ADR-FORMAT.md)。
