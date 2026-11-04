---
name: alias
description: >
  通用短名登记：用户嫌实体全名长（专家/仓库/服务器/任务/项目…）时，agent 批量
  推荐尽量短的名字（❓+➡️ emoji 格式，单字母/单汉字优先，撞名顺延），确认后登记
  进全局 ~/.alias-registry.json，之后用户直接打短名，agent 查表解析。
  触发词：起名 / 起个名 / 叫它 X / 登记别名 / 用短名指代实体 /
  输入里出现登记表中的短名。任何 agent（codebuddy/claude/codex…）通用。
---

# alias — 通用短名登记

## 硬规则

- **登记表**：`~/.alias-registry.json`，全局一份，跨项目跨会话跨 agent 共用
- **短名全局唯一**：一个短名只指一个实体；新场景顺延分配（`next` 命令给下一个可用），
  不复用已占用的；覆盖必须显式（`add --yes`，脚本警告一次）
- **短名风格**：单字符优先——英文单字母（A/B/C…）或单个汉字（诊/维/仓…），
  中英皆可，用户说了算；再不够用短词（`db`、`189`）
- **context 必填**：一句场景说明，防未来会话误解析

## 交互规范

推荐短名时用 emoji 格式，**按场景批量**——一次对话出现几个实体就一次推齐：

```text
❓ **起名推荐**：
| 实体 | 推荐短名 | 说明 |
|---|---|---|
| 设备诊断运维专家 | A | 平台原生专家 |
| 设备诊断运维专家-189 | B | 189 exec-host 副本 |

➡️ 回复 ok 全部登记，或指出要改的（如「B 改成诊」）
```

单实体自然退化为一条。用户确认后一次登记全部。

## 登记流程

1. **查表现状**：`node <skill目录>/scripts/alias.mjs list`（或 next 拿顺延推荐）
2. **批量推荐**：按上面格式给出 ❓ 表格 + ➡️ 确认提示，等用户拍板
3. **登记**：每条执行 `node <skill目录>/scripts/alias.mjs add <短名> <全名> --kind <类型> --context <一句场景> [--key value ...]`
4. **CodeBuddy 专属**（其他 agent 跳过）：项目 memory 首次登记后加一条指针
   「用户会用短名指代实体，先查 ~/.alias-registry.json 解析」

## 解析短名

用户输入里的短名：

- **表里有** → 直接解析使用，不要再问
- **表里没有** → 先查再问：「❓ A 是指 X 吗？➡️ 是的话我登记一下」——确认后顺手登记，
  下次就不用再问

## 条目格式

```json
{
  "A": {
    "name": "设备诊断运维专家",
    "kind": "agent",
    "context": "agent-teams 平台原生专家(deepexios-workspace)",
    "registered": "2026-11-04",
    "id": "3b4ad9e4-...",
    "workspace": "deepexios-workspace"
  }
}
```

- `name`（必填）：全名，解析目标
- `kind`：agent / repo / server / task / project / file / other
- 其余字段（id / workspace / host / path…）按实体类型放定位信息，够定位即可，
  不做统一 schema

## 什么时候不用

- 全名本身已很短（≤4 字符），起名反而多一层
- 一次性临时指代（「上面那个文件」），不值得登记

## 脚本速查

```bash
S=<skill目录>/scripts/alias.mjs
node $S list              # 全部（短名 = 全名 [类型] # 场景）
node $S get A             # 单条 JSON
node $S next              # 顺延推荐下一个可用短名
node $S add A "全名" --kind agent --context "场景" --id xxx --workspace yyy
node $S add A "全名" --yes ...   # 显式覆盖（警告后放行）
node $S remove A
```
