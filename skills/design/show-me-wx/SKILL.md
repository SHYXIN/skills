---
name: show-me-wx
description: 中文版可视化讲解技能——讲解当前话题时配随文视图（伪代码、调用树、组件树、文件树、diff、终端字符图），全部终端友好，不产 Mermaid 源码。终端宿主（Claude Code / CodeBuddy / Codex / Hermes Agent）优先用本技能而非 show-me。
---

帮用户看懂当前话题。跳过开场白，文字简短，选能说清关键点的最小视图。

讲解文字用中文；代码令牌（组件名、函数名、API、路径）保留英文原样，注释和示意文字译中文。

- 讲逻辑或算法 → 伪代码：

```text
on(save)
  if 内容没变
    返回缓存结果
  写入新内容
  返回新结果
```

- 讲运行时控制流 → 调用树：

```text
提交表单
  创建会话
    持久化提示词
    启动 agent
  跳转会话页
```

- 讲 UI 结构 → 组件树（标出关键的状态和模块边界）：

```tsx
<SessionPage> (apps/example/src/routes/session.tsx)
  useSessionEvents()
  <SessionToolbar>
    <RunSkillButton> (packages/ui)
```

- 讲文件职责或大重构 → 浅层文件树：

```text
src/
├── commands/       # 解析用户操作
├── sessions/       # 持有会话状态
└── transport/      # 发送 API 请求
```

- 讲交互、控制流或数据流 → **终端字符时序图**（用 tui-diagram 的盒线规范，禁止 Mermaid 代码块）：

```text
用户            界面           守护进程
  │              │              │
  ├──选命令─────▶│              │
  │              ├──发扩展提示─▶│
  │              │◀──流式结果──┤
  │◀──展示──────┤              │
```

**保真规则（硬性）**：字符图是 Mermaid 的替代排版，不是摘要。Mermaid 版里有的参与者、消息、自调用、alt/opt 分支、note，字符图必须一一对应，一个不许丢：

- 参与者数量 = 生命线数量。横向放不下（>80 列）时压缩参与者名或改纵向布局，不许砍参与者
- 自调用（Mermaid 的 `A->>A`）画成同一条生命线上的右出左回小环：

```text
  │              │              │
  │              ├──校验签名───┐
  │              │◀────────────┘    ← 自调用：右侧出、右侧回
  │              │
```

- `alt` / `opt` 分支用横贯全图的分隔行标注：

```text
  │              │              │
  ├─ alt [缓存未命中] ──────────
  │              ├──回源加载───▶│
  ├─ end ───────────────────────
  │              │◀──返回数据──┤
  │              │
```

- 超宽标签（如完整 URL）可截断为可辨识的短形式，但截断后仍要能对回原语义

排版硬规则（选型表、宽度对齐、80 列上限、字符白名单）直接引用 **tui-diagram 技能**的规范，不重复发明。

- 讲「改了什么」→ diff（周边形状已存在、重点是变化时用；diff 形态跟话题匹配）：

组件改动：

```diff
 <SessionPage>
   useSessionEvents()
   <SessionToolbar>
+    <RunSkillButton />
   <SessionTimeline>
+    <SkillResultCard />
```

文件布局改动：

```diff
 src/
 ├── commands/
+│   └── show-me.ts       # 展开斜杠命令
 ├── sessions/
-└── transport.ts
+└── transport/
+    ├── client.ts
+    └── stream.ts
```

调用树改动：

```diff
 提交表单
   创建会话
     持久化提示词
+    展开技能引用
     启动 agent
-  跳转会话页
+  跳转会话页
+    订阅事件
```

状态/控制流改动：

```diff
 on(save)
-  写入内容
+  if 内容没变
+    返回缓存结果
+  写入新内容
+  使缓存失效
```

- 大部分内容都是新的、省略上下文会掩盖归属或顺序、或用户需要可直接照抄的目标形状时 → 展示整块代码：

```ts
function expandSkill(command: string): string {
  const skillName = command.slice(1)
  return `use the ${skillName} skill`
}
```

- 视觉 UI、布局、状态对比、或字符图画不动的密集概念 → 写一个聚焦的 HTML 文件（图解、信息图或短幻灯片，哪个合适用哪个）。配色、字体、间距、组件贴近目标产品的风格；用真实标签和数据；兼顾桌面和移动。然后打开给用户：

```
Bash(open path/to/show-me-{描述}.html)
```

### 使用原则

每个视图放在它所支撑的那段短文字旁边。只保留回答当前问题所需的调用、文件、props、状态和边界。

可以只用一种，可以用几种，不太可能全用上。自己判断，别把用户淹没。
