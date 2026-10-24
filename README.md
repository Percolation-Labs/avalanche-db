# Avalanche DB

A record is a point; meaning is the path. Avalanche DB is a memory you **walk**, not one
you search. It reads the places your work already lives, turns them into a typed graph that
never forgets its own history, and answers a question by walking from it, one step at a
time, until the open questions run out. Every walk is kept.

It is one binary and one file on disk. It sits beside your repository and replaces nothing.

The theory it implements is in Sirsh's *The Physics of Meaning*, *Walking towards Meaning*
and *Decisions Over Graphs*; the engine spec is *Avalanche DB: a portable graph engine for
the Percolate pattern*. This README is the user story (REM-1172), and it is also the
acceptance test: see the last section.

## Three layers

Everything Avalanche does sits in one of three layers, over one store.

| Layer | What it does | Code | Calls a model |
|---|---|---|---|
| **Construct** | Builds the data. Adapters record what sources say outright (`ingest`); dreaming decides what a mention means (`dream`). | `src/construct/` | only `dream`, through infer |
| **Infer** | The decision model. Typed questions go in; one choice with a probability comes out; nothing is generated. Every request is recorded and replayed. | `src/infer.rs` | yes, and nowhere else |
| **Walk** | Uses the data. Search draws the circle; a walk steps through a frontier of open questions ranked by a priority policy; `why` prints the result. Pure algorithm. | `src/walk/` | never (a test checks) |
| Store | An append-only log of typed facts with two times, indexed four ways on redb. | `src/store.rs`, `src/model.rs` | |

The line matters. What the walk can find is bounded by what construction wrote, and
construction is where the cost and the judgement are. The walk itself is cheap, exact and
repeatable, so it can be measured.

## 1. Install

```console no-test
$ cargo install --locked --git https://github.com/Percolation-Labs/avalanche-db
```

```console
$ ava --version
ava 0.1.0
```

## 2. Start a store

The repository ships an example: a small billing service, its git history, and its notes (a
decision record, a proposal, two bugs and a support ticket). The rest of this story uses it,
and every output below is what you will see.

```console
$ cd examples/billing
$ ./make.sh
built repo/: 7 commits
$ ava init
created avalanche.toml and .avalanche/store.redb (tenant "me")
  sources: markdown notes, git repo
  ids: ADR decision, BUG issue, P proposal, SUP issue
```

`ava init` looks at the folder and writes `avalanche.toml`: the sources it found, and which
kind of thing each id prefix names, read from the notes' frontmatter. Edit it to add
sources or ids.

```toml
tenant = "me"

[[source]]
adapter = "markdown"     # notes with frontmatter: id, kind, title, date
path = "notes"

[[source]]
adapter = "git"          # commits, parents, files, and every id a message names
path = "repo"

[ids]                    # which kind of thing an id names, by its prefix
ADR = "decision"
BUG = "issue"
P = "proposal"
SUP = "issue"

[model]
provider = "jev"         # the decision model `ava dream` uses; the walk never calls it
model = "jev-1.13.0"
key_env = "AVALANCHE_MODEL_KEY"
```

## 3. Ingest (construct, mechanical)

```console
$ ava ingest
markdown  notes    5 notes    →  16 facts
git       repo     7 commits  →  38 facts
T1: 54 facts
```

Ingestion needs no model. It records what the sources say outright: commits and their
parents, files touched, notes, and every id or path a commit or a note names, as a plain
`mentions` link. Each fact points back to where its content lives, and carries two times:
when it was true, and when the store learned it.

## 4. Configure your key (infer)

```console needs-key
$ ava key check
jev-1.13.0: key accepted
```

Set `AVALANCHE_MODEL_KEY`, or pipe the key to `ava key set` once to keep it in your user
config. You can skip this for the example: every model call it needs is recorded in
`.avalanche/decisions.jsonl`, keyed by a hash of the exact request, and replayed instead of
called. That is why the example gives the same answers, and the same bill, on every
machine.

## 5. Dream (construct, by inference)

```console
$ ava dream
9 mentions to decide, from 3 commits, 1 decision, 1 issue
asked 9 questions in 5 calls (5 replayed, 0 called), $0.0000 billed
  commit:cc746808d1  implements  decision:ADR-007           0.99
  commit:cc746808d1  fixes       issue:BUG-12               0.95
  commit:f1817a41ef  fixes       issue:BUG-3                0.98
  decision:ADR-007   because     issue:BUG-12               1.00
  decision:ADR-007   rejects     proposal:P-3               1.00
  decision:ADR-007   decides     file:src/invoice/round.rs  1.00
  issue:SUP-88       duplicates  issue:BUG-12               1.00
  only mentions: commit:ab90792f34 → decision:ADR-007, decision:ADR-007 → issue:BUG-3
  undecided (p < 0.8): none
T2: 7 facts
```

Code finds the candidates and gathers the evidence; the model only judges what a mention
means. Each question is atomic: one source, one id it names, the link types that fit those
two kinds, one answer with a probability. A source's evidence is sent once for all its
questions: a note's text, or a commit's message with the files it changed and its diff
(bounded). The diff is what lets the model see that "round totals half-even (ADR-007,
BUG-12)" both carries out the decision and fixes the bug; from the message alone it could
not decide. A docs commit that links ADR-007 only mentions it, and ADR-007 saying it is
not about BUG-3 only mentions BUG-3. Only answers at 0.8 or above become links.

## 6. Ask, and walk (walk)

A customer writes in: their invoice is a cent off from their spreadsheet. Search first, the
usual way, by drawing a circle of likeness around the question:

```console
$ ava search "why is the invoice a cent off from the customer's spreadsheet?"
  issue:BUG-12       "A cent off on long invoices"                        5.27
  issue:SUP-88       "Invoice total differs from customer spreadsheet"    3.99
  commit:b9adc7af54  "export: invoices to a spreadsheet"                  2.22
  issue:BUG-3        "Spreadsheet export drops the currency symbol"       1.30
  commit:5b17c0bfa2  "invoice: compute totals"                            0.65
8 records share a word with the question; the best 5 shown
```

The circle finds the problem, not the reason. The decision shares no words with the
question, so it is not in the circle at all. Now walk, starting where the circle is
strongest:

```console
$ ava ask "why is the invoice a cent off from the customer's spreadsheet?"
session s1 at issue:BUG-12, pinned to T2, budget 20
  token s1.0.2
$ ava step s1.0.2
step 1  issue:BUG-12 "A cent off on long invoices"
  + <-because- decision:ADR-007  "Banker's rounding for money amounts"  0.90
  + <-fixes- commit:cc746808d1  "invoice: round totals half-even (ADR-007, BUG-12)"  0.72
  + <-duplicates- issue:SUP-88  "Invoice total differs from customer spreadsheet"  0.45
  open 3 (opened 3, closed 1); next: decision:ADR-007 0.90, commit:cc746808d1 0.72, issue:SUP-88 0.45
  stats: out 2 in 6; held back 0; budget left 16; path use 0; 31 keys in 954µs
  token s1.1.2
$ ava step s1.1.2
step 2  decision:ADR-007 "Banker's rounding for money amounts"
  + -rejects-> proposal:P-3  "Round halves away from zero"  0.73
  + -decides-> file:src/invoice/round.rs  0.49
    -because-> issue:BUG-12  (visited)
    <-implements- commit:cc746808d1  (already open)
  open 4 (opened 2, closed 1); next: proposal:P-3 0.73, commit:cc746808d1 0.72, file:src/invoice/round.rs 0.49
  stats: out 9 in 3; held back 0; budget left 14; path use 0; 26 keys in 872µs
  token s1.2.2
$ ava step s1.2.2
step 3  proposal:P-3 "Round halves away from zero"
    <-rejects- decision:ADR-007  (visited)
  open 3 (opened 0, closed 1); next: commit:cc746808d1 0.72, file:src/invoice/round.rs 0.49, issue:SUP-88 0.45
  stats: out 3 in 2; held back 0; budget left 14; path use 0; 14 keys in 638µs
  token s1.3.2
```

Two hops, and the question changed at each one: what was decided because of this bug, and
what did that decision turn down. ADR-007 rounds the total once, with halves to even, and
rejected P-3, rounding halves away from zero, which is what a spreadsheet does. The cent is
by design. **The walk found it; the circle never did.**

### Steering

The open questions are a frontier, and each carries a priority: the weight of the link
that opened it under the session's policy, less 10% per hop from the start. The default
policy prefers why something was decided (`because` 1.0) and what it turned down
(`rejects` 0.9) over what carried it out (`implements`, `fixes` 0.8), what it governs
(`decides` 0.6) and what else reports the same (`duplicates` 0.5); mechanical links
(`mentions`, `parent`, `touches`) weigh 0 and are not followed. This is the value landscape
that tilts a walk away from wandering, and the agent holds it: every step shows the ranked
frontier, `--take` picks any open question by name, and `--prefer kind=weight` changes the
policy mid-walk.

```console
$ ava step s1.3.2 --take file:src/invoice/round.rs
step 4  file:src/invoice/round.rs
    <-decides- decision:ADR-007  (visited)
  open 2 (opened 0, closed 1); next: commit:cc746808d1 0.72, issue:SUP-88 0.45
  stats: out 0 in 5; held back 0; budget left 14; path use 0; 14 keys in 598µs
  token s1.4.2
```

The token pins the snapshot, so the agent can take as long as it likes between steps and
the graph will not move under it.

### For a person

`ava why` runs the same walk, always taking the best open question, until none are left,
and prints each record under the one that led to it:

```console
$ ava why "why is the invoice a cent off from the customer's spreadsheet?"
issue:BUG-12                            2026-04-09 "A cent off on long invoices"
  led to  decision:ADR-007              2026-04-11 "Banker's rounding for money amounts"
    rejects  proposal:P-3               2026-03-02 "Round halves away from zero"
    decides  file:src/invoice/round.rs
  fixed by  commit:cc746808d1           2026-04-12 "invoice: round totals half-even (ADR-007, BUG-12)"
  duplicated by  issue:SUP-88           2026-04-08 "Invoice total differs from customer spreadsheet"
6 steps, 5 link kinds
$ ava why "why is the invoice a cent off from the customer's spreadsheet?" --prefer duplicates=0
issue:BUG-12                            2026-04-09 "A cent off on long invoices"
  led to  decision:ADR-007              2026-04-11 "Banker's rounding for money amounts"
    rejects  proposal:P-3               2026-03-02 "Round halves away from zero"
    decides  file:src/invoice/round.rs
  fixed by  commit:cc746808d1           2026-04-12 "invoice: round totals half-even (ADR-007, BUG-12)"
5 steps, 4 link kinds
```

## 7. Ask what was known then (walk)

Everything has a date. Ask the same question as it stood the day after the bug was filed:

```console
$ ava why "why is the invoice a cent off from the customer's spreadsheet?" --valid-at 2026-04-10
issue:BUG-12                   2026-04-09 "A cent off on long invoices"
  duplicated by  issue:SUP-88  2026-04-08 "Invoice total differs from customer spreadsheet"
2 steps, 1 link kind
```

On 10 April the bug was known and nothing had been decided. What happened and what it was
taken to mean are kept apart, each with its own date, so any answer can be explained by
what was known when it was given.

## 8. See how the memory is used

```console
$ ava usage
4 sessions, 17 steps
most walked: issue:BUG-12 (4), decision:ADR-007 (3), file:src/invoice/round.rs (3)
link kinds walked: because 3, decides 3, rejects 3, duplicates 2, fixes 2
$ ava log
T1  2026-10-24 11:39Z  54 facts
T2  2026-10-24 11:39Z  7 facts
```

Every step of every walk, and every `--take` and `--prefer`, is logged, so usage is
something you query. The usage log is kept apart from the data's own log: after four walks
the data is still at T2, so a transaction number always names a state of the data.

## Your own history

The same commands run on real work. This is the configuration used on Percolate's own
history (REM-1185): board cards read from a git revision, two repositories, and their merged
pull requests, whose titles, bodies and branch names say which card they carry out.

```toml
tenant = "percolate"

[[source]]
adapter = "markdown"
path = "/Users/sirsh/code/p8-subsystems"
rev = "origin/main"            # read at a revision, so a stale checkout does not matter
dir = "board/cards"

[[source]]
adapter = "git"
path = "/Users/sirsh/code/percolate"
rev = "origin/main"

[[source]]
adapter = "github"             # merged PRs, through `gh`
repo = "Percolation-Labs/percolate"

[ids]
REM = "card"
```

`ava dream --dry-run` says what a dream would ask and roughly what it would cost before
anything is sent, and `--since` limits it to recent sources.

## Phase two

From the theory, next: measuring a walk against diffusion and running the fire test on the
edges it used (`ava measure`); letting walks bend the graph, reinforcing used paths and
decaying unused ones; splitting crowded nodes into shorter links (REM-1168). From the spec,
later: immutable snapshot files, per-tenant encryption and crypto-shredding, a Postgres
adapter, query languages over the step core, and distribution.

## How this README is tested

`cargo test --test readme` builds `ava`, copies `examples/` to a fresh folder, and runs
every `console` block above in order, comparing each command's output to the block with
only durations and wall-clock times masked. Blocks marked `no-test` are skipped, and
`needs-key` blocks run only when `AVALANCHE_MODEL_KEY` is set; every other block runs with
no key, so `dream` must replay. `make.sh` builds the example repository with fixed authors
and dates, so commit ids match on every machine. If the story and the binary disagree, the
build fails.
