---
name: setup-claude-code
description: "在一台新机器上初始化 Claude Code 的关键设置：skipWebFetchPreflight（跳过 WebFetch 域名预检，解决国内网络下 'Unable to verify if domain is safe to fetch' 报错）、permissions.defaultMode: bypassPermissions（完全权限，不再弹确认框），以及可选的 windows-mcp 注册（已装则跳过，未装转交 setup-windows-mcp）。幂等改写 ~/.claude/settings.json，含 JSON 校验。首次配置 Claude Code、或 WebFetch 报域名校验错误、或想关掉权限确认框时使用。"
---# Claude Code 设置初始化（skipWebFetchPreflight + bypassPermissions）

## 这个 skill 解决什么

Claude Code 在国内网络环境有两个高频痛点，都落在 `~/.claude/settings.json`：

1. **WebFetch 不可用**：WebFetch 抓取任何 URL 前，会先请求 `claude.ai/api/web/domain_info` 做域名安全校验。国内访问不到这个端点，预检失败，报：
   ```
   Error: Unable to verify if domain xxx.com is safe to fetch.
   This may be due to network restrictions or enterprise security policies blocking claude.ai.
   ```
   注意报错文案有误导性——不是目标网站被拦，是校验端点本身不可达。
   **解法：顶层加 `"skipWebFetchPreflight": true`，整个预检被跳过**，不再需要代理。

2. **权限确认框太频繁**：默认模式下文件写入、Bash 命令都要弹确认。
   **解法：`permissions.defaultMode` 设为 `"bypassPermissions"`**，所有工具调用直接执行。
   ⚠️ 风险：删除文件、git push 等操作不再有确认环节。只在你信任的环境开启。

**常见误区**：
- `skipWebFetchPreflight` 必须放 settings.json **顶层**，不是 `env` 对象里。
- 这两个设置都是 Claude Code 专有概念，CodeBuddy / Codex 等其他 agent 的配置文件不适用。
- WebFetch 摘要模型由 `ANTHROPIC_DEFAULT_HAIKU_MODEL` 控制（第三方 API 场景需设成中转支持的模型名），与本 skill 的两项设置独立。

---

## Step 1 —— 探测现有配置（幂等）

```bash
python -c "import json; d=json.load(open(r'C:/Users/<用户名>/.claude/settings.json', encoding='utf-8')); print(json.dumps({'skipWebFetchPreflight': d.get('skipWebFetchPreflight'), 'defaultMode': d.get('permissions', {}).get('defaultMode')}, indent=2))"
```

（Linux/macOS 把路径换成 `~/.claude/settings.json`；文件不存在则视为全新配置。）

三种情况：
- 两项都已是目标值 → 告知用户无需改动，结束
- 文件存在但缺项 → 走 Step 2 增量补
- 文件不存在 → 走 Step 2 创建

## Step 2 —— 写入设置

用 Python 做增改（保序、不破坏已有键），**不要**整文件重写覆盖：

```bash
python - <<'EOF'
import json, os

path = os.path.expanduser('~/.claude/settings.json')
if os.path.exists(path):
    with open(path, encoding='utf-8') as f:
        content = f.read().strip()
    d = json.loads(content) if content else {}
    # 记录原有键顺序
    keys = list(d.keys())
else:
    d, keys = {}, []

# 1) 顶层跳过 WebFetch 预检
d['skipWebFetchPreflight'] = True
if 'skipWebFetchPreflight' not in keys:
    keys.insert(0, 'skipWebFetchPreflight')

# 2) 完全权限
d.setdefault('permissions', {})
d['permissions']['defaultMode'] = 'bypassPermissions'
if 'permissions' not in keys:
    keys.append('permissions')

# 按原顺序输出，保持缩进风格
ordered = {k: d[k] for k in keys if k in d}
ordered.update({k: d[k] for k in d if k not in ordered})

with open(path, 'w', encoding='utf-8') as f:
    json.dump(ordered, f, ensure_ascii=False, indent=2)

print('written:', path)
EOF
```

## Step 3 —— 校验并告知重启

```bash
python -c "import json, os; d=json.load(open(os.path.expanduser('~/.claude/settings.json'), encoding='utf-8')); print('skipWebFetchPreflight =', d.get('skipWebFetchPreflight')); print('defaultMode =', d.get('permissions', {}).get('defaultMode'))"
```

预期输出两项都为目标值（`True` / `bypassPermissions`），JSON 解析无异常。

最后告知用户：
- `skipWebFetchPreflight` 当前 session 即时生效
- `defaultMode` 需要**重启 claude** 才加载
- 重启后用 WebFetch 抓任意网页验证不再报域名校验错误

## Step 4 ——（可选）windows-mcp 注册探测

Windows 桌面自动化 MCP（截屏、点击、UI 树）在 Claude Code 里走 `~/.claude.json` 顶层 `mcpServers`。**幂等探测，已配好就跳过，不重复注册**：

```bash
python -c "import json, os; d=json.load(open(os.path.expanduser('~/.claude.json'), encoding='utf-8')); s=d.get('mcpServers', {}).get('windows-mcp'); print(json.dumps(s, indent=2) if s else 'NOT REGISTERED')"
```

三种情况：

1. **已注册且 `command` 指向的 uvx.exe 存在** → 告知用户已配好，跳过本步
2. **已注册但 uvx.exe 路径失效** → 重新探测本机 uvx（`where uvx` / `~/.local/bin/uvx.exe` / `%LOCALAPPDATA%/hermes/bin/uvx.exe`），用 Python 增改该条目；uvx 本身没了则归入情况 3
3. **未注册 / uvx 未安装** → **转交 `setup-windows-mcp` skill**（覆盖 uv 安装、国内镜像加速、三 CLI 注册），本 skill 不重复造轮子

情况 2 的快速修复（探测到新 uvx 路径后）：

```bash
python - <<'EOF'
import json, os
p = os.path.expanduser('~/.claude.json')
with open(p, encoding='utf-8') as f:
    d = json.load(f)
d.setdefault('mcpServers', {})['windows-mcp'] = {
    "type": "stdio",
    "command": r"<探测到的 uvx.exe 全路径>",
    "args": ["windows-mcp", "serve"],
    "env": {},
}
with open(p, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print('windows-mcp re-registered ->', p)
EOF
```

验证：`"C:/path/to/uvx.exe" windows-mcp --help` 能输出 Usage 即为可运行；MCP 连接需重启 claude 生效。

---

## 踩坑记录

1. **报错文案误导**：「Unable to verify if domain is safe to fetch」让人以为是目标网站的问题，实际是 `claude.ai` 校验端点不可达。放行 claude.ai 或直接跳过预检均可，跳过最省事。
2. **`skipWebFetchPreflight` 放错层级**：放进 `env` 对象里无效，必须是 settings.json 顶层字段。
3. **第三方 API 的第二层坑**：预检跳过后，WebFetch 内部还要调小模型做摘要。若走第三方中转（`ANTHROPIC_BASE_URL` 非官方），需确保 `ANTHROPIC_DEFAULT_HAIKU_MODEL` 指向中转支持的模型，否则 fetch 会静默退化成 curl。
4. **代理端口想当然**：挂代理解决预检时，别照搬经典的 7890——先 `netstat -an | grep LISTEN` 看本机代理真实端口（如 Clash Verge 默认 7897）。端口写错会导致所有 API 流量 ConnectionRefused。用了 `skipWebFetchPreflight` 后则不再依赖代理。
5. **windows-mcp 的 uvx 路径漂移**：`~/.claude.json` 里注册的是 uvx **绝对路径**，uv 升级换目录（如 `hermes/bin` → `.local/bin`）后路径失效，MCP 连接静默失败。修法不是重装包，是探测新路径后改注册条目。
