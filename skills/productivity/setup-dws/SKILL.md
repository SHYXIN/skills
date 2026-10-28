---
name: setup-dws
description: 在一台新机器上配置 dws CLI（钉钉 Workspace CLI，npm 包 dingtalk-workspace-cli）——让 agent 能操作钉钉消息/日历/文档/待办/审批等 25+ 服务。覆盖前置检查、npm 安装、OAuth 扫码登录、auth status 验证与常见排障。用户手动调用（/setup-dws）。
---

# dws CLI（钉钉）配置

让 agent 能操作用户**已登录的钉钉**：消息、日历、文档、待办、审批、钉盘、知识库等。dws 自带认证管理（OAuth 扫码 + token 自动刷新），**无需配任何环境变量**。

 dingtalk-* 官方家族技能（dingtalk-chat / dingtalk-calendar / dingtalk-doc 等 15 个）是 dws 的使用说明书，本技能只管装环境和登录。

---

## Step 1 —— 探测现状（幂等）

```bash
dws --version        # CLI 是否已装
dws auth status      # 认证是否有效
```

三种情况：

- **已装且 `authenticated: true`、`token_valid: true`** → 无需配置，直接可用
- **已装但 token 失效** → 跳 Step 3 重新登录
- **全新机器** → 从 Step 2 开始

`GREEN:` 两项现状已知。

---

## Step 2 —— 安装 CLI

```bash
npm install -g dingtalk-workspace-cli
dws --version
```

`GREEN:` `dws --version` 输出版本号（当前已知可用 1.0.62+）。

Node 版本过低时先用 nvm 升级再装。

---

## Step 3 —— 登录（引导用户扫码）

```bash
dws auth login
```

会弹出 OAuth 流程：终端展示二维码或链接，**用户用钉钉 App 扫码确认**。脚本零凭据——认证态由 dws 自己保存并自动刷新（refresh token 有效期约 30 天）。

`GREEN:` `dws auth status` 输出 `"authenticated": true, "token_valid": true`。

---

## Step 4 —— 冒烟测试

```bash
dws auth status
```

再让 agent 跑一条只读命令确认端到端可用（如查今日日程或列未读会话，任选对应 dingtalk-* 技能里的命令）。

`GREEN:` 只读命令返回真实数据。

---

## 排障

| 症状 | 原因与处理 |
|------|-----------|
| `token_valid: false` 但 `refresh_token_valid: true` | 跑 `dws auth login`，通常静默刷新无需扫码 |
| `refresh_token_valid: false` | refresh token 过期（约 30 天），必须重新扫码登录 |
| 多组织登录混乱 | `dws auth logout` 后重新 login，按提示选组织 |
| npm 安装慢 | 用国内镜像 `--registry=https://registry.npmmirror.com` |

---

## 完成后

告诉用户：直接用自然语言说「看下钉钉今天日程」「给 XX 发消息」即可；日常操作由 dingtalk-* 家族技能承载，本技能以后只在换机器或 token 彻底过期时才需要。
