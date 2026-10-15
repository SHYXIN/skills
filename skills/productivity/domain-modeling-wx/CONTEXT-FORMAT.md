# CONTEXT.md Format

`CONTEXT.md` 是领域词汇的**关系层**：术语间关系、示范对话、歧义裁决。术语定义一律不放这里——那属于 `GLOSSARY.md`。

## Structure

```md
# {Context Name}

词汇定义见 [GLOSSARY.md](./GLOSSARY.md)。本文件只记录术语间的关系、澄清性对话与歧义裁决。

## Relationships

- An **Order** produces one or more **Invoices**
- An **Invoice** belongs to exactly one **Customer**
- A **Shipment** references exactly one **Order**; cancelling the Order cancels its Shipments

## Example dialogue

> **Dev:** "When a **Customer** places an **Order**, do we create the **Invoice** immediately?"
> **Domain expert:** "No — an **Invoice** is only generated once a **Fulfillment** is confirmed."

## Flagged ambiguities

- "account" 被同时用于指 **Customer** 和 **User** — 裁决：是两个概念，"account" 进各术语的 _Avoid_ 列表
- "cancellation" 一度指整单取消 — 裁决：支持部分取消；整单取消是部分取消的特例
```

## Rules

- **术语定义只进 GLOSSARY.md。** 本文件提到术语时加粗（**Order**），不重复定义。发现自己在 CONTEXT.md 里写"**X**：一句定义"——停下来，那句定义属于 GLOSSARY.md。
- **Relationships 写业务断言，不写实现。** "Order 产生 Invoice" 可以；"Order 表有 invoice_id 外键" 不行——那是实现细节。
- **对话示例服务边界澄清。** 只留真正澄清了概念间界限的对话轮次，寒暄和过程全删。术语敲定后对话里的旧用词已无意义，示例要按最终术语写。
- **歧义必须带裁决。** Flagged ambiguities 每条都要有结论（裁决了什么、落在了哪个术语的哪个定义/关系上）；没有裁决的疑惑用对话继续磨，不进文件。
- **惰性创建。** 第一条关系/裁决/对话值得记时才建本文件；纯术语讨论不留空壳。
