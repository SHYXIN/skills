---
name: ask-dp
description: DeepWorks 技能闭环路由器。你不会记得 company 里每个 dp-* 技能怎么配合，所以问。当用户说「用 DeepWorks 干一件事但不知道从哪开始」「跑一遍设备诊断评测」「改知识库然后验证」「查 agent 为什么这么答」，或任何要串多个 dp-* 技能的任务，先用本图裁决入口；也可先跑 preflight 看环境缺什么。
---

# ask-dp — DeepWorks 技能闭环路由器

一张地图 + 一次体检，替代「记得每个技能」。company 里的 dp-* 技能构成一个闭环：

```
准备层              知识层              执行层              诊断层            回归层
dp-dev-bootstrap ─┐
dp-deepworks-dev-start ─┬→ dp-knowledge-compile → dp-ask-deepworks ─┐
dp-dth-key-setup ─┘    （xmind→知识库）      dp-ask-teams        │ 行为不符
                                                                ▼
                                                    dp-session-forensics-cloud
                                                    （--source local|teams）
                                                                │ 定位原因
                          dp-knowledge-compile（改知识）←───────┘
                                                                │ 修复后
                                                        dp-eval-run（回归对比）─→ 回到知识层
```

## 第 0 步：环境体检（不确定环境时先跑）

```bash
python <skill_dir>/scripts/preflight.py
```

只读检查：双环境桌面端端口活性、teams token、deepworks 仓库、python/node。
缺项会打印影响面。桌面端开着但端口失活 = 状态文件陈旧快照，重开工作区即可。

## 路由裁决（按用户意图，一轮问一条澄清）

| 用户想… | 入口 | 后续 |
|---|---|---|
| 把 xmind 诊断树变成可用的知识库 | `dp-knowledge-compile` | 编译完直接进执行层试问 |
| 问本地工作区 agent 一个问题 | `dp-ask-deepworks` | 默认模型 DeepSeek，--working-dir 按需 |
| 让云端专家跑一个任务 | `dp-ask-teams` | 不带 --agent-name 先列专家 |
| agent 答得不对，要查为什么 | `dp-session-forensics-cloud` | 云端任务 `--source teams`；本地会话 `--source local` |
| 改完知识库，要确认没退步 | `dp-eval-run` | 先 baseline 后 after，再 diff 两轮 |
| 本地环境跑不起来 | `dp-dev-bootstrap`（monorepo）/ `dp-deepworks-dev-start`（桌面开发环境） | preflight 缺项也可从这里修 |
| 配积分 key / TokenHub | `dp-dth-key-setup` | 独立支线 |

## 典型闭环走法（评测一条龙）

1. **体检**：`preflight.py` 确认桌面端/token 就绪
2. **基线**：`dp-eval-run --label before --questions q.json`
3. **改动**：`dp-knowledge-compile` 重新编译知识库
4. **回归**：`dp-eval-run --label after` + `diff` 两轮 run 目录
5. **取证**：diff 有 FAIL → `dp-session-forensics-cloud` 拉 case 对应会话看实际收发
6. 回到 3，直到全绿

## 参数速记（全家族统一）

- `--env prod|test`：双环境。local 系默认 prod（正式桌面端），teams 系默认 test（test.deepworks.cn）
- `--source local|teams`：取证/评测的数据面选择
- 会话清理：两个 ask 脚本的 `--delete-session last` / `--delete-ask-sessions`（先 `--list-sessions` 盘点）

## 纠错层

迷路了 → `/where-am-i-wx`；没听懂 → `/wait-what-wx`；追出处 → `/source-trace-wx`。
