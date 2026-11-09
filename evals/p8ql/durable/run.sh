#!/bin/sh
# evals/p8ql/durable/run.sh OUT REPS -- a durable walk handed between two agents, against one
# agent walking alone. STORE is a folder with avalanche.toml and .avalanche/ (history/build.sh,
# then a dream). Each handoff run: agent A asks and takes two steps, writes the token, and stops;
# agent B gets only the question and the token. Writes OUT/{handoff,single}-<rep>/ with
# answer.json, a.log and b.log (or calls.log), and agent JSON.
set -e
here="$(cd "$(dirname "$0")" && pwd)"; out="$1"; reps="${2:-3}"
q="Why does every release train now measure memory retrieval? Name the problem that prompted it, and what caused that problem."
mkdir -p "$out"; out="$(cd "$out" && pwd)"
agent() { # run-dir prompt-file... ; fills {RUN} {QUESTION} {TOKEN}
  run="$1"; shift
  p=$(cat "$here/common.txt" "$@" | RUN="$run" Q="$q" TOKEN="$(cat "$run/handoff.txt" 2>/dev/null || true)" python3 -c "import os,sys;print(sys.stdin.read().replace('{RUN}',os.environ['RUN']).replace('{QUESTION}',os.environ['Q']).replace('{TOKEN}',os.environ['TOKEN']))")
  (cd "$run" && claude -p "$p" --model sonnet --effort low --output-format json --allowedTools Bash \
     --disallowedTools Read Write Edit Glob Grep WebFetch WebSearch Agent --strict-mcp-config --no-session-persistence)
}
for rep in $(seq 1 "$reps"); do
  r="$out/handoff-$rep"; "$here/../setup.sh" "$r" baseline >/dev/null
  agent "$r" "$here/a.txt" > "$r/agent-a.json"; mv "$r/calls.log" "$r/a.log"; : > "$r/calls.log"
  agent "$r" "$here/b.txt" > "$r/agent-b.json"; mv "$r/calls.log" "$r/b.log"
  rm -rf "$r/store" "$r/bin"; echo "handoff-$rep: token $(cat "$r/handoff.txt" 2>/dev/null), b made $(grep -c . "$r/b.log") calls"
  s="$out/single-$rep"; "$here/../setup.sh" "$s" baseline >/dev/null
  agent "$s" "$here/single.txt" > "$s/agent.json"; rm -rf "$s/store" "$s/bin"; echo "single-$rep: $(grep -c . "$s/calls.log") calls"
done
