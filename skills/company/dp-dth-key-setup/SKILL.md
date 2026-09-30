---
name: dp-dth-key-setup
description: 把 DeepWorks 桌面端（闫丽霞企业账号）的积分计费 DTH/TokenHub API key 接入本地 AI coding agent 的 pi 配置。触发词：配 DeepWorks 积分 key / DTH key / TokenHub / 积分接 pi / key 轮换后重新同步。从 Electron localStorage (leveldb) 提取 modelPlatformApiKey 并写入 ~/.pi/agent/ 三件套，端到端验证。仅 Windows + 已安装 DeepWorks 桌面端。
---

# DTH Key Setup（DeepWorks 积分 key → pi）

把"DeepWorks 桌面端登录后每天发的 token"接进 pi coding agent，走**积分计费**通道（TokenHub），而不是 DTS 美元余额。

## 适用 / 不适用

**适用**：
- 用户说"把 DeepWorks 积分接进 pi / 配 DTH key / TokenHub key 轮换后同步"
- 新机器装好 DeepWorks 桌面端并登录后，第一次给 pi 配 key
- key 过期/轮换后的重新同步（桌面端重新登录即可拿到新 key）

**不适用**：
- DeepWorks 桌面端未安装或从未登录（没有 localStorage 凭据可提取）
- 给 DTS（dts.deepexi.com 美元余额）配 key——那是另一套体系
- Linux/macOS（leveldb 路径、APPDATA 布局不同，脚本未适配）

## 原理链路（30 秒版）

```
IAM 登录（企业 SSO 账号）
  → userInfo.modelPlatformApiKey（积分计费 key，形如 sk-xxx，长约 51）
  → DeepWorks 桌面端 Electron window.localStorage（leveldb，磁盘持久层）
  → 本 skill 脚本解析 leveldb 提取最新 key
  → 写入 ~/.pi/agent/{auth.json, models.json, settings.json}
  → pi 走 https://tokenhub-<env>.deepexios.cn/gateway/api/v1（OpenAI 兼容）
```

网关按安装版本自动判定：userData 目录名带 `.test`（如 `com.deepexi.deepworks.test`）→ test 网关；否则 prod 网关。两套环境 key 不通用（test key 打 prod 网关 401，属正常隔离）。

## 快速路径（首选）

```powershell
# 1. 先看检测到什么（不改任何文件）
node <skill_dir>/scripts/sync-deepworks-dth-key.mjs --dry-run

# 2. 确认账号/网关无误后写入（幂等；写前自动备份）
node <skill_dir>/scripts/sync-deepworks-dth-key.mjs

# 3. 端到端验证（消耗几十 token 积分）
pi --provider dth --model DeepSeek-V4-Flash --no-session --no-tools -p "回复一个字：好"
```

脚本行为：
- 自动扫 `%APPDATA%\com.deepexi.deepworks` 和 `%APPDATA%\com.deepexi.deepworks.test` 两个 userData 的 leveldb（运行中的 DeepWorks 会锁文件，脚本先拷到 temp 再解析，不会影响桌面端）
- 多条凭据按 `updated_at` 取最新；打印账号/租户/更新时间/key 指纹（不打印完整 key）
- 已一致时不重写；写入前对三件套做 `*.bak-<时间戳>` 备份
- 参数：`--gateway test|prod` 强制网关；`--pi-dir <dir>` 指定其他 pi 目录；`--deepworks-dir <dir>` 指定非默认 userData

写入内容：
| 文件 | 变化 |
|---|---|
| `auth.json` | 新增/更新 `"dth": {"type": "api_key", "key": "..."}`，不动其他 provider |
| `models.json` | 新增/更新 `providers.dth`：baseUrl + api=openai-completions + 13 个模型 |
| `settings.json` | `defaultProvider=dth`、`defaultModel=DeepSeek-V4-Flash`，enabledModels 追加 `dth/*` |

## 手工路径（脚本失败时）

脚本输出"未找到任何 DeepWorks 登录凭据"时，按序排查：

1. **确认登录过**：打开 DeepWorks 桌面端看右上角是否已登录企业账号
2. **确认 userData 目录**：`Get-ChildItem $env:APPDATA -Filter "com.deepexi.deepworks*"`，把实际目录用 `--deepworks-dir` 传给脚本
3. **leveldb 解析要点**（自己解析时的坑，均已踩过）：
   - `.ldb` 文件被进程锁定 → 先 `Copy-Item` 到 temp 再读
   - data block 可能 snappy 压缩（compression 字节 0=raw 1=snappy + 4B crc）
   - localStorage value **首字节 `\x00` 是编码标记，必须去掉**再按 UTF-16LE 解码（否则错位 1 字节，正则全失配）
   - key 在 `deepworks.iamAuth.userInfo.v1` 条目里，正则 `"modelPlatformApiKey":\s*"([^"]+)"`，同时比对 `updated_at` 取新
   - `.log`（WAL）里也可能有最新未 compact 的记录，按 UTF-16 直接扫同一正则
4. **网关连通性**：拿到 key 后先 curl `/models`，401 → 换另一个 env 网关试试；`invalid JSON body` → PowerShell 5.1 用 curl.exe 传 JSON 体常坏，改 `Invoke-WebRequest` + UTF8 bytes
5. **400 `developer is not one of ['system','assistant',...]`**（或 GLM 系报"角色信息不正确"）：TokenHub 网关背后的模型不认 OpenAI 新式 `developer` 角色。pi 侧修复 = models.json 的 dth provider 加 `"compat": {"supportsDeveloperRole": false}`（脚本已内置）。诊断技巧：本地起一个日志代理（node http 转发并落盘请求体），把 baseUrl 临时指过去，抓 pi 真实请求做 bisect
6. **400 `model is not configured` / `No available channel`**：网关模型目录会变（如 Qwen3.8-Flash-Next 已下线、Deepexi-E-Max-2.0 曾无渠道）。以 `/models` 实时返回为准，从 models.json 里删掉失效模型，settings.json enabledModels 同步清理

## 切回其他 provider

```powershell
pi --provider openai   # DTS 美元余额（淘汰中）
pi --provider nous     # 本地 nous
# 或改 ~/.pi/agent/settings.json 的 defaultProvider/defaultModel
```

## 扩展：接入其他 agent（预留位）

skill 当前只实现了 pi 目标。要支持其他 coding agent，在 `scripts/` 加对应的写入模块、复用提取逻辑即可。已知的对接点：

- **opencode**：DeepWorks 源码里 DTH 本来就走 opencode `auth.set`（providerId=`"dth"`，`{type:"api",key}`）写入 `~/.local/share/opencode/auth.json`（XDG_DATA_HOME 隔离时路径不同）
- **claude code / 其他**：凡是"OpenAI 兼容 baseUrl + api key"型配置都能接，网关 `https://tokenhub-<env>.deepexios.cn/gateway/api/v1`，模型 id 必须与网关 `/models` 返回完全一致（大小写敏感，如 `DeepSeek-V4-Flash`）

新 agent 的写入模块做成 `sync-deepworks-dth-key-<agent>.mjs`，共享同一个提取函数；提取脚本可从 `scripts/sync-deepworks-dth-key.mjs` 里的 `collectCandidates()`/`parseTable()` 拷贝（纯 Node 零依赖，含 snappy 解码）。

## 模型目录（test 网关，2026-09-30 校准）

DeepSeek-V4-Flash / V4-Pro / V4.1-Flash、GLM-5.2 / 5.3 / 5.3-Flash、Kimi-K3 / K2.6、Qwen-3.8-Max / Qwen3.8-27B、Deepexi-E-Max-2.0 / E-Pro-2.0。应用默认模型是 Deepexi-E-Max-2.0；脚本给 pi 设的默认是 DeepSeek-V4-Flash（便宜）。**目录会变**：Qwen3.8-Flash-Next 已于 2026-09-30 前下线；以网关 `/models` 实时返回为准。全部模型必须走 `compat.supportsDeveloperRole: false`（部分模型拒绝 developer 角色，见手工路径第 5 条）。
