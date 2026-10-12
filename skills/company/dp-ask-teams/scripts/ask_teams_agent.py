#!/usr/bin/env python3
"""Single-shot task to an Agent Teams cloud agent. Self-contained.

Reads AGENT_TEAMS_* settings from --env-file (or OS env), logs in via IAM,
resolves workspace/project/agent, creates a chat session, sends ONE message
as-is, polls (SSE first, snapshot fallback) to completion, and collects the
latest assistant reply.

Standard library only -- no agent-eval import, no third-party deps, runs with
any system Python from any working directory.

Usage:
  python ask_teams_agent.py                     # no --message / --agent-name: list agents, exit
  python ask_teams_agent.py \
      --message "你好，请用一句话介绍你自己" \
      [--env-file "C:/path/to/agent-eval/.env"] --agent-name "设备故障诊断专家" \
      [--note "背景"] [--timeout 1200] [--out-dir <dir>] [--no-sync-token] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

LOG_STEPS: list[dict] = []
TERMINAL_EVENTS = {"task:completed", "task:failed", "task:cancelled", "chat_squad_run:completed", "chat_squad_run:failed"}


def log(step: str, detail: str = "") -> None:
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {step}" + (f" {detail}" if detail else "")
    print(line, flush=True)
    LOG_STEPS.append({"t": datetime.now().isoformat(timespec="seconds"), "step": step, "detail": detail})


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip().lstrip("\ufeff")] = value.strip().strip('"').strip("'")
    return values


def text(value: object) -> str:
    return value if isinstance(value, str) else ""


def items(payload: object) -> list:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("items", "workspaces", "projects", "agents", "squads", "sessions", "messages", "artifacts"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


class TeamsClient:
    def __init__(self, env: dict[str, str]):
        self.env = env
        self._cached: tuple[str, str] | None = None

    def _env(self, key: str, default: str = "") -> str:
        value = self.env.get(key, default)
        return value.strip() if isinstance(value, str) else ""

    def base_url(self) -> str:
        base = self._env("AGENT_TEAMS_BASE_URL")
        if not base:
            raise RuntimeError("AGENT_TEAMS_BASE_URL is required")
        return base.rstrip("/")

    def bearer(self) -> str:
        token = self._env("AGENT_TEAMS_TOKEN")
        if not token:
            raise RuntimeError("AGENT_TEAMS_TOKEN is required")
        if self._env("AGENT_TEAMS_AUTH_MODE", "iam").lower() == "pat":
            return token
        if self._cached and self._cached[0] == token:
            return self._cached[1]
        session_response = self.request("/auth/session-token", method="POST",
                                        body={"token": token}, auth=False, allow_error=True)
        session_token = text(session_response.get("token")) if isinstance(session_response, dict) else ""
        if not session_token:
            iam = self.request("/auth/iam/access-token", method="POST", body={"accessToken": token}, auth=False)
            session_token = text(iam.get("token")) if isinstance(iam, dict) else ""
        if not session_token:
            raise RuntimeError("Agent Teams login did not return a bearer token")
        self._cached = (token, session_token)
        return session_token

    def request(self, path: str, method: str = "GET", workspace_slug: str | None = None,
                body: dict | None = None, auth: bool = True, allow_error: bool = False) -> object:
        headers = {"Accept": "application/json"}
        if workspace_slug:
            headers["x-workspace-slug"] = workspace_slug
        if auth:
            headers["Authorization"] = f"Bearer {self.bearer()}"
        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(f"{self.base_url()}{path}", data=data, headers=headers, method=method)
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
                    raw = response.read().decode("utf-8")
                return json.loads(raw) if raw.strip() else {}
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                if allow_error:
                    return {"_http_error": exc.code, "body": detail}
                last_error = RuntimeError(f"{method} {path} failed: HTTP {exc.code}: {detail}")
                if exc.code not in {502, 503, 504} or attempt == 2:
                    raise last_error from exc
            except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
                last_error = exc
                if attempt == 2:
                    raise
            time.sleep(2 * (attempt + 1))
        raise last_error or RuntimeError("request failed")

    def stream_sse(self, path: str, workspace_slug: str, deadline: float) -> list:
        headers = {
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {self.bearer()}",
            "x-workspace-slug": workspace_slug,
        }
        request = urllib.request.Request(f"{self.base_url()}{path}", headers=headers, method="GET")
        events: list = []
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            for raw_line in response:
                if time.monotonic() >= deadline:
                    break
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if not data or data == "[DONE]":
                    continue
                event = json.loads(data)
                events.append(event)
                if has_terminal_event([event]):
                    break
        return events


def has_terminal_event(events: list) -> bool:
    for event in events:
        if not isinstance(event, dict):
            continue
        if text(event.get("type")) in TERMINAL_EVENTS:
            return True
        payload = event.get("payload")
        if isinstance(payload, dict) and text(payload.get("status")).lower() in {"completed", "failed", "cancelled"}:
            return True
    return False


def find_by_name(entries: list, name: str, kind: str) -> dict:
    if not entries:
        raise RuntimeError(f"No Agent Teams {kind} items available")
    dicts = [e for e in entries if isinstance(e, dict)]
    if not name:
        return dicts[0]
    matches = [e for e in dicts if text(e.get("name")).strip() == name]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        available = ", ".join(text(e.get("name")) for e in dicts)
        raise RuntimeError(f"Agent Teams {kind} not found by name '{name}'. Available: {available}")
    raise RuntimeError(f"Agent Teams {kind} name is ambiguous: {name}")


def resolve_workspace(client: TeamsClient, env: dict[str, str]) -> str:
    workspace_slug = env.get("AGENT_TEAMS_WORKSPACE_SLUG", "").strip()
    if not workspace_slug:
        workspaces = items(client.request("/api/workspaces"))
        workspace = find_by_name(workspaces, env.get("AGENT_TEAMS_WORKSPACE_NAME", "").strip(), "workspace")
        workspace_slug = text(workspace.get("slug"))
    if not workspace_slug:
        raise RuntimeError("Agent Teams workspace not resolved")
    return workspace_slug


def resolve_target(client: TeamsClient, env: dict[str, str], agent_name: str) -> dict[str, str]:
    workspace_slug = resolve_workspace(client, env)
    agent_id = env.get("AGENT_TEAMS_TARGET_ID", "").strip()
    if agent_id:
        project_id = env.get("AGENT_TEAMS_PROJECT_ID", "").strip()
        if not project_id:
            projects = items(client.request("/api/projects", workspace_slug=workspace_slug))
            project = find_by_name(projects, env.get("AGENT_TEAMS_PROJECT_NAME", "").strip(), "project")
            project_id = text(project.get("id"))
        if not project_id:
            raise RuntimeError("Agent Teams project not resolved")
        return {"workspace_slug": workspace_slug, "project_id": project_id, "agent_id": agent_id}

    # Search the preferred project first, then every other project — experts
    # live in different projects (e.g. 通用 vs DeepSense in Deepology UI).
    projects = items(client.request("/api/projects", workspace_slug=workspace_slug))
    preferred_name = env.get("AGENT_TEAMS_PROJECT_NAME", "").strip()
    preferred_id = env.get("AGENT_TEAMS_PROJECT_ID", "").strip()
    ordered = sorted(
        [p for p in projects if isinstance(p, dict)],
        key=lambda p: 0 if text(p.get("id")) == preferred_id or text(p.get("name")).strip() == preferred_name else 1,
    )
    searched: list[str] = []
    for project in ordered:
        project_id = text(project.get("id"))
        params = urllib.parse.urlencode({"project_id": project_id})
        agents = items(client.request(f"/api/agents?{params}", workspace_slug=workspace_slug))
        dicts = [a for a in agents if isinstance(a, dict)]
        matches = [a for a in dicts if text(a.get("name")).strip() == agent_name]
        if len(matches) == 1:
            return {"workspace_slug": workspace_slug, "project_id": project_id,
                    "agent_id": text(matches[0].get("id"))}
        searched.extend(text(a.get("name")) for a in dicts)
    raise RuntimeError(f"Agent Teams agent not found by name '{agent_name}'. Available: " + ", ".join(searched))


def list_agents(client: TeamsClient, env: dict[str, str]) -> None:
    workspace_slug = resolve_workspace(client, env)
    projects = items(client.request("/api/projects", workspace_slug=workspace_slug))
    preferred_name = env.get("AGENT_TEAMS_PROJECT_NAME", "").strip()
    preferred_id = env.get("AGENT_TEAMS_PROJECT_ID", "").strip()
    ordered = sorted(
        [p for p in projects if isinstance(p, dict)],
        key=lambda p: 0 if text(p.get("id")) == preferred_id or text(p.get("name")).strip() == preferred_name else 1,
    )
    total = 0
    print(f"workspace: {workspace_slug}")
    for project in ordered:
        project_name = text(project.get("name")) or text(project.get("id"))
        params = urllib.parse.urlencode({"project_id": text(project.get("id"))})
        agents = [a for a in items(client.request(f"/api/agents?{params}", workspace_slug=workspace_slug))
                  if isinstance(a, dict)]
        print(f"\n## {project_name} ({len(agents)} agents)")
        for agent in agents:
            total += 1
            desc = text(agent.get("description")).strip().splitlines()
            summary = desc[0][:60] if desc else ""
            print(f"- {text(agent.get('name')).strip()}  {('# ' + summary) if summary else ''}")
    print(f"\n{total} agents total. Re-run with --agent-name <名称> --message <任务> to send one task.")


def main() -> int:
    ap = argparse.ArgumentParser(description="Send one task to an Agent Teams cloud agent and wait for completion.")
    ap.add_argument("--message", default="", help="the task, sent to the agent as-is (omit to just list agents)")
    ap.add_argument("--env-file", default=None,
                    help="env file with AGENT_TEAMS_* (default: C:/code_proj/gitlab-proj/agent-eval/.env)")
    ap.add_argument("--agent-name", default="",
                    help="agent name; omit (or use --list) to list available agents and exit")
    ap.add_argument("--list", action="store_true", help="list all agents across projects, then exit")
    ap.add_argument("--note", default="", help="optional context note prepended to the message")
    ap.add_argument("--out-dir", default="C:/code_proj/tmp/dp-agent-eval-logs", help="where to write answer+log")
    ap.add_argument("--timeout", type=int, default=1200, help="seconds to wait for completion")
    ap.add_argument("--no-sync-token", action="store_true", help="skip IAM token refresh from desktop app")
    ap.add_argument("--dry-run", action="store_true", help="print the message that would be sent, then exit")
    args = ap.parse_args()

    env_path = Path(args.env_file) if args.env_file else Path("C:/code_proj/gitlab-proj/agent-eval/.env")
    env = dict(os.environ)
    env.update(load_env_file(env_path))
    if "AGENT_TEAMS_TOKEN" not in env or not env["AGENT_TEAMS_TOKEN"].strip():
        print(f"FAIL: AGENT_TEAMS_TOKEN missing (env file: {env_path})", file=sys.stderr)
        return 2
    agent_name = args.agent_name.strip()

    note = args.note.strip()
    message = f"{note}\n{args.message}" if note else args.message

    client = TeamsClient(env)
    if args.list or not message or not agent_name:
        if message and not agent_name:
            print("No --agent-name given; listing available agents instead of sending.\n")
        elif agent_name and not message:
            print("No --message given; listing available agents instead of sending.\n")
        log("login via IAM")
        list_agents(client, env)
        return 0
    if args.dry_run:
        print("===== MESSAGE (dry-run, as-is) =====\n")
        print(message)
        return 0

    if not args.no_sync_token:
        try:
            import urllib.request as _u
            _u.urlopen("http://127.0.0.1:9223", timeout=2)
            sync_script = env_path.parent / "scripts" / "sync_deepworks_iam_token.py"
            if sync_script.is_file():
                log("refreshing IAM token from desktop app")
                subprocess.run([sys.executable, str(sync_script)], check=False, capture_output=True)
        except OSError:
            log("desktop debug port unreachable, keep existing token")

    t0 = time.perf_counter()
    log("login via IAM")
    target = resolve_target(client, env, agent_name)
    log("target resolved", f"workspace={target['workspace_slug']} agent_id={target['agent_id'][:12]}...")

    session = client.request("/api/chat/sessions", method="POST", workspace_slug=target["workspace_slug"],
                             body={"project_id": target["project_id"], "target_type": "agent",
                                   "agent_id": target["agent_id"],
                                   "title": f"ask-teams {datetime.now().strftime('%Y%m%d-%H%M%S')}"})
    session_id = text(session.get("id")) if isinstance(session, dict) else ""
    if not session_id:
        raise RuntimeError(f"create chat session did not return id: {session}")
    log("session created", f"session_id={session_id}")

    sent = client.request(f"/api/chat/sessions/{urllib.parse.quote(session_id)}/messages", method="POST",
                          workspace_slug=target["workspace_slug"],
                          body={"content": message, "attachment_ids": [], "force_fresh_session": False})
    task_id = text(sent.get("taskId") or sent.get("task_id")) if isinstance(sent, dict) else ""
    run_id = text(sent.get("runId") or sent.get("run_id")) if isinstance(sent, dict) else ""
    log("message sent", f"task_id={task_id} run_id={run_id} raw_keys={sorted(sent.keys()) if isinstance(sent, dict) else '?'}")

    deadline = time.monotonic() + args.timeout
    status = ""
    if run_id:
        try:
            log("streaming run events (SSE)")
            events = client.stream_sse(f"/api/chat/runs/{urllib.parse.quote(run_id)}/events",
                                       target["workspace_slug"], deadline)
            status = "completed" if has_terminal_event(events) else "stream-incomplete"
            log("stream ended", f"{len(events)} events, terminal={has_terminal_event(events)}")
        except Exception as exc:  # noqa: BLE001
            log("stream failed, fall back to polling", str(exc)[:120])

    if status != "completed":
        while time.monotonic() < deadline:
            if run_id:
                snapshot = client.request(f"/api/chat/runs/{urllib.parse.quote(run_id)}/snapshot",
                                          workspace_slug=target["workspace_slug"])
                status = text(snapshot.get("status")).lower() if isinstance(snapshot, dict) else ""
            elif task_id:
                task = client.request(f"/api/tasks/{urllib.parse.quote(task_id)}",
                                      workspace_slug=target["workspace_slug"])
                status = text(task.get("status")).lower() if isinstance(task, dict) else ""
            else:
                raise RuntimeError("neither run_id nor task_id returned from send")
            if status in {"completed", "failed", "cancelled"}:
                break
            time.sleep(3)
        else:
            raise TimeoutError(f"Agent Teams run did not complete within {args.timeout}s")

    payload = client.request(f"/api/chat/sessions/{urllib.parse.quote(session_id)}/messages",
                             workspace_slug=target["workspace_slug"])
    answer = ""
    for entry in reversed(items(payload)):
        if isinstance(entry, dict) and text(entry.get("role")) == "assistant" and text(entry.get("content")).strip():
            answer = text(entry.get("content")).strip()
            break
    if not answer:
        raise RuntimeError(f"run {status} but no assistant text found in session messages")
    latency = time.perf_counter() - t0
    log("answer received", f"status={status} latency={latency:.1f}s")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    answer_path = out_dir / f"teams-{stamp}.answer.md"
    log_path = out_dir / f"teams-{stamp}.log.json"
    answer_path.write_text(
        f"# ask-teams {stamp}\n\n- agent: {agent_name}\n- status: {status}\n- latency: {latency:.1f}s\n\n"
        f"## 任务\n\n{args.message}\n\n## 结果\n\n{answer}\n",
        encoding="utf-8",
    )
    log_path.write_text(json.dumps({
        "session_id": session_id, "task_id": task_id, "run_id": run_id, "status": status,
        "agent_name": agent_name, "latency_seconds": round(latency, 1), "steps": LOG_STEPS,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    log("saved", f"{answer_path.name}, {log_path.name}")

    print("\n===== ANSWER =====\n")
    print(answer)
    print(f"\n-----\nfiles: {answer_path}\n        {log_path}")
    return 0 if status == "completed" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, TimeoutError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
