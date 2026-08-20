---
name: visual-verdict
description: 结构化视觉 QA 判定——把生成的 UI 截图与一张或多张参考图对比，返回可驱动下一轮修改的严格 JSON 判定。适用于截图还原度 / 布局间距 / 字体 / 配色一致性验收（触发词：对比截图、视觉验收、还原度、UI 截图比对；visualize / screenshot / visual verdict）。
level: 2
---

<Purpose>
用本技能把生成的 UI 截图与一张或多张参考图对比，返回一份严格的 JSON 判定，用来驱动下一轮修改迭代。
</Purpose>

<Use_When>
- 任务包含视觉还原度要求（布局、间距、字体、组件样式）
- 你有一张生成的截图和至少一张参考图
- 在继续修改前，需要确定性的通过 / 不通过（pass/fail）指引
</Use_When>

<Inputs>
- `reference_images[]`（一张或多张图片路径）
- `generated_screenshot`（当前输出的图片）
- 可选：`category_hint`（例如 `hackernews`、`sns-feed`、`dashboard`）
</Inputs>

<Output_Contract>
只返回 **JSON**，且严格符合以下结构：

```json
{
  "score": 0,
  "verdict": "revise",
  "category_match": false,
  "differences": ["..."],
  "suggestions": ["..."],
  "reasoning": "short explanation"
}
```

规则：
- `score`：整数 0-100
- `verdict`：简短状态（`pass`、`revise` 或 `fail`）
- `category_match`：当生成截图符合预期的 UI 分类 / 风格时为 `true`
- `differences[]`：具体的视觉差异（布局、间距、字体、颜色、层级）
- `suggestions[]`：与差异对应的、可执行的下一步修改
- `reasoning`：1-2 句话的总结
</Output_Contract>

<Threshold_And_Loop>
- 目标通过阈值是 **90+**。
- 若 `score < 90`，继续修改并在任何进一步视觉复查前重跑 `/oh-my-claudecode:visual-verdict`。
- 在下一轮截图达到阈值之前，不要把视觉任务视为完成。
</Threshold_And_Loop>

<Debug_Visualization>
当差异诊断困难时：
1. 以 `$visual-verdict` 作为权威判定。
2. 用像素级 diff 工具（pixel diff / pixelmatch overlay）作为**辅助调试手段**来定位热点。
3. 把像素 diff 热点转化为具体的 `differences[]` 与 `suggestions[]` 更新。
</Debug_Visualization>

<Example>
```json
{
  "score": 87,
  "verdict": "revise",
  "category_match": true,
  "differences": [
    "顶部导航间距比参考图更紧",
    "主按钮字体字重偏小"
  ],
  "suggestions": [
    "导航项水平内边距增加 4px",
    "主按钮 font-weight 设为 600"
  ],
  "reasoning": "核心布局一致，但样式细节仍有出入。"
}
```
</Example>

Task: {{ARGUMENTS}}
