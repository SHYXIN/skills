#!/usr/bin/env python3
"""ask-dp preflight: one-shot health check for the whole DeepWorks skill loop.

Checks (all read-only):
  - desktop installs (prod/test): process dir exists, port-state file parses,
    at least one recorded workspace port actually alive
  - agent-eval .env: AGENT_TEAMS_TOKEN / AGENT_TEAMS_TOKEN_PROD present
  - deepworks repo present (needed by dp-knowledge-compile validators)
  - python / node available

Output: one line per check, then a summary telling which skills are ready to use.

Usage: python preflight.py [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import urllib.request
from pathlib import Path

APPDATA = Path(os.environ.get("APPDATA", ""))

DESKTOPS = {
    "prod": APPDATA / "com.deepexi.deepworks",
    "test": APPDATA / "com.deepexi.deepworks.test",
}

ENV_FILE = Path("C:/code_proj/gitlab-proj/agent-eval/.env")
DEEPWORKS_REPO = Path("C:/code_proj/deepworks")

results: list[dict] = []


def check(name: str, ok: bool, detail: str) -> None:
    mark = "OK  " if ok else "MISS"
    print(f"[{mark}] {name}: {detail}", flush=True)
    results.append({"name": name, "ok": ok, "detail": detail})


def probe_port(port: int, timeout: float = 2.0) -> bool:
    try:
        # any HTTP response (incl. 401/404) means something is listening
        urllib.request.urlopen(f"http://127.0.0.1:{port}/doc", timeout=timeout)
        return True
    except Exception as exc:  # noqa: BLE001
        return "refused" not in str(exc) and "10061" not in str(exc)


def check_desktop(env_name: str) -> None:
    root = DESKTOPS[env_name]
    if not root.is_dir():
        check(f"desktop {env_name}", False, f"{root} 不存在（未安装或未登录过）")
        return
    port_file = root / "deepworks-port-state.json"
    if not port_file.is_file():
        check(f"desktop {env_name}", False, "缺 deepworks-port-state.json（桌面端从未启动？）")
        return
    try:
        ports = json.loads(port_file.read_text(encoding="utf-8")).get("workspacePorts", {})
    except (json.JSONDecodeError, OSError) as exc:
        check(f"desktop {env_name}", False, f"端口文件解析失败: {exc}")
        return
    if not ports:
        check(f"desktop {env_name}", False, "端口文件里没有工作区记录")
        return
    alive = [(wd, p) for wd, p in ports.items() if isinstance(p, int) and probe_port(p)]
    if alive:
        wd, port = alive[0]
        check(f"desktop {env_name}", True,
              f"{len(alive)}/{len(ports)} 个工作区端口存活，如 {wd} (:{port})")
    else:
        check(f"desktop {env_name}", False,
              f"记录了 {len(ports)} 个工作区但端口全部失活——桌面端没开，或状态文件是陈旧快照")


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def check_teams_token() -> None:
    env = load_env_file(ENV_FILE)
    for key, env_name in (("AGENT_TEAMS_TOKEN", "test"), ("AGENT_TEAMS_TOKEN_PROD", "prod")):
        if env.get(key, "").strip():
            check(f"teams token {env_name}", True, f"{key} present in .env")
        else:
            check(f"teams token {env_name}", False,
                  f".env 缺 {key}（打开已登录的 {env_name} 桌面端可自动同步）")


def check_tool(name: str, hint: str) -> None:
    path = shutil.which(name)
    check(f"tool {name}", bool(path), path or hint)


def main() -> int:
    ap = argparse.ArgumentParser(description="ask-dp preflight 环境体检")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    for env_name in sorted(DESKTOPS):
        check_desktop(env_name)
    check_teams_token()

    if DEEPWORKS_REPO.is_dir():
        check("deepworks repo", True, str(DEEPWORKS_REPO))
    else:
        check("deepworks repo", False, f"{DEEPWORKS_REPO} 不存在（dp-knowledge-compile 需要）")

    check_tool("python", "未找到 python")
    check_tool("node", "未找到 node（dp-knowledge-compile 校验器需要）")

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=1))

    missed = [r["name"] for r in results if not r["ok"]]
    print()
    if not missed:
        print("全部就绪：闭环所有技能可用。")
        return 0
    print(f"缺 {len(missed)} 项：{', '.join(missed)}")
    print("影响：")
    if any("desktop prod" in m for m in missed):
        print("  - dp-ask-deepworks / dp-eval-run(local/prod) / dp-session-forensics local 不可用；"
              "可先开桌面端或用 dp-deepworks-dev-start")
    if any("desktop test" in m for m in missed):
        print("  - local/test 相关路径不可用")
    if any("teams token" in m for m in missed):
        print("  - dp-ask-teams / dp-eval-run(teams) 对应环境不可用；打开已登录桌面端自动同步 token")
    if any("deepworks repo" in m for m in missed):
        print("  - dp-knowledge-compile 不可用")
    return 1


if __name__ == "__main__":
    sys.exit(main())
