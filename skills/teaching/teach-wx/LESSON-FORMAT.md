# Lesson HTML 格式

主线 lesson 放在 `./lessons/`，文件名按顺序递增：

```text
0001-slug.html
0002-slug.html
```

HTML lesson 是主线讲课的默认产物。每个主线学习单元对应一个可复习页面；澄清问题和短旁路问题不单独生成 lesson。

## UI 方向

采用 Tufte-ish 技术讲义风格：白底、窄正文栏、强排版层级、克制颜色、适合阅读和打印。不要做 dashboard/card UI，不要用大面积彩色块，不要把页面做成 Markdown 默认样式。

每个 lesson 应该像一页可长期复习的技术讲义：有标题、元信息、目录、主体解释、代码或字符图、自检题、底部导航和参考链接。

## 内容结构

每个 HTML lesson 默认包含：

1. 标题
2. lesson 元信息：编号、主题、节奏、预计阅读时间
3. 一句话结论
4. 页内目录
5. 为什么需要它
6. 它是什么
7. 直觉类比
8. 核心结构或流程图
9. 最小例子
10. 常见误解和边界
11. 示例项目
12. 自检问题
13. 下一步和相关链接

每节主线 lesson 默认包含一个短的“直觉类比”。类比只负责建立直觉，不代替定义；必须说明它哪里像、哪里不像，并立刻回到技术结构。fast 模式可以压缩成一句话，normal/slow 模式可以多解释一点。不要写成长故事。扩展阅读是可选项。

## HTML 要求

- 中文优先，专业名词保留英文或缩写。
- 使用简单、可打印的共享样式。
- 字符图放进 `<pre><code>`。
- 不写官方文档腔，也不过度口语化。
- 不把旁路问答放进 lesson。
- 不依赖外部 CDN。HTML 文件应能单独打开。
- 优先复用 `../assets/lesson.css`；第一次生成 lesson 时创建共享样式。
- 每个主要章节使用稳定 `id`，目录通过锚点跳转。
- 代码路径、命令、文件名使用统一的 `.path` 或 `code` 样式。
- 技术主题、代码库和 GitHub 仓库类 lesson 默认包含“示例项目”章节，链接到 `../examples/000N-{slug}/`。
- 示例项目章节必须写清：目标、路径、运行命令、预期结果、观察重点。
- 如果存在上一课、下一课、`OUTLINE.md`、`REPO-BRIEF.md` 或参考资料，在页尾提供链接。

## 推荐骨架

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{标题}</title>
  <link rel="stylesheet" href="../assets/lesson.css">
  <style>
    /* 只放本节课独有的少量样式；通用样式放在 ../assets/lesson.css。 */
  </style>
</head>
<body>
  <article class="lesson">
    <header class="lesson-header">
      <p class="eyebrow">Lesson {编号} · {主题} · {fast/normal/slow} · {预计阅读时间}</p>
      <h1>{标题}</h1>
      <p class="lede">{一句话结论}</p>
    </header>

    <nav class="toc" aria-label="本节目录">
      <a href="#why">为什么需要它</a>
      <a href="#what">它是什么</a>
      <a href="#analogy">直觉类比</a>
      <a href="#map">核心结构</a>
      <a href="#example">最小例子</a>
      <a href="#limits">误解和边界</a>
      <a href="#demo">示例项目</a>
      <a href="#check">自检问题</a>
      <a href="#next">下一步</a>
    </nav>

    <section id="why">
      <h2>为什么需要它</h2>
      <p>{从问题背景讲原因}</p>
    </section>

    <section id="what">
      <h2>它是什么</h2>
      <p>{准确、克制的解释}</p>
    </section>

    <section id="analogy">
      <h2>直觉类比</h2>
      <p>{短类比：它像什么}</p>
      <p class="caption">{边界：哪里像，哪里不像。类比不是定义。}</p>
    </section>

    <section id="map">
      <h2>核心结构</h2>
      <pre><code>{ASCII 图}</code></pre>
      <p class="caption">{用 2-4 句话解释图中的箭头和边界}</p>
    </section>

    <section id="example">
      <h2>最小例子</h2>
      <p>{必要例子}</p>
    </section>

    <section id="limits">
      <h2>常见误解和边界</h2>
      <ul>
        <li>{误解 + 纠正}</li>
      </ul>
    </section>

    <section id="demo">
      <h2>示例项目</h2>
      <p>{这个示例验证什么机制}</p>
      <ul>
        <li>路径：<a href="../examples/000N-{slug}/"><code>../examples/000N-{slug}/</code></a></li>
        <li>运行：<code>{命令}</code></li>
        <li>预期结果：{看到什么输出或现象}</li>
        <li>观察重点：{运行后应该回看 lesson 的哪个机制}</li>
      </ul>
    </section>

    <section id="check" class="question-block">
      <h2>自检问题</h2>
      <p>{一个复述题、判断题或应用题}</p>
    </section>

    <footer id="next" class="lesson-footer">
      <h2>下一步</h2>
      <p>{建议回到 OUTLINE.md 的哪个节点}</p>
      <ul class="links">
        <li><a href="../OUTLINE.md">回到大纲</a></li>
        <li><a href="{上一课路径}">上一课</a></li>
        <li><a href="{下一课路径}">下一课</a></li>
        <li><a href="../REPO-BRIEF.md">仓库导览</a></li>
      </ul>
    </footer>
  </article>
</body>
</html>
```

如果某个链接不存在，不要生成空链接；直接省略该项。
