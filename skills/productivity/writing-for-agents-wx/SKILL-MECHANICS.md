# Skill 机制（skill mechanics）

本文件是 [`writing-for-agents`](SKILL.md) 的 skill 专属分支：当文档本身是一个 skill 时，什么会变——frontmatter、调用方式选择、路由类 skill。其余所有写作内容都在 `SKILL.md` 的通用参考里。

## 调用（invocation）

两种选择，交易那两种负担：

- 一个 **model-invoked（模型调用）** skill 保留 `description`，让 agent 能自主触发它——其他 skill 也能触达它。你仍然可以打它的名字：模型调用永远*包含*人的触达；一个 description 只会增加 agent 的发现能力，从不会去掉人的。`description` 是 skill 顶层级的上下文指针，被强制常驻加载——用永久的上下文负担换取可发现性。一个内容全是参考的 model-invoked skill 也是共享参考的一个家：另一个 skill 可以调用它，所以多个 skill 都需要的参考就住在一处。机制：省略 `disable-model-invocation`，并写一个带触发分支的、面向模型的 description（SKILL.md 里的指针写法规则完全适用）。
- 一个 **user-invoked（用户调用）** skill 把 `description` 从 agent 的触达里剥掉：只有人打名字才能调用它，别的 skill 都不行。零上下文负担，但它花认知负担——你就是那个必须记住它存在的索引。机制：设 `disable-model-invocation: true`；`description` 变成面向人的——一句话总结，触发词列表剥掉。

只在 agent 必须自己够到这个 skill、或另一个 skill 必须够到它时才选模型调用。如果它永远只靠手点触发，就做成 user-invoked，不花任何上下文负担。

两个 user-invoked skill 都需要、却谁都放不下的共享参考——没有 description，谁都触发不了谁。把它推到 skill 系统之外的一个普通文件：任何 skill 都能指向的外部参考。

## 按调用拆分（splitting by invocation）

拆分里的「按调用」这一刀（「按序列」那刀在 SKILL.md 里）：当你有一个独特的引导词、应当单独触发它——一个你真的在 prompt 里用的触发词——或另一个 skill 必须够到它时，就拆出一个 model-invoked skill。你要为那个新的常驻 description 付上下文负担，所以那种独立触达必须值得。

## 路由类 skill（router skills）

当 user-invoked skill 多到你记不住时，那种堆起来的认知负担靠一个 **router skill（路由类 skill）** 治好：一个 user-invoked skill，它点名其他的、以及何时去够哪一个，这样人只要记一个 skill 而不是很多个。它只能提示，从不能触发它们：user-invoked skill 没有 description，所以除了人谁都够不到它们。
