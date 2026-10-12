#!/usr/bin/env python3
"""Single-shot prompt to a local DeepWorks workspace via the agent-eval runner.

Not an eval: no dataset, no judge, no scores. Sends ONE prompt, streams progress
to stdout, and writes a full log next to the answer.

Usage:
  uv run python <skill_dir>/scripts/ask_local_deepworks.py \
      --repo <agent-eval path> --target agent_demo1_deepworks \
      --message "燃气报警了怎么排查" \
      [--working-dir-note "现场情况说明"] [--out-dir <dir>] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

LOG_STEPS: list[dict] = []


def log(step: str, detail: str = "") -> None:
    """Print one progress line AND keep it for the log file."""
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {step}" + (f" {detail}" if detail else "")
    print(line, flush=True)
    LOG_STEPS.append({"t": datetime.now().isoformat(timespec="seconds"), "step": step, "detail": detail})


def main() -> int:
    ap = argparse.ArgumentParser(description="Ask the local DeepWorks workspace agent one question.")
    ap.add_argument("--repo", required=True, help="agent-eval repo path")
    ap.add_argument("--target", default="agent_demo1_deepworks", help="target name (deepworks-api family)")
    ap.add_argument("--message", required=True, help="the prompt to send (current_node)")
    ap.add_argument("--working-dir", default=None,
                    help="override target workspace dir (must be open in DeepWorks desktop)")
    ap.add_argument("--working-dir-note", default="", help="optional scene note prepended as history context")
    ap.add_argument("--out-dir", default=None, help="where to write answer+log (default: <repo>/outputs/single-shot)")
    ap.add_argument("--timeout", type=int, default=None, help="override timeout_seconds from target yaml")
    ap.add_argument("--model", default=None,
                    help="model for this call, e.g. 'dth/DeepSeek-V4.1-Flash' (provider prefix optional, default dth)")
    ap.add_argument("--dry-run", action="store_true", help="build prompt, do not call DeepWorks")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if not (repo / "src" / "agent_eval").is_dir():
        print(f"FAIL: not an agent-eval repo: {repo}", file=sys.stderr)
        return 2
    sys.path.insert(0, str(repo / "src"))

    from agent_eval.config import load_resolved_config
    from agent_eval.runners.framework_registry import build_runner
    from agent_eval.schema.case import DiagnosisCase, DiagnosisCaseExpected, DiagnosisCaseInput

    t0 = time.perf_counter()
    log("load config", f"repo={repo.name} target={args.target}")
    cfg = load_resolved_config(repo, "smoke", args.target)
    if args.working_dir:
        cfg.target.working_dir = args.working_dir
    if args.timeout is not None:
        cfg.target.timeout_seconds = args.timeout
    runner = build_runner(cfg)

    # Patch model selection into the prompt body. Verified via opencode server
    # log (2026-10-12): prompt_async's "model" field must be an OBJECT
    #   {"providerID": "dth", "modelID": "DeepSeek-V4.1-Flash"}
    # a plain string is rejected by payload schema ("Expected object | null")
    # and the prompt is silently dropped. Also: NEVER patch /session (HTTP 400).
    if args.model:
        orig_request_json = runner._request_json  # noqa: SLF001 - deliberate patch point
        provider, _, model_id = args.model.partition("/")
        if not model_id:
            provider, model_id = "dth", args.model

        def _request_json_with_model(url, method="GET", headers=None, body=None, **kw):
            if body is not None and method == "POST" and "/prompt_async" in url:
                body = {**body, "model": {"providerID": provider, "modelID": model_id}}
            return orig_request_json(url, method=method, headers=headers, body=body, **kw)

        runner._request_json = _request_json_with_model  # noqa: SLF001

    note = args.working_dir_note.strip()
    user_message = f"{note}\n{args.message}" if note else args.message
    case = DiagnosisCase(
        case_id=f"single-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        input=DiagnosisCaseInput(
            user_message=user_message,
            runtime_snapshot={"current_node": args.message},
        ),
        expected=DiagnosisCaseExpected(),
        tags=["single-shot"],
    )
    log("prompt built", f"case_id={case.case_id} chars={len(user_message)}")

    if args.dry_run:
        result = runner.run_case(case, dry_run=True)
        print("\n===== RENDERED PROMPT (dry-run) =====\n")
        print(getattr(result, "rendered_prompt_text", "") or "(no rendered prompt attr)")
        return 0

    log("calling local DeepWorks workspace", f"timeout={cfg.target.timeout_seconds}s")
    result = runner.run_case(case)
    latency = time.perf_counter() - t0
    log("runner returned", f"exit={result.exit_code} latency={result.latency_seconds:.1f}s")

    parsed = result.structured_output
    answer = (parsed.final_text if parsed and parsed.final_text else result.raw_stdout)
    out_dir = Path(args.out_dir) if args.out_dir else repo / "outputs" / "single-shot"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = case.case_id.replace("single-", "")
    answer_path = out_dir / f"{stamp}.answer.md"
    log_path = out_dir / f"{stamp}.log.json"

    answer_path.write_text(
        f"# {case.case_id}\n\n- target: {args.target}\n- latency: {latency:.1f}s\n\n"
        f"## 提问\n\n{args.message}\n\n## 回答\n\n{answer}\n",
        encoding="utf-8",
    )
    log_payload = {
        "case_id": case.case_id, "target": args.target, "exit_code": result.exit_code,
        "latency_seconds": round(latency, 1), "session_id": result.session_id,
        "parse_error": getattr(result, "parse_error", None),
        "raw_stderr_tail": (getattr(result, "raw_stderr", "") or "")[-4000:],
        "steps": LOG_STEPS,
        "raw_stdout_tail": result.raw_stdout[-4000:],
    }
    log_path.write_text(json.dumps(log_payload, ensure_ascii=False, indent=1), encoding="utf-8")
    log("saved", f"{answer_path.name}, {log_path.name}")

    print("\n===== ANSWER =====\n")
    print(answer)
    print(f"\n-----\nfiles: {answer_path}\n        {log_path}")
    return 0 if result.exit_code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
