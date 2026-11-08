#!/bin/sh
# evals/p8ql/run.sh OUT [REPS] [JOBS] -- every question x both arms x REPS headless agent runs,
# JOBS at a time. Each run gets a fresh store (setup.sh) and its arm's prompt from prompts/, and
# runs `claude -p` with Sonnet at low effort, Bash only, no MCP servers. Writes
# OUT/<arm>-<Q>-<rep>/{answer.json,calls.log,agent.json}; a run with an answer is skipped, so a
# rerun resumes. Score with: python3 evals/p8ql/score.py OUT
set -e
here="$(cd "$(dirname "$0")" && pwd)"
if [ "$1" = --one ]; then
  out="$2"; arm="$3"; q="$4"; rep="$5"; run="$out/$arm-$q-$rep"
  [ -s "$run/answer.json" ] && exit 0
  "$here/setup.sh" "$run" "$arm" >/dev/null
  prompt=$(RUN="$run" python3 - "$here" "$arm" "$q" <<'PY'
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
  rm -rf billing bin; [ -s agent.err ] || rm -f agent.err   # keep only the results
  echo "done $arm-$q-$rep: $(grep -c . calls.log) calls"
  exit 0
fi
out="$1"; reps="${2:-3}"; jobs="${3:-5}"
mkdir -p "$out"; out="$(cd "$out" && pwd)"
python3 - "$here/questions.jsonl" "$reps" <<'PY' | xargs -P "$jobs" -n 3 "$0" --one "$out"
import json, sys
for rep in range(1, int(sys.argv[2]) + 1):
    for line in open(sys.argv[1]):
        for arm in ("p8ql", "baseline"):
            print(arm, json.loads(line)["id"], rep)
PY
