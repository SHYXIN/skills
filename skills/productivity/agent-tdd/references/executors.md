# 执行器事实（当前机器：dp-eval-run）

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

## 注入型 skill：run_eval.py 测不了，逐 case 走 ask 脚本

`run_eval.py` **不支持 system 注入**。要测的 skill 是「宿主 @ 入口」类（agent 行为完全由宿主注入的 system 串驱动）时，裸会话根本不知道该 skill 存在，会直接答「技能不存在」——所有案例 0.1 秒内假红，跑出来的结果全部作废。判别方法：看 skill 的激活方式，需要宿主 @mention 或动态指令拉取的，就是注入型。

注入型 skill 的正确姿势：

```bash
# 注入 facade 惯例放被测仓 eval/ 目录：txt 唯一源 + md 说明（用法/出处/机制）
SYSTEM=$(cat <被测仓>/eval/system-<skill名>.txt)
A=<dp-ask-deepworks 安装目录>/scripts/ask_local_deepworks.py

python $A --env prod --working-dir <工作区> --system "$SYSTEM" \
  --message "<case 的 user_message>" \
  --timeout 600 --out-dir <run目录>
```

判分逻辑简单（关键词 + 禁词 + 长度），套着案例集 JSON 写个十几行的本地脚本循环即可，不必改执行器技能。facade 只保留驱动行为的最小段（行为级一致，不逐字复刻宿主全文）；内容来自会话取证（dp-session-forensics dump 出真实会话的 `system` 字段）。

## 环境事实（踩过的坑）

- 桌面端开着多个工作区时，`run_eval.py` 和 ask 脚本都必须显式 `--working-dir`，否则报「multiple/no workspaces open」直接失败（不是案例红，是环境挡）
- 要真实装环境/真建模的 case，600s 常常不够；**超时 ≠ 失败**——agent 可能还在跑，用 ask 脚本的 `--read --session <id>` 轮询同一会话拿最终回答
- 模型网关偶发 `credentials are unavailable`（平台侧瞬时故障），重跑即可，与被测改动无关

## 红期排查

案例跑红且改不动 md 时，可用 **dp-session-forensics** 看该次会话的注入与工具调用，区分「规则没写对」和「规则没被读到」。

## 注意

- 评测会真实建会话，跑完可 `cleanup.py --yes` 清理
- 单 case 默认超时 900s，云端专家冷启动建议加大 `--timeout`
- 题目集快照（`questions.snapshot.json`）随 run 落盘，事后可复现这轮跑了什么
