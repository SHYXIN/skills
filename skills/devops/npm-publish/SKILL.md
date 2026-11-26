---
name: npm-publish
description: "把本地 npm 包发到 registry.npmjs.org 的完整流程（首次配置 + 日常发包，同一个技能内两段）。覆盖：镜像源与官方源的区分、npm adduser 设备授权登录、passkey/WebAuthn 2FA（npm 已停用 TOTP 新建）、发包前预检（包名占用 / publishConfig / prepublishOnly）、发后验证，以及 ENEEDAUTH / EOTP / 403 / EPUBLISHCONFLICT 排障。触发词：npm 发包 / npm publish 报错 / 新电脑发包 / ENEEDAUTH / EOTP / npm 2FA 没有验证器选项 / 账号要 --otp。user-invoked：只允许用户手动调用，不得自动触发。"
---

# npm publish（发包 / 新机器首发）

## 0. 定位与边界

做：把当前仓库的 npm 包发到公共 registry；在新机器上把发包所需的认证一次配好。

不做：版本策略与 changelog、dist-tag 矩阵、`deprecate`/`unpublish`、monorepo 多包发布、CI 流水线编写（CI 只给指针，见 §2.4）。

> 发布不可逆：版本号发出去无法覆盖，改代码只能用新版本号重发。执行前确认 `package.json` 的 `name` / `version` 是想要的。

## 1. 先查事实，不要猜

```powershell
npm config get registry                              # 通常是镜像源
npm whoami --registry=https://registry.npmjs.org     # 失败 = 本机未登录官方源
npm --version
```

再核对 registry 出现的三个位置是否指向同一个源：

- 全局 `~/.npmrc`
- 项目级 `.npmrc`
- `package.json` 的 `publishConfig.registry`

不一致时以 `publishConfig` 为准——改动最小，且不会污染 install 的镜像加速。

## 2. 一次配好（新机器 / 换账号才做，幂等）

### 2.1 把 registry 钉在包上（推荐，一劳永逸）

```json
"publishConfig": {
  "registry": "https://registry.npmjs.org/",
  "access": "public"
}
```

理由：全局源设成 npmmirror 是为了 install 快，但**镜像不接 publish**。钉在包上之后裸跑 `npm publish` 也对，装包仍走镜像。

不要用 `npm config set registry https://registry.npmjs.org` 来发包——装包会变慢，而且下次换机器又会踩回同一个坑。

### 2.2 登录官方源（设备授权，不是输密码）

```powershell
npm adduser --registry=https://registry.npmjs.org
```

- 终端打印 `Create your account at: https://www.npmjs.com/login?next=/login/cli/...`
- 按回车打开浏览器 → 登录 → 网页里过 2FA
- 看到 `Logged in on https://registry.npmjs.org/.` 才算成功

> 通行密钥（passkey）只解决「网页侧 2FA」，**不等于本机已登录**。两步都要做：先配 2FA，再 `npm adduser` 授权本机。

### 2.3 2FA 只能选 passkey（没有验证器 APP 选项）

npm 自 2025-10 起永久禁用 TOTP（Google Authenticator 那类 6 位码）的新建与重配。开通页面只剩 Security key 一类入口：

- 选 Security key 后若提示「请将安全密钥插入 USB 端口」，那是给 YubiKey 的硬件槽位，没有硬件就点【更改】
- Chrome 的通行密钥对话框里选 **Google 密码管理工具（你的谷歌账号）** 或手机；选 Google 密码管理器时，底层仍走 Windows Hello（PIN / 指纹）
- 通行密钥不是可复制的 6 位数字，只在验证时唤起。查看 / 删除：`chrome://password-manager/settings` 或 <https://passwords.google.com>
- 页面给的恢复码必须抄下来——手机丢了、密钥删了只能靠它

### 2.4 token 备选（只作副本，别当主线）

- Granular Access Token：寿命默认 7 天、上限 90 天
- 勾 `bypass 2FA` 的 token 自 2026-07/08 起不能再做账号 / 组织管理，直发已收窄到 staging，官方口径 2027-01 全面取消（实际已滚动执行）
- CI 一律走 Trusted Publishing (OIDC)：<https://docs.npmjs.com/trusted-publishers>

> 旧攻略里「用 automation token 免 OTP 直接发」的写法**已经失效**，不要照抄。

## 3. 发包（每次的动作）

```powershell
npm whoami --registry=https://registry.npmjs.org   # 必须返回你的账号名
npm view <包名> version                            # 404 / 无输出 = 名字没被占
npm publish                                       # 设了 publishConfig 就不用带 --registry
```

- 有 `prepublishOnly` 会把 build + test 再跑一遍，耗时是正常的，别以为卡住
- 终端出现 `Authenticate your account at: https://www.npmjs.com/auth/cli/***` 是正常的：回车 → 浏览器点 **Use security key** → Windows Hello 确认
- 页面上可勾 `Do not challenge requests from this IP for the next N minutes`，本机连着发几个包时少弹几次
- 成功标志是最后一行 `+ <包名>@<版本>`

## 4. 发完立刻验证

```powershell
npm view <包名> version --registry=https://registry.npmjs.org
npm view <包名> dist-tags
```

看到 `Your package is being processed and may take a few minutes to become available` 不算失败：官网可搜到、可被 install 要等几分钟。此时 `npm install -g <包名>` 可能 404，等 1–5 分钟重试。

## 5. 排障：报错 → 病因 → 修法

| 报错 / 现象 | 病因 | 修法 |
|---|---|---|
| `ENEEDAUTH ... logged in to https://registry.npmmirror.com` | 全局源是镜像，镜像不接 publish | 加 `publishConfig.registry`，或临时 `--registry=https://registry.npmjs.org` |
| `ENEEDAUTH ... logged in to https://registry.npmjs.org/` | 本机未登录官方源（配了 passkey 也没用） | `npm adduser --registry=https://registry.npmjs.org` 走设备授权 |
| `EOTP`，或提示要 `--otp` | 账号 2FA 是 auth-and-writes，强制交互式验证 | 按提示在浏览器确认；`--otp=` 收的是会话 token，不是验证器的 6 位数字 |
| 2FA 页面只有 Security key、提示插 USB | TOTP 已被禁用，只剩 WebAuthn 入口 | 点【更改】/在 Chrome 对话框里选「Google 密码管理工具」，别选 USB 安全密钥 |
| `403 Forbidden ... 2FA or granular access token with bypass 2fa required` | registry 侧强制交互式 2FA，与 token 权限无关 | 走 passkey 网页确认；token 直发不可靠 |
| `EPUBLISHCONFLICT` / cannot publish over previously published version | 该版本号已在 registry 上 | 换版本号，npm 不允许覆盖已发版本 |
| `gh auth status` 里 keyring 一行报红 | 那是 GitHub CLI 的凭据，与 npm 无关 | 不要因此去重配 npm |

## 6. 现状事实（截至 2026-11 核实，政策仍在收紧）

- TOTP（验证器 APP）新建与重配：**永久禁用**（2025-10 起）
- bypass-2FA 的 Granular Token：2026-08 起不能做账号 / 组织管理；直发收窄到 staging，2027-01 起全面取消
- CI 官方路径：Trusted Publishing (OIDC)，无需长寿命 token
- 结论：本机手动发 = passkey WebAuthn 确认；CI = trusted publishing；长寿命 token 直发不要再依赖

来源（政策原文，读者可自查）：

- <https://github.blog/changelog/2025-10-10-strengthening-npm-security-important-changes-to-authentication-and-token-management/>
- <https://github.blog/changelog/2026-07-08-npm-install-time-security-and-gat-bypass2fa-deprecation/>
- <https://docs.npmjs.com/about-access-tokens/>
- <https://docs.npmjs.com/trusted-publishers>
