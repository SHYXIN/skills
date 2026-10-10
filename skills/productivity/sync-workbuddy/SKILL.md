---
name: sync-workbuddy
description: "把技能仓库的本地克隆同步（复制覆盖）到 WorkBuddy 的 ~/.workbuddy/skills/。npx skills 暂不支持 workbuddy agent，故用直接复制；只增改、永不删除目标目录中已有技能。适用于改完 skill 后同步、新电脑初始化 WorkBuddy 环境。"
---

# Sync WorkBuddy

把一个技能仓库克隆里的全部技能，复制覆盖到 WorkBuddy 的技能目录。

## 机制

- WorkBuddy 按目录约定发现技能：`~/.workbuddy/skills/<skill-name>/SKILL.md`。
- WorkBuddy 不在 `npx skills` 支持的 agent 列表里，所以用脚本直接复制。

## 操作

运行本 skill 目录内（`SKILL.md` 同级）的 `sync-workbuddy.sh`。第一个参数为技能仓库的本地克隆路径，第二个参数可选（目标目录，默认 `~/.workbuddy/skills`）：

```bash
bash <本skill目录>/sync-workbuddy.sh /path/to/skills-repo-clone
bash <本skill目录>/sync-workbuddy.sh /path/to/skills-repo-clone /path/to/workbuddy/skills
```

克隆路径在会话上下文里通常可知（用户刚操作过该仓库）；拿不准就先问用户。

脚本行为：遍历源仓库 `skills/` 下所有 `SKILL.md`，把所在目录整体复制覆盖到目标目录。只增改、永不删除。

## 验证

- 输出 `✅ 已同步 N 个技能`，N 等于源仓库中 `SKILL.md` 的数量。
- 目标目录中已存在的第三方技能（不在源仓库中的）原样保留。

## 边界

- 不删除目标目录任何内容。源仓库中改名/删除的技能会在目标目录残留旧副本，需手动删除。
- 只管复制到 WorkBuddy；其他 agent（CodeBuddy/Claude Code 等）走各自的安装通道。
