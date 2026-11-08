# P8QL agent eval

Does an agent answer questions about a history better, or more cheaply, through P8QL than
through search and the raw walk ([specs/p8ql.md](../../specs/p8ql.md), "Evals")? Each question
in `questions.jsonl` has gold answers as record ids, in one of four tiers: record select, fuzzy
lookup, graph pattern and iterated walk.

Each run is one agent and one question in one arm, against its own fresh copy of the billing
example, because walks write to the store's usage log:

```sh
cargo build --release
./evals/p8ql/setup.sh RUNS/p8ql-Q3 p8ql          # ava query, ava query --explain, ava schema
./evals/p8ql/setup.sh RUNS/baseline-Q3 baseline  # ava search, ask, step, why, edges
```

`setup.sh` puts an `ava` on the run's PATH that refuses the other arm's commands and logs
every call to `calls.log`. The agent is told only the commands of its arm and the question, may
use nothing but `ava`, and writes `answer.json` as `{"ids": [...], "answer": "..."}`. Both arms
use the same model and the same prompt apart from the command list.

```sh
python3 evals/p8ql/score.py RUNS
```

prints recall and precision of the gold ids and the number of `ava` calls, per question and per
arm. One run per question is directional, not a measurement: the first round is 5 questions x 2
arms, and a claim of a difference waits for replicates. Results go in `RESULTS.md`, newest first.
