---
name: verify-replay
description: 在 verify-run 验证报告全绿后，把本次执行过程固化为 YAML 回放清单，供后续 agent+opencli 快速回归重放。用于用户要求"固化回放""生成回归清单""把这次验证存成可重放的""以后一键回归"等场景。报告有 fail 时拒绝固化。
---

# 回放清单固化

把一次跑通的验证执行固化为 YAML 步骤清单。默认输出到：

`docs/verification/replay.yml`

只有 URL、没有仓库时，写到当前工作目录 `replay.yml`。

## 输入门槛（fail closed）

- 输入是 verify-run 产出的验证报告（`docs/verification/verify-run-report.md` 或用户指定路径）。
- 报告中存在任何 `fail` 项时**拒绝固化**，明确告知：回放清单是执行产物，必须先修复、重跑、全绿后再固化。这是硬性门槛，用户坚持也不做。
- 报告不存在时，提示先跑 verify-run。

## YAML 格式

每步一个条目，字段固定：

```yaml
# 回放清单：由 verify-replay 于 2026-10-10 从 verify-run 报告固化
# 来源报告：docs/verification/verify-run-report.md（全绿）
meta:
  target: http://localhost:5173        # 被验证目标（URL 或本地服务说明）
  setup:                               # 重放前的环境准备（启动命令等，可空）
    - bash scripts/dev.sh
  teardown:                            # 重放后的清理（可空）
    - 停止 dev 服务

steps:
  - id: 1
    action: open                       # open | click | fill | upload | curl | run | wait | screenshot
    target: http://localhost:5173/login
    expect: 页面出现"登录"标题           # 断言描述，agent 重放时据此判定
    evidence: screenshots/01-login.png # 期望留存的证据（可选）
  - id: 2
    action: fill
    target: 用户名
    value: demo@example.com
  - id: 3
    action: curl
    target: GET http://localhost:8790/api/health
    expect: "HTTP 200，响应含 {\"status\":\"ok\"}"
```

固化规则：

- 只收录报告里 pass 的验证点及其操作路径；skip 项注释形式附在末尾，不进 steps。
- target / URL / 选择器描述一律用本次执行中**实际验证过的值**，不要回头改成理想化的写法。
- 断言描述保留人眼级判断（"出现订单列表""无控制台报错"），不强行转成硬编码断言——重放时由 agent 判定。
- 尽量少加 wait；确需等待的步骤把条件写实（"出现 X 文本"而不是"等 3 秒"）。

## 重放方式

重放不由本技能执行。用户要重放时：

- 直接按 replay.yml 逐条驱动 opencli / curl 执行，每条用 expect 由 agent 判定，证据按 evidence 字段留存。
- 重放结果默认写到 `docs/verification/replay-run-report.md`（覆盖更新）。
- 某步 fail 时记录并继续后续步骤，最后汇总；连续多轮同一步 fail，说明目标已漂移，提示用户重新跑 verify-run 并重新固化，而不是反复修补 YAML。

## 输出要求

- 使用中文。
- 生成完成后，在最终回复中列出：replay.yml 路径、收录步骤数、跳过项、重放的调用方式。
