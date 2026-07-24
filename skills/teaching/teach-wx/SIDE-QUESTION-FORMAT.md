# Side Question HTML 格式

旁路问答放在 `./side-questions/`，文件名按顺序递增：

```text
0001-slug.html
0002-slug.html
```

旁路问答是学习中途的临时问题。它要被认真回答，但默认不改变主线大纲，也不写入 lesson。

## 内容结构

1. 问题原文
2. 简短回答
3. 为什么是这样
4. 必要时的字符图
5. 和主线的关系
6. 是否调整大纲：默认“不调整”

## 规则

- 不链接进主线 lesson。
- 不合并进主线 lesson。
- 用户明确要求“加入大纲/单独开一节/调整路线”时，才改变主线。
- 回答仍然遵守中文优先、讲为什么、少堆术语的规则。

## 推荐骨架

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{问题短标题}</title>
  <style>
    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.7; max-width: 780px; margin: 40px auto; padding: 0 20px; color: #1f2937; }
    h1, h2 { line-height: 1.3; }
    .answer { background: #f3f4f6; padding: 14px 16px; border-radius: 8px; }
    pre { background: #111827; color: #f9fafb; padding: 16px; border-radius: 8px; overflow-x: auto; }
  </style>
</head>
<body>
  <h1>{问题原文}</h1>

  <h2>简短回答</h2>
  <p class="answer">{直接回答}</p>

  <h2>为什么</h2>
  <p>{原因链}</p>

  <h2>字符图</h2>
  <pre><code>{可选 ASCII 图}</code></pre>

  <h2>和主线的关系</h2>
  <p>{相关但不改变主线 / 需要用户确认后才调整}</p>

  <h2>是否调整大纲</h2>
  <p>默认不调整。</p>
</body>
</html>
```
