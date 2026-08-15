# 私人技能（personal）

本目录下的技能是**私人/私有**的，只放自己用、不对外分发：

- **不写进** 仓库根 `plugin.json` 的 `skills` 数组，所以 `npx skills add SHYXIN/skills` / `cn-skills add SHYXIN/skills` 等一键安装**不会带它们**。
- 仍随仓库提交、push 到 Gitee / GitHub（可备份、可版本管理），只是默认不进公开安装包。
- 需要时按下面的「子路径」方式单独安装即可。

## 安装某个私人技能

用仓库源 + 技能在仓库内的子路径（`skills/personal/<name>`）：

```bash
# Gitee（cn-skills，国内）
cn-skills add SHYXIN/skills/skills/personal/<name> --yes --global --agent codebuddy

# GitHub（npx skills）
npx skills@latest add SHYXIN/skills/skills/personal/<name> -y -g -a codebuddy
```

`<name>` 换成具体技能目录名，例如 `weekly-report`：

```bash
cn-skills add SHYXIN/skills/skills/personal/weekly-report --yes --global --agent codebuddy
```

## 已收录

| 技能 | 说明 | 调用 |
| --- | --- | --- |
| `weekly-report` | 例会全文 → 单人周报邮件正文（默认王鑫） | `/weekly-report [成员名]` |
