# Avalanche DB

A memory you **walk**, not one you search. Avalanche DB reads the places your work already
lives (git history, notes, research), turns them into a typed graph that never forgets its
own history, and answers a question by walking from it, one step at a time, until the open
questions run out.

It is one binary and one file on disk. It sits beside your repository and replaces nothing.

## Install

```console no-test
$ curl -fsSL https://raw.githubusercontent.com/Percolation-Labs/avalanche-db/main/install.sh | sh
```

From a clone, `./install.sh --local` builds it instead (it needs a Rust toolchain).

## A cent off

The repository ships an example: a small billing service with its git history, a few notes
and a Percolate research package. Build it and read it all in:

```console
$ cd examples/billing
$ ./make.sh
built repo/: 7 commits
$ ava init
created avalanche.toml and .avalanche/store.redb (tenant "me")
  sources: markdown notes, git repo, percolate percolate.json
  ids: ADR decision, BUG issue, P proposal, SUP issue
$ ava ingest
markdown  notes          5 notes    →  16 facts
git       repo           7 commits  →  38 facts
percolate percolate.json 3 claims   →  28 facts
T1: 82 facts in 48.4ms
```

Ingesting records only what the sources say outright. `ava dream` asks a model what each
mention means: does this commit fix that bug, does this claim support that decision. The
example's model answers are recorded, so it needs no key and bills nothing:

```console
$ ava dream
12 mentions to decide, from 3 commits, 3 claims, 1 decision, 1 issue
asked 12 questions in 8 calls (8 replayed, 0 called), $0.0000 billed
  claim:rp-rounding/C1  supports    decision:ADR-007           0.96
  commit:cc746808d1     implements  decision:ADR-007           0.99
  commit:cc746808d1     fixes       issue:BUG-12               0.94
  commit:f1817a41ef     fixes       issue:BUG-3                0.97
  decision:ADR-007      decides     file:src/invoice/round.rs  1.00
  decision:ADR-007      because     issue:BUG-12               1.00
  decision:ADR-007      rejects     proposal:P-3               1.00
  issue:SUP-88          duplicates  issue:BUG-12               1.00
  only mentions: claim:rp-rounding/C3 → decision:ADR-007, commit:ab90792f34 → decision:ADR-007, decision:ADR-007 → issue:BUG-3
  undecided (p < 0.8): claim:rp-rounding/C2 challenges proposal:P-3 (0.40)
T2: 8 facts
```

A customer writes in: their invoice is a cent off from their spreadsheet. Ask why:

```console
$ ava why "why is the invoice a cent off from the customer's spreadsheet?" --prefer duplicates=0,cites=0
issue:BUG-12                               2026-04-09 "A cent off on long invoices"
  led to  decision:ADR-007                 2026-04-11 "Banker's rounding for money amounts"
    rejects  proposal:P-3                  2026-03-02 "Round halves away from zero"
    supported by  claim:rp-rounding/C1     2026-04-14 "Rounding every line and adding the results lets rounding er…"
      answers  question:q-round-once       2026-04-14 "Should an invoice total be rounded once, or line by line?"
        answered by  claim:rp-rounding/C3  2026-04-14 "People judge a total by whether it matches their own sheet,…"
      made by  package:rp-rounding         2026-04-14 "Rounding money on long invoices: once per invoice, or once…"
        makes  claim:rp-rounding/C2        2026-04-14 "Sheet formulas round each line with halves away from zero,…"
    decides  file:src/invoice/round.rs               
  fixed by  commit:cc746808d1              2026-04-12 "invoice: round totals half-even (ADR-007, BUG-12)"
10 steps, 7 link kinds; 202 keys read in 2.4ms
```

Search finds the bug report and stops there, because the reason shares no words with the
question. The walk goes on from the bug to the decision made because of it, ADR-007 (round
the total once, halves to even), and to the proposal ADR-007 turned down, P-3 (halves away
from zero, which is what a spreadsheet does). The cent is by design.

## Read more

- [docs/stories.md](docs/stories.md): the ten stories in full, including walking one step
  at a time, asking what the graph knew then, retracting a link, replaying questions, and
  serving the walk to an agent over MCP.
- [docs/architecture.md](docs/architecture.md): the three layers (construct, infer, walk)
  and how to point Avalanche at your own history.
- [docs/testing.md](docs/testing.md): how this README and the stories run as tests.
- [specs/engine.md](specs/engine.md): the design principles (Rust and redb, one file,
  append-only, bitemporal quads, typed predicates, durable sessions, tenant isolation) and
  which of them are built.
- [specs/p8ql.md](specs/p8ql.md): P8QL, the proposed query language: SQL-like statements
  whose every clause is one walk step, with likeness and connection as the two kinds of step.
- [specs/plan.md](specs/plan.md): the approved plans, what we measured, and what comes next.
