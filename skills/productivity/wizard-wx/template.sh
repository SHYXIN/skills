#!/usr/bin/env bash
#
# 向导（wizard）——一步步带着人走完一个手工流程。
# 由 /wizard-wx skill 生成。
#
# “STAGES” 标记以上的都是 wizard 库：不要手改。在标记以下编写每一步的 stage。

set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────
# wizard 库——顺滑且一致的体验。在每个 wizard 里都一模一样。
# ──────────────────────────────────────────────────────────────────────────

if [[ -t 1 ]] && command -v tput >/dev/null 2>&1 && [[ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]]; then
  BOLD=$(tput bold); DIM=$(tput dim); RESET=$(tput sgr0)
  BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1)
else
  BOLD=""; DIM=""; RESET=""; BLUE=""; GREEN=""; YELLOW=""; RED=""
fi

# Author sets this at the top of the stages section.
TOTAL_STAGES=0

_STAGE_INDEX=0
ENV_FILE="${ENV_FILE:-.env}"
WRITTEN_ENV=()    # KEYs written to ENV_FILE this run
WRITTEN_SECRET=() # secret NAMEs set this run
SKIPPED=()        # things we couldn't do (e.g. gh missing)

# _clear —— 清屏，让屏幕上只显示当前这一步。非终端输出时为空操作，保证管道日志仍可读。
_clear() {
  [[ -t 1 ]] || return 0
  if command -v tput >/dev/null 2>&1; then tput clear; else printf '\033[2J\033[3J\033[H'; fi
}

# banner "Title" —— 开场框：说明这个 wizard 要做什么。
banner() {
  _clear
  printf '\n%s%s  %s%s\n' "$BOLD" "$BLUE" "$1" "$RESET"
  printf '%s  %s stages%s\n\n' "$DIM" "$TOTAL_STAGES" "$RESET"
  printf '%s  你负责操作浏览器；这个向导会一步步告诉你该做什么，\n' "$DIM"
  printf '  并把你复制回来的值收好。随时可按 Ctrl-C 停下，稍后重跑——\n'
  printf '  它记得已经存过的值。%s\n' "$RESET"
  pause "准备好了就开始？"
}

# stage "Name" —— 清屏，然后宣布一个 stage 并显示进度。清屏让屏幕上只留当前这一步。
stage() {
  _clear
  _STAGE_INDEX=$((_STAGE_INDEX + 1))
  printf '\n%s%s▸ Stage %s/%s · %s%s\n' \
    "$BOLD" "$BLUE" "$_STAGE_INDEX" "$TOTAL_STAGES" "$1" "$RESET"
}

# say "..." —— 一行普通说明。
say()  { printf '  %s\n' "$1"; }
# step "..." —— 人在浏览器里要做的一个带项目符号的动作。
step() { printf '  %s•%s %s\n' "$BLUE" "$RESET" "$1"; }
note() { printf '  %s%s%s\n' "$DIM" "$1" "$RESET"; }
warn() { printf '  %s⚠ %s%s\n' "$YELLOW" "$1" "$RESET"; }

# open_url URL —— 在人的浏览器里打开，跨平台（含 WSL）。
open_url() {
  local url="$1"
  printf '  %s↗ 正在打开%s %s\n' "$GREEN" "$RESET" "$url"
  { if   command -v wslview     >/dev/null 2>&1; then wslview "$url"
    elif command -v explorer.exe >/dev/null 2>&1; then explorer.exe "$url"
    elif command -v xdg-open    >/dev/null 2>&1; then xdg-open "$url"
    elif command -v open        >/dev/null 2>&1; then open "$url"
    else warn "无法打开浏览器——请手动访问：$url"; fi
  } >/dev/null 2>&1 || warn "无法打开浏览器——请手动访问：$url"
}

# pause "msg" —— 等人对刚做的手工步骤确认。
pause() {
  printf '  %s%s%s ' "$DIM" "${1:-按回车继续}" "$RESET"
  read -r _ || true
}

# confirm "question" —— y/N 闸门；选 yes 时返回成功。
confirm() {
  local reply=""
  printf '  %s? %s [y/N] ' "$YELLOW" "$1"
  read -r reply || true
  [[ "$reply" =~ ^[Yy] ]]
}

# _existing KEY —— ENV_FILE 里 KEY 的当前值（如有）。
_existing() {
  [[ -f "$ENV_FILE" ]] || return 1
  local line; line=$(grep -E "^${1}=" "$ENV_FILE" | tail -n1) || return 1
  printf '%s' "${line#*=}"
}

# ask KEY "Prompt" —— 把一个值读进 $KEY。重跑时把 .env 里已有的值作为默认值（回车保留）。可见输入（非 secret）。
ask() {
  local key="$1" prompt="$2" current input
  current=$(_existing "$key" || true)
  if [[ -n "$current" ]]; then
    printf '  %s%s%s %s[回车保留当前值]%s ' "$BOLD" "$prompt" "$RESET" "$DIM" "$RESET"
  else
    printf '  %s%s%s ' "$BOLD" "$prompt" "$RESET"
  fi
  read -r input || true
  [[ -z "$input" && -n "$current" ]] && input="$current"
  printf -v "$key" '%s' "$input"
}

# ask_secret KEY "Prompt" —— 同 ask，但输入隐藏。
ask_secret() {
  local key="$1" prompt="$2" current input
  current=$(_existing "$key" || true)
  if [[ -n "$current" ]]; then
    printf '  %s%s%s %s[回车保留当前值]%s ' "$BOLD" "$prompt" "$RESET" "$DIM" "$RESET"
  else
    printf '  %s%s%s ' "$BOLD" "$prompt" "$RESET"
  fi
  read -rs input || true
  printf '\n'
  [[ -z "$input" && -n "$current" ]] && input="$current"
  printf -v "$key" '%s' "$input"
}

# write_env KEY VALUE —— 把 KEY=VALUE 幂等地 upsert 进 ENV_FILE（没有就创建；有就替换该行）。
write_env() {
  local key="$1" value="$2" tmp
  touch "$ENV_FILE"
  tmp=$(mktemp)
  grep -vE "^${key}=" "$ENV_FILE" > "$tmp" || true
  printf '%s=%s\n' "$key" "$value" >> "$tmp"
  mv "$tmp" "$ENV_FILE"
  WRITTEN_ENV+=("$key")
  printf '  %s✓ 已写入%s %s → %s\n' "$GREEN" "$RESET" "$key" "$ENV_FILE"
}

# set_secret NAME VALUE —— 通过 gh 设置一个 GitHub Actions 仓库 secret。若 gh 不可用或未登录，则降级为警告（并记下）。
set_secret() {
  local name="$1" value="$2"
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    if printf '%s' "$value" | gh secret set "$name" >/dev/null 2>&1; then
      WRITTEN_SECRET+=("$name")
      printf '  %s✓ 已设置%s GitHub secret %s\n' "$GREEN" "$RESET" "$name"
      return
    fi
  fi
  SKIPPED+=("GitHub secret $name（手动设置：gh secret set $name）")
  warn "跳过 GitHub secret $name——gh 未就绪，稍后手动设置"
}

# set_var NAME VALUE —— 设置一个 GitHub Actions 仓库 variable（非 secret）。
set_var() {
  local name="$1" value="$2"
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    if gh variable set "$name" --body "$value" >/dev/null 2>&1; then
      printf '  %s✓ 已设置%s GitHub variable %s\n' "$GREEN" "$RESET" "$name"
      return
    fi
  fi
  SKIPPED+=("GitHub variable $name")
  warn "跳过 GitHub variable $name——gh 未就绪，稍后手动设置"
}

# finish —— 清屏，然后给出一份收尾总结，列出本次配置的所有内容。
finish() {
  _clear
  printf '\n%s%s  ✓ 配置完成%s\n' "$BOLD" "$GREEN" "$RESET"
  (( ${#WRITTEN_ENV[@]} ))    && note "已写入 ${#WRITTEN_ENV[@]} 个值到 $ENV_FILE：${WRITTEN_ENV[*]}"
  (( ${#WRITTEN_SECRET[@]} )) && note "已设置 ${#WRITTEN_SECRET[@]} 个 GitHub secret：${WRITTEN_SECRET[*]}"
  if (( ${#SKIPPED[@]} )); then
    printf '\n'; warn "仍需手动完成："
    for s in "${SKIPPED[@]}"; do note "  - $s"; done
  fi
  printf '\n'
}

# ──────────────────────────────────────────────────────────────────────────
# STAGES —— 编写这一节。人每走一步就写一个 stage()。
# 把下面示例替换掉。把 TOTAL_STAGES 设成你写的 stage 数量。
# ──────────────────────────────────────────────────────────────────────────

TOTAL_STAGES=1

banner "Stripe 配置"

# ── 示例 stage：换成你真实的步骤 ───────────────────────────────────────────
stage "Stripe — API 密钥"
say "我们要取你的 Stripe 测试密钥，存好供本地开发 + CI 使用。"
open_url "https://dashboard.stripe.com/test/apikeys"
step "在 API keys 页面，复制 Publishable key（以 pk_test_ 开头）。"
ask STRIPE_PUBLISHABLE_KEY "粘贴 publishable key："
step "在 Secret key 那一行点 'Reveal test key'，然后复制。"
ask_secret STRIPE_SECRET_KEY "粘贴 secret key："
write_env STRIPE_PUBLISHABLE_KEY "$STRIPE_PUBLISHABLE_KEY"
write_env STRIPE_SECRET_KEY "$STRIPE_SECRET_KEY"
set_secret STRIPE_SECRET_KEY "$STRIPE_SECRET_KEY"   # CI 需要这一个
# ──────────────────────────────────────────────────────────────────────────

finish
