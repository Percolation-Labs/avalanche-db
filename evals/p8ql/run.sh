#!/bin/sh
# evals/p8ql/run.sh OUT [REPS] [JOBS] -- every question x both arms x REPS headless agent runs,
# JOBS at a time. Each run gets a fresh store (setup.sh) and its arm's prompt from prompts/, and
# runs `claude -p` with Sonnet at low effort, Bash only, no MCP servers. Writes
# OUT/<arm>-<Q>-<rep>/{answer.json,calls.log,agent.json}; a run with an answer is skipped, so a
# rerun resumes. Score with: python3 evals/p8ql/score.py OUT
# SET=history runs history/questions.jsonl with history/prompts/ against the store in STORE
# (history/build.sh); the default set is the billing example. ONLY=Q2,Q4 runs just those;
# ARMS=p8ql runs one arm. Runs load the user's Claude Code settings, so a Stop hook there
# can cost each run a turn; that is the same in every arm and variant.
# Every run counts against CLAUDE_BUDGET (default 0): see claude_budget.sh.
set -e
here="$(cd "$(dirname "$0")" && pwd)"; set_dir="$here${SET:+/$SET}"; export SET STORE
if [ "$1" = --one ]; then
  out="$2"; arm="$3"; q="$4"; rep="$5"; run="$out/$arm-$q-$rep"
  [ -s "$run/answer.json" ] && exit 0
  . "$here/claude_budget.sh"; claude_allowed "$out" || exit 0
  "$here/setup.sh" "$run" "$arm" >/dev/null
  prompt=$(RUN="$run" python3 - "$set_dir" "$arm" "$q" <<'PY'
import json, os, sys
here, arm, qid = sys.argv[1:]
q = next(d for d in map(json.loads, open(f"{here}/questions.jsonl")) if d["id"] == qid)
print(open(f"{here}/prompts/{arm}.txt").read().replace("{RUN}", os.environ["RUN"]).replace("{QUESTION}", q["question"]))
PY
)
  cd "$run"
  claude -p "$prompt" --model sonnet --effort low --output-format json \
    --allowedTools Bash --disallowedTools Read Write Edit Glob Grep WebFetch WebSearch Agent \
    --strict-mcp-config --no-session-persistence > agent.json 2> agent.err \
    || echo "$arm-$q-$rep: claude exited $?" >&2
  rm -rf store bin; [ -s agent.err ] || rm -f agent.err   # keep only the results
  echo "done $arm-$q-$rep: $(grep -c . calls.log) calls"
  exit 0
fi
out="$1"; reps="${2:-3}"; jobs="${3:-5}"
mkdir -p "$out"; out="$(cd "$out" && pwd)"
ONLY="$ONLY" ARMS="$ARMS" python3 - "$set_dir/questions.jsonl" "$reps" <<'PY' | xargs -P "$jobs" -n 3 "$0" --one "$out"
import json, os, sys
only = set(filter(None, os.environ.get("ONLY", "").split(",")))
arms = [a for a in ("p8ql", "baseline") if a in (os.environ.get("ARMS") or "p8ql,baseline").split(",")]
for rep in range(1, int(sys.argv[2]) + 1):
    for line in open(sys.argv[1]):
        q = json.loads(line)["id"]
        if not only or q in only:
            for arm in arms:
                print(arm, q, rep)
PY
