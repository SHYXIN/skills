---
name: guided-book-reader
description: 带读英文技术书 PDF 的工作流 skill。用于用户想认真阅读一本英文技术书、论文集或长篇 PDF，并希望 Codex 先读取和解析 PDF、转成 txt、按章节拆分，然后用中文为主的 teach 风格逐小节讲解、出选择题检查理解，并把每节阅读总结追加到 notes markdown。
---

# Guided Book Reader

## 目标

把一本英文技术书 PDF 变成可持续阅读的学习项目：

1. 读取 PDF。
2. 转成全文 txt。
3. 按章节拆分成独立 txt。
4. 创建 `notes/`。
5. 用中文为主、少量英文术语的方式逐小节带读。
6. 每小节后用选择题确认理解。
7. 每读完一节，更新对应 markdown 笔记。

## 工作流

### 1. 准备文本

当用户给出 PDF 路径时，先检查文件是否存在。然后运行：

```powershell
python <skill_dir>/scripts/split_pdf_by_chapters.py "<pdf_path>"
```

脚本会优先调用本机的 `pdftotext -layout`，将 PDF 转成全文 txt，再根据正文中的章节标题自动切分。

如果脚本输出的章节明显不完整，先不要继续讲书。把 `MANIFEST.txt` 展示给用户，让用户确认或提供需要修正的章节标题/边界。

### 2. 建立阅读目录

默认在 PDF 同级目录下创建同名目录，例如：

```text
book.pdf
book/
  00-Preamble.txt
  01-Chapter.txt
  notes/
  MANIFEST.txt
```

如果用户指定输出目录，使用用户指定目录。

### 3. 带读方式

读取对应章节 txt，一次只讲一个小节。不要一次讲完整章，除非用户明确要求。

每小节使用这个结构：

1. 小节标题和少量必要英文术语。
2. 中文解释核心意思。
3. 给一个贴近日常或工程场景的例子。
4. 用一句话总结。
5. 给一道选择题，并标出推荐答案。

详细风格见 `references/teaching-style.md`。

### 4. 笔记更新

每读完一节，都更新 `notes/chapter-XX-<slug>-notes.md`。

笔记保持中文复习版，不要堆英文原文：

- 核心意思
- 例子
- 结论

只保留必要英文术语，例如 `facts`、`concepts`、`categories`、`modalities`。

### 5. 继续阅读

用户说“继续”时：

1. 找到当前章节和上次读到的小节。
2. 继续下一小节。
3. 保持同样讲解粒度。
4. 更新 notes。

如果无法确定进度，读取 `notes/` 和当前章节 txt，推断最近读到的位置；推断不稳时，简短询问用户。

## PDF 切分策略

优先使用已经验证过的路线：

```text
pdftotext -layout -> full.txt -> Python 按章节标题切分
```

不要默认依赖 `pypdf`、`PyPDF2`、`pdfplumber` 等 Python 包。只有在 `pdftotext` 不可用时，才考虑其它方案或提示用户安装 Poppler/Git for Windows。

## 交互原则

- 中文为主。
- 少量英文术语要带中文解释。
- 不要大段复制原文。
- 用户说“太简洁”时，补充例子和解释。
- 用户说“太多”时，拆小节、缩短输出。
- 用户希望选择题时，固定用 A/B/C/D。
- 用户要求写 notes 时，立即落盘，不只在聊天里总结。

