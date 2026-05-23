---
title: "两数之和 II（有序数组）"
tags: [array, two-pointers, 左右指针]
difficulty: M
companies: [字节, 腾讯, Google]
round: 技术一面
estimated_time: 15min
---

# 两数之和 II

## 题目

给定一个已按**升序排列**的整数数组 `numbers`，找出两个数使它们的和等于目标数 `target`。

这两个数分别是 `numbers[index1]` 和 `numbers[index2]`，且 `index1 < index2`。

返回这两个数的索引 `[index1, index2]`（索引从 1 开始）。

**假设每个输入只对应一个答案，且不能重复使用同一个元素。**

**示例：**
```
输入：numbers = [2,7,11,15], target = 9
输出：[1,2]
解释：2 + 7 = 9
```

## 考察点

- 双指针技巧（左右指针）
- 时间复杂度优化（从 O(n²) 到 O(n)）
- 空间复杂度分析

## 推荐解法

```python
def twoSum(numbers, target):
    left, right = 0, len(numbers) - 1
    while left < right:
        s = numbers[left] + numbers[right]
        if s == target:
            return [left + 1, right + 1]
        elif s < target:
            left += 1
        else:
            right -= 1
```

- **时间复杂度：** O(n)
- **空间复杂度：** O(1)

## 追问方向

1. "如果数组无序呢？" → 哈希表 O(n) 空间换时间
2. "如果有多个答案呢？" → 继续移动指针收集所有组合
3. "你能证明双指针不会漏掉正确答案吗？" → 理解单调性保证
4. "如果要求返回所有不重复的三元组和为 0 呢？" → 延伸到三数之和

## 评分维度

| 维度 | 优秀 | 及格 | 需改进 |
|------|------|------|--------|
| 思路 | 直接想到双指针 | 先想到暴力再优化 | 完全没有思路 |
| 代码 | 一次写对，边界正确 | 有小错但能修正 | 边界条件漏写 |
| 复杂度 | 主动分析 O(n)/O(1) | 被问到能答上来 | 不会分析 |
| 沟通 | 先说思路再写代码 | 能解释自己的代码 | 闷头写不说话 |
