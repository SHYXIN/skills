---
name: webshot
description: 把 HTML（文件/字符串）或 URL 用系统已有浏览器（Edge/Chrome/Chromium/Brave 自动探测）无头渲染成 PNG 截图。用户说「截图」「HTML转图片」「网页截图」「把这个页面出成图」「README 配图」「生成分享图」「图表截成 PNG」时使用。零依赖零安装——只探测本机已有浏览器，全没有才报安装指引。支持宽高、2x 缩放、等待 JS 渲染（图表类页面）。
---

# webshot — HTML / URL → PNG 截图

把 HTML 或网页用本机已有的 Chromium 系浏览器无头渲染成 PNG。

## 何时用

- 给 README / 文档 / issue 配一张「渲染结果」图（终端面板、图表、卡片、报告）
- 把一段 HTML（比如 agent 刚生成的可视化、表格、SVG 包装页）固化成图片交付
- 网页整页快照存档

不要用于：需要交互/滚动的长页面分段（每次只截一个视口）；需要透明背景的场合（Chromium 无头截图背景是白的，给 body 设深色底）。

## 用法（一行命令）

优先用技能自带脚本（已内置浏览器探测链与参数校验）：

```powershell
# HTML 文件 → PNG
& "<技能目录>/scripts/webshot.ps1" -Html C:\tmp\page.html -Out page.png   # <技能目录> = 本 SKILL.md 所在目录

# URL → PNG（宽高自定义）
& ".../webshot.ps1" -Url https://example.com -Out site.png -Width 1280 -Height 800

# HTML 字符串 → PNG（脚本自动落临时文件）
& ".../webshot.ps1" -HtmlString '<html><body><h1>hi</h1></body></html>' -Out hi.png

# 动态图表页：等 JS 渲染 3 秒再截
& ".../webshot.ps1" -Html chart.html -WaitMs 3000 -Width 1024 -Height 640
```

参数：`-Out`（默认 webshot.png）· `-Width 760` · `-Height 470` · `-Scale 2`（README/文档用 2x，快速预览 1x）· `-WaitMs 0`。

不想用脚本时，核心命令一行也能拼（Edge/Chrome 通用）：

```sh
msedge --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
  --window-size=760,470 --screenshot=out.png "file:///C:/abs/path/page.html"
```

## 探测链

Edge（出厂自带，×3 常见路径）→ Chrome（×3）→ Chromium → Brave → PATH 上的同名可执行文件。全找不到才报错，报错里带安装指引（`winget install --id Microsoft.Edge`）。

## 坑位

1. **PowerShell 会吃内嵌双引号**：HTML/JSX 里带引号的字符串，用单引号包裹参数，或走 `-HtmlString`/`-Html` 让脚本落临时文件——不要现场拼带引号的长参数
2. **`file:///` 必须三斜杠 + 正斜杠 + 绝对路径**：`file:///C:/abs/page.html`，反斜杠和相对路径都会静默失败
3. **渲染即截**：图表库/懒加载/字体加载需要时间，给 `-WaitMs 3000`（底层是 `--virtual-time-budget`）
4. **README 用图给 `-Scale 2`**：2x 在 GitHub/npm 页面上才清晰；快速自检用 1x 省体积
5. **写 PNG 偶发 EIO（Win32 1175）**：手动重跑同一条命令一次即过，不是浏览器坏了（脚本无内置重试）
6. **深色截图给 body 设背景色**：无头截图不继承系统深色模式，`<body style="background:#0d1117">`
7. **CJK 无需额外配置**：Windows 系统字体直接可用；Linux 无头机器注意装 noto-cjk
8. **验证输出**：截图后检查文件存在且 >0 字节（脚本已内置）

## 场景速查

终端面板类截图：`-Html panel.html -Out panel.png -Scale 2`。
