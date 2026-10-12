#!/usr/bin/env python3
"""DeepWorks 会话取证 -- 云端版（Agent Teams cloud sessions）+ 本地转发。

与本地版（dp-session-forensics）的分工：
  --source teams  查 Agent Teams 云端会话（走云 API，IAM token 自动同步）
  --source local  转发兄弟技能 dp-session-forensics 的 query_sessions.py（查本机 opencode.db）

用法:
  python query_cloud_sessions.py [--source teams] [--env test] list [--limit 20] [--title KEYWORD]
  python query_cloud_sessions.py [--source teams] [--env test] dump <session_id>
  python query_cloud_sessions.py [--source teams] [--env test] export <session_id> [--out DIR]
  # --source local 时同名子命令转发本地版；本地版专属子命令（injections/reasoning）请直接用本地技能。

环境:
  --env test  云端 test.deepworks.cn（默认，对齐 dp-ask-teams）
  --env prod  云端 agentteam.deepworks.cn（需 AGENT_TEAMS_TOKEN_PROD）
  # --source local 时 --env 映射为本地桌面端 prod/test 库。

自包含策略：认证链路直接 import 兄弟技能 dp-ask-teams 的 ask_teams_agent.py，
不复制 TeamsClient / token 同步代码，避免两份漂移。找不到时用 --teams-script 指定。
"""
from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_ENV = "test"
SOURCES = ("teams", "local")

SKILL_DIR = Path(__file__).resolve().parent  # .../company/dp-session-forensics-cloud/scripts
COMPANY_DIR = SKILL_DIR.parent.parent  # .../company

TEAMS_SCRIPT = COMPANY_DIR / "dp-ask-teams" / "scripts" / "ask_teams_agent.py"
LOCAL_SCRIPT = COMPANY_DIR / "dp-session-forensics" / "scripts" / "query_sessions.py"


def load_teams_module(script: Path):
    if not script.is_file():
        sys.exit(
            f"找不到 dp-ask-teams 脚本: {script}\n"
            f"用 --teams-script 指定 ask_teams_agent.py 路径后重试。"
        )
    spec = importlib.util.spec_from_file_location("ask_teams_agent", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def items(payload: object) -> list:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("items", "list", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []


def fmt_ts(value: object) -> str:
    raw = str(value or "")
    return raw[:19].replace("T", " ")


# ---------------------------------------------------------------------------
# teams source
# ---------------------------------------------------------------------------

def teams_client(teams, args):
    env_file = Path(args.env_file) if args.env_file else Path(teams.DEFAULT_ENV_FILE) \
        if hasattr(teams, "DEFAULT_ENV_FILE") else Path("C:/code_proj/gitlab-proj/agent-eval/.env")
    import os
    env = dict(os.environ)
    env.update(teams.load_env_file(env_file))
    if not args.no_sync_token:
        teams.sync_iam_token(env, args.env)
    return teams.TeamsClient(env, env_name=args.env)


def resolve_ws(teams, client, args) -> str:
    import os
    env = dict(os.environ)
    env.update(teams.load_env_file(Path(args.env_file) if args.env_file
                                   else Path("C:/code_proj/gitlab-proj/agent-eval/.env")))
    return teams.resolve_workspace(client, env)


def cmd_teams_list(teams, args) -> int:
    client = teams_client(teams, args)
    ws = resolve_ws(teams, client, args)
    resp = client.request("/api/chat/sessions", workspace_slug=ws)
    sessions = items(resp)
    keyword = (args.title or "").lower()
    if keyword:
        sessions = [s for s in sessions if keyword in str(s.get("title", "")).lower()]
    sessions.sort(key=lambda s: str(s.get("created_at", "")), reverse=True)
    sessions = sessions[: args.limit]
    print(f"共 {len(sessions)} 个会话 (env={args.env} workspace={ws})")
    for s in sessions:
        ts = fmt_ts(s.get("created_at"))
        target = s.get("target_type", "")
        agent = s.get("agent_id", "") or s.get("squad_id", "")
        print(f"{s['id']}  {ts}  [{target}]  {str(s.get('title', ''))[:60]}  agent={str(agent)[:8]}")
    return 0


def fetch_messages(client, ws: str, session_id: str) -> list:
    resp = client.request(
        f"/api/chat/sessions/{session_id}/messages", workspace_slug=ws, allow_error=True
    )
    if isinstance(resp, dict) and "_http_error" in resp:
        sys.exit(f"拉取消息失败: HTTP {resp['_http_error']}: {resp['body'][:200]}")
    return items(resp)


def render_conversation(messages: list) -> str:
    lines = []
    for m in messages:
        role = str(m.get("role", "?")).upper()
        ts = fmt_ts(m.get("created_at"))
        elapsed = m.get("elapsed_ms")
        head = f"=== [{ts}] {role}"
        if elapsed:
            head += f"  ({int(elapsed) / 1000:.1f}s)"
        lines.append(head)
        lines.append(str(m.get("content", "")))
        lines.append("")
    return "\n".join(lines)


def cmd_teams_dump(teams, args) -> int:
    client = teams_client(teams, args)
    ws = resolve_ws(teams, client, args)
    messages = fetch_messages(client, ws, args.session_id)
    print(render_conversation(messages))
    return 0


def cmd_teams_export(teams, args) -> int:
    client = teams_client(teams, args)
    ws = resolve_ws(teams, client, args)
    messages = fetch_messages(client, ws, args.session_id)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = out_dir / f"teams-session-{args.session_id[:8]}-{stamp}"

    jsonl_path = base.with_suffix(".jsonl")
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for m in messages:
            fh.write(json.dumps(m, ensure_ascii=False) + "\n")

    md_path = base.with_suffix(".md")
    md_path.write_text(
        f"# Agent Teams 会话导出\n\n- session: `{args.session_id}`\n"
        f"- env: {args.env}\n- exported: {stamp}\n- messages: {len(messages)}\n\n"
        f"---\n\n{render_conversation(messages)}",
        encoding="utf-8",
    )
    print(f"exported: {jsonl_path}")
    print(f"exported: {md_path}")
    return 0


# ---------------------------------------------------------------------------
# local forwarding
# ---------------------------------------------------------------------------

def forward_local(args, extra: list) -> int:
    if not LOCAL_SCRIPT.is_file():
        sys.exit(f"找不到本地取证脚本: {LOCAL_SCRIPT}")
    cmd = [sys.executable, str(LOCAL_SCRIPT), "--env", args.env] + extra
    proc = subprocess.run(cmd)
    return proc.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description="DeepWorks 会话取证：云端(Agent Teams) + 本地转发。")
    ap.add_argument("--source", default="teams", choices=SOURCES,
                    help="teams=云 API（默认）; local=转发本地版查 opencode.db")
    ap.add_argument("--env", default=None, choices=("prod", "test"),
                    help="test=测试环境（云端默认）/ prod=正式环境；本地库同名映射")
    ap.add_argument("--env-file", default=None, help="AGENT_TEAMS_* env 文件（teams 源用）")
    ap.add_argument("--no-sync-token", action="store_true", help="跳过从桌面端同步 IAM token")
    ap.add_argument("--teams-script", default=str(TEAMS_SCRIPT),
                    help="dp-ask-teams 的 ask_teams_agent.py 路径")

    sub = ap.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="列出会话")
    p_list.add_argument("--limit", type=int, default=20)
    p_list.add_argument("--title", default="", help="按标题关键字过滤（teams）")
    p_list.add_argument("--dir", default="", help="按目录关键字过滤（local）")

    p_dump = sub.add_parser("dump", help="打印一个会话的消息明细")
    p_dump.add_argument("session_id")
    p_dump.add_argument("--roles", default="", help="role 过滤（local 转发用）")

    p_export = sub.add_parser("export", help="导出 jsonl + markdown")
    p_export.add_argument("session_id")
    p_export.add_argument("--out", default="C:/code_proj/tmp/dp-forensics-cloud")
    p_export.add_argument("--roles", default="", help="role 过滤（local 转发用）")

    args = ap.parse_args()

    # 默认环境：teams 源对齐 dp-ask-teams 的 test；local 源对齐本地版的 prod。
    if args.env is None:
        args.env = DEFAULT_ENV if args.source == "teams" else "prod"

    if args.source == "local":
        extra = [args.cmd]
        if args.cmd == "list":
            extra += ["--limit", str(args.limit)]
            if args.dir:
                extra += ["--dir", args.dir]
        else:
            extra += [args.session_id]
            if args.roles:
                extra += ["--roles", args.roles]
            if args.cmd == "export" and args.out:
                extra += ["--out", args.out]
        return forward_local(args, extra)

    teams = load_teams_module(Path(args.teams_script))
    if args.cmd == "list":
        return cmd_teams_list(teams, args)
    if args.cmd == "dump":
        return cmd_teams_dump(teams, args)
    if args.cmd == "export":
        return cmd_teams_export(teams, args)
    ap.error(f"未知子命令: {args.cmd}")


if __name__ == "__main__":
    sys.exit(main())
