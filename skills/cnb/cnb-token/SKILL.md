---
name: cnb-token
description: 引导用户创建或粘贴 CNB 访问令牌（PAT）并持久化，安装 cnb CLI 并配置 git 凭据，使 cnb 命令行与 git push/pull 到 cnb.cool 免密可用。首次配置 CNB 工具链、cnb 命令报 401/403、或 git 推拉 cnb.cool 要求认证时使用。
---

# CNB 访问令牌初始化

把「让用户拥有可用 CNB 令牌 + cnb CLI + git 免密」这一步标准化。这是 CNB 工具链（建仓、提交、PR、流水线）的入口前置条件。

完成标志是**两条独立链路各自打通**：

- **CLI 链路**：`cnb <子命令>` 能调 API（读用户信息 200）
- **git 链路**：`git push/pull` 到 `https://cnb.cool/...` 免密

两条链路凭据来源不同，配好一条不代表另一条通。

## 背景：为什么不能直接 `cnb login`

`cnb login` 走 OAuth2 设备流，拿到的 `access_token` **默认不含 `group-resource:rw`**，
导致在**组织（group）下建仓库**被 403 拦截（`errcode: 10023, Missing required scopes: group-resource:rw`）。
个人命名空间也可能因 scope 不足失败。

> 正确做法：用 **Personal Access Token (PAT)**，显式勾选所需授权范围，再通过 `CNB_TOKEN`
> 环境变量提供给 cnb CLI 与其 `git-credential` helper。

## 步骤

### 1. 安装 cnb CLI（必经前置，不是可选）

git 凭据助手配置的是 `!cnb git-credential`——**没有 `cnb` 可执行文件，helper 静默失败**，
git 会回落到 Git Credential Manager 弹窗或报 Authentication failed。后续验证步骤也全依赖 CLI。
所以先装 CLI：

```bash
# 跨平台统一（macOS / Linux / Windows 均可，走 npm 镜像加速）
npm install @cnbcool/cnb-cli -g
```

Windows 也可用 PowerShell 官方脚本：

```powershell
irm https://cnb.cool/cnb/skills/cnb-skill/-/git/raw/main/install.ps1 | iex
```

macOS / Linux：`curl -fsSL https://cnb.cool/cnb/skills/cnb-skill/-/git/raw/main/install.sh | sh`

装完验证：`cnb --version` 有输出即可。找不到命令时开新终端（PATH 刷新），或检查 npm 全局 bin 目录。

### 2. 先检查是否已有可用令牌

不要上来就让用户建新令牌。先探测：

```bash
# 方式 A：环境变量里是否已有（CLI 优先读这个）
echo "CNB_TOKEN=${CNB_TOKEN:+已设置}"

# 方式 B：cnb CLI 是否已登录且能正常调用 API
cnb status            # 看是否“已登录”
cnb users get-user-info   # 能返回 200 说明 token 基本可用
```

判断：
- 若 `CNB_TOKEN` 已设置且第 5 步验证通过 → **跳过创建，直接复用**，告诉用户「已就绪」。
- 若 `~/.cnb/token` 存在但只够读个人信息、建组织仓库仍 403 → 仍需走下面建 PAT 的流程。

### 3. 没有令牌 → 引导去创建（只提示，不替用户点）

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

### 4. 持久化令牌

拿到令牌后（记为 `<PAT>`），做三件事：

**(a) 写入环境变量 `CNB_TOKEN`（CLI 优先读它，且会盖掉 `~/.cnb/token` 里缺 scope 的 OAuth token）**

Windows（用户级，重启/新终端自动生效）：

```bash
setx CNB_TOKEN "<PAT>"
```

> 其他平台：`export CNB_TOKEN="<PAT>"` 写进 shell profile（如 `~/.bashrc`），
> 或 CI 里由平台注入。

**(b) 当前会话立即生效**

`setx` 只影响**新**进程，当前 shell 里手动 `export CNB_TOKEN "<PAT>"`（bash）或在 PowerShell 里
`$env:CNB_TOKEN = "<PAT>"`，否则本会话后续命令读不到。

**(c) 配置 git 凭据助手（否则 push 仍要密码）**

```bash
git config --global credential.https://cnb.cool.helper '!cnb git-credential'
```

> 注意 helper 值必须带 `!` 前缀，否则 git 会把 `cnb git-credential` 误解析成
> `git credential-cnb` 子命令而报错（`git: 'credential-cnb' is not a git command`）。
> `!` 让 git 当 shell 命令执行；`cnb git-credential` 在 `CNB_TOKEN` 存在时会返回
> `username=cnb` + `password=<PAT>`。

### 5. 验证「完成」（分链路核对）

两条链路凭据来源不同，**必须各自验证**：

```bash
# ── CLI 链路 ──
cnb users get-user-info        # 期望 status: 200，返回用户信息

# ── git 链路（用一个真实存在的公开/私有仓库测）──
git ls-remote https://cnb.cool/<组织>/<仓库>.git HEAD
# 期望：直接返回 commit hash，全程无弹窗、无 401
```

**判读表**：

| 现象 | 根因 | 处理 |
|------|------|------|
| CLI 200，但 git 报 Authentication failed | helper 依赖的 `cnb` 不在 PATH（CLI 没装或新终端未开） | 回步骤 1 装 CLI / 重开终端，重跑 git 链路验证 |
| git 弹出 Git Credential Manager 窗口 | helper 静默失败的回落行为 | **这不是死路**：弹窗里 Username 填 `cnb`，Password 填 PAT，GCM 会存进 Windows 凭据管理器，之后免密——填完重跑 ls-remote 即可 |
| `cnb git-credential get` 报 unknown host | CLI 子命令对裸 host 的解析怪癖，不影响实际 push | 忽略；以 `git ls-remote` 实测为准 |
| CLI 401/403 且提示缺 scope | `cnb login` 的 OAuth token 残留被读到 | 确认 `CNB_TOKEN` 在当前会话已 export（步骤 4b） |

git 链路通过后，push/pull 免密彻底打通（helper 返回凭据或 GCM 已存凭据，二者任一生效）。

## 完成标志（给用户的话术）

> ✅ CNB 令牌已配置并持久化：
> - `CNB_TOKEN` 已写入环境变量（新终端自动生效）
> - cnb CLI 已安装，API 调用正常
> - git 凭据助手已配置，push/pull 到 cnb.cool 免密
> 接下来建仓库、推代码可直接执行，无需再粘贴令牌。

## 注意事项

- **`~/.cnb/token` 可保留**：它存的是 `cnb login` 的 OAuth token，设置 `CNB_TOKEN` 后会被遮蔽，无需删除。
- **PAT 过期**：到期后用新 PAT 重新 `setx CNB_TOKEN "<PAT>"` 即可。
- **撤销持久化**：`setx CNB_TOKEN ""`（Windows）或在系统属性→环境变量中删除；吊销令牌去 `cnb.cool/profile/token`。
- **GCM 已存凭据的替换**：若凭据管理器里存了旧 PAT，换新 token 后 git 可能仍读旧值。
  Windows 路径：控制面板 → 凭据管理器 → Windows 凭据 → 删除 `git:https://cnb.cool` 条目，下次操作会重新取。
