# skill-curator —— 市场结构参考

技能启动时读一次。

---

## 三处权威源对比

| 权威源 | 文件 | 承载内容 | 何时为真 |
|---|---|---|---|
| 技能实体 | `skills/*/SKILL.md` | frontmatter (name + description) + 正文 | 用户创建 |
| 注册清单 | `.claude-plugin/plugin.json` | `skills[]` 路径数组 | curator 同步 |
| 用户文档 | `README.md` | 更新命令 + 技能列表 + 目录树 | curator 同步 |

任一技能的生命周期事件 → 至少两个权威源要跟着变：

| 事件 | 变更的权威源 |
|---|---|
| 新建 skill | 实体（用户创建）+ 注册清单 + 用户文档（curator 同步后两者）|
| 下架 skill | 注册清单 + 用户文档（curator 同步）；实体可选保留或删除（用户决定）|
| category 迁移 | 实体（mv）+ 注册清单 + 用户文档 |
| description 更新 | 实体（用户改）+ 用户文档（curator 同步）|

---

## plugin.json 格式

```json
{
  "name": "shyxin-skills",
  "skills": [
    "./skills/<category>/<skill-name>",
    ...
  ]
}
```

每条路径必须指向含 `SKILL.md` 的目录。jq 读写示例：

```bash
# 追加
jq --arg p "./skills/productivity/foo" '.skills += [$p]' plugin.json > tmp && mv tmp plugin.json

# 移除
jq --arg p "./skills/productivity/foo" '.skills = [.skills[] | select(. != $p)]' plugin.json > tmp && mv tmp plugin.json
```

---

## README.md 三处精确位置

### 1. 更新命令区（`## 更新` 下方）

两个位置要改：
- 每个单技能一行：`npx skills@latest update <skill-name>` （按字母序插入）
- 批量更新行：末尾追加 `<skill-name>`

### 2. 技能列表区（`## 技能列表` 下方各 `### 类别`）

格式：
```
- **<skill-name>** — <description>
```

`description` 取自对应 SKILL.md frontmatter 的 `description:` 字段。新类别没在 README 里出现过要新增 `### 类别名` 标题。

### 3. 目录树区（`## 目录结构` 下方）

格式：
```
│   └── <skill-name>/ # <备注>
```

按 category 的树形结构放置；缩进和延续线 `│` 对齐。

---

## 当前已登记 skill 清单（快照）

| skill | category | frontmatter name |
|---|---|---|
| socratic-tutor | teaching | socratic-tutor |
| idea-alchemist | productivity | idea-alchemist |
| anysearch | productivity | anysearch |
| interview-coach | productivity | interview-coach |
| fastapi-starlette-admin | backend | fastapi-starlette-admin |
| verify-manual | _（登记在 plugin.json） | verify-manual |
| miniprogram-iconfont | frontend | miniprogram-iconfont |
| ssh-key-setup | productivity | ssh-key-setup |

---

## Git 同步规范

- commit message 类型：`feat: add <skill>` / `chore: remove <skill>` / `chore: sync registry`
- 一次 curator 调用对应一个 commit（大改动也合一个）
- push 永远由用户在外部触发（curator 不 push）
