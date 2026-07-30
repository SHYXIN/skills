# 教学工作区初始化

新主题开始时，在当前目录初始化学习区。缺什么补什么，不覆盖已有内容。

## 目录

```text
.
├── MISSION.md
├── OUTLINE.md
├── RESOURCES.md
├── GLOSSARY.md
├── NOTES.md
├── lessons/
├── learning-records/
├── side-questions/
├── examples/
│   ├── README.md
│   └── .gitignore
└── assets/
    └── lesson.css
```

## 初始化规则

- `MISSION.md`：先问清学习目标，再按 `MISSION-FORMAT.md` 写入。
- `OUTLINE.md`：先给 2-4 个可完成学习单元，再按 `OUTLINE-FORMAT.md` 写入。
- `RESOURCES.md`：没有资源时也创建，标注“待补充”。
- `GLOSSARY.md`：没有术语时也创建，标注“待积累”。
- `NOTES.md`：记录用户偏好；没有偏好时写“暂无”。
- `lessons/`：主线 HTML lesson 存放处。
- `learning-records/`：重要理解、误区修正、目标变化的记录。
- `side-questions/`：有长期价值的旁路问答。
- `examples/`：技术 lesson 配套的小示例和共享运行环境。格式见 `EXAMPLE-FORMAT.md`。
- `examples/README.md`：说明共享环境和示例运行规则。
- `examples/.gitignore`：忽略 `.venv/`、`node_modules/`、`.env`、构建产物和 Python 缓存。
- `assets/lesson.css`：主线 lesson 共享样式。HTML lesson 默认引用它。

## assets/lesson.css 最小要求

采用 Tufte-ish 技术讲义风格：克制、清晰、适合长期复习和打印。

必须包含这些样式能力：

- 白底，正文栏宽度约 760-820px，页面留白充足。
- 使用系统 serif 或 system-ui 字体均可，但正文必须易读；不要使用外部字体或 CDN。
- 标题层级清楚，`h2` 不要只靠大色块区分。
- `.eyebrow` 用于 lesson 编号、主题、节奏和预计阅读时间。
- `.lede` 用于一句话结论，克制强调，不用大面积彩色背景。
- `.toc` 用于页内目录，链接到各章节锚点。
- `pre` 支持 ASCII 图横向滚动；背景可以浅色或深色，但不能压过正文。
- `.caption` 用于解释图表，不要和正文抢层级。
- `.question-block` 用于自检题，边框或浅色底即可。
- `.path`、`code`、`.links` 有统一样式。
- `@media print` 中隐藏不必要装饰，避免在代码块和自检题内部断页。
- 不做 dashboard/card UI，不使用大面积彩色块，不做炫技动画。

推荐 `assets/lesson.css` 起点：

```css
:root {
  color-scheme: light;
  --text: #1f2933;
  --muted: #687385;
  --rule: #d8dee8;
  --soft: #f6f7f9;
  --accent: #8a5a2b;
  --code-bg: #f3f5f7;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  padding: 48px 22px 64px;
  color: var(--text);
  background: #fff;
  font-family: ui-serif, Georgia, "Times New Roman", "Noto Serif SC", serif;
  line-height: 1.72;
}

.lesson {
  max-width: 800px;
  margin: 0 auto;
}

.lesson-header {
  padding-bottom: 22px;
  border-bottom: 1px solid var(--rule);
}

.eyebrow {
  margin: 0 0 10px;
  color: var(--muted);
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.86rem;
}

h1 {
  margin: 0;
  font-size: 2.15rem;
  line-height: 1.18;
  font-weight: 650;
}

.lede {
  margin: 18px 0 0;
  padding-left: 16px;
  border-left: 3px solid var(--accent);
  font-size: 1.08rem;
}

.toc {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin: 22px 0 34px;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.92rem;
}

.toc a,
.links a {
  color: #2f5d7c;
  text-decoration-thickness: 1px;
  text-underline-offset: 3px;
}

section {
  margin: 34px 0;
}

h2 {
  margin: 0 0 12px;
  font-size: 1.28rem;
  line-height: 1.3;
}

p { margin: 0 0 14px; }

pre {
  margin: 16px 0 10px;
  padding: 16px 18px;
  overflow-x: auto;
  background: var(--code-bg);
  border: 1px solid var(--rule);
  border-radius: 6px;
  line-height: 1.45;
}

code,
.path {
  font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
  font-size: 0.94em;
}

.path {
  padding: 1px 4px;
  background: var(--soft);
  border-radius: 4px;
}

.caption {
  color: var(--muted);
  font-size: 0.94rem;
}

.question-block {
  padding: 18px 20px;
  background: var(--soft);
  border: 1px solid var(--rule);
  border-radius: 6px;
}

.lesson-footer {
  margin-top: 42px;
  padding-top: 22px;
  border-top: 1px solid var(--rule);
}

.links {
  padding-left: 20px;
}

@media print {
  body { padding: 0; }
  .lesson { max-width: none; }
  .toc { display: none; }
  pre,
  .question-block { break-inside: avoid; }
}
```
