#!/usr/bin/env python3
"""Single-shot prompt to a local DeepWorks workspace agent. Self-contained.

Reads the DeepWorks desktop port/token files, creates an opencode session in
the target workspace, sends ONE user message as-is (the workspace agent's own
system prompt shapes the reply), polls for the final assistant answer, and
writes the answer + a step log next to it.

Standard library only -- no agent-eval import, no third-party deps, runs with
any system Python from any working directory.

Usage:
  python ask_local_deepworks.py \
      --message "你好，请用一句话介绍你自己" \
      [--env prod|test] [--working-dir "C:/path/to/workspace"] [--agent deepworks] \
      [--model "dth/DeepSeek-V4.1-Flash"] [--working-dir-note "背景"] \
      [--timeout 900] [--out-dir <dir>] [--dry-run]

  python ask_local_deepworks.py --delete-session <id|last> [--working-dir ...] [--env ...]
  python ask_local_deepworks.py --delete-ask-sessions [--working-dir ...] [--env ...]

--env picks the desktop install: prod = com.deepexi.deepworks (default),
test = com.deepexi.deepworks.test. The target desktop must be running.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

LOG_STEPS: list[dict] = []
# AppData dir name per environment: prod = official desktop, test = test desktop.
ENV_DIRS = {
    "prod": "com.deepexi.deepworks",
    "test": "com.deepexi.deepworks.test",
}


def appdata_root(env_name: str) -> Path:
    dirname = ENV_DIRS.get(env_name)
    if not dirname:
        raise RuntimeError(f"unknown --env '{env_name}' (expected: {', '.join(ENV_DIRS)})")
    return Path(os.environ.get("APPDATA", "")) / dirname


def log(step: str, detail: str = "") -> None:
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {step}" + (f" {detail}" if detail else "")
    print(line, flush=True)
    LOG_STEPS.append({"t": datetime.now().isoformat(timespec="seconds"), "step": step, "detail": detail})


def norm_key(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").lower()


def read_host_info(working_dir: Path, env_name: str) -> dict:
    root = appdata_root(env_name)
    ports = json.loads((root / "deepworks-port-state.json").read_text(encoding="utf-8"))
    tokens = json.loads((root / "deepworks-server-tokens.json").read_text(encoding="utf-8"))
    key = norm_key(working_dir)
    port = ports.get("workspacePorts", {}).get(key)
    info = tokens.get("workspaces", {}).get(key)
    if not port or not info:
        avail = ", ".join(sorted(ports.get("workspacePorts", {}))) or "(none)"
        raise RuntimeError(f"workspace not open in DeepWorks desktop ({env_name}): {working_dir}\nopen workspaces: {avail}")
    headers = {
        "Authorization": f"Bearer {info.get('clientToken', '')}",
        "X-DeepWorks-Host-Token": info.get("hostToken", ""),
    }
    return {"base_url": f"http://127.0.0.1:{port}", "headers": headers}


def request_json(url: str, method: str = "GET", headers: dict | None = None,
                 body: dict | None = None, timeout: int = 20) -> object:
    data = None
    request_headers = dict(headers or {})
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed: HTTP {exc.code}: {detail}") from exc
    return json.loads(raw) if raw else {}


def resolve_workspace_id(host: dict, working_dir: Path) -> str:
    payload = request_json(f"{host['base_url']}/workspaces", headers=host["headers"])
    key = norm_key(working_dir)
    for item in payload.get("items", []) if isinstance(payload, dict) else []:
        if norm_key(Path(str(item.get("path", "")))) == key:
            return str(item["id"])
    raise RuntimeError(f"workspace not visible from /workspaces: {working_dir}")


def final_assistant_text(messages: list) -> str:
    for message in reversed(messages):
        info = message.get("info", {})
        if info.get("role") != "assistant" or info.get("finish") != "stop":
            continue
        text = "\n".join(str(p.get("text", "")) for p in message.get("parts", []) if p.get("type") == "text")
        if text.strip():
            return text
    return ""


def find_last_session_id(out_dir: Path, env_name: str = "") -> str:
    """Most recent live session_id recorded by this script in out-dir logs.

    With env_name given, only logs from that environment qualify (each env's
    desktop has its own sessions). Records marked session_deleted are skipped
    so 'last' never points at an already-deleted session.
    """
    if not out_dir.is_dir():
        return ""
    for log_path in sorted(out_dir.glob("*.log.json"), reverse=True):
        try:
            data = json.loads(log_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if str(log_path.name).startswith("teams-"):
            continue
        if data.get("session_deleted"):
            continue
        if env_name and data.get("env") != env_name:
            continue
        sid = str(data.get("session_id") or "").strip()
        if sid:
            return sid
    return ""


def recorded_session_ids(out_dir: Path, env_name: str = "") -> list[str]:
    """All live session_ids this script ever recorded in out-dir logs, newest first."""
    ids: list[str] = []
    if not out_dir.is_dir():
        return ids
    for log_path in sorted(out_dir.glob("*.log.json"), reverse=True):
        try:
            data = json.loads(log_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if str(log_path.name).startswith("teams-"):
            continue
        if data.get("session_deleted"):
            continue
        if env_name and data.get("env") != env_name:
            continue
        sid = str(data.get("session_id") or "").strip()
        if sid and sid not in ids:
            ids.append(sid)
    return ids


def mark_session_deleted(out_dir: Path, session_id: str) -> None:
    """Flag the log(s) recording this session as deleted (idempotent)."""
    from datetime import datetime
    for log_path in out_dir.glob("*.log.json"):
        if str(log_path.name).startswith("teams-"):
            continue
        try:
            data = json.loads(log_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if str(data.get("session_id") or "").strip() == session_id and not data.get("session_deleted"):
            data["session_deleted"] = True
            data["session_deleted_at"] = datetime.now().isoformat(timespec="seconds")
            log_path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Ask the local DeepWorks workspace agent one question.")
    ap.add_argument("--message", default="", help="the question, sent to the agent as-is (omit for delete modes)")
    ap.add_argument("--working-dir", default=None,
                    help="workspace dir open in DeepWorks desktop (auto-picked if only one is open)")
    ap.add_argument("--agent", default="deepworks", help="agent name inside the workspace (default: deepworks)")
    ap.add_argument("--model", default=None,
                    help="model for this call, e.g. 'dth/DeepSeek-V4.1-Flash' (provider prefix optional, default dth)")
    ap.add_argument("--working-dir-note", default="", help="optional context note prepended to the message")
    ap.add_argument("--env", default="prod", choices=sorted(ENV_DIRS),
                    help="which DeepWorks desktop install to talk to (default: prod)")
    ap.add_argument("--out-dir", default="C:/code_proj/tmp/dp-agent-eval-logs", help="where to write answer+log")
    ap.add_argument("--timeout", type=int, default=900, help="seconds to wait for the final answer")
    ap.add_argument("--dry-run", action="store_true", help="print the message that would be sent, then exit")
    ap.add_argument("--delete-session", default="", metavar="ID|last",
                    help="delete one session by id, or 'last' for the one created by the most recent run (from out-dir logs), then exit")
    ap.add_argument("--delete-ask-sessions", action="store_true",
                    help="delete ALL sessions recorded in out-dir logs (every run of this script), then exit")
    ap.add_argument("--list-sessions", nargs="?", const="20", default="", metavar="N",
                    help="list the N most recent sessions in the workspace (default 20), then exit")
    args = ap.parse_args()

    wd = Path(args.working_dir).resolve() if args.working_dir else None
    note = args.working_dir_note.strip()
    message = f"{note}\n{args.message}" if note else args.message

    # ----- list mode (same prerequisites as delete: desktop up + working dir) -----
    if args.list_sessions:
        try:
            limit = int(args.list_sessions)
        except ValueError:
            print(f"FAIL: --list-sessions expects a number, got {args.list_sessions!r}", file=sys.stderr)
            return 2
        if wd is None:
            print("FAIL: --working-dir is required for --list-sessions", file=sys.stderr)
            return 2
        log(f"environment: {args.env} ({ENV_DIRS[args.env]})")
        host = read_host_info(wd, args.env)
        workspace_id = resolve_workspace_id(host, wd)
        base = f"{host['base_url']}/workspace/{urllib.parse.quote(workspace_id)}/sessions"
        rows = request_json(base, headers=host["headers"])
        rows = rows.get("items", []) if isinstance(rows, dict) else rows
        print(f"== sessions in {wd} (env={args.env}, showing up to {limit}) ==")
        shown = 0
        for r in rows:
            if shown >= limit:
                break
            sid = str(r.get("id") or "")
            title = str(r.get("title") or r.get("name") or "(untitled)")
            print(f"{sid} | {title}")
            shown += 1
        if not shown:
            print("(no sessions)")
        return 0

    # ----- delete modes (need desktop up + working dir, but no prompting) -----
    if args.delete_session or args.delete_ask_sessions:
        if wd is None:
            print("FAIL: --working-dir is required for delete modes", file=sys.stderr)
            return 2
        log(f"environment: {args.env} ({ENV_DIRS[args.env]})")
        host = read_host_info(wd, args.env)
        workspace_id = resolve_workspace_id(host, wd)
        base = f"{host['base_url']}/workspace/{urllib.parse.quote(workspace_id)}/sessions"

        def delete_one(sid: str) -> None:
            request_json(f"{base}/{urllib.parse.quote(sid)}", method="DELETE", headers=host["headers"])
            mark_session_deleted(Path(args.out_dir), sid)
            log("session deleted", f"env={args.env} session_id={sid}")

        if args.delete_session:
            target_id = args.delete_session.strip()
            if target_id == "last":
                target_id = find_last_session_id(Path(args.out_dir), args.env)
                if not target_id:
                    print(f"FAIL: no previous live session id found in out-dir logs for env={args.env}",
                          file=sys.stderr)
                    return 2
            delete_one(target_id)
        if args.delete_ask_sessions:
            ids = recorded_session_ids(Path(args.out_dir), args.env)
            deleted, failed = 0, 0
            for sid in ids:
                try:
                    delete_one(sid)
                    deleted += 1
                except Exception as exc:  # noqa: BLE001
                    failed += 1
                    log("delete failed, keep going", f"session_id={sid} {str(exc)[:100]}")
            log("batch delete done", f"{deleted} deleted, {failed} failed, {len(ids)} recorded in {args.out_dir}")
        return 0

    if args.dry_run:
        print("===== MESSAGE (dry-run, as-is) =====\n")
        print(message)
        return 0

    if not message.strip():
        print("FAIL: --message is required (or use --delete-session / --delete-ask-sessions)",
              file=sys.stderr)
        return 2

    if wd is None:
        root = appdata_root(args.env)
        opened = list(json.loads(
            (root / "deepworks-port-state.json").read_text(encoding="utf-8")
        ).get("workspacePorts", {}))
        if len(opened) == 1:
            wd = Path(opened[0])
            log("workspace auto-picked", str(wd))
        else:
            print(f"FAIL: multiple/no workspaces open in {args.env} desktop, pass --working-dir. Open: "
                  + ", ".join(opened), file=sys.stderr)
            return 2

    t0 = time.perf_counter()
    log(f"environment: {args.env} ({ENV_DIRS[args.env]})")
    log("read desktop port/token files")
    host = read_host_info(wd, args.env)
    log("resolve workspace", f"{wd}")
    workspace_id = resolve_workspace_id(host, wd)
    base = f"{host['base_url']}/workspace/{urllib.parse.quote(workspace_id)}/opencode"
    log("creating session", f"workspace_id={workspace_id} agent={args.agent}")
    session = request_json(
        f"{base}/session", method="POST", headers=host["headers"],
        body={"directory": str(wd), "title": f"ask-local {datetime.now().strftime('%Y%m%d-%H%M%S')}",
              "agent": args.agent},
    )
    session_id = session.get("id") or session.get("sessionID") if isinstance(session, dict) else None
    if not session_id:
        raise RuntimeError(f"create session did not return id: {session}")
    log("session created", f"session_id={session_id}")

    # Record the session id immediately so --delete-session/--delete-ask-sessions
    # can clean it up even if this run later times out.
    out_dir_early = Path(args.out_dir)
    out_dir_early.mkdir(parents=True, exist_ok=True)
    record_path = out_dir_early / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.log.json"
    record_path.write_text(json.dumps({
        "env": args.env, "session_id": session_id, "working_dir": str(wd),
        "status": "started", "steps": LOG_STEPS,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    log("session recorded", record_path.name)

    prompt_headers = {**host["headers"], "x-opencode-directory": str(wd)}
    prompt_body: dict = {"agent": args.agent, "parts": [{"type": "text", "text": message}]}
    if args.model:
        # Verified 2026-10-12: "model" must be an OBJECT here; a plain string is
        # rejected by payload schema and the prompt is silently dropped.
        provider, _, model_id = args.model.partition("/")
        if not model_id:
            provider, model_id = "dth", args.model
        prompt_body["model"] = {"providerID": provider, "modelID": model_id}
        log("model override", f"{provider}/{model_id}")
    request_json(f"{base}/session/{urllib.parse.quote(session_id)}/prompt_async",
                 method="POST", headers=prompt_headers, body=prompt_body)
    log("prompt sent", f"chars={len(message)}")

    deadline = time.monotonic() + args.timeout
    messages: list = []
    while time.monotonic() < deadline:
        url = (f"{base}/session/{urllib.parse.quote(session_id)}/message"
               f"?limit=200&directory={urllib.parse.quote(str(wd))}")
        payload = request_json(url, headers=prompt_headers)
        messages = payload if isinstance(payload, list) else (payload.get("items", []) if isinstance(payload, dict) else [])
        if final_assistant_text(messages):
            break
        time.sleep(2)

    answer = final_assistant_text(messages)
    if not answer:
        raise TimeoutError(f"no final assistant answer within {args.timeout}s: {session_id}")
    latency = time.perf_counter() - t0
    log("answer received", f"latency={latency:.1f}s")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = record_path.stem.removesuffix(".log")
    answer_path = out_dir / f"{stamp}.answer.md"
    log_path = record_path
    answer_path.write_text(
        f"# ask-local {stamp}\n\n- env: {args.env}\n- workspace: {wd}\n- model: {args.model or '(workspace default)'}\n"
        f"- latency: {latency:.1f}s\n\n## 提问\n\n{args.message}\n\n## 回答\n\n{answer}\n",
        encoding="utf-8",
    )
    log_path.write_text(json.dumps({
        "env": args.env, "session_id": session_id, "workspace_id": workspace_id, "working_dir": str(wd),
        "latency_seconds": round(latency, 1), "steps": LOG_STEPS,
        "messages_tail": json.dumps(messages, ensure_ascii=False)[-4000:],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    log("saved", f"{answer_path.name}, {log_path.name}")

    print("\n===== ANSWER =====\n")
    print(answer)
    print(f"\n-----\nfiles: {answer_path}\n        {log_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, TimeoutError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
