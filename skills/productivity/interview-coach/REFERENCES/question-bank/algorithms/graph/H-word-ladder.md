---
title: "单词接龙（Word Ladder）"
tags: [graph, BFS, 最短路径, 哈希表]
difficulty: H
companies: [字节, Google, Meta]
round: 技术二面
estimated_time: 25min
---

# 单词接龙

## 题目

给定两个单词（`beginWord` 和 `endWord`）和一个字典 `wordList`，找到从 `beginWord` 到 `endWord` 的最短转换序列的长度。

转换规则：
- 每次只能改变一个字母
- 转换过程中的每个单词都必须在字典中存在

**示例：**
```
输入：beginWord = "hit", endWord = "cog", wordList = ["hot","dot","dog","lot","log","cog"]
输出：5
解释：hit → hot → dot → dog → cog
```

## 考察点

- BFS 求最短路径
- 图的建模（单词是节点，差一个字母的单词之间有边）
- 时间复杂度优化（双向 BFS）

## 推荐解法：BFS

```python
from collections import deque, defaultdict

def ladderLength(beginWord, endWord, wordList):
    if endWord not in wordList:
        return 0

    wordList = set(wordList)
    queue = deque([(beginWord, 1)])
    visited = {beginWord}

    while queue:
        word, steps = queue.popleft()
        if word == endWord:
            return steps
        for i in range(len(word)):
            for c in 'abcdefghijklmnopqrstuvwxyz':
                next_word = word[:i] + c + word[i+1:]
                if next_word in wordList and next_word not in visited:
                    visited.add(next_word)
                    queue.append((next_word, steps + 1))
    return 0
```

- **时间复杂度：** O(N × L × 26)，N=单词数，L=单词长度
- **空间复杂度：** O(N)

## 追问方向

1. "如果字典很大怎么办？" → 双向 BFS，从两端同时搜索
2. "如果要返回所有最短路径呢？" → BFS + DFS 回溯
3. "如果字母表不是 26 个而是 Unicode 呢？" → 预处理邻接关系
4. "时间复杂度能更精确地分析吗？" → 讨论最坏情况

## 评分维度

| 维度 | 优秀 | 及格 | 需改进 |
|------|------|------|--------|
| 思路 | 识别为 BFS 最短路径 | 提示后想到 BFS | 完全没有思路 |
| 代码 | 一次写对 + 考虑双向 BFS | 基本 BFS 能写对 | 代码逻辑混乱 |
| 复杂度 | 主动分析并讨论优化 | 被问到能答上来 | 不会分析 |
| 沟通 | 先建模再实现 | 能解释代码 | 没有建模意识 |
