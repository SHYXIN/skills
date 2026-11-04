# 决策记录（不随技能发布）

运行时配置（SKILL.md / snap.mjs）保持克制，决策史集中在这里。

## machine-snap：从整机快照收窄为 agent 工具箱白名单（2026-11-04）

初版（v1）走「整机快照」路线：capture 全量扫描 winget/choco/pip/npm，实测采出 238 条
（winget 68 / pip 144 / npm 17 / choco 9）。用户审阅后否决——pip 144 条大半是 Python 库
传递依赖（docling/Flask 等拖进来的 certifi/click/requests/urllib3），对 agent 毫无用处。

修订共识（grill 一轮八问）：
- 定位收窄为「agent 工具箱」：只记有利于 agent 工作的东西
- manifest 改为手工白名单：`core`（agent 直接用的 CLI）+ `coreRuntimes`（MCP/skills 依赖
  的 runtime，restore 先装）；白名单随 skill 包走（whitelist.json，可进 git）
- MCP 三客户端 + PATH 增量仍从本机实采（`snap-mcp` 命令），存 ~/.machine-snap/（含 token，
  不进 git）
- capture 的职责由「采集」改为「校验」：doctor 对白名单逐条核对在位性

### v1→v2 实测数据留档

- v1 实测基线：capture 238 条（winget 68 / pip ~150 / npm 17 / choco 3），MCP 4+2+2，
  PATH 36 条；doctor 本机 MISSING=0；redact 全部 `[REDACTED]`
- v2 实测基线：白名单 core 18 + coreRuntimes 4，doctor 22/22 ok；snap-mcp MCP 4+2+2 +
  PATH 36 条；restore --dry-run 正确识别全部已装；redact 无 token 残留

### v2 开发期踩的坑（已修进脚本/白名单，此处留记录）

- 在位探测不能只信当前 shell PATH——Git Bash 会话持陈旧 PATH，winget/pip 刚装完的命令
  会被误判 MISSING；`has()` 已改为合并用户注册表 PATH 一起找
- winget 包 ID 大小写敏感（`GLab.GLab` 不是 `GLab.GitLab`）
- `cn-skills-cli` 包装出来的命令是 `cn-skills`（不是 `skills`）；日常用 `npx skills@latest`
- 本机 python 是 uv 管的（`~/.local/bin`），winget 里没有 Python 条目，白名单记 manual
- v1 时代坑：winget 的 HTTPie.HTTPie 是 Electron GUI 假货不带 `http` CLI（CLI 版走 pip）；
  choco list 的 "Validation Warnings" 提示行曾被包名正则误命中（解析噪音已过滤）
