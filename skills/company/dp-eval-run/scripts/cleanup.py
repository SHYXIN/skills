#!/usr/bin/env python3
"""dp-eval-run cleanup: delete the chat sessions created by eval runs.

Reads every run dir under the output root, collects session_ids recorded by the
sibling ask scripts (ask-logs/*.log.json), and delegates deletion to those same
scripts (--delete-session), so markers/tokens/env handling stay in one place.

Usage:
  python cleanup.py --list                     # show what would be deleted
  python cleanup.py [--label t1] [--yes]       # delete (dry-run unless --yes)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
COMPANY_DIR = SKILL_DIR.parent.parent

LOCAL_ASK = COMPANY_DIR / "dp-ask-deepworks" / "scripts" / "ask_local_deepworks.py"
TEAMS_ASK = COMPANY_DIR / "dp-ask-teams" / "scripts" / "ask_teams_agent.py"
DEFAULT_OUT_ROOT = Path("C:/code_proj/tmp/dp-eval-runs")


def collect(records_dir: Path) -> list[dict]:
    """Collect live session records from one run dir's ask-logs/."""
    out = []
    logs_dir = records_dir / "ask-logs"
    if not logs_dir.is_dir():
        return out
    for log_path in sorted(logs_dir.glob("*.log.json")):
        try:
            data = json.loads(log_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        sid = str(data.get("session_id", "")).strip()
        if not sid or data.get("session_deleted"):
            continue
        out.append({
            "session_id": sid,
            "env": data.get("env", ""),
            "source": "teams" if log_path.name.startswith("teams-") else "local",
            "run_dir": records_dir.name,
            "log_path": log_path,
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="删除 eval run 建立的会话（复用 ask 脚本删除逻辑）")
    ap.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT))
    ap.add_argument("--label", default="", help="只清理 run 目录名含此关键字的 run（如 t1、baseline）")
    ap.add_argument("--source", default="", choices=("local", "teams"), help="只清理指定源")
    ap.add_argument("--list", action="store_true", help="只列出，不删除")
    ap.add_argument("--yes", action="store_true", help="真删；缺省 dry-run")
    args = ap.parse_args()

    root = Path(args.out_root)
    if not root.is_dir():
        sys.exit(f"输出根目录不存在: {root}")

    records = []
    for run_dir in sorted(root.iterdir()):
        if not run_dir.is_dir():
            continue
        if args.label and args.label not in run_dir.name:
            continue
        records.extend(collect(run_dir))
    if args.source:
        records = [r for r in records if r["source"] == args.source]

    if not records:
        print("没有待清理的会话（都删过或没有 run 记录）")
        return 0

    print(f"{'RUN':50s} {'SOURCE':6s} {'ENV':5s} SESSION")
    for r in records:
        print(f"{r['run_dir']:50s} {r['source']:6s} {r['env']:5s} {r['session_id']}")

    if args.list or not args.yes:
        print(f"\n共 {len(records)} 条。预览模式，加 --yes 真删。")
        return 0

    print()
    deleted = failed = 0
    for r in records:
        script = TEAMS_ASK if r["source"] == "teams" else LOCAL_ASK
        cmd = [sys.executable, str(script), "--delete-session", r["session_id"], "--env", r["env"]]
        if r["source"] == "teams":
            cmd += ["--no-sync-token"]
        else:
            # delete mode requires --working-dir; recorded in the log json
            try:
                wd = json.loads(r["log_path"].read_text(encoding="utf-8")).get("working_dir", "")
            except (OSError, ValueError):
                wd = ""
            if not wd:
                print(f"FAIL {r['session_id']}: log 里没有 working_dir，跳过")
                failed += 1
                continue
            cmd += ["--working-dir", wd]
        # point the ask script at this run's ask-logs so its session_deleted
        # marker lands on the same log file we read (not its default out-dir)
        cmd += ["--out-dir", str(r["log_path"].parent)]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode == 0:
            deleted += 1
            print(f"deleted {r['session_id']} ({r['source']}/{r['env']})")
        else:
            failed += 1
            print(f"FAIL {r['session_id']} ({r['source']}/{r['env']}): {proc.stderr.strip()[-150:]}")

    print(f"\n{deleted} deleted, {failed} failed, {len(records)} total")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
