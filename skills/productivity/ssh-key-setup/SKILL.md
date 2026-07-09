---
name: ssh-key-setup
description: 在一台新机器上生成一对 SSH 密钥并登记到多个远端 git 服务（gitLab、GitHub、Gitee 等）。每台机器只生成一次密钥，同一把公钥可登记到任意多个远端；最后 ssh -T 验证每个远端连通、清除 https 残留凭据。用户手动调用（/ssh-key-setup）。
---

# SSH 密钥设置

给一台机器建立和各个远端 git 服务的 **联姻（marriage）**：这台机器有一对唯一的 ed25519 密钥代表它的身份，同一把公钥可以登记（联姻）到 gitLab、GitHub、Gitee 等多个远端。之后所有 git 走 SSH，不再落 token 到 URL / 凭据文件里。

**核心概念 — 联姻（marriage）**：机器身份与远端服务账号之间的一次绑定。一台机器 → 一对密钥（唯一身份）→ 可以登记多个远端。某天某个远端"离婚"（删掉公钥）不影响机器本身的身份，也不影响其他远端。

---

## 前置条件

1. 先读 `references/server-facts.md` —— 默认远端清单、各远端验证命令都在里面
2. 确认这是**新机器初始化**场景 —— 技能假设机器上还没有需要迁移的 https 老仓库（那是另一个任务）
3. 如果你的权限系统挡了到 `gitlab.*` / `github.*` 的 SSH 出站，先告知用户停下

然后进 Step 1。

---

## Step 1 —— 探测本机已有身份（幂等）

```bash
ls -la ~/.ssh/id_ed25519* 2>/dev/null
```

三种情况：

- **密钥已存在** → 读指纹：`ssh-keygen -lf ~/.ssh/id_ed25519.pub`，告知用户现有指纹，进入 Step 2（复用，不再生成）
- **没有密钥** → 进 Step 1b

`GREEN:` 两个分支之一落定，指纹已知。

### Step 1b —— 生成身份

```bash
ssh-keygen -t ed25519 -C "$(whoami)@$(hostname)-$(date +%Y%m%d)" -f ~/.ssh/id_ed25519 -N ""
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
```

`GREEN:` `~/.ssh/id_ed25519` 存在、权限 600、`ssh-keygen -lf` 输出合法指纹。

---

## Step 2 —— 确认远端清单

展示 `server-facts.md` 中的默认远端清单。每条显示：
- 远端域名
- 当前婚姻状况（`~/.ssh/known_hosts` + 用户是否已在该服务有账号）

列完**问一次**让用户增删名单，得到的清单就是这轮要走完的"联姻计划"。

`GREEN:` 用户确认了最终清单（至少一个远端）。

---

## Step 3 —— 逐个登记

对计划里每个远端：

### 3a. 上传公钥

在生成密钥的那台机器上打印公钥，让用户去网页粘贴：

```bash
cat ~/.ssh/id_ed25519.pub
```

同时给出每个远端的**上传页面地址**（从 `server-facts.md` 取）。指导用户：
1. 打开上传页面
2. 整行粘入公钥
3. 保存

**不要**尝试自动化上传 —— 每家服务 API/UI 都不同，自动化凭证存储恰恰是本技能要避免的风险。

`GREEN:` 用户确认"已上传到 <host>"。

### 3b. 验证婚姻

跑 `server-facts.md` 里对应远端的验证命令，返回远端用户名则成功。

gitLab 示例:
```bash
ssh -T -o StrictHostKeyChecking=accept-new git@gitlab.deepexi.com
# → Welcome to GitLab, @<用户名>!
```

GitHub 示例:
```bash
ssh -T -o StrictHostKeyChecking=accept-new git@github.com
# → Hi <用户名>! You've successfully authenticated...
```

`GREEN:` 得到远端返回的身份字符串。失败 → 重新检查是否已上传；不要继续下一个远端。

---

## Step 4 —— 清理旧 https 凭据（可选）

提醒用户检查旧的 token 凭据：

```bash
cat ~/.git-credentials 2>/dev/null                   # 应为空
grep -rn "glpat\|oauth2:" ~/.git-credentials ~/.netrc 2>/dev/null
```

条目存在且用户确认清理：

```bash
: > ~/.git-credentials
```

`GREEN:` 凭据文件里无 PAT / token（或用户选择保留）。

---

## Step 5 —— 出报告

每个登记完的远端打印：
- 远端域名
- 婚姻状态（验证通过的身份）
- 公钥指纹（留档）
- 以后可随时跑的验证命令：`ssh -T git@<host>`

末尾提示：
- 新密钥对无需备份 —— 将来"再婚"（登记新远端）很便宜，只有这台机器重新生成才是锚定步骤；
- 未来新机器重复本技能即可。每台机器各有自己的密钥对，同一远端服务通过接受同一用户账号下的多把公钥来"联姻多台机器"。

`GREEN:` N 个远端验证通过、零 token 残留、报告交付。

---

## 踩过的坑

### 坑 1 —— Windows 公钥带 CRLF

Windows 上复制公钥粘进网页时可能带入不可见字符。验证失败且无明显原因时：

```bash
# 在生成密钥的那台机器上清洗
sed -i 's/\r$//' ~/.ssh/id_ed25519.pub
cat ~/.ssh/id_ed25519.pub   # 重新复制这个干净版本
```

### 坑 2 —— 老 sshd 拒绝 `accept-new`

gitLab 15.2 / CentOS 8 上验证命令会打出：

```
command-line line 0: unsupported option "accept-new".
```

**这是外观警告，底层的认证握手已成功。不要当失败处理。** 想静音：

```bash
ssh -T -o StrictHostKeyChecking=no git@host
```

### 坑 3 —— 开通 2FA 的服务用 https 需要 token、用 SSH 不需要

本技能故意绕开 2FA 摩擦。技能跑完后，这台机器上不再需要给 git 操作备 personal access token —— 密钥对比 token 强：
- 旧 PAT（如有）应该去服务后台**吊销**，减小攻击面；
- 恢复码 / 备份访问仍需安全存放（防机器丢钥）。

### 坑 4 —— 一台机器、一把钥匙、多家服务

不要每个远端生成一把新密钥。**一把钥匙、多家联姻。** 只有在新机器上才需要新密钥对。

---

## 按需"离婚"（回滚）

按远端单个操作：
1. 去服务的网页（SSH Keys 设置页）删掉对应的公钥
2. 无需重新生成本地密钥对 —— 和一个远端离婚不影响其他远端

整台机器身份泄露：

```bash
rm ~/.ssh/id_ed25519 ~/.ssh/id_ed25519.pub
# 从 Step 1b 重跑本技能
```
