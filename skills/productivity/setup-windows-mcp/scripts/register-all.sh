#!/usr/bin/env bash
# register-all.sh — 在新 Windows 机器上一键把 windows-mcp 注册到 codebuddy / claude / codex
# 用法:
#   bash register-all.sh              # 注册到全部检测到的 CLI
#   bash register-all.sh codebuddy    # 只注册指定 CLI（可多个，空格分隔）
#   bash register-all.sh --mirror     # 先写 UV_DEFAULT_INDEX 国内镜像（用户级）再注册
set -euo pipefail

# ---------- 颜色 ----------
info()  { printf '\033[36m[info]\033[0m %s\n' "$*"; }
ok()    { printf '\033[32m[ ok ]\033[0m %s\n' "$*"; }
warn()  { printf '\033[33m[warn]\033[0m %s\n' "$*"; }
fail()  { printf '\033[31m[fail]\033[0m %s\n' "$*"; exit 1; }

MIRROR=0
TARGETS=()
for arg in "$@"; do
  case "$arg" in
    --mirror) MIRROR=1 ;;
    codebuddy|claude|codex) TARGETS+=("$arg") ;;
    *) warn "未知参数: $arg（忽略）" ;;
  esac
done
# 不指定目标 = 三件套全试
[[ ${#TARGETS[@]} -eq 0 ]] && TARGETS=(codebuddy claude codex)

# ---------- 可选：先配 PyPI 国内镜像（Windows 用户级） ----------
if [[ $MIRROR -eq 1 ]]; then
  info "写入 UV_DEFAULT_INDEX 用户级环境变量（清华镜像）..."
  powershell.exe -NoProfile -Command '[Environment]::SetEnvironmentVariable("UV_DEFAULT_INDEX", "https://pypi.tuna.tsinghua.edu.cn/simple", "User")' \
    && ok "UV_DEFAULT_INDEX 已写入用户级" \
    || warn "镜像写入失败，可按 SKILL.md 步骤二手动配置"
fi

# ---------- 探测 uvx 全路径 ----------
UVX=""
for p in \
  "$USERPROFILE/.local/bin/uvx.exe" \
  "$LOCALAPPDATA/hermes/bin/uvx.exe" \
  "$LOCALAPPDATA/Programs/uv/uvx.exe"; do
  [[ -f "$p" ]] && UVX="$p" && break
done
# PATH 里找（cygpath 把 /c/... 转成 C:\...）
if [[ -z "$UVX" ]]; then
  if command -v uvx.exe >/dev/null 2>&1; then
    UVX=$(cygpath -w "$(command -v uvx.exe)")
  elif command -v uvx >/dev/null 2>&1; then
    UVX=$(cygpath -w "$(command -v uvx)")
  fi
fi
[[ -z "$UVX" ]] && fail "找不到 uvx.exe。先安装 uv（见 SKILL.md 步骤一），开新终端后重试。"
# 统一分隔符：候选列表里是混合分隔符拼出来的路径，各 CLI 配置里统一用反斜杠（避免 C:\Users\x/.local 混用）
UVX=$(cygpath -w "$UVX")
ok "uvx 路径: $UVX"

# 预拉包验证（把网络问题暴露在可控阶段）
info "预拉 windows-mcp 包（首次约 1-2 分钟）..."
"$UVX" windows-mcp --help >/dev/null 2>&1 \
  && ok "windows-mcp 可运行" \
  || fail "windows-mcp 运行失败。国内网络超时？加 --mirror 重跑本脚本。"

register_failed=()
for t in "${TARGETS[@]}"; do
  case "$t" in
    codebuddy)
      if ! command -v codebuddy >/dev/null 2>&1; then warn "codebuddy 未安装，跳过"; register_failed+=("codebuddy(未装)"); continue; fi
      # 会话运行中 mcp add 可能 EADDRINUSE，失败则退回直接写配置文件
      if codebuddy mcp add --scope user --transport stdio windows-mcp -- "$UVX" windows-mcp serve >/dev/null 2>&1; then
        ok "codebuddy: 已注册（user 级）"
      else
        MCPJSON="$USERPROFILE/.codebuddy/.mcp.json"
        mkdir -p "$USERPROFILE/.codebuddy"
        if [[ -f "$MCPJSON" ]] && grep -q windows-mcp "$MCPJSON"; then
          ok "codebuddy: 配置文件已含 windows-mcp，跳过"
        else
          # 合并进已有 JSON 或新建（用 node 避免手拼 JSON 出错；node 随 codebuddy/nvm 必有）
          if command -v node >/dev/null 2>&1; then
            node -e '
              const fs = require("fs");
              const p = process.argv[1], uvx = process.argv[2];
              let c = {};
              if (fs.existsSync(p)) { try { c = JSON.parse(fs.readFileSync(p, "utf8")); } catch (e) { c = {}; } }
              c.mcpServers = c.mcpServers || {};
              c.mcpServers["windows-mcp"] = { type: "stdio", command: uvx, args: ["windows-mcp", "serve"] };
              fs.writeFileSync(p, JSON.stringify(c, null, 2));
            ' "$MCPJSON" "$UVX" && ok "codebuddy: 已写入 $MCPJSON（mcp add 被占用，走文件合并）" \
              || { warn "codebuddy: 写入失败"; register_failed+=("codebuddy"); }
          else
            warn "codebuddy: mcp add 失败且无 node 可合并 JSON，请按 SKILL.md 手动编辑 $MCPJSON"; register_failed+=("codebuddy")
          fi
        fi
      fi
      ;;
    claude)
      if ! command -v claude >/dev/null 2>&1; then warn "claude 未安装，跳过"; register_failed+=("claude(未装)"); continue; fi
      # 注意：claude mcp add 默认写「当前目录的项目级」local 配置，必须 -s user 才是全局；
      # 且必须从 home 目录跑，避免注册进某个项目的 local scope
      if (cd "$USERPROFILE" && claude mcp add -s user --transport stdio windows-mcp -- "$UVX" windows-mcp serve >/dev/null 2>&1); then
        ok "claude: 已注册（user 级）"
      elif (cd "$USERPROFILE" && claude mcp get windows-mcp >/dev/null 2>&1); then
        ok "claude: user 级已存在，跳过"
      else
        warn "claude: user 级注册失败，请按 SKILL.md 手动执行"; register_failed+=("claude")
      fi
      ;;
    codex)
      if [[ ! -f "$USERPROFILE/.codex/config.toml" ]]; then warn "codex 未安装（无 config.toml），跳过"; register_failed+=("codex(未装)"); continue; fi
      if grep -q 'mcp_servers.windows-mcp' "$USERPROFILE/.codex/config.toml"; then
        ok "codex: config.toml 已含 windows-mcp，跳过"
      else
        # TOML 追加（command 用单引号字面量，反斜杠无需转义）
        {
          printf '\n[mcp_servers.windows-mcp]\n'
          printf "command = '%s'\n" "$UVX"
          printf 'args = ["windows-mcp", "serve"]\n'
          printf 'startup_timeout_sec = 120\n'
        } >> "$USERPROFILE/.codex/config.toml" \
          && ok "codex: 已追加到 config.toml" \
          || { warn "codex: 追加失败"; register_failed+=("codex"); }
      fi
      ;;
  esac
done

echo
echo "=========================================="
if [[ ${#register_failed[@]} -eq 0 ]]; then
  ok "全部完成。重启各 CLI 后用 /mcp 验证连接，再让 agent 截屏测试。"
else
  warn "完成，但以下目标需人工处理: ${register_failed[*]}"
fi
