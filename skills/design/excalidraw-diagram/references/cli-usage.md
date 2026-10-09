# CLI 用法（excalidraw-cli@0.0.2）

统一用 `npx -y excalidraw-cli@0.0.2` 调用，无需全局安装。下面为简洁用 `EXC` 代指：

```bash
EXC="npx -y excalidraw-cli@0.0.2"
```

## 命令总览

| 命令 | 作用 |
|------|------|
| `$EXC create --json '[...]' -o out.excalidraw` | 从内联 JSON 出文件 |
| `$EXC create elements.json -o out.excalidraw` | 从文件出文件 |
| `echo '[...]' \| $EXC create -o out.excalidraw` | 从 stdin 出文件 |
| `$EXC export out.excalidraw` | 上传到 excalidraw.com，返回分享链接 |
| `$EXC checkpoint list` | 列出已存 checkpoint |
| `$EXC checkpoint save <name> <file>` | 保存 checkpoint |
| `$EXC checkpoint load <name> -o <file>` | 载入 checkpoint |
| `$EXC checkpoint remove <name>` | 删除 checkpoint |
| `$EXC reference` | 打印元素格式速查表 |

## 内置默认值（JSON 里可以省略）

CLI 会自动套用这些，所以 JSON 写得更少：

| 属性 | 默认值 | 作用于 |
|------|--------|--------|
| `roughness` | `2`（手绘/sloppy） | 形状、箭头 |
| `roundness` | `{ "type": 3 }`（圆角） | 形状 |
| `fontFamily` | `1`（Excalifont/Virgil 手写） | 文字 |
| `strokeColor` | `"#1e1e1e"` | 全部 |
| `backgroundColor` | `"transparent"` | 全部 |
| `fillStyle` | `"solid"` | 全部 |
| `strokeWidth` | `2` | 全部 |
| `opacity` | `100` | 全部 |

要改就显式写出来覆盖。

## 元素格式

### 形状（rectangle / ellipse / diamond）

最简：只要 type、id、位置、尺寸：

```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 100 }
```

填色：

```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 100, "backgroundColor": "#a5d8ff", "fillStyle": "solid" }
```

### 标签（形状内文字，label 简写）

任何形状加 `label` 就行——CLI 会自动展开成正确的绑定文字元素：

```json
{ "type": "rectangle", "id": "b1", "x": 100, "y": 100, "width": 200, "height": 80, "label": { "text": "标签", "fontSize": 20 } }
```

可用于 `rectangle`、`ellipse`、`diamond`、`arrow`。label 可选：`fontSize`（默认 20）、`fontFamily`、`strokeColor`。

深色模式下用 `label.strokeColor` 指定文字色：

```json
"label": { "text": "你好", "strokeColor": "#e5e5e5" }
```

### 独立文字（标题、注释）

```json
{ "type": "text", "id": "t1", "x": 100, "y": 50, "text": "图标题", "fontSize": 28 }
```

要在 `cx` 处居中：`x = cx - (文字长度 × fontSize × 0.5) / 2`

### 箭头

```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 200, "height": 0, "points": [[0,0],[200,0]], "endArrowhead": "arrow" }
```

- `points`：相对箭头 `x, y` 的 `[dx, dy]` 偏移
- `endArrowhead`：`null` | `"arrow"` | `"bar"` | `"dot"` | `"triangle"`

### 箭头绑定（连接形状）

```json
{
  "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 150, "height": 0,
  "points": [[0,0],[150,0]], "endArrowhead": "arrow",
  "startBinding": { "elementId": "b1", "fixedPoint": [1, 0.5] },
  "endBinding": { "elementId": "b2", "fixedPoint": [0, 0.5] }
}
```

**fixedPoint** `[x, y]`（形状边上的归一化位置）：右 `[1,0.5]`、左 `[0,0.5]`、上 `[0.5,0]`、下 `[0.5,1]`。

绑定箭头时，也要把箭头加进每个形状的 `boundElements`：

```json
{ "type": "rectangle", "id": "b1", "boundElements": [{ "id": "b1_label", "type": "text" }, { "id": "a1", "type": "arrow" }] }
```

### 箭头标签

箭头同样用 `label` 简写：

```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 150, "height": 0, "points": [[0,0],[150,0]], "endArrowhead": "arrow", "label": { "text": "连接", "fontSize": 16 } }
```

## 相机（视口）

控制打开时看到哪里。MUST 是 4:3 比例：

```json
{ "type": "cameraUpdate", "width": 800, "height": 600, "x": 50, "y": 20 }
```

| 档位 | 尺寸 | 用途 |
|------|------|------|
| S | 400×300 | 2-3 个元素特写 |
| M | 600×450 | 图中一段 |
| **L** | **800×600** | **标准（默认）** |
| XL | 1200×900 | 大图总览 |
| XXL | 1600×1200 | 全景 |

把 `x, y` 设成内容区左上角（留约 50px 边距）。

## 伪元素

### cameraUpdate（视口控制）

```json
{ "type": "cameraUpdate", "width": 800, "height": 600, "x": 0, "y": 0 }
```

### delete（按 id 删元素）

```json
{ "type": "delete", "ids": "b2,a1,t3" }
```

### restoreCheckpoint（在已有图上继续画）

```json
{ "type": "restoreCheckpoint", "id": "checkpoint-id" }
```

## Checkpoint（跨轮增量改图）

```bash
$EXC checkpoint save mydiagram diagram.excalidraw
$EXC checkpoint load mydiagram -o restored.excalidraw
```

在 JSON 里用 `restoreCheckpoint` 载入上一张图，再用 `delete` 去掉不要的元素、追加新元素——实现"在上一版基础上改"而不是重画。

## 绘制顺序

数组顺序 = z 轴顺序（先画在后，后画在前）。**渐进式输出**：

```
相机 → 背景区域 → 形状1 → 形状1文字 → 箭头1 → 箭头1文字 → 形状2 → ...
```

**反例**：所有矩形 → 所有文字 → 所有箭头
**正例**：形状 → 它的文字 → 它的箭头 → 下一个形状 → ...

## JSON 校验

`create` 会做两项检查并给 warning：
- 相机非 4:3 → 警告（比例应接近 4/3，容差 0.15）
- JSON 非法（注释/尾逗号/引号错）→ 直接报错
