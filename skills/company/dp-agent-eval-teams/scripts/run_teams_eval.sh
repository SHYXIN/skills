#!/usr/bin/env bash
# dp-agent-eval-teams: run Agent Teams long-horizon eval in agent-eval repo.
# All machine paths are required args (fail closed); nothing is hardcoded.
# Usage: run_teams_eval.sh --repo <path> --benchmark <name> --target <name>
#        [--dataset <relpath>] [--dry-run] [--skip-render] [--no-sync-token]
set -euo pipefail

REPO="" BENCH="" TARGET="" DATASET="" DRYRUN=0 RENDER=1 SYNC=1
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --benchmark) BENCH="$2"; shift 2 ;;
    --target) TARGET="$2"; shift 2 ;;
    --dataset) DATASET="$2"; shift 2 ;;
    --dry-run) DRYRUN=1; shift ;;
    --skip-render) RENDER=0; shift ;;
    --no-sync-token) SYNC=0; shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

fail() { echo "PREFLIGHT FAIL: $*" >&2; exit 1; }
[ -n "$REPO" ] || fail "--repo is required"
[ -n "$BENCH" ] || fail "--benchmark is required"
[ -n "$TARGET" ] || fail "--target is required"
[ -d "$REPO" ] || fail "repo not found: $REPO"
[ -d "$REPO/.venv" ] || fail ".venv missing — run 'uv sync' in $REPO first"
[ -f "$REPO/scripts/run_smoke.py" ] || fail "not an agent-eval repo (scripts/run_smoke.py missing)"
[ -f "$REPO/configs/targets/$TARGET.yaml" ] || fail "target config missing: configs/targets/$TARGET.yaml"

# IAM token presence: .env must exist and carry a non-empty AGENT_TEAMS_TOKEN.
if [ ! -f "$REPO/.env" ] || ! grep -q "^AGENT_TEAMS_TOKEN=..*" "$REPO/.env"; then
  fail "AGENT_TEAMS_TOKEN missing/empty in $REPO/.env — log in to DeepWorks desktop and re-run with token sync, or fill .env manually (see SKILL.md)"
fi
echo "preflight OK: repo=$REPO bench=$BENCH target=$TARGET"

[ "$DRYRUN" = "1" ] && { echo "dry-run: stopping before real run."; exit 0; }

cd "$REPO"

# Best-effort token refresh from the logged-in desktop app (long runs need fresh IAM).
if [ "$SYNC" = "1" ]; then
  if curl -sf --noproxy '*' -m 2 http://127.0.0.1:9223 >/dev/null 2>&1; then
    echo "refreshing AGENT_TEAMS_TOKEN from desktop app..."
    uv run python scripts/sync_deepworks_iam_token.py || echo "token sync failed, keeping existing token" >&2
  else
    echo "desktop debug port not reachable, skip token refresh (using existing token)"
  fi
fi

DATASET_ARGS=()
[ -n "$DATASET" ] && DATASET_ARGS=(--dataset "$DATASET")
uv run python scripts/run_smoke.py --benchmark "$BENCH" --target "$TARGET" "${DATASET_ARGS[@]}"

if [ "$RENDER" = "1" ]; then
  # render_partial_report works for both complete and interrupted runs.
  uv run python scripts/render_partial_report.py --benchmark "$BENCH" --target "$TARGET" || \
    echo "render failed; raw output is in outputs/$BENCH/" >&2
fi

echo "done. report: $REPO/reports/$BENCH/latest.html (if rendered); details: $REPO/outputs/$BENCH/"
