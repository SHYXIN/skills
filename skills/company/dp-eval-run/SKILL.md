---
name: dp-eval-run
description: DeepWorks 回归评测。问题集 JSON 批量跑本地工作区 agent 或云端 Agent Teams，逐 case 打分（标记命中/禁词/超长/延迟），落盘 run 目录；diff 子命令对比两轮 run 出 markdown 报告。当用户说「跑一遍评测」「回归测一下 agent」「这两轮结果对比下」「改完知识库验证有没有退步」时使用。
---

# dp-eval-run — 批量评测 + 两轮对比

补上闭环的最后一步：取证定位 → 修复（改知识库/配置）→ **回归验证**。像食品加工机的
出厂质检：同一批问题丢进去跑两轮，diff 报告直接告诉你哪几道工序退步了。

判分刻意从简（标记命中 + 禁词 + 长度 + 延迟）；深度语义判分属于 agent-eval 仓库或人工。

## 用法

```bash
S=C:/code_proj/github-proj/wangxin/skills/skills/company/dp-eval-run/scripts

# 跑一轮（本地，默认 env=prod；--model 不传时用 ask 脚本的默认 DeepSeek）
python $S/run_eval.py --source local --env prod \
  --questions q.json --label baseline \
  --working-dir "C:/code_proj/tmp/mes-file-card5"

# 跑第二轮（改完知识库后）
python $S/run_eval.py --source local --questions q.json --label after-fix \
  --working-dir "C:/code_proj/tmp/mes-file-card5"

# 对比两轮，出 markdown 报告（写到 current run 目录）
python $S/run_eval.py diff <run_dir_a> <run_dir_b>

# 云端（默认 env=test；--agent-name 不传会先列专家）
python $S/run_eval.py --source teams --questions q.json --agent-name 设备故障诊断专家
```

## 问题集格式

JSON（见 `questions.example.json`），兼容 agent-eval 的 JSONL 与字段名
（`input.user_message` / `required_trace_markers` / `forbidden_behaviors`）：

```json
{
  "cases": [
    {
      "case_id": "demo-001",
      "user_message": "用一句话介绍你自己",
      "expected": {
        "required_markers": ["必须出现的关键词"],
        "forbidden_markers": ["不允许出现的词"],
        "answer_max_chars": 500
      },
      "tags": ["smoke"]
    }
  ]
}
```

## run 目录结构

每次 run 落 `C:/code_proj/tmp/dp-eval-runs/<stamp>-<source>-<env>-<label>/`：

- `questions.snapshot.json` — 问题集快照（事后可复现这轮跑了什么）
- `ask-logs/` — 兄弟 ask 脚本的原始落盘（`.answer.md` 问答对 + `.log.json` 含 session_id）
- `summary.json` — 每 case 状态/延迟/得分 + 汇总

## 参数

| 参数 | 说明 |
|---|---|
| `--source local\|teams` | 本地工作区 / 云端 Agent Teams（默认 local） |
| `--env prod\|test` | local 默认 prod，teams 默认 test |
| `--only id1,id2` | 只跑指定 case（调试问题集时用） |
| `--model` | local 源模型覆盖（默认走 ask 脚本的 DeepSeek-V4.1-Flash） |
| `--agent-name` | teams 源目标专家 |
| `--timeout` | 单 case 等待秒数（默认 900，云端冷启动建议加大） |

## 清理评测会话

评测会真实建会话，跑完可一键清理（复用 ask 脚本的删除逻辑，成功后回写标记不会重复删）：

```bash
python <skill_dir>/scripts/cleanup.py --list          # 预览待删会话
python <skill_dir>/scripts/cleanup.py --yes           # 全删
python <skill_dir>/scripts/cleanup.py --label t1 --yes  # 只删某个 run
```

## 前置

- local：对应环境桌面端已打开目标工作区（端口文件是陈旧快照时用 dp-ask-deepworks
  的 `--list-sessions` 或重开工作区排查）
- teams：`AGENT_TEAMS_TOKEN[_PROD]` 可用（已登录桌面端自动同步）

## 典型闭环流程

1. `dp-knowledge-compile` 改知识库
2. `dp-eval-run --label before`（改前基线，或用历史 run）
3. `dp-eval-run --label after` + `diff` → 看回退/改善
4. 有分歧 → `dp-session-forensics(-cloud)` 取证定位 → 回到 1
