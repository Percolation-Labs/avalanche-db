#!/bin/sh
# evals/p8ql/history/build.sh OUT [P8_SUBSYSTEMS] [PERCOLATE] -- a store of Percolate's own history
# for the eval (SET=history STORE=OUT run.sh ...): board cards at origin/main, the percolate
# repository at origin/main, and its merged pull requests through gh. Gold answers in
# questions.jsonl were computed from git under the git adapter's rules: card ids from commit
# subjects only, and at most 40 files per commit.
set -e
out="$1"; sub="${2:-$HOME/code/p8-subsystems}"; perc="${3:-$HOME/code/percolate}"
root="$(cd "$(dirname "$0")/../../.." && pwd)"
git -C "$sub" fetch -q origin main; git -C "$perc" fetch -q origin main
rm -rf "$out" && mkdir -p "$out/.avalanche"
cat > "$out/avalanche.toml" <<TOML
tenant = "percolate"

[[source]]
adapter = "markdown"
path = "$sub"
rev = "origin/main"
dir = "board/cards"

[[source]]
adapter = "git"
path = "$perc"
rev = "origin/main"

[[source]]
adapter = "github"
repo = "Percolation-Labs/percolate"

[ids]
REM = "card"

[paths]
works_with = "<-authoredBy- commit -touches-> file <-touches- commit -authoredBy->"

[model]
provider = "jev"
model = "jev-1.13.0"
key_env = "AVALANCHE_MODEL_KEY"
TOML
(cd "$out" && "$root/target/release/midb" ingest)
echo "pinned: p8-subsystems $(git -C "$sub" rev-parse --short origin/main), percolate $(git -C "$perc" rev-parse --short origin/main)"
