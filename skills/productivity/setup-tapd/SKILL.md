---
name: setup-tapd
description: 在一台新机器上配置 tapd-cli（TAPD OpenAPI CLI）——让 agent 能查询/更新 TAPD 需求、缺陷、任务、评论、迭代、Wiki、测试用例等。覆盖 exe 获取（官方 cnb.cool 发版页）、用户级环境变量三件套（TAPD_API_ENDPOINT / TAPD_TOKEN / TAPD_WORKSPACE_IDS）、只读命令验证与排障。用户手动调用（/setup-tapd）。
---

# tapd-cli（TAPD）配置

让 agent 能操作 TAPD：查需求/缺陷/任务、加评论、管理迭代与测试用例等。tapd-cli 是 Bun 打包的 Windows 单文件 exe，走 **个人访问令牌** 认证（存用户级环境变量，无内置 login）。

tapd-cli 技能（官方，level=product）是 CLI 的使用说明书，本技能只管装 exe 和配凭据。

---

## Step 1 —— 探测现状（幂等）

```bash
tapd-cli --help        # exe 是否已装（应输出 Usage 头）
echo "EP=${TAPD_API_ENDPOINT:+set} TOKEN=${TAPD_TOKEN:+set} WS=${TAPD_WORKSPACE_IDS:+set}"
```

（PowerShell 检查环境变量：`[Environment]::GetEnvironmentVariable('TAPD_TOKEN','User')`）

四种情况：

- **exe 在 + 三个 env 全 set** → 无需配置，直接冒烟（Step 4）
- **exe 在、env 缺** → 跳 Step 3
- **exe 不在、env 在** → 跳 Step 2
- **全新机器** → 从 Step 2 开始

`GREEN:` 现状已知。

---

## Step 2 —— 获取 exe（官方发版页）

官方发布页：<https://cnb.cool/tapd.cn/skills/tapd-cli/-/releases>

1. 打开发版页，取最新版本（当前已知可用 **1.13.0**）的 Windows x64 附件
2. 下载后放到 `~/.local/bin/tapd-cli.exe`（确保该目录在 PATH 里；不在则加）
3. 已装旧版时可直接自升级：`tapd-cli self update`

```bash
tapd-cli --help
```

`GREEN:` 输出 `Usage: tapd-cli [options] [command]`。

> exe 无包管理器分发，发版页是唯一官方来源；无法访问时找 TAPD 团队或同事拿同版本文件。

---

## Step 3 —— 配置凭据（用户级环境变量）

三个变量缺一不可，用 PowerShell 写入**用户级**（重装系统前一直有效，所有 shell 可见）：

```powershell
[Environment]::SetEnvironmentVariable('TAPD_API_ENDPOINT', 'https://openapi.tapd.cn', 'User')
[Environment]::SetEnvironmentVariable('TAPD_TOKEN', '<个人访问令牌>', 'User')
[Environment]::SetEnvironmentVariable('TAPD_WORKSPACE_IDS', '<默认项目ID，多个逗号分隔>', 'User')
```

令牌获取：TAPD 网页 → 个人设置 → API 账号/个人访问令牌，创建时勾选所需权限。**令牌值不进任何仓库文件**。

可选变量：`TAPD_NPC_ROLE`（默认 author）、`TAPD_CLI_LOG`（1=text | json | silent，默认静默）。

写入后**重开终端**让 PATH/env 生效。

`GREEN:` 新终端里三个变量全部可读。

---

## Step 4 —— 冒烟测试

```bash
tapd-cli user list workspaceid=<你的项目ID> limit=1
```

（或任一条只读查询。）期望返回 JSON 数据而非报错。

`GREEN:` 返回真实数据。

---

## 排障

| 症状 | 原因与处理 |
|------|-----------|
| `command not found` | exe 不在 PATH → 确认 `~/.local/bin` 在 PATH，重开终端 |
| `错误: 未设置环境变量 TAPD_API_ENDPOINT` | env 写在 User 级但终端没重启，或变量名拼错 |
| 401/403 | 令牌无效或权限不足 → TAPD 网页重建令牌，注意 workspace 权限 |
| `self update` 报无法获取最新版本 | cnb.cool 访问问题（代理/VPN），或手动去发版页下载 |
| workspaceid 不对 | 查项目 URL 里的数字，或先 `tapd-cli user list` 试一个已知 ID |

---

## 完成后

告诉用户：直接用自然语言说「查一下 XX 项目的缺陷」「给这个需求加条评论」即可；日常操作由 tapd-cli 技能承载，本技能以后只在换机器时才需要。
