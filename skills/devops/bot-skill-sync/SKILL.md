---
name: bot-skill-sync
description: 把本地技能同步到 bot 宿主（open-superagent DSH 技能目录）：list 对比两端清单、push 覆盖推送（保护远端 .env 与 DEPLOY-NOTES.md）、remove 软删到 /tmp 备份。升级/下线/盘点 bot 技能时使用。
---

# Bot Skill Sync — 同步本地技能到 bot 宿主

本地技能仓是唯一真源，bot 宿主的技能目录是部署副本；该目录 bind mount 进容器，**文件变更即时生效，不需要重启**。本技能固化同步配方，避免手敲 scp 漏步骤（漏 .env 保护会把 bot 凭据冲掉）。

## 前置（环境事实从 memory 取，本技能不记地址）

- **宿主地址、技能目录路径：先查 memory**（服务器现状类条目，含免密 SSH 形态），找不到再问用户；脚本只认环境变量，不内置任何地址
- 宿主 root 免密 SSH 已配置；首次用新别名连接若卡在 host key 确认，先手动 ssh 一次确认指纹
- Python 3
- 本地技能源目录：`--src` 显式指定（如 deepsense-skills 仓的技能根目录）

环境变量：

| 变量 | 说明 |
|---|---|
| BOT_SKILL_SYNC_SSH_HOST | **必填**，宿主地址（查 memory） |
| BOT_SKILL_SYNC_REMOTE_DIR | 宿主技能目录（有默认，见脚本头部） |
| BOT_SKILL_SYNC_CHANGELOG | 全局部署台账路径（有默认） |

## 子命令

```bash
export BOT_SKILL_SYNC_SSH_HOST=<宿主地址，查 memory>

# 对比两端：远端技能清单、本地源目录、.env 在否、最近一条部署记录
python <脚本路径>/bot_skill_sync.py list --src <技能源目录>

# 覆盖推送（本地源目录 → 远端）
python <脚本路径>/bot_skill_sync.py push <skill> --src <技能源目录>

# 软删（mv 到 /tmp 备份，必须显式 --yes）
python <脚本路径>/bot_skill_sync.py remove <skill> --yes
```

## 行为约定

- **push**：同步本地技能目录下全部顶层文件与子目录，跳过 `.env`、`DEPLOY-NOTES.md`、点开头文件、`__pycache__`；本地同名子目录先删远端再整体复制，**远端独有的文件不动**；推送前后对远端 `.env` 做 md5 校验，变化即报错终止；完成后在远端 `DEPLOY-NOTES.md` 追加一行记录（含 git rev）。
- **remove**：先往技能的 `DEPLOY-NOTES.md` 补一行删除记录，再整体 `mv` 到 `/tmp/<skill>-removed-<时间戳>/`，并在全局台账追加一行。恢复 = 把备份目录 mv 回去。
- **list**：只读，随便跑。

## 排查

- 命令失败先看 stderr 原始报错；`Permission denied (publickey)` = 免密失效，重新配 SSH key。
- `.env` 校验失败：立即从备份恢复远端 `.env`，再排查脚本参数。
- 推送后 bot 面板没变化：确认推的技能名与面板展示一致；bind mount 即时生效，刷新面板即可。
