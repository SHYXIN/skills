#!/usr/bin/env python3
"""DeepWorks console admin: manage agents / skills / squads via the Agent Teams
management API -- executed inside the logged-in management console tab through
Chrome DevTools Protocol (CDP).

Management write operations require a console session (Workbench OIDC
login, JWT src=console); desktop-app tokens (src=app) carry no
permissions, so a pure-Bearer CLI cannot do writes here.

Auth flow (first run): script launches a controlled Chrome with a dedicated
profile (cookie persists across runs), opens the console; the Workbench
enterprise login page appears; the script auto-fills enterprise
account/password (or you log in manually) and waits for the redirect. Later
runs reuse the persisted session silently.

Usage:
  python dp_console_admin.py list agents|skills|squads|runtimes
  python dp_console_admin.py create-skill --name N --instructions I [--publish]
  python dp_console_admin.py create-agent --name N [--description D]
          [--skills "a,b"] [--publish-skills] [--publish] [--release-note R] [--force]
  python dp_console_admin.py create-squad --name N --leader AGENT
  python dp_console_admin.py bind --agent A --skills "a,b" [--publish-skills] [--replace]
  python dp_console_admin.py publish agent|skill --name X [--release-note R]
  python dp_console_admin.py delete agents|skills|squads --name X [--yes]
  python dp_console_admin.py login     # (re-)open console and (re-)run auto-login

Management constraints:
  1. skill must be PUBLISHED before binding (draft -> 404 "skill not found")
  2. agent needs runtime_id before publish
  3. PUT /agents/{id}/skills is full-replace (this tool merges by default)
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import socket
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

CONSOLE_URL = "https://agentteam-test.deepworks.cn/deepsense-workspace/agents"
API_BASE = "/deepexi-agent-teams-backend/api"
PROFILE_DIR = Path("C:/code_proj/tmp/dp-console-chrome-profile")
CDP_PORT = 9333
CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.environ.get("LOCALAPPDATA", "") + r"\Google\Chrome\Application\chrome.exe",
]
# Enterprise login credentials for the controlled profile's Workbench OIDC.
# Overridable via env (DP_CONSOLE_USER / DP_CONSOLE_TENANT / DP_CONSOLE_PASS).
ENTERPRISE_USER = os.environ.get("DP_CONSOLE_USER", "deepsense")
ENTERPRISE_TENANT = os.environ.get("DP_CONSOLE_TENANT", "deepsense")
ENTERPRISE_PASS = os.environ.get("DP_CONSOLE_PASS", "Deepexi@2026")


def log(step: str, detail: str = "") -> None:
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {step}" + (f" {detail}" if detail else "")
    print(line, flush=True)


def text(value: object) -> str:
    return value if isinstance(value, str) else ""


# ---------------------------------------------------------------------------
# Minimal CDP client (stdlib only).
# ---------------------------------------------------------------------------

def _http_json(url: str, timeout: float = 3.0) -> object:
    with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def _ws_handshake_key() -> str:
    return base64.b64encode(os.urandom(16)).decode("ascii")


def _read_exact(sock: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise RuntimeError("WebSocket closed unexpectedly")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


class DevToolsWebSocket:
    """Minimal WebSocket client, just enough for DevTools JSON messages."""

    def __init__(self, ws_url: str) -> None:
        parsed = urllib.parse.urlparse(ws_url)
        if parsed.scheme != "ws":
            raise RuntimeError(f"Only ws:// DevTools URLs are supported: {ws_url}")
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 80
        self.path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
        self.sock = socket.create_connection((host, port), timeout=10)
        self.sock.settimeout(60)
        request = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {_ws_handshake_key()}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(request.encode("ascii"))
        response = b""
        while b"\r\n\r\n" not in response:
            response += self.sock.recv(4096)
        if b" 101 " not in response.split(b"\r\n", 1)[0]:
            raise RuntimeError(f"DevTools WebSocket handshake failed: {response[:200]!r}")

    def send_json(self, payload: dict) -> None:
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        if len(raw) >= 126:
            header = bytearray([0x81, 0x80 | 126])
            header.extend(struct.pack("!H", len(raw)))
        else:
            header = bytearray([0x81, 0x80 | len(raw)])
        mask = os.urandom(4)
        header.extend(mask)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(raw))
        self.sock.sendall(bytes(header) + masked)

    def recv_json(self) -> dict:
        first, second = _read_exact(self.sock, 2)
        opcode = first & 0x0F
        if opcode == 0x8:
            raise RuntimeError("DevTools WebSocket closed")
        length = second & 0x7F
        if length == 126:
            length = struct.unpack("!H", _read_exact(self.sock, 2))[0]
        elif length == 127:
            length = struct.unpack("!Q", _read_exact(self.sock, 8))[0]
        if second & 0x80:
            mask = _read_exact(self.sock, 4)
            raw = bytes(byte ^ mask[index % 4] for index, byte in enumerate(_read_exact(self.sock, length)))
        else:
            raw = _read_exact(self.sock, length)
        return json.loads(raw.decode("utf-8"))

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


class ConsoleBridge:
    """Run authenticated fetches inside the console tab via CDP."""

    def __init__(self, port: int = CDP_PORT, auto_launch: bool = True,
                 auto_login: bool = True, head: bool = False):
        self.port = port
        self._mid = 100

    # -- browser lifecycle -------------------------------------------------

    def cdp_alive(self) -> bool:
        try:
            _http_json(f"http://127.0.0.1:{self.port}/json/version", timeout=1.5)
            return True
        except (OSError, urllib.error.URLError, ValueError):
            return False

    def launch(self) -> None:
        exe = next((p for p in CHROME_CANDIDATES if p and Path(p).is_file()), None)
        if not exe:
            raise RuntimeError("Chrome not found; edit CHROME_CANDIDATES")
        profile = str(PROFILE_DIR)
        profile.mkdir(parents=True, exist_ok=True)
        subprocess.Popen([
            exe, f"--remote-debugging-port={self.port}",
            f"--user-data-dir={profile}",
            "--no-first-run", "--no-default-browser-check",
            "--window-size=1280,900", CONSOLE_URL,
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(20):
            time.sleep(1)
            if self.cdp_alive():
                return
        raise RuntimeError("controlled Chrome did not expose CDP port")

    def ensure_browser(self) -> None:
        if not self.cdp_alive():
            log("launching controlled Chrome", f"port={self.port} profile={PROFILE_DIR.name}")
            self.launch()

    # -- tab helpers ---------------------------------------------------------

    def tabs(self) -> list[dict]:
        return [t for t in _http_json(f"http://127.0.0.1:{self.port}/json/list")
                if isinstance(t, dict) and t.get("type") == "page"]

    def find_console_tab(self) -> dict | None:
        for tab in self.tabs():
            if "agentteam-test.deepworks.cn" in text(tab.get("url")):
                return tab
        return None

    def navigate(self, tab: dict, url: str) -> None:
        ws = DevToolsWebSocket(tab["webSocketDebuggerUrl"])
        try:
            self._mid += 1
            ws.send_json({"id": self._mid, "method": "Page.enable", "params": {}})
            ws.recv_json()
            self._mid += 1
            ws.send_json({"id": self._mid, "method": "Page.navigate", "params": {"url": url}})
            ws.recv_json()
        finally:
            ws.close()

    # -- eval ----------------------------------------------------------------

    def eval_js(self, expression: str, timeout_ms: int = 45000) -> object:
        tab = self.find_console_tab()
        if tab is None:
            raise RuntimeError(
                "console tab not found; run: dp_console_admin.py login")
        ws = DevToolsWebSocket(tab["webSocketDebuggerUrl"])
        try:
            self._mid += 1
            ws.send_json({"id": self._mid, "method": "Runtime.enable", "params": {}})
            ws.recv_json()
            self._mid += 1
            ws.send_json({
                "id": self._mid, "method": "Runtime.evaluate",
                "params": {"expression": expression, "returnByValue": True,
                           "awaitPromise": True, "timeout": timeout_ms},
            })
            while True:
                msg = ws.recv_json()
                if msg.get("id") != self._mid:
                    continue
                result = msg.get("result", {})
                if result.get("subtype") == "error":
                    raise RuntimeError(text(result.get("description"))[:400])
                return result.get("result", {}).get("value")
        finally:
            ws.close()

    # -- authenticated API call ----------------------------------------------

    def api(self, path: str, method: str = "GET", body: dict | None = None) -> object:
        """fetch() inside the page; cookie+CSRF automatic. Raises on HTTP >=400."""
        body_js = json.dumps(body, ensure_ascii=False) if body is not None else "null"
        js = f"""
(async function(){{
  const m = document.cookie.match(/deepexi_csrf=([^;]+)/);
  const csrf = m ? decodeURIComponent(m[1]) : '';
  const r = await fetch('{API_BASE}{path}', {{
    method: '{method}',
    headers: {{ 'Content-Type': 'application/json', 'x-csrf-token': csrf }},
    credentials: 'include',
    body: {body_js if body is None else 'JSON.stringify(' + body_js + ')'},
  }});
  const t = await r.text();
  let data = null;
  try {{ data = JSON.parse(t); }} catch (e) {{ data = null; }}
  return JSON.stringify({{status: r.status, data: data, raw: data === null ? t.slice(0, 200) : null}});
}})()
"""
        value = self.eval_js(js)
        payload = json.loads(value) if isinstance(value, str) else value
        if not isinstance(payload, dict):
            raise RuntimeError(f"unexpected eval result: {payload!r}")
        status = int(payload.get("status", 0))
        if status >= 400:
            detail = payload.get("data") or payload.get("raw")
            raise RuntimeError(f"{method} {path} -> HTTP {status}: {str(detail)[:300]}")
        return payload.get("data")

    def login(self) -> None:
        """Ensure browser+tab+session; auto-fill enterprise OIDC login if needed."""
        self.ensure_browser()
        tab = self.find_console_tab()
        if tab is None:
            log("opening console URL")
            self.launch()  # re-launch navigates to CONSOLE_URL
            time.sleep(3)
            tab = self.find_console_tab()
            if tab is None:
                raise RuntimeError("console tab still missing after launch")
        url = text(tab.get("url"))
        if "workbench-test.deepexios.cn" in url or "oidc-login" in url:
            log("Workbench login page detected; auto-filling enterprise login")
            self._auto_login(tab)
        # final check: session works
        probe = self.api("/agents/page?page=1&page_size=1")
        log("console session OK", f"user workspace reachable, agents sample={str(probe)[:60]}")

    def _auto_login(self, tab: dict) -> None:
        ws = DevToolsWebSocket(tab["webSocketDebuggerUrl"])
        try:
            def ev(expr: str) -> object:
                self._mid += 1
                ws.send_json({"id": self._mid, "method": "Runtime.evaluate",
                              "params": {"expression": expr, "returnByValue": True,
                                         "awaitPromise": True}})
                while True:
                    msg = ws.recv_json()
                    if msg.get("id") != self._mid:
                        continue
                    res = msg.get("result", {})
                    if res.get("subtype") == "error":
                        raise RuntimeError(text(res.get("description"))[:300])
                    return res.get("result", {}).get("value")

            ev("""(function(){
  const tabs = Array.from(document.querySelectorAll('.ant-segmented-item, [role=radio]'));
  const ent = tabs.find(t => t.textContent.trim() === '企业登录');
  if (ent) ent.click();
  return 1;
})()""")
            time.sleep(0.5)
            ev("""(function(){
  const labels = Array.from(document.querySelectorAll('label'));
  const a = labels.find(l => l.textContent.includes('我已阅读'));
  if (!a) return 0;
  const input = a.querySelector('input.ant-checkbox-input, input[type=checkbox], input.ant-radio-input');
  if (input && !input.checked) input.click();
  return 1;
})()""")
            for sel, val in (("#enterprise-password-login_username", ENTERPRISE_USER),
                             ("#enterprise-password-login_tenantId", ENTERPRISE_TENANT),
                             ("#enterprise-password-login_password", ENTERPRISE_PASS)):
                ev(f"""(function(){{
  const el = document.querySelector('{sel}');
  if (!el) return 'missing:{sel}';
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  setter.call(el, '{val}');
  el.dispatchEvent(new Event('input', {{bubbles: true}}));
  el.dispatchEvent(new Event('change', {{bubbles: true}}));
  return 'ok';
}})()""")
            time.sleep(0.3)
            ev("""(function(){
  const btn = document.querySelector('button[aria-label=登录], button[type=submit]');
  if (btn) btn.click();
  return 1;
})()""")
            for _ in range(20):
                time.sleep(1.5)
                here = text(self.eval_js("location.href"))
                if "agentteam-test.deepworks.cn" in here:
                    log("login OK", "redirected to console")
                    time.sleep(2)
                    return
            raise RuntimeError("login redirect timeout; log in manually in the controlled Chrome window")
        finally:
            ws.close()


# ---------------------------------------------------------------------------
# item helpers
# ---------------------------------------------------------------------------

def items(payload: object) -> list:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("items", "skills", "squads", "runtimes"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def list_all_pages(bridge: ConsoleBridge, path: str, page_size: int = 100) -> list[dict]:
    out: list[dict] = []
    page = 1
    while True:
        query = urllib.parse.urlencode({"page": page, "page_size": page_size})
        payload = bridge.api(f"{path}?{query}")
        rows = [r for r in items(payload) if isinstance(r, dict)]
        out.extend(rows)
        total = payload.get("total") if isinstance(payload, dict) else None
        if rows and isinstance(total, int) and len(out) < total:
            page += 1
            continue
        break
    return out


def resolve_agent(bridge: ConsoleBridge, name_or_id: str) -> dict:
    rows = list_all_pages(bridge, "/agents/page")
    for row in rows:
        if text(row.get("id")) == name_or_id:
            return row
    matches = [r for r in rows if text(r.get("name")).strip() == name_or_id]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        available = ", ".join(sorted({text(r.get("name")) for r in rows}))
        raise RuntimeError(f"agent not found by name '{name_or_id}'. Available: {available}")
    raise RuntimeError(f"agent name is ambiguous: {name_or_id}")


def resolve_skill(bridge: ConsoleBridge, name_or_id: str) -> dict:
    rows = list_all_pages(bridge, "/skills")
    for row in rows:
        if text(row.get("id")) == name_or_id:
            return row
    matches = [r for r in rows if text(r.get("name")).strip() == name_or_id]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        available = ", ".join(sorted({text(r.get("name")) for r in rows}))
        raise RuntimeError(f"skill not found by name '{name_or_id}'. Available: {available}")
    raise RuntimeError(f"skill name is ambiguous: {name_or_id}")


def resolve_runtime(bridge: ConsoleBridge) -> str:
    workspaces = [w for w in items(bridge.api("/workspaces")) if isinstance(w, dict)]
    if not workspaces:
        raise RuntimeError("no workspaces visible for this account")
    ws_id = text(workspaces[0].get("id"))
    rows = [r for r in items(bridge.api(f"/runtimes?{urllib.parse.urlencode({'workspace_id': ws_id})}"))
            if isinstance(r, dict)]
    if not rows:
        raise RuntimeError(f"no runtimes in workspace {ws_id}; cannot publish")
    runtime_id = text(rows[0].get("id"))
    log("runtime resolved", f"runtime_id={runtime_id} (first of {len(rows)})")
    return runtime_id


def parse_skill_list(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def ensure_skills_published(bridge: ConsoleBridge, names: list[str], auto_publish: bool) -> list[str]:
    ids: list[str] = []
    for name in names:
        skill = resolve_skill(bridge, name)
        sid, status = text(skill.get("id")), text(skill.get("status"))
        if status != "published":
            if not auto_publish:
                raise RuntimeError(
                    f"skill '{name}' is '{status}', not published - binding would 404. "
                    "Re-run with --publish-skills.")
            log("publishing draft skill", name)
            bridge.api(f"/skills/{sid}/publish", method="POST", body={})
            log("skill published", name)
        ids.append(sid)
    return ids


def agent_skill_ids(bridge: ConsoleBridge, agent_id: str) -> list[str]:
    return [text(s.get("id")) for s in items(bridge.api(f"/agents/{agent_id}/skills"))
            if isinstance(s, dict) and s.get("id")]


def put_agent_skills(bridge: ConsoleBridge, agent_id: str, skill_ids: list[str]) -> None:
    bridge.api(f"/agents/{agent_id}/skills", method="PUT", body={"skill_ids": skill_ids})


def publish_agent(bridge: ConsoleBridge, agent_id: str, name: str, release_note: str) -> None:
    agent = bridge.api(f"/agents/{agent_id}")
    if isinstance(agent, dict) and not agent.get("runtime_id"):
        runtime_id = resolve_runtime(bridge)
        bridge.api(f"/agents/{agent_id}", method="PATCH", body={"runtime_id": runtime_id})
        log("runtime set on agent", f"{name} runtime_id={runtime_id}")
    bridge.api(f"/agents/{agent_id}/publish", method="POST", body={"release_note": release_note})
    log("agent published", name)


def name_taken(rows: list[dict], name: str) -> bool:
    return any(text(r.get("name")).strip() == name for r in rows)


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

def cmd_login(bridge: ConsoleBridge, _args) -> int:
    bridge.login()
    return 0


def cmd_list(bridge: ConsoleBridge, args) -> int:
    kind = args.what
    log("console session", f"controlled Chrome port={bridge.port}")
    if kind == "runtimes":
        workspaces = [w for w in items(bridge.api("/workspaces")) if isinstance(w, dict)]
        ws_id = text(workspaces[0].get("id")) if workspaces else ""
        rows = [r for r in items(bridge.api(f"/runtimes?{urllib.parse.urlencode({'workspace_id': ws_id})}"))
                if isinstance(r, dict)]
        print(f"== runtimes ({len(rows)}) ==")
        for r in rows:
            print(f"{text(r.get('id'))} | {text(r.get('name')) or text(r.get('slug'))} | {text(r.get('status'))}")
        return 0
    path = {"agents": "/agents/page", "skills": "/skills", "squads": "/squads"}[kind]
    rows = list_all_pages(bridge, path)
    print(f"== {kind} ({len(rows)} total) ==")
    for r in rows:
        status = text(r.get("status")) or text(r.get("live_status")) or "-"
        desc = text(r.get("description")).strip().splitlines()
        summary = desc[0][:50] if desc else ""
        print(f"{text(r.get('id'))[:8]} | {text(r.get('name'))} | {status}  {('# ' + summary) if summary else ''}")
    return 0


def cmd_create_skill(bridge: ConsoleBridge, args) -> int:
    existing = list_all_pages(bridge, "/skills")
    if name_taken(existing, args.name.strip()) and not args.force:
        raise RuntimeError(f"skill '{args.name}' already exists; use --force")
    payload = {"name": args.name.strip(), "instructions": args.instructions, "scope": "custom"}
    if args.description:
        payload["description"] = args.description
    created = bridge.api("/skills", method="POST", body=payload)
    sid = text(created.get("id")) if isinstance(created, dict) else ""
    log("skill created", f"id={sid} status={text(created.get('status')) if isinstance(created, dict) else '?'}")
    if args.publish:
        bridge.api(f"/skills/{sid}/publish", method="POST", body={})
        log("skill published", args.name)
    print(json.dumps({"id": sid, "name": args.name, "published": args.publish}, ensure_ascii=False))
    return 0


def cmd_create_agent(bridge: ConsoleBridge, args) -> int:
    existing = list_all_pages(bridge, "/agents/page")
    if name_taken(existing, args.name.strip()) and not args.force:
        raise RuntimeError(f"agent '{args.name}' already exists; use --force")
    created = bridge.api("/agents", method="POST", body={"name": args.name.strip()})
    aid = text(created.get("id")) if isinstance(created, dict) else ""
    log("agent draft created", f"id={aid}")
    if args.description:
        bridge.api(f"/agents/{aid}", method="PATCH", body={"description": args.description})
    skill_ids: list[str] = []
    if args.skills:
        skill_ids = ensure_skills_published(bridge, parse_skill_list(args.skills), args.publish_skills)
        runtime_id = resolve_runtime(bridge)
        bridge.api(f"/agents/{aid}", method="PATCH", body={"runtime_id": runtime_id})
        put_agent_skills(bridge, aid, skill_ids)
        log("skills bound", f"{len(skill_ids)} bound")
    if args.publish:
        note = args.release_note or f"dp-console-admin {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        publish_agent(bridge, aid, args.name.strip(), note)
    print(json.dumps({"id": aid, "name": args.name, "skills": skill_ids,
                      "published": args.publish}, ensure_ascii=False))
    return 0


def cmd_create_squad(bridge: ConsoleBridge, args) -> int:
    leader = resolve_agent(bridge, args.leader.strip())
    existing = list_all_pages(bridge, "/squads")
    if name_taken(existing, args.name.strip()) and not args.force:
        raise RuntimeError(f"squad '{args.name}' already exists; use --force")
    created = bridge.api("/squads", method="POST",
                         body={"name": args.name.strip(), "leader_agent_id": text(leader.get("id"))})
    sid = text(created.get("id")) if isinstance(created, dict) else ""
    log("squad created", f"id={sid} leader={text(leader.get('name'))}")
    print(json.dumps({"id": sid, "name": args.name, "leader": text(leader.get("name"))},
                     ensure_ascii=False))
    return 0


def cmd_bind(bridge: ConsoleBridge, args) -> int:
    agent = resolve_agent(bridge, args.agent.strip())
    aid, aname = text(agent.get("id")), text(agent.get("name"))
    skill_ids = ensure_skills_published(bridge, parse_skill_list(args.skills), args.publish_skills)
    current = agent_skill_ids(bridge, aid)
    final = skill_ids if args.replace else list(dict.fromkeys(current + skill_ids))
    put_agent_skills(bridge, aid, final)
    log("skills bound", f"agent={aname} had={len(current)} now={len(final)}")
    print(json.dumps({"agent": aname, "agent_id": aid, "skill_ids": final,
                      "mode": "replace" if args.replace else "merge"}, ensure_ascii=False))
    return 0


def cmd_publish(bridge: ConsoleBridge, args) -> int:
    target = args.name.strip()
    if args.what == "skill":
        skill = resolve_skill(bridge, target)
        if text(skill.get("status")) == "published":
            log("skill already published, nothing to do", target)
            return 0
        bridge.api(f"/skills/{text(skill.get('id'))}/publish", method="POST", body={})
        log("skill published", target)
        print(json.dumps({"id": text(skill.get("id")), "name": target, "published": True},
                         ensure_ascii=False))
        return 0
    agent = resolve_agent(bridge, target)
    note = args.release_note or f"dp-console-admin {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    publish_agent(bridge, text(agent.get("id")), text(agent.get("name")), note)
    print(json.dumps({"id": text(agent.get("id")), "name": text(agent.get("name")),
                      "published": True}, ensure_ascii=False))
    return 0


DELETE_PATHS = {"agents": "/agents/{id}", "skills": "/skills/{id}", "squads": "/squads/{id}"}


def cmd_delete(bridge: ConsoleBridge, args) -> int:
    kind, target = args.what, args.name.strip()
    if kind == "agents":
        row = resolve_agent(bridge, target)
    elif kind == "skills":
        row = resolve_skill(bridge, target)
    else:
        rows = list_all_pages(bridge, "/squads")
        matches = [r for r in rows if text(r.get("name")).strip() == target or text(r.get("id")) == target]
        if len(matches) != 1:
            available = ", ".join(sorted({text(r.get("name")) for r in rows}))
            raise RuntimeError(f"squad not found (or ambiguous): {target}. Available: {available}")
        row = matches[0]
    rid, rname = text(row.get("id")), text(row.get("name"))
    if not args.yes:
        print(f"DRY-RUN: would DELETE {kind[:-1]} '{rname}' ({rid}). Re-run with --yes to confirm.")
        return 0
    bridge.api(DELETE_PATHS[kind].format(id=rid), method="DELETE")
    log("deleted", f"{kind[:-1]} '{rname}' ({rid})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="DeepWorks console admin (CDP bridge).")
    ap.add_argument("command", choices=["login", "list", "create-skill", "create-agent",
                                        "create-squad", "bind", "publish", "delete"])
    ap.add_argument("what", nargs="?", default="",
                    help="list/delete: agents|skills|squads|runtimes; publish: agent|skill")
    ap.add_argument("--name", default="")
    ap.add_argument("--description", default="")
    ap.add_argument("--instructions", default="")
    ap.add_argument("--skills", default="")
    ap.add_argument("--leader", default="")
    ap.add_argument("--agent", default="")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--publish-skills", action="store_true")
    ap.add_argument("--replace", action="store_true")
    ap.add_argument("--release-note", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--cdp-port", type=int, default=CDP_PORT)
    args = ap.parse_args()

    bridge = ConsoleBridge(port=args.cdp_port)

    if args.command == "login":
        return cmd_login(bridge, args)
    if args.command == "list":
        if args.what not in {"agents", "skills", "squads", "runtimes"}:
            ap.error("list needs: agents|skills|squads|runtimes")
        return cmd_list(bridge, args)
    if args.command == "create-skill":
        if not args.name or not args.instructions:
            ap.error("create-skill needs --name and --instructions")
        return cmd_create_skill(bridge, args)
    if args.command == "create-agent":
        if not args.name:
            ap.error("create-agent needs --name")
        return cmd_create_agent(bridge, args)
    if args.command == "create-squad":
        if not args.name or not args.leader:
            ap.error("create-squad needs --name and --leader")
        return cmd_create_squad(bridge, args)
    if args.command == "bind":
        if not args.agent or not args.skills:
            ap.error("bind needs --agent and --skills")
        return cmd_bind(bridge, args)
    if args.command == "publish":
        if args.what not in {"agent", "skill"} or not args.name:
            ap.error("publish needs: agent|skill --name X")
        return cmd_publish(bridge, args)
    if args.command == "delete":
        if args.what not in DELETE_PATHS or not args.name:
            ap.error("delete needs: agents|skills|squads --name X [--yes]")
        return cmd_delete(bridge, args)
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, TimeoutError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
