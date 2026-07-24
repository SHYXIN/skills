# Lesson HTML 格式

主线 lesson 放在 `./lessons/`，文件名按顺序递增：

```text
0001-slug.html
0002-slug.html
```

## 内容结构

每个 HTML lesson 默认包含：

1. 标题
2. 一句话结论
3. 它到底是什么
4. 为什么会有它
5. 字符流程图
6. 小故事或类比
7. 最小例子
8. 常见误解
9. 用自己的话复述
10. 下一步

## HTML 要求

- 中文优先，专业名词保留英文或缩写。
- 使用简单、可打印的样式。
- 字符图放进 `<pre>`。
- 不写官方文档腔。
- 不把旁路问答放进 lesson。
- 不依赖外部 CDN。HTML 文件应能单独打开。

## 推荐骨架

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{标题}</title>
  <style>
    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.7; max-width: 860px; margin: 40px auto; padding: 0 20px; color: #1f2937; }
    h1, h2 { line-height: 1.3; }
    .summary { font-size: 1.15rem; font-weight: 600; background: #f3f4f6; padding: 14px 16px; border-radius: 8px; }
    pre { background: #111827; color: #f9fafb; padding: 16px; border-radius: 8px; overflow-x: auto; }
    code { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }
  </style>
</head>
<body>
  <h1>{标题}</h1>
  <p class="summary">{一句话结论}</p>

  <h2>它到底是什么</h2>
  <p>{白话解释}</p>

  <h2>为什么会有它</h2>
  <p>{从痛点讲原因}</p>

  <h2>字符流程图</h2>
  <pre><code>{ASCII 图}</code></pre>
  <p>{解释图中的箭头}</p>

  <h2>小故事</h2>
  <p>{类比或故事}</p>

  <h2>最小例子</h2>
  <p>{必要例子}</p>

  <h2>常见误解</h2>
  <ul>
    <li>{误解 + 纠正}</li>
  </ul>

  <h2>用自己的话复述</h2>
  <p>{一个复述题或应用题}</p>

  <h2>下一步</h2>
  <p>{建议的下一个主线节点}</p>
</body>
</html>
```
