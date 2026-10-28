---
name: setup-tencent-docs
description: 在一台新机器上配置腾讯文档（docs.qq.com）访问——安装官方 tencent-docs 技能、配置 TENCENT_DOCS_TOKEN 用户级环境变量、API 连通性验证与排障。无本地 CLI，认证走个人 token。用户手动调用（/setup-tencent-docs）。
---

# 腾讯文档（docs.qq.com）配置

让 agent 能创建/读取/编辑腾讯文档：在线文档、智能表格、知识库空间、文件管理等。**无本地 CLI**——官方 tencent-docs 技能直接调 docs.qq.com 开放 API，认证只靠一个个人 token（存用户级环境变量）。

---

## Step 1 —— 探测现状（幂等）

```bash
echo "TOKEN=${TENCENT_DOCS_TOKEN:+set}"
ls ~/.agents/skills/tencent-docs/SKILL.md 2>/dev/null && echo "skill: installed"
```

（PowerShell 检查：`[Environment]::GetEnvironmentVariable('TENCENT_DOCS_TOKEN','User')`）

四种情况：

- **token set + skill 已装** → 无需配置，直接冒烟（Step 4）
- **token set、skill 未装** → 跳 Step 2
- **token 缺、skill 已装** → 跳 Step 3
- **全新机器** → 从 Step 2 开始

`GREEN:` 现状已知。

---

## Step 2 —— 安装官方技能

```bash
npx skills@latest add tencent-docs --skill tencent-docs -y -g -a codebuddy claude-code codex
```

（技能来源以官方发布渠道为准；已装过的跳过。）

`GREEN:` `~/.agents/skills/tencent-docs/SKILL.md` 存在。

---

## Step 3 —— 配置 token（用户级环境变量）

用 PowerShell 写入**用户级**：

```powershell
[Environment]::SetEnvironmentVariable('TENCENT_DOCS_TOKEN', '<个人token>', 'User')
```

token 获取：打开 <https://docs.qq.com/scenario/open-claw.html?nlc=1>（官方技能 metadata 里的 tokenUrl），按页面指引创建/复制个人 token。**token 值不进任何仓库文件**。

写入后**重开终端**生效。

`GREEN:` 新终端里 `echo ${TENCENT_DOCS_TOKEN:+set}` 输出 `set`。

---

## Step 4 —— 冒烟测试

让 agent 用 tencent-docs 技能跑一条只读操作（如搜索一个文档、列知识库空间）。

`GREEN:` 返回真实数据而非 401/403。

---

## 排障

| 症状 | 原因与处理 |
|------|-----------|
| 401/403 | token 无效或过期 → 回 tokenUrl 页面重新生成，更新 User 级 env |
| agent 说"没有 tencent-docs 技能" | skill 未装或未注册 → 回 Step 2，装完重开会话 |
| env 写了但不生效 | 终端没重启；或写成了临时 `$env:`（会话级）而非 User 级 |
| 技能调 API 超时 | 公司网络对 docs.qq.com 的连通性，换网络验证 |

---

## 完成后

告诉用户：直接用自然语言说「新建一个腾讯文档」「把这段内容写进 XX 文档」即可；日常操作由 tencent-docs 技能承载，本技能以后只在换机器或 token 轮换时才需要。
