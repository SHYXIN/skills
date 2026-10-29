# 执行器事实（当前机器：dp-eval-run）

本文件是可变事实层：方法论（SKILL.md）不变，工具换掉时只改这里。

当前执行器：**dp-eval-run**（公司仓 deepsense-skills/wangxin，安装后位于全局技能目录）。支持「案例集批量跑 + 逐 case 判分 + 两轮 diff」，两源可用：

- `--source local`：本地工作区 agent（走 dp-ask-deepworks），测**本地 agent-kit 形态**（agents/templates/SKILL.md）
- `--source teams`：云端 Agent Teams 专家（走 dp-ask-teams），测**云端专家**（agent md/soul/skill）

## 常用命令

```bash
S=<dp-eval-run 安装目录>/scripts

# 护栏轨：改前基线
python $S/run_eval.py --source local --env prod \
  --questions <被测仓>/eval/questions.json --label baseline

# 先行轨：改 md 前跑红（新案例预期失败）
python $S/run_eval.py --source teams \
  --questions <被测仓>/eval/questions-new.json --label red-check

# 改后再跑 + diff（报告写入新 run 目录）
python $S/run_eval.py --source local \
  --questions <被测仓>/eval/questions.json --label after-fix
python $S/run_eval.py diff <baseline_run_dir> <after_run_dir>

# flaky 仲裁：单 case 复跑
python $S/run_eval.py --source local --only <case_id> \
  --questions <被测仓>/eval/questions.json --label rejudge
```

## 案例集格式

JSON，字段：`case_id` / `user_message` / `expected.required_markers` / `expected.forbidden_markers` / `expected.answer_max_chars` / `tags`。完整示例见 dp-eval-run 的 `questions.example.json`。

## 红期排查

案例跑红且改不动 md 时，可用 **dp-session-forensics** 看该次会话的注入与工具调用，区分「规则没写对」和「规则没被读到」。

## 注意

- 评测会真实建会话，跑完可 `cleanup.py --yes` 清理
- 单 case 默认超时 900s，云端专家冷启动建议加大 `--timeout`
- 题目集快照（`questions.snapshot.json`）随 run 落盘，事后可复现这轮跑了什么
