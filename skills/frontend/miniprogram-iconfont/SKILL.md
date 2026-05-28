---
name: miniprogram-iconfont
description: 微信小程序 Iconfont 图标集成技能。从 iconfont.cn 挑选下载图标，自动替换字体文件、更新 CSS、扫描并替换 WXML/JS 中的 emoji 为 iconfont 类名。触发词："更新图标"、"添加图标"、"替换 emoji"、"iconfont"、"图标集成"、"小程序图标"。
---

# 小程序 Iconfont 图标集成技能

将 iconfont.cn 图标集成到微信小程序的完整流程，分 5 步执行。

## 前置信息

- **iconfont 项目 ID**：`5170982`（佳馨心理咨询小程序）
- **字体文件目录**：`{project}/images/font_icon/`
- **CSS 文件**：`{project}/styles/iconfont.wxss`
- **emoji 对照表**：`{project}/emoji-icon-mapping.md`

## 流程

### Step 1：确认需要哪些图标

1. 读取 `{project}/emoji-icon-mapping.md`，列出所有 emoji 及其对应的搜索关键词
2. 询问用户：
   - 要新增哪些图标？（按分类展示对照表供选择）
   - 还是全部未替换的图标都处理？
3. 生成精确的 iconfont 搜索链接，例如：
   ```
   https://www.iconfont.cn/search/index?q=设置&type=icon
   ```
4. 提示用户：
   - 登录 iconfont.cn
   - 搜索关键词 → 添加入库
   - 右上角购物车 → **添加至项目** → 选择项目 `5170982`
   - 项目页 → **下载至本地**
   - 解压后将所有文件覆盖到 `{project}/images/font_icon/`

### Step 2：替换字体文件

用户下载完成后，检查 `{project}/images/font_icon/` 目录：

```bash
ls {project}/images/font_icon/
# 应包含：iconfont.ttf, iconfont.woff, iconfont.woff2, iconfont.css, iconfont.js, iconfont.json
```

如果用户只提供了 `.ttf`，也可以只替换 `.ttf`（脚本只需要它）。

### Step 3：运行更新脚本

使用技能自带的参数化脚本：

```bash
node {skill-dir}/scripts/update-iconfont.js \
  --ttf  {project}/images/font_icon/iconfont.ttf \
  --wxss {project}/styles/iconfont.wxss
```

如果项目已有 `scripts/update-iconfont.js`，也可以直接用项目的版本：

```bash
cd {project}
node scripts/update-iconfont.js
```

**检查输出**：确认脚本报告 "IconFont 更新完成"。

### Step 4：确认 CSS 类名

1. 打开 `{project}/iconfont.css`（下载包里的），查看所有图标的类名
2. 打开 `{project}/styles/iconfont.wxss`，确认新图标的 CSS 类名已存在
3. 如果 wxss 中缺少某些类名，从 `iconfont.css` 中复制对应的 `.icon-xxx:before` 规则到 wxss

### Step 5：替换 WXML/JS 中的 emoji

使用技能自带的替换脚本：

```bash
node {skill-dir}/scripts/replace-emoji.js {project} --dry-run
```

1. **先 dry-run**：扫描所有 `.wxml` 和 `.js` 文件，输出变更清单
2. **给用户确认**：展示每个文件的替换详情（文件、行号、emoji → 类名）
3. **执行替换**：

```bash
node {skill-dir}/scripts/replace-emoji.js {project}
```

用户确认后执行实际替换。

替换规则：`⚙️` → `<text class="iconfont icon-settings"></text>`

### Step 6：重新编译验证

提示用户在微信开发者工具中：
1. 点击「编译」
2. 检查图标是否正常显示
3. 如果显示为方框 → 回到 Step 4 检查 CSS 类名

## 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 图标不显示 | wxss 未更新 | 重新运行 `node scripts/update-iconfont.js` |
| 图标显示为方框 | CSS 类名不存在 | 从 `iconfont.css` 复制类名到 `iconfont.wxss` |
| 图标颜色不对 | 未设置 color | 添加 `color: var(--primary)` 或具体色值 |
| 图标尺寸不对 | 未设置 font-size | 设置 `font-size: 32rpx`（根据场景调整） |
| 替换后页面报错 | WXML 中 emoji 在属性值里 | 手动检查并修复属性值中的 emoji |

## 注意事项

1. **先备份**：替换 WXML/JS 前建议用户提交 git 或备份
2. **分批替换**：如果图标很多，按分类分批替换，降低风险
3. **特殊位置**：JS 中动态拼接的 emoji（如 `pages/management/index.js`）需要手动处理，脚本只处理字面量
4. **成对图标**：❤️（实心）和 🤍（空心）可能映射到相同类名，需手动区分
