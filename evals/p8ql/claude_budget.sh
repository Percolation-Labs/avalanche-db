# claude_budget.sh -- sourced by the eval scripts. No batch run uses Claude (Sirsh, 13 Nov 2026):
# each headless agent run counts against CLAUDE_BUDGET, which defaults to 0, so a run refuses
# unless it names a budget. Runs are counted per output folder in DIR/.claude-runs; a lock keeps
# the count right when runs go in parallel (run.sh's JOBS).
claude_allowed() { # DIR
  dir="$1"; budget="${CLAUDE_BUDGET:-0}"
  while ! mkdir "$dir/.claude.lock" 2>/dev/null; do sleep 1; done
  n=$(cat "$dir/.claude-runs" 2>/dev/null || echo 0)
  if [ "$n" -ge "$budget" ]; then
    rmdir "$dir/.claude.lock"
    echo "refused: $n of CLAUDE_BUDGET=$budget headless Claude runs used in $dir. No batch run uses Claude; name a small budget for a hand-picked check." >&2
    return 1
  fi
  echo $((n + 1)) > "$dir/.claude-runs"; rmdir "$dir/.claude.lock"
}
