# Avalanche DB

A record is a point; meaning is the path. Avalanche DB is a memory you **walk**, not one
you search. It reads the places your work already lives, turns them into a typed graph that
never forgets its own history, and answers a question by walking from it, one step at a
time, until the open questions run out. Every walk is kept.

It is one binary and one file on disk. It sits beside your repository and replaces nothing.

The theory it implements is in Sirsh's *The Physics of Meaning*, *Walking towards Meaning*
and *Decisions Over Graphs*; the engine spec is *Avalanche DB: a portable graph engine for
the Percolate pattern*. This README is the v1 user story (REM-1172), and it is also the
acceptance test: see the last section.

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
provider = "jev"         # the decision model `ava dream` uses; queries never call it
model = "jev-1.13.0"
key_env = "AVALANCHE_MODEL_KEY"
```

## 3. Ingest: the records

```console
$ ava ingest
markdown  notes    5 notes    →  16 facts
git       repo     7 commits  →  38 facts
T1: 54 facts
```

Ingestion is mechanical and needs no model. It records what the sources say outright:
commits and their parents, files touched, notes, and every id or path a commit or a note
names, as a plain `mentions` link. Each fact points back to where its content lives, and
carries two times: when it was true, and when the store learned it.

## 4. Configure your key

```console needs-key
$ ava key check
jev-1.13.0: key accepted
```

Set `AVALANCHE_MODEL_KEY`, or pipe the key to `ava key set` once to keep it in your user
config. You can skip this for the example: every model call it needs is recorded in
`.avalanche/decisions.jsonl`, keyed by a hash of the request, and replayed instead of
called. That is why the example gives the same answers, and the same bill, on every
machine.

## 5. Dream: turn mentions into links you can walk

```console
$ ava dream
9 mentions to decide, from 3 commits, 1 decision, 1 issue
asked 9 questions in 5 calls (5 replayed, 0 called), $0.0001
  commit:f1817a41ef  fixes       issue:BUG-3                0.86
  decision:ADR-007   because     issue:BUG-12               1.00
  decision:ADR-007   rejects     proposal:P-3               1.00
  decision:ADR-007   decides     file:src/invoice/round.rs  1.00
  issue:SUP-88       duplicates  issue:BUG-12               1.00
  only mentions: commit:ab90792f34 → decision:ADR-007, decision:ADR-007 → issue:BUG-3
  undecided (p < 0.8): commit:cc746808d1 implements decision:ADR-007 (0.69), commit:cc746808d1 fixes issue:BUG-12 (0.64)
T2: 5 facts
```

Dreaming is the only place a model runs, and each question it asks is atomic: one source,
one id it names, the link types that fit those two kinds, and one answer with a
probability. Code finds the candidates; the model only judges what a mention means. A
commit that links to ADR-007 from the README only mentions it; ADR-007 saying it is not
about BUG-3 only mentions BUG-3. The commit that made the change says just "round totals
half-even (ADR-007, BUG-12)", too little for the model to be sure, so those two stay
mentions until there is more to read. Only answers at 0.8 or above become links, and each
source's text is sent once for all of its questions.

## 6. Ask, and walk

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
  + <-because- decision:ADR-007  "Banker's rounding for money amounts"
  + <-duplicates- issue:SUP-88  "Invoice total differs from customer spreadsheet"
  open 2 (opened 2, closed 1); link kinds: none yet
  stats: out 2 in 5; held back 0; budget left 17; path use 0; 27 keys in 696µs
  token s1.1.2
$ ava step s1.1.2
step 2  decision:ADR-007 "Banker's rounding for money amounts"
    -because-> issue:BUG-12  (visited)
  + -rejects-> proposal:P-3  "Round halves away from zero"
  + -decides-> file:src/invoice/round.rs
  open 3 (opened 2, closed 1); link kinds: because
  stats: out 9 in 2; held back 0; budget left 15; path use 0; 18 keys in 767µs
  token s1.2.2
$ ava step s1.2.2
step 3  proposal:P-3 "Round halves away from zero"
    <-rejects- decision:ADR-007  (visited)
  open 2 (opened 0, closed 1); link kinds: because, rejects
  stats: out 3 in 2; held back 0; budget left 15; path use 0; 16 keys in 731µs
  token s1.3.2
```

Two hops, and the question changed at each one: what was decided because of this bug, and
what did that decision turn down. ADR-007 rounds the total once, with halves to even, and
rejected P-3, rounding halves away from zero, which is what a spreadsheet does. The cent is
by design. **The walk found it; the circle never did.**

Each step returns what it found, how many questions are still open, statistics about the
graph around it, and a token. The open questions are the reasoning stack: an agent reasons
between steps and chooses what to follow (`--follow because,rejects`). The token pins the
snapshot, so the agent can take as long as it likes and the graph will not move under it.

For a person, `ava why` runs the same walk until no questions are open and prints what it
reached, each record under the one that led to it:

```console
$ ava why "why is the invoice a cent off from the customer's spreadsheet?"
issue:BUG-12                            2026-04-09 "A cent off on long invoices"
  led to  decision:ADR-007              2026-04-11 "Banker's rounding for money amounts"
    rejects  proposal:P-3               2026-03-02 "Round halves away from zero"
    decides  file:src/invoice/round.rs
  duplicated by  issue:SUP-88           2026-04-08 "Invoice total differs from customer spreadsheet"
5 steps, 4 link kinds
```

## 7. Ask what was known then

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
3 sessions, 10 steps
most walked: issue:BUG-12 (3), decision:ADR-007 (2), issue:SUP-88 (2)
link kinds walked: because 2, duplicates 2, rejects 2, decides 1
```

Every step of every walk is logged in the same store, so usage is something you query.

## Phase two

From the theory, next: measuring a walk against diffusion and running the fire test on the
edges it used (`ava measure`); letting walks bend the graph, reinforcing used paths and
decaying unused ones; splitting crowded nodes into shorter links (REM-1168). From the spec,
later: immutable snapshot files, per-tenant encryption and crypto-shredding, a Postgres
adapter, query languages over the step core, and distribution.

## How this README is tested

`cargo test --test readme` builds `ava`, copies `examples/` to a fresh folder, and runs
every `console` block above in order, comparing each command's output to the block with
only durations masked. Blocks marked `no-test` are skipped, and `needs-key` blocks run only
when `AVALANCHE_MODEL_KEY` is set; every other block runs with no key, so `dream` must
replay. `make.sh` builds the example repository with fixed authors and dates, so commit ids
match on every machine. If the story and the binary disagree, the build fails.
