#!/usr/bin/env python3
"""Open a local workspace in the DeepWorks desktop app from the CLI, no UI clicks.

Why this works: the desktop main process boots the engine for the selected
workspace at startup itself (bootRuntimeForSelectedWorkspace in
apps/desktop/electron/main.mjs, priority watchedId > selectedId > activeId
> first entry), before any renderer code runs. So pre-writing
workspace-state.json in the app's userData dir and launching the exe is
enough: the engine starts and deepworks-port-state.json / -tokens.json get
populated, which ask_local_deepworks.py consumes.

Id rule verified against the live install on 2026-10-22: workspace id =
"ws_" + sha256(native backslash path)[:12]; reproduced ws_1394a6832c3c
(ddddxxx) and ws_66e374793506 (ds-04) from the real state file.

Usage:
  python open_local_workspace.py --path "C:/code_proj/tmp/ws-dir/ds-05" [--env prod]
  python open_local_workspace.py --path ... --dry-run
  python open_local_workspace.py --path ... --no-wait

Preconditions:
  - target directory must exist
  - the matching desktop (prod or test) must NOT be running: workspace state
    is only read at startup, and the single-instance lock forwards any new
    launch to the running app (which silently ignores plain path arguments)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ENV_DIRS = {
    "prod": "com.deepexi.deepworks",
    "test": "com.deepexi.deepworks.test",
}
# (tasklist image name, installed exe path) per environment
EXES = {
    "prod": ("DeepWorks.exe",
             Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "deepworks" / "DeepWorks.exe"),
    "test": ("DeepWorks Test.exe",
             Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "DeepWorks Test" / "DeepWorks Test.exe"),
}
# Fields observed as null in every local entry of workspace-state.json.
ENTRY_NULLS = ("cloudProvider", "agentTeams", "remoteType", "baseUrl", "directory",
               "deepworksHostUrl", "deepworksToken", "deepworksClientToken",
               "deepworksHostToken", "deepworksWorkspaceId", "deepworksWorkspaceName",
               "sandboxBackend", "sandboxRunId", "sandboxContainerName")


def log(step: str, detail: str = "") -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {step}" + (f" {detail}" if detail else ""), flush=True)


def native_path(raw: str) -> str:
    # Electron path.resolve() equivalent: absolute native form, backslashes,
    # no trailing separator. The workspace id hashes EXACTLY this string.
    return str(Path(raw).resolve())


def workspace_id(native: str) -> str:
    return "ws_" + hashlib.sha256(native.encode("utf-8")).hexdigest()[:12]


def port_key(native: str) -> str:
    # normalizeWorkspaceKey in runtime.mjs: resolve, forward slashes, lower.
    return native.replace("\\", "/").lower()


def desktop_running(image_name: str) -> bool:
    try:
        out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {image_name}",
                              "/FO", "CSV", "/NH"], capture_output=True, timeout=15)
        text = out.stdout.decode("gbk", "replace")
    except Exception:  # noqa: BLE001 - detection is best effort; false negative just skips the guard
        return False
    return image_name.lower() in text.lower()


def build_entry(native: str, preset: str) -> dict:
    name = Path(native).name
    entry = {"id": workspace_id(native), "name": name, "displayName": name,
             "path": native, "preset": preset,
             "conversationEnabled": preset != "knowledge",
             "workspaceType": "local"}
    entry.update({k: None for k in ENTRY_NULLS})
    entry.update({"directoryMissing": False, "directoryInInstallation": False})
    return entry


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--path", required=True, help="workspace directory (any spelling; resolved internally)")
    ap.add_argument("--env", default="prod", choices=sorted(ENV_DIRS),
                    help="which desktop install to launch (default prod)")
    ap.add_argument("--preset", default="starter", choices=["starter", "knowledge"],
                    help="starter = conversation workspace, knowledge = knowledge preset (default starter)")
    ap.add_argument("--timeout", type=int, default=180,
                    help="seconds to wait for the engine port registration (default 180)")
    ap.add_argument("--no-wait", action="store_true",
                    help="launch the desktop and exit without polling the port file")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the planned workspace-state.json and exit")
    args = ap.parse_args()

    native = native_path(args.path)
    if not Path(native).is_dir():
        print(f"FAIL: directory does not exist: {native}", file=sys.stderr)
        return 2
    wsid = workspace_id(native)
    key = port_key(native)
    image, exe = EXES[args.env]
    log(f"environment: {args.env} ({ENV_DIRS[args.env]})")
    log("target", f"{native}  id={wsid}")

    if not exe.exists():
        print(f"FAIL: desktop exe not found: {exe}", file=sys.stderr)
        return 2
    if desktop_running(image):
        print(f"FAIL: {image} is already running. Quit it first, then rerun: "
              "workspace-state.json is only read at startup.", file=sys.stderr)
        return 2

    user_data = Path(os.environ["APPDATA"]) / ENV_DIRS[args.env]
    state_path = user_data / "workspace-state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
    else:
        state = {}
    before = state.get("workspaces", [])
    # Keep every existing entry AS-IS (the desktop's own write is authoritative);
    # if the target entry is missing, append one. NEVER filter-then-forget: an
    # earlier version removed the entry when it existed and booted the wrong
    # workspace as a result.
    existed = any(isinstance(w, dict) and w.get("id") == wsid for w in before)
    workspaces = [w for w in before if isinstance(w, dict)]
    if not existed:
        workspaces.append(build_entry(native, args.preset))
    state["workspaces"] = workspaces
    # Boot priority is watchedId > selectedId > activeId; set all three.
    for field in ("selectedId", "watchedId", "activeId"):
        state[field] = wsid

    if args.dry_run:
        print("===== planned workspace-state.json =====")
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0

    state_path.parent.mkdir(parents=True, exist_ok=True)
    if state_path.exists():
        backup = state_path.with_suffix(".json.bak")
        backup.write_text(state_path.read_text(encoding="utf-8"), encoding="utf-8")
        log("backup written", backup.name)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    log("state written", f"{state_path.name} ({'updated existing entry' if existed else 'appended new entry'})")

    log("launching desktop", str(exe))
    subprocess.Popen([str(exe)], cwd=str(exe.parent), close_fds=True,
                     creationflags=getattr(subprocess, "DETACHED_PROCESS", 0)
                     | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if args.no_wait:
        log("launched (--no-wait)")
        return 0

    port_file = user_data / "deepworks-port-state.json"
    tokens_file = user_data / "deepworks-server-tokens.json"
    deadline = time.monotonic() + args.timeout
    log("waiting for engine", f"polling {port_file.name} for key {key}")
    stale_reported = False
    while time.monotonic() < deadline:
        port = None
        token_ok = False
        try:
            port = json.loads(port_file.read_text(encoding="utf-8")).get("workspacePorts", {}).get(key)
        except Exception:  # noqa: BLE001 - file may be mid-write; retry until deadline
            pass
        if port:
            try:
                info = json.loads(tokens_file.read_text(encoding="utf-8")).get("workspaces", {}).get(key) or {}
                request = urllib.request.Request(
                    f"http://127.0.0.1:{port}/workspaces",
                    headers={"Authorization": f"Bearer {info.get('clientToken', '')}",
                             "X-DeepWorks-Host-Token": info.get("hostToken", "")})
                with urllib.request.urlopen(request, timeout=4) as response:
                    response.read()
                token_ok = True
            except urllib.error.HTTPError as exc:
                # Server alive but token rejected: the freshly booted engine has
                # not flushed its new token file yet (or tokens are stale).
                if not stale_reported:
                    log("engine responding but token rejected", f"HTTP {exc.code}; keep polling")
                    stale_reported = True
            except Exception:  # noqa: BLE001 - stale port entry from a previous run: keep polling
                if not stale_reported:
                    log("stale port entry", f"{port} not accepting yet; keep polling")
                    stale_reported = True
        if token_ok:
            log("engine up", f"port={port} tokens=ok")
            print(f"\nWORKSPACE OPEN: {native}\n  port: {port}\n"
                  f"  ready for ask_local_deepworks.py --working-dir \"{args.path}\" --env {args.env}")
            return 0
        time.sleep(2)
    print(f"FAIL: engine port not registered within {args.timeout}s "
          "(desktop may still be starting, or boot failed -- check the desktop window)",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
