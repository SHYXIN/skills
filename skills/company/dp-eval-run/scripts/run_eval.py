#!/usr/bin/env python3
"""dp-eval-run: batch question-set evaluation against DeepWorks local / Agent Teams cloud.

Flow:
  1. Load a question set (JSON: {"cases": [...]}, or agent-eval style JSONL via --jsonl).
  2. For each case, invoke the sibling ask script as a subprocess (local: dp-ask-deepworks,
     teams: dp-ask-teams) and collect the answer markdown it writes to disk.
  3. Score the answer: required/forbidden marker hits, length, latency.
  4. Write one run directory: questions snapshot + per-case answer/score + summary.json.
  5. `diff` subcommand compares two run dirs into a markdown report.

Usage:
  python run_eval.py --source local --env prod --questions q.json --label baseline
  python run_eval.py --source teams --env test --questions q.json --label after-fix
  python run_eval.py diff <run_dir_a> <run_dir_b> [--out report.md]

Scoring is intentionally simple (marker in answer, length cap): this skill closes the
regression loop; deep semantic judging belongs to agent-eval or a human.
"""
from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
import time
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
COMPANY_DIR = SKILL_DIR.parent.parent  # .../company

LOCAL_ASK = COMPANY_DIR / "dp-ask-deepworks" / "scripts" / "ask_local_deepworks.py"
TEAMS_ASK = COMPANY_DIR / "dp-ask-teams" / "scripts" / "ask_teams_agent.py"

DEFAULT_OUT_ROOT = "C:/code_proj/tmp/dp-eval-runs"


def log(step: str, detail: str = "") -> None:
    line = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {step}" + (f" {detail}" if detail else "")
    print(line, flush=True)


def load_questions(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        cases = [json.loads(line) for line in raw.splitlines() if line.strip()]
    else:
        cases = json.loads(raw).get("cases", [])
    # normalize: accept agent-eval style (input.user_message) and flat (user_message)
    out = []
    for c in cases:
        inp = c.get("input") or {}
        msg = inp.get("user_message") or c.get("user_message") or ""
        expected = c.get("expected") or {}
        out.append({
            "case_id": c.get("case_id", f"case-{len(out) + 1}"),
            "user_message": msg,
            # note/callout fields the ask scripts prepend
            "note": c.get("note") or inp.get("note") or "",
            "expected": {
                "required_markers": expected.get("required_markers", expected.get("required_trace_markers", [])),
                "forbidden_markers": expected.get("forbidden_markers", expected.get("forbidden_behaviors", [])),
                "answer_max_chars": expected.get("answer_max_chars", 0),
            },
            "tags": c.get("tags", []),
        })
    return out


def run_case(case: dict, args, run_dir: Path) -> dict:
    if args.source == "local":
        script = LOCAL_ASK
        cmd = [sys.executable, str(script),
               "--message", case["user_message"],
               "--env", args.env,
               "--out-dir", str(run_dir / "ask-logs"),
               "--timeout", str(args.timeout)]
        if args.working_dir:
            cmd += ["--working-dir", args.working_dir]
        if args.model:
            cmd += ["--model", args.model]
    else:
        script = TEAMS_ASK
        cmd = [sys.executable, str(script),
               "--message", case["user_message"],
               "--env", args.env,
               "--out-dir", str(run_dir / "ask-logs"),
               "--timeout", str(args.timeout),
               "--max-wait", str(args.timeout * 2)]
        if args.agent_name:
            cmd += ["--agent-name", args.agent_name]

    if case.get("note"):
        cmd += ["--note", case["note"]]

    t0 = time.monotonic()
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    latency = time.monotonic() - t0

    answer = ""
    # ask scripts write <stamp>.answer.md into --out-dir; newest one for this case
    ask_logs = run_dir / "ask-logs"
    answers = sorted(ask_logs.glob("*.answer.md"), key=lambda p: p.stat().st_mtime) if ask_logs.is_dir() else []
    if answers:
        answer = answers[-1].read_text(encoding="utf-8")

    status = "ok" if proc.returncode == 0 and answer.strip() else "fail"
    if status == "fail":
        answer = (proc.stdout[-2000:] + "\n[stderr]\n" + proc.stderr[-2000:]) if not answer else answer

    return {
        "case_id": case["case_id"],
        "status": status,
        "latency_seconds": round(latency, 1),
        "answer_chars": len(answer),
        "answer": answer,
        "session_hint": f"see {ask_logs.name}/",
    }


def score_case(case: dict, result: dict) -> dict:
    answer = result.get("answer", "")
    expected = case["expected"]
    low = answer.lower()
    required_missed = [m for m in expected["required_markers"] if m.lower() not in low]
    forbidden_hit = [m for m in expected["forbidden_markers"] if m.lower() in low]
    too_long = bool(expected["answer_max_chars"]) and result["answer_chars"] > expected["answer_max_chars"]

    checks = {
        "required_missed": required_missed,
        "forbidden_hit": forbidden_hit,
        "too_long": too_long,
        "no_answer": result["status"] != "ok",
    }
    passed = result["status"] == "ok" and not required_missed and not forbidden_hit and not too_long
    return {"passed": passed, "checks": checks}


def cmd_run(args) -> int:
    qpath = Path(args.questions)
    if not qpath.is_file():
        sys.exit(f"问题集不存在: {qpath}")
    cases = load_questions(qpath)
    if args.only:
        wanted = {s.strip() for s in args.only.split(",")}
        cases = [c for c in cases if c["case_id"] in wanted]
        log("filter --only", f"{len(cases)} case(s)")
    if not cases:
        sys.exit("问题集为空（或 --only 过滤后为空）")

    if args.source == "local" and not args.working_dir:
        log("提示", "local 源建议带 --working-dir（桌面端只开了一个工作区时可省）")

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    label = args.label or stamp
    run_dir = Path(args.out_root) / f"{stamp}-{args.source}-{args.env}-{label}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "questions.snapshot.json").write_text(
        json.dumps({"cases": cases}, ensure_ascii=False, indent=1), encoding="utf-8")
    log("run dir", str(run_dir))

    results = []
    for i, case in enumerate(cases, 1):
        log(f"case {i}/{len(cases)}", f"{case['case_id']} via {args.source}/{args.env}")
        result = run_case(case, args, run_dir)
        result["score"] = score_case(case, result)
        results.append({**result, "answer": result["answer"][:20000]})
        mark = "PASS" if result["score"]["passed"] else "FAIL"
        log(f"  -> {mark}", f"latency={result['latency_seconds']}s chars={result['answer_chars']}")

    passed = sum(1 for r in results if r["score"]["passed"])
    summary = {
        "label": label,
        "source": args.source,
        "env": args.env,
        "questions": str(qpath),
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "avg_latency_seconds": round(sum(r["latency_seconds"] for r in results) / len(results), 1),
        "finished_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "results": results,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    log("done", f"{passed}/{len(results)} passed, summary: {run_dir / 'summary.json'}")
    return 0 if passed == len(results) else 1


def load_summary(run_dir: Path) -> dict:
    return json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))


def cmd_diff(args) -> int:
    a_dir, b_dir = Path(args.run_a), Path(args.run_b)
    a, b = load_summary(a_dir), load_summary(b_dir)
    b_by_id = {r["case_id"]: r for r in b["results"]}

    lines = [
        "# dp-eval-run 对比报告",
        "",
        f"- baseline: `{a_dir.name}` ({a['source']}/{a['env']}, {a['finished_at']})",
        f"- current:  `{b_dir.name}` ({b['source']}/{b['env']}, {b['finished_at']})",
        f"- 通过率: {a['passed']}/{a['total']} -> {b['passed']}/{b['total']}"
        f"（{'改善' if b['passed'] > a['passed'] else '持平' if b['passed'] == a['passed'] else '回退'}）",
        f"- 平均延迟: {a['avg_latency_seconds']}s -> {b['avg_latency_seconds']}s",
        "",
        "| case | baseline | current | 延迟变化 | 说明 |",
        "|---|---|---|---|---|",
    ]
    for r in a["results"]:
        rb = b_by_id.get(r["case_id"])
        if not rb:
            lines.append(f"| {r['case_id']} | {'PASS' if r['score']['passed'] else 'FAIL'} | (缺失) | - | current run 没有这个 case |")
            continue
        d_lat = rb["latency_seconds"] - r["latency_seconds"]
        lines.append(
            f"| {r['case_id']} | {'PASS' if r['score']['passed'] else 'FAIL'} "
            f"| {'PASS' if rb['score']['passed'] else 'FAIL'} "
            f"| {d_lat:+.1f}s "
            f"| {format_checks(rb['score']['checks'])} |"
        )
    for rb in b["results"]:
        if not any(r["case_id"] == rb["case_id"] for r in a["results"]):
            lines.append(f"| {rb['case_id']} | (新增) | {'PASS' if rb['score']['passed'] else 'FAIL'} | - | {format_checks(rb['score']['checks'])} |")

    out = Path(args.out) if args.out else b_dir / f"diff-vs-{a_dir.name}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    log("report written", str(out))
    return 0


def format_checks(checks: dict) -> str:
    parts = []
    if checks["required_missed"]:
        parts.append(f"缺标记: {', '.join(checks['required_missed'][:3])}")
    if checks["forbidden_hit"]:
        parts.append(f"触禁词: {', '.join(checks['forbidden_hit'][:3])}")
    if checks["too_long"]:
        parts.append("超长")
    if checks["no_answer"]:
        parts.append("无回答")
    return "; ".join(parts) if parts else "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description="dp-eval-run: 批量评测 DeepWorks 本地/云端 agent。")
    ap.add_argument("--source", default="local", choices=("local", "teams"))
    ap.add_argument("--env", default=None, choices=("prod", "test"),
                    help="local 默认 prod；teams 默认 test")
    ap.add_argument("--questions", default="", help="问题集 JSON/JSONL（diff 子命令时不需要）")
    ap.add_argument("--label", default="", help="run 标签，便于对比")
    ap.add_argument("--only", default="", help="只跑这些 case_id（逗号分隔）")
    ap.add_argument("--out-root", default=DEFAULT_OUT_ROOT)
    ap.add_argument("--timeout", type=int, default=900, help="单个 case 等待秒数")
    ap.add_argument("--working-dir", default="", help="local 源：工作区目录")
    ap.add_argument("--model", default="", help="local 源：模型覆盖")
    ap.add_argument("--agent-name", default="", help="teams 源：目标 agent 名")

    sub = ap.add_subparsers(dest="cmd")
    p_diff = sub.add_parser("diff", help="对比两个 run 目录")
    p_diff.add_argument("run_a")
    p_diff.add_argument("run_b")
    p_diff.add_argument("--out", default="")

    args = ap.parse_args()
    if args.env is None:
        args.env = "test" if args.source == "teams" else "prod"

    if args.cmd == "diff":
        return cmd_diff(args)
    if not args.questions:
        ap.error("--questions is required (unless using the diff subcommand)")
    return cmd_run(args)


if __name__ == "__main__":
    sys.exit(main())
