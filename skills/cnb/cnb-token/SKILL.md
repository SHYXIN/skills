---
name: cnb-token
description: 引导用户创建或粘贴 CNB 访问令牌（PAT）并持久化，使 cnb CLI 与 git push/pull 到 cnb.cool 免密可用；仅负责拿 token，建仓/推送交给 cnb-api、cnb-code-commit 等技能。
---

# CNB 访问令牌初始化

把「让用户拥有可用 CNB 令牌并持久化」这一步标准化。这是 CNB 工具链（建仓、提交、PR、流水线）的入口前置条件。

## 背景：为什么不能直接 `cnb login`

`cnb login` 走 OAuth2 设备流，拿到的 `access_token` **默认不含 `group-resource:rw`**，
导致在**组织（group）下建仓库**被 403 拦截（`errcode: 10023, Missing required scopes: group-resource:rw`）。
个人命名空间也可能因 scope 不足失败。

> 正确做法：用 **Personal Access Token (PAT)**，显式勾选所需授权范围，再通过 `CNB_TOKEN`
> 环境变量提供给 cnb CLI 与其 `git-credential` helper。

## 触发场景

- 用户要新建 CNB 仓库 / 推送代码，但还没配过令牌
- `cnb ...` 命令报 401/403，提示 scope 缺失或「未登录」
- 用户明确要「配 CNB token」「创建访问令牌」

## 步骤

### 1. 先检查是否已有可用令牌

不要上来就让用户建新令牌。先探测：

```bash
# 方式 A：环境变量里是否已有（CLI 优先读这个）
echo "CNB_TOKEN=${CNB_TOKEN:+已设置}"

# 方式 B：cnb CLI 是否已登录且能正常调用 API
cnb status            # 看是否“已登录”
cnb users get-user-info   # 能返回 200 说明 token 基本可用
```

判断：
- 若 `CNB_TOKEN` 已设置且下述「验证」步骤通过 → **跳过创建，直接复用**，告诉用户「已就绪」。
- 若 `~/.cnb/token` 存在但只够读个人信息、建组织仓库仍 403 → 仍需走下面建 PAT 的流程。

### 2. 没有令牌 → 引导去创建（只提示，不替用户点）

提示用户打开：**https://cnb.cool/profile/token** → `添加访问令牌`，并明确勾选：

- **使用范围**：选「私有」（组织/仓库），否则私有资源默认无权限
- **授权范围（按需勾选）**：
  - `group-resource:rw` —— **建/改组织下仓库必备**（最常见的 403 就缺它）
  - 代码仓库读写 —— `git push` 需要
  - 制品库/OpenAPI 等其他范围 —— 视后续用途补勾
- 令牌名称随便（如 `iao-cli`、`cnb-cli`）
- 到期时间按需设置（注意：到期后需重新生成并 `setx`）

创建后让用户**把令牌复制回来粘贴给你**。

> ⚠️ 安全：PAT 是明文密钥。提示用户不要在公开场合粘贴；本技能只临时用于配置，
> 不写进仓库文件。若担心泄漏，用完后可在令牌页吊销并重新生成。

### 3. 持久化令牌

拿到令牌后（记为 `<PAT>`），做两件事：

**(a) 写入环境变量 `CNB_TOKEN`（CLI 优先读它，且会盖掉 `~/.cnb/token` 里缺 scope 的 OAuth token）**

Windows（用户级，重启/新终端自动生效）：

```bash
setx CNB_TOKEN "<PAT>"
```

> 其他平台用等价方式：`export CNB_TOKEN="<PAT>"` 写进 shell profile（如 `~/.bashrc`），
> 或 CI 里由平台注入。

**(b) 让 git push/pull 自动用该令牌（关键，否则 push 仍要输密码）**

```bash
git config --global credential.https://cnb.cool.helper '!cnb git-credential'
```

> 注意 helper 值必须带 `!` 前缀，否则 git 会把 `cnb git-credential` 误解析成
> `git credential-cnb` 子命令而报错（`git: 'credential-cnb' is not a git command`）。
> `!` 让 git 当 shell 命令执行；`cnb git-credential` 在 `CNB_TOKEN` 存在时会返回
> `username=cnb` + `password=<PAT>`。

### 4. 验证「完成」

在本会话也 `export CNB_TOKEN="<PAT>"`（让当前 shell 立即生效），然后验证：

```bash
# 1) CLI 走 CNB_TOKEN（给个假 token 应 401，证明 CLI 优先用 CNB_TOKEN 而非回退 OAuth 文件）
CNB_TOKEN="invalid_token_xyz" cnb users get-user-info   # 期望 401

# 2) 真实 token 下读接口 200
cnb users get-user-info                                    # 期望 status: 200

# 3) git 经 helper 取到凭据（无需把 token 拼进 URL）
git ls-remote https://cnb.cool/<组织>/<仓库>.git           # 期望返回 commit，无 401
```

三项通过即「完成」：后续 `cnb ...` 命令与 `git push/pull` 到 `cnb.cool` 均免密。

## 完成标志（给用户的话术）

> ✅ CNB 令牌已配置并持久化：
> - `CNB_TOKEN` 已写入环境变量（新终端自动生效）
> - git 凭据助手已指向 `cnb git-credential`，push/pull 免密
> 接下来建仓库用 `cnb repositories create-repo --slug <组织> --name <项目>`，
> 推代码直接 `git push`，无需再粘贴令牌。

## 注意事项

- **API base 易踩坑**（建仓时）：OpenAPI 是 `https://api.cnb.cool`，不是 `https://cnb.cool/api/v1`（后者 400）。
  建仓端点示例：`POST https://api.cnb.cool/<slug>/-/repos`，body `{"name":...,"visibility":"private","description":...}`。
  （建仓属 cnb-api 技能范围，本技能不展开。）
- **`~/.cnb/token` 可保留**：它存的是 `cnb login` 的 OAuth token，设置 `CNB_TOKEN` 后会被遮蔽，无需删除。
- **PAT 过期**：到期后用新 PAT 重新 `setx CNB_TOKEN "<PAT>"` 即可。
- **撤销持久化**：`setx CNB_TOKEN ""`（Windows）或在系统属性→环境变量中删除；吊销令牌去 `cnb.cool/profile/token`。
