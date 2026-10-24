# Avalanche DB

> **Draft 2 for review (REM-1172).** This README is the user story. Nothing new below is
> built until Sirsh agrees the story; then each section becomes tickets, and this file
> becomes the acceptance test (last section). The theory it implements is in *The Physics
> of Meaning*, *Walking towards Meaning* and *Decisions Over Graphs*; the engine spec is
> *Avalanche DB: a portable graph engine for the Percolate pattern*.

A record is a point; meaning is the path. Avalanche DB is a memory you **walk**, not one
you search. It reads the places your work already lives, turns them into a typed graph that
never forgets its own history, and answers a question by walking from it, one decision at a
time, until the open questions run out. Every walk is kept, and every walk bends the graph
for the next one.

It is one binary and one file on disk. It sits beside your repository and replaces nothing.

## 1. Install

```console
$ cargo install --locked --git https://github.com/Percolation-Labs/avalanche-db ava
$ ava --version
ava 0.1.0
```

## 2. Start a store

The repository ships an example: a small billing service, its git history, and its notes
(two decision records, a proposal, a bug and a support ticket). The rest of this story uses
it, and every output below is what you will see.

```console
$ cd avalanche-db/examples/billing
$ ava init
created avalanche.toml and .avalanche/store.redb (tenant "me")
```

```toml
# avalanche.toml
tenant = "me"

[[source]]
adapter = "git"          # commits, parents, files, and every id a message names
path = "repo"

[[source]]
adapter = "markdown"     # notes, decision records, tickets
path = "notes"

[model]
provider = "jev"         # the decision model `ava dream` uses; queries never call it
key_env = "AVALANCHE_MODEL_KEY"
```

## 3. Ingest: the records

```console
$ ava ingest
git       repo    24 commits  →  141 facts
markdown  notes    6 notes    →   38 facts
T1: 179 facts
```

Ingestion is mechanical and needs no model. It records what the sources say outright:
commits and their parents, files touched, notes, and every explicit reference such as
`ADR-007` or `BUG-12`. Each fact points back to where its content lives; no text is copied
in. Each fact carries two times: when it was true, and when the store learned it.

## 4. Configure your key

```console
$ export AVALANCHE_MODEL_KEY=...       # or: ava key set
$ ava key check
jev: key accepted ($0.042 per million input tokens)
```

You can skip this for the example. Every model call the example needs is recorded in
`.avalanche/decisions.jsonl`, keyed by its input, and replayed instead of called. That is
why the example gives the same answers, and the same bill, on every machine.

## 5. Dream: turn records into links you can walk

```console
$ ava dream
extract   6 notes, 24 commit messages
          11 decisions asked in 3 calls (3 replayed, 0 called), cost $0.0004
          proposed 19 links, accepted 17, refused 2 (outside the type system)
T2: 17 facts
  ADR-007 "Round invoice totals half-even"
    decides           src/invoice/round.rs
    rejects           proposal: round half-up          (notes/2026-03-02-rounding.md)
    because           BUG-12 "a cent off on long invoices"
    implemented by    commit 9c1e04a2b7
  SUP-88 duplicates   BUG-12
```

Dreaming is the only place a model runs. Each question it asks is an *atomic* decision:
one input, a fixed set of choices, one answer with a probability, nothing generated.
"Does this note decide something? Which file? Which alternative does it reject?" The
engine keeps only the answers that fit its types; the rest are listed by
`ava dream --show-refused`. A good dream makes every later step of a walk an atom.

## 6. Ask, and walk

A support ticket says a customer's invoice is a cent off from their spreadsheet. Search
first, the usual way: draw a circle of likeness around the question.

```console
$ ava search "why is the invoice a cent off from the customer's spreadsheet?"
  SUP-88   "Invoice total differs from customer spreadsheet"   0.71
  BUG-12   "A cent off on long invoices"                       0.52
  BUG-3    "Spreadsheet export drops currency symbol"          0.38
(the circle: 3 records; ADR-007 is not in it)
```

The answer is not in the circle. Now walk:

```console
$ ava ask "why is the invoice a cent off from the customer's spreadsheet?"
session s1 at SUP-88, pinned to T2, budget 20
  open questions 1
  token s1.0.2

$ ava step s1.0.2
step 1  SUP-88 "Invoice total differs from customer spreadsheet"
  + -duplicates->   BUG-12   "A cent off on long invoices"
  open questions 1 (opened 1, closed 1)   link kinds so far: duplicates
  token s1.1.2

$ ava step s1.1.2
step 2  BUG-12 "A cent off on long invoices"
  + <-because-      ADR-007  "Round invoice totals half-even"
  + <-fixes-        commit 9c1e04a2b7
  open questions 2 (opened 2, closed 1)   link kinds so far: duplicates, because
  token s1.2.2

$ ava step s1.2.2
step 3  ADR-007 "Round invoice totals half-even"
  + -rejects->      proposal: round half-up   "matches what spreadsheets do"
    -implemented by-> commit 9c1e04a2b7      (already open)
  open questions 2 (opened 1, closed 1)   link kinds so far: duplicates, because, rejects
  token s1.3.2

$ ava step s1.3.2
step 4  proposal: round half-up "matches what spreadsheets do"   rejected 2026-04-11
  open questions 1 (opened 0, closed 1)   getting warmer: branching 0.0
  token s1.4.2
```

Four hops, four kinds of link, and the question changed at each one. The cent is by
design: ADR-007 chose half-even rounding after BUG-12, and rejected half-up, which is what
the customer's spreadsheet does. **The walk found it; the circle never did.**

Each step returns what it found, the open questions, and a token. The open questions are
the reasoning stack: an agent reasons between steps and chooses what to follow. When each
question closes more than it opens, the walk is getting warmer. The token pins the snapshot,
so the agent can think as long as it likes and the graph will not move under it.

For a person, `ava why` runs the same walk to its budget and prints the path:

```console
$ ava why "why is the invoice a cent off from the customer's spreadsheet?"
SUP-88 "Invoice total differs from customer spreadsheet"
  duplicates  BUG-12 "A cent off on long invoices"                 (2026-04-09)
  because of  ADR-007 "Round invoice totals half-even"             (2026-04-11)
    rejected  round half-up "matches what spreadsheets do"         (2026-03-02)
    built in  commit 9c1e04a2b7                                    (2026-04-12)
4 hops, 4 link kinds; from BUG-12, 2 independent paths reach ADR-007
```

From the bug, two independent paths reach the decision (directly, and through the commit
that fixed it), so that part of the answer does not hang on one link.

## 7. Measure the walk

```console
$ ava measure s1
diffusion   a random walk from SUP-88 reaches ADR-007 in 38.4 steps on average
this walk   4 steps; departure from diffusion 3.1 bits
fire test   scrambling the 4 edges this walk used loses the answer;
            scrambling 4 random edges loses it 6% of the time
```

This is the number to optimise instead of similarity: value reached against departure from
wandering. A random walk is the zero point, worked out exactly from the graph rather than
sampled, so it is the same on every run. The fire test says which links the answer depended
on: scramble them and see what is lost.

## 8. Remembering bends the memory

The walk is now part of the store, and the next dream bends the graph by it:

```console
$ ava dream
bend      1 walk since T2: 4 edges reinforced, 0 decayed
T8: 4 facts

$ ava why "why is the invoice a cent off from the customer's spreadsheet?"
...
3 hops (was 4): the walked path is now the easiest one
```

Paths that are walked get easier; paths left unused fade. Nothing is deleted: a
reinforcement or a decay is a fact with its own time, so you can always ask what the graph
looked like before.

## 9. Ask what was known then

```console
$ ava why "why is the invoice a cent off from the customer's spreadsheet?" --valid-at 2026-03-05
SUP-88 is not yet known
nearest at 2026-03-05: proposal round half-up "matches what spreadsheets do"  (open)
no decision yet
```

What happened and what it was taken to mean are kept apart, each with its own date. A
rejected proposal stays in the graph as rejected, and any answer can be explained by what
the graph knew when it was given.

## 10. See how the memory is used

```console
$ ava usage
3 sessions, 11 steps
most walked: BUG-12 (3), ADR-007 (3), SUP-88 (2)
link kinds walked: duplicates 3, because 3, rejects 2, fixes 1
```

Every step of every walk is logged in the same store, so usage is something you query.

## What is not in this story

From the spec, for later: snapshots as separate immutable files, per-tenant encryption and
crypto-shredding, a Postgres adapter, query languages on top of the step core, splitting
crowded nodes into shorter links (REM-1168), the sidecar and cluster roles, and
distribution.

## How this README is tested

Every `console` block above is a test. `cargo test --test readme` builds `ava`, copies
`examples/billing` to a fresh folder, runs each command in order, and compares the output
to the block, with only durations masked. `examples/billing/make.sh` builds the example
repository with fixed authors and dates, so commit ids match on every machine. The model's
answers and their cost come from `decisions.jsonl`, so the test runs offline with no key.
The diffusion baseline is computed exactly, not sampled. If the story and the binary
disagree, the build fails.

## Today's spike

`ava` already ingests git history, takes typed facts and refuses those outside its types,
and has `ask`, `step` (stack, budget, token, statistics), `--as-of` reads and a usage
graph. Not yet built: `init`, the markdown adapter, `key`, `dream` (extract and bend),
`search`, `why`, `measure`, `--valid-at` on walks, and the billing example.
