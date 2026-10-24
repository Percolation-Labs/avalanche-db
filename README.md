# Avalanche DB

A record is a point; meaning is the path. Avalanche DB is a memory you **walk**, not one
you search. It reads the places your work already lives, turns them into a typed graph that
never forgets its own history, and answers a question by walking from it, one step at a
time, until the open questions run out. Every walk is kept.

It is one binary and one file on disk. It sits beside your repository and replaces nothing.

The theory it implements is in Sirsh's *The Physics of Meaning*, *Walking towards Meaning*
and *Decisions Over Graphs*; the engine spec is *Avalanche DB: a portable graph engine for
the Percolate pattern*. This README is the user story (REM-1172): ten stories, each shown
below as commands with their real output. It is also the acceptance test: see the last
section.

| # | Story | Section |
|---|---|---|
| 1 | Install one binary with a single command, on a laptop, with no server | [1](#1-install-one-binary) |
| 2 | Point it at a Git repo and ingest the full history in seconds | [2](#2-ingest-a-git-history) |
| 3 | Add notes, or Percolate claims and questions, through a second adapter | [3](#3-add-notes-and-percolate-research) |
| 4 | Set your key and dream: link commits, cards and claims | [4](#4-set-your-key-and-dream) |
| 5 | Ask why, and walk from the question to the decision to the commits, step by step | [5](#5-ask-why-and-walk) |
| 6 | Ask what the graph knew then, and see how it differs from now | [6](#6-what-was-known-then) |
| 7 | Retract a wrong link; the rejection stays on record as a fact | [7](#7-retract-a-wrong-link) |
| 8 | Every answer comes with its path and statistics | [8](#8-the-path-and-the-statistics) |
| 9 | Replay old questions after re-indexing: a regression test for the graph | [9](#9-replay-questions-after-a-rebuild) |
| 10 | Give an agent the same session API over MCP | [10](#10-the-same-walk-for-an-agent) |

## Three layers

Everything Avalanche does sits in one of three layers, over one store.

| Layer | What it does | Code | Calls a model |
|---|---|---|---|
| **Construct** | Builds the data. Adapters record what sources say outright (`ingest`); dreaming decides what a mention means (`dream`); a person takes a link back (`retract`). | `src/construct/` | only `dream`, through infer |
| **Infer** | The decision model. Typed questions go in; one choice with a probability comes out; nothing is generated. Every request is recorded and replayed. | `src/infer.rs` | yes, and nowhere else |
| **Walk** | Uses the data. Search draws the circle; a walk steps through a frontier of open questions ranked by a priority policy; `why` prints the result; the suite replays kept questions; `mcp` serves the walk to an agent. Pure algorithm. | `src/walk/` | never (a test checks) |
| Store | An append-only log of typed facts with two times, indexed four ways on redb. | `src/store.rs`, `src/model.rs` | |

The line matters. What the walk can find is bounded by what construction wrote, and
construction is where the cost and the judgement are. The walk itself is cheap, exact and
repeatable, so it can be measured.

## 1. Install one binary

```console no-test
$ curl -fsSL https://raw.githubusercontent.com/Percolation-Labs/avalanche-db/main/install.sh | sh
installed ava 0.1.0 at /Users/you/.local/bin/ava
```

`install.sh` downloads the release built for your machine (macOS or Linux, on Apple
silicon, Intel or ARM), checks it against its published checksum, and puts `ava` in
`~/.local/bin`. There is no server, daemon or account: `ava` is one 6 MB binary, and a
store is one file in the folder you run it in. With a Rust toolchain you can build it
instead:

```console no-test
$ cargo install --locked --git https://github.com/Percolation-Labs/avalanche-db
```

```console
$ ava --version
ava 0.1.0
```

## 2. Ingest a Git history

The repository ships an example: a small billing service, its git history, its notes (a
decision record, a proposal, two bugs and a support ticket) and a Percolate research
package about it. The rest of this story uses it, and every output below is what you will
see.

```console
$ cd examples/billing
$ ./make.sh
built repo/: 7 commits
$ ava init
created avalanche.toml and .avalanche/store.redb (tenant "me")
  sources: markdown notes, git repo, percolate percolate.json
  ids: ADR decision, BUG issue, P proposal, SUP issue
$ ava ingest repo
git       repo           7 commits  →  38 facts
T1: 38 facts in 34.6ms
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

[[source]]
adapter = "percolate"    # Percolate packages, their claims, and the questions they answer
path = "percolate.json"

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

`ava ingest repo` reads only the git source. Ingestion needs no model. It records what the
history says outright: commits and their parents, authors, files touched, and every id a
commit message names, as a plain `mentions` link. Each fact points back to where its
content lives (no text is copied, only short labels) and carries two times: when it was
true, and when the store learned it. Each `ingest` is one numbered transaction: this one
is T1.

On real history the same command reads Percolate's two repositories, 3,322 commits, into
33,853 facts in 10 seconds on a laptop.

## 3. Add notes and Percolate research

Each kind of source has an adapter. Notes are markdown with frontmatter. Percolate research
is an export of packages and questions as Percolate returns them: each package makes
claims, each claim cites sources, and a question lists the claims that answer it, with
their stance.

```console
$ ava ingest notes percolate.json
markdown  notes          5 notes    →  16 facts
percolate percolate.json 3 claims   →  28 facts
T2: 44 facts in 25.0ms
```

A claim that names an id (`ADR-007`) mentions it, exactly as a commit does. What that
mention means, whether the claim argues for the decision or against it, is left to
dreaming.

## 4. Set your key and dream

```console needs-key
$ ava key check
jev-1.13.0: key accepted
```

Set `AVALANCHE_MODEL_KEY`, or pipe the key to `ava key set` once to keep it in your user
config. You can skip this for the example: every model call it needs is recorded in
`.avalanche/decisions.jsonl`, keyed by a hash of the exact request, and replayed instead of
called. That is why the example gives the same answers, and the same bill, on every
machine. On your own history, `ava dream --dry-run` says how many calls a dream would make
and roughly what they cost before anything is sent.

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
T3: 8 facts
```

Code finds the candidates and gathers the evidence; the model only judges what a mention
means. Each question is atomic: one source, one id it names, the link types that fit those
two kinds, one answer with a probability. A source's evidence is sent once for all its
questions: a note's text, a claim with its package and sources, or a commit's message with
the files it changed and its diff (bounded). The diff is what lets the model see that
"round totals half-even (ADR-007, BUG-12)" both carries out the decision and fixes the bug.
Claim C1 argues for ADR-007, so it `supports` it. C3 names a cost of ADR-007, but the model
would not call that a challenge, so it stays a mention. Only answers at 0.8 or above become
links.

## 5. Ask why, and walk

A customer writes in: their invoice is a cent off from their spreadsheet. Search first, the
usual way, by drawing a circle of likeness around the question:

```console
$ ava search "why is the invoice a cent off from the customer's spreadsheet?"
  issue:BUG-12          "A cent off on long invoices"                                   6.69
  issue:SUP-88          "Invoice total differs from customer spreadsheet"               5.87
  commit:b9adc7af54     "export: invoices to a spreadsheet"                             3.27
  issue:BUG-3           "Spreadsheet export drops the currency symbol"                  2.05
  claim:rp-rounding/C3  "People judge a total by whether it matches their own sheet,…"  1.32
12 records share a word with the question; the best 5 shown
```

The circle finds the problem, not the reason. The decision shares no words with the
question, so it is not in the circle at all. Now walk, starting where the circle is
strongest:

```console
$ ava ask "why is the invoice a cent off from the customer's spreadsheet?"
session s1 at issue:BUG-12, pinned to T3, budget 20
  token s1.0.3
$ ava step s1.0.3
step 1  issue:BUG-12 "A cent off on long invoices"
  + <-because- decision:ADR-007  "Banker's rounding for money amounts"  0.90
  + <-fixes- commit:cc746808d1  "invoice: round totals half-even (ADR-007, BUG-12)"  0.72
  + <-duplicates- issue:SUP-88  "Invoice total differs from customer spreadsheet"  0.45
  open 3 (opened 3, closed 1); next: decision:ADR-007 0.90, commit:cc746808d1 0.72, issue:SUP-88 0.45
  stats: out 2 in 7; held back 0; budget left 16; path use 0; 32 keys in 471µs
  token s1.1.3
$ ava step s1.1.3
step 2  decision:ADR-007 "Banker's rounding for money amounts"
  + -rejects-> proposal:P-3  "Round halves away from zero"  0.73
  + <-supports- claim:rp-rounding/C1  "Rounding every line and adding the results lets rounding er…"  0.57
  + -decides-> file:src/invoice/round.rs  0.49
    -because-> issue:BUG-12  (visited)
    <-implements- commit:cc746808d1  (already open)
  open 5 (opened 3, closed 1); next: proposal:P-3 0.73, commit:cc746808d1 0.72, claim:rp-rounding/C1 0.57
  stats: out 9 in 6; held back 0; budget left 13; path use 0; 37 keys in 555µs
  token s1.2.3
$ ava step s1.2.3
step 3  proposal:P-3 "Round halves away from zero"
    <-rejects- decision:ADR-007  (visited)
  open 4 (opened 0, closed 1); next: commit:cc746808d1 0.72, claim:rp-rounding/C1 0.57, file:src/invoice/round.rs 0.49
  stats: out 3 in 3; held back 0; budget left 13; path use 0; 15 keys in 400µs
  token s1.3.3
```

Two hops, and the question changed at each one: what was decided because of this bug, and
what did that decision turn down. ADR-007 rounds the total once, with halves to even, and
rejected P-3, rounding halves away from zero, which is what a spreadsheet does. The cent is
by design. **The walk found it; the circle never did.**

### Steering

The open questions are a frontier, and each carries a priority: the weight of the link
that opened it under the session's policy, less 10% per hop from the start. The default
policy prefers why something was decided (`because` 1.0) and what it turned down
(`rejects` 0.9) over what carried it out (`implements`, `fixes` 0.8), the research for and
against it (`challenges` 0.8, `supports` 0.7), what it governs (`decides` 0.6) and what
else reports the same (`duplicates` 0.5). Mechanical links (`mentions`, `parent`,
`touches`) weigh 0 and are not followed. This is the value landscape that tilts a walk away
from wandering, and the agent holds it: every step shows the ranked frontier, `--take`
picks any open question by name, and `--prefer kind=weight` changes the policy mid-walk.

```console
$ ava step s1.3.3 --take file:src/invoice/round.rs
step 4  file:src/invoice/round.rs
    <-decides- decision:ADR-007  (visited)
  open 3 (opened 0, closed 1); next: commit:cc746808d1 0.72, claim:rp-rounding/C1 0.57, issue:SUP-88 0.45
  stats: out 0 in 5; held back 0; budget left 13; path use 0; 14 keys in 414µs
  token s1.4.3
```

The token pins the snapshot, so the agent can take as long as it likes between steps and
the graph will not move under it.

### For a person

`ava why` runs the same walk, always taking the best open question, until none are left,
and prints each record under the one that led to it, with the date it became true:

```console
$ ava why "why is the invoice a cent off from the customer's spreadsheet?"
issue:BUG-12                               2026-04-09 "A cent off on long invoices"
  led to  decision:ADR-007                 2026-04-11 "Banker's rounding for money amounts"
    rejects  proposal:P-3                  2026-03-02 "Round halves away from zero"
    supported by  claim:rp-rounding/C1     2026-04-14 "Rounding every line and adding the results lets rounding er…"
      answers  question:q-round-once       2026-04-14 "Should an invoice total be rounded once, or line by line?"
        answered by  claim:rp-rounding/C3  2026-04-14 "People judge a total by whether it matches their own sheet,…"
          cites  source:rp-rounding/S3     2026-04-14 "Support ticket SUP-88"
      made by  package:rp-rounding         2026-04-14 "Rounding money on long invoices: once per invoice, or once…"
        makes  claim:rp-rounding/C2        2026-04-14 "Sheet formulas round each line with halves away from zero,…"
          cites  source:rp-rounding/S2     2026-04-14 "ROUND function, Microsoft Support"
      cites  source:rp-rounding/S1         2026-04-14 "IEEE 754-2019, section 4.3.1: roundTiesToEven"
    decides  file:src/invoice/round.rs               
  fixed by  commit:cc746808d1              2026-04-12 "invoice: round totals half-even (ADR-007, BUG-12)"
  duplicated by  issue:SUP-88              2026-04-08 "Invoice total differs from customer spreadsheet"
14 steps, 9 link kinds; 248 keys read in 7.9ms
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
10 steps, 7 link kinds; 218 keys read in 5.4ms
```

The research joins the walk where it bears on the decision: C1 supports ADR-007 and answers
the question "rounded once, or line by line?", and C3 answers it the other way, citing the
support ticket.

Once you trust an answer, keep the question; story 9 replays it:

```console
$ ava suite add "why is the invoice a cent off from the customer's spreadsheet?"
kept: 14 records reached; 1 question in .avalanche/suite.jsonl
```

## 6. What was known then

Everything has a date. Ask the same question as it stood the day after the bug was filed:

```console
$ ava why "why is the invoice a cent off from the customer's spreadsheet?" --valid-at 2026-04-10
issue:BUG-12                   2026-04-09 "A cent off on long invoices"
  duplicated by  issue:SUP-88  2026-04-08 "Invoice total differs from customer spreadsheet"
2 steps, 1 link kind; 30 keys read in 730.0µs
```

On 10 April the bug was known and nothing had been decided. `--changed-since` walks the
question both ways and marks what is new (`+`) and what is no longer reached (`-`):

```console
$ ava why "why is the invoice a cent off from the customer's spreadsheet?" --changed-since 2026-04-10
  issue:BUG-12                               2026-04-09 "A cent off on long invoices"
+   led to  decision:ADR-007                 2026-04-11 "Banker's rounding for money amounts"
+     rejects  proposal:P-3                  2026-03-02 "Round halves away from zero"
+     supported by  claim:rp-rounding/C1     2026-04-14 "Rounding every line and adding the results lets rounding er…"
+       answers  question:q-round-once       2026-04-14 "Should an invoice total be rounded once, or line by line?"
+         answered by  claim:rp-rounding/C3  2026-04-14 "People judge a total by whether it matches their own sheet,…"
+           cites  source:rp-rounding/S3     2026-04-14 "Support ticket SUP-88"
+       made by  package:rp-rounding         2026-04-14 "Rounding money on long invoices: once per invoice, or once…"
+         makes  claim:rp-rounding/C2        2026-04-14 "Sheet formulas round each line with halves away from zero,…"
+           cites  source:rp-rounding/S2     2026-04-14 "ROUND function, Microsoft Support"
+       cites  source:rp-rounding/S1         2026-04-14 "IEEE 754-2019, section 4.3.1: roundTiesToEven"
+     decides  file:src/invoice/round.rs               
+   fixed by  commit:cc746808d1              2026-04-12 "invoice: round totals half-even (ADR-007, BUG-12)"
    duplicated by  issue:SUP-88              2026-04-08 "Invoice total differs from customer spreadsheet"
14 steps, 9 link kinds; 295 keys read in 7.5ms
against 2026-04-10: 12 reached since, 0 no longer reached
```

There are two clocks, and both can be asked. `--valid-at`, or `--changed-since` a date, is
when things were true in the world: the decision on 11 April. `--as-of`, or
`--changed-since` a transaction such as `T3`, is what the store had been told; the next
story uses it. What happened and what it was taken to mean are kept apart, so any answer
can be explained by what was known when it was given.

## 7. Retract a wrong link

Dreaming said SUP-88 duplicates BUG-12, and the ticket itself says so. But after ADR-007
shipped, Northwind's sheet still differed by a cent: the ticket was the difference ADR-007
accepts, not the drift it fixed. Take the link back, with the reason:

```console
$ ava retract issue:SUP-88 duplicates issue:BUG-12 --because "Northwind's sheet rounds each line, so it still differs after ADR-007; SUP-88 is not the drift BUG-12 fixed"
T4: retracted issue:SUP-88 duplicates issue:BUG-12, kept as review:1
$ ava why "why is the invoice a cent off from the customer's spreadsheet?" --changed-since T3
  issue:BUG-12                               2026-04-09 "A cent off on long invoices"
    led to  decision:ADR-007                 2026-04-11 "Banker's rounding for money amounts"
      rejects  proposal:P-3                  2026-03-02 "Round halves away from zero"
      supported by  claim:rp-rounding/C1     2026-04-14 "Rounding every line and adding the results lets rounding er…"
        answers  question:q-round-once       2026-04-14 "Should an invoice total be rounded once, or line by line?"
          answered by  claim:rp-rounding/C3  2026-04-14 "People judge a total by whether it matches their own sheet,…"
            cites  source:rp-rounding/S3     2026-04-14 "Support ticket SUP-88"
        made by  package:rp-rounding         2026-04-14 "Rounding money on long invoices: once per invoice, or once…"
          makes  claim:rp-rounding/C2        2026-04-14 "Sheet formulas round each line with halves away from zero,…"
            cites  source:rp-rounding/S2     2026-04-14 "ROUND function, Microsoft Support"
        cites  source:rp-rounding/S1         2026-04-14 "IEEE 754-2019, section 4.3.1: roundTiesToEven"
      decides  file:src/invoice/round.rs               
    fixed by  commit:cc746808d1              2026-04-12 "invoice: round totals half-even (ADR-007, BUG-12)"
13 steps, 8 link kinds; 310 keys read in 5.2ms
- issue:BUG-12 duplicated by issue:SUP-88
against T3: 0 reached since, 1 no longer reached
$ ava log 4
RETRACT issue:SUP-88 duplicates issue:BUG-12  [dream]
review:1 label lit:Northwind's sheet rounds each line, so it still differs after ADR-007; SUP-88 is not the drift BUG-12 fixed  [review]
review:1 retracts lit:issue:SUP-88 duplicates issue:BUG-12  [review]
```

Nothing is deleted. The link is retracted as of T4, so every walk pinned to T3 or earlier
still sees it. The rejection is three facts of its own: the retraction, the review's
reason, and what the review retracts. Reviews are also kept in `.avalanche/reviews.jsonl`,
beside the model's recorded decisions, so they survive a rebuild (story 9), and dreaming
will not write the link again:

```console
$ ava dream
8 mentions to decide, from 1 commit, 2 claims, 1 decision, 1 issue
asked 8 questions in 5 calls (5 replayed, 0 called), $0.0000 billed
  only mentions: claim:rp-rounding/C3 → decision:ADR-007, commit:ab90792f34 → decision:ADR-007, decision:ADR-007 → issue:BUG-3
  undecided (p < 0.8): claim:rp-rounding/C2 challenges proposal:P-3 (0.40)
  already linked: 3
  rejected in review, not written: issue:SUP-88 duplicates issue:BUG-12
nothing new to write
```

## 8. The path and the statistics

Every answer says how it was reached. A step lists each link it read (`+` for a question it
opened, with its priority), the ranked frontier, and a statistics line: links out of and
into the record, how many the budget held back, the budget left, how often earlier walks
passed this way (`path use`), and the index keys read and time taken. `why` ends with the
steps, link kinds and keys of the whole walk. Behind each link is where it came from, when
it became true and which transaction wrote it:

```console
$ ava edges decision:ADR-007 --in
  <-mentions- commit:ab90792f34  [repo; T1; valid from 2026-04-13 10:00Z]
  <-mentions- commit:cc746808d1  [repo; T1; valid from 2026-04-12 10:00Z]
  <-implements- commit:cc746808d1  [dream; T3; valid from 2026-04-12 10:00Z]
  <-mentions- claim:rp-rounding/C1  [percolate; T2; valid from 2026-04-14 00:00Z]
  <-supports- claim:rp-rounding/C1  [dream; T3; valid from 2026-04-14 00:00Z]
  <-mentions- claim:rp-rounding/C3  [percolate; T2; valid from 2026-04-14 00:00Z]
6 links at T4 of T4
```

`dream` marks the model's links; `notes`, `repo` and `percolate` mark what a source said
outright. Every step of every walk, and every `--take` and `--prefer`, is logged, so usage
is something you query too:

```console
$ ava usage
9 sessions, 87 steps
most walked: issue:BUG-12 (9), decision:ADR-007 (7), file:src/invoice/round.rs (7)
link kinds walked: cites 15, answers 12, makes 12, because 7, decides 7, rejects 7, duplicates 6, fixes 6, supports 6
$ ava log
T1  2026-10-24 18:22Z  38 facts
T2  2026-10-24 18:22Z  44 facts
T3  2026-10-24 18:22Z  8 facts
T4  2026-10-24 18:22Z  3 facts
```

The usage log is kept apart from the data's own log: after all those walks the data is
still at T4, so a transaction number always names a state of the data.

## 9. Replay questions after a rebuild

The store is derived: delete it and build it again from the sources, the recorded model
decisions and the reviews.

```console
$ rm .avalanche/store.redb
$ ava ingest
markdown  notes          5 notes    →  16 facts
git       repo           7 commits  →  38 facts
percolate percolate.json 3 claims   →  28 facts
reviews   reviews.jsonl  1 review   →  2 facts
T1: 84 facts in 53.2ms
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
  only mentions: claim:rp-rounding/C3 → decision:ADR-007, commit:ab90792f34 → decision:ADR-007, decision:ADR-007 → issue:BUG-3
  undecided (p < 0.8): claim:rp-rounding/C2 challenges proposal:P-3 (0.40)
  rejected in review, not written: issue:SUP-88 duplicates issue:BUG-12
T2: 7 facts
```

Every model answer was replayed, at no cost, and the review was read back, so SUP-88's link
stayed out. Now replay the question kept in story 5:

```console fails
$ ava suite run
changed  why is the invoice a cent off from the customer's spreadsheet?
  - issue:BUG-12 duplicated by issue:SUP-88
0 of 1 questions reach what they reached when kept
```

The suite walks each kept question again and compares what it reaches with what it reached
when it was kept. Here the difference is the retraction from story 7, so it is expected:
keep the new answer, and the suite passes.

```console
$ ava suite add "why is the invoice a cent off from the customer's spreadsheet?"
kept: 13 records reached; 1 question in .avalanche/suite.jsonl
$ ava suite run
same     why is the invoice a cent off from the customer's spreadsheet?
1 of 1 questions reach what they reached when kept
```

`ava suite run` exits non-zero when any answer changed, so it can gate a new adapter, a new
model version or a change to the walk in CI. The suite lives in `.avalanche/suite.jsonl`;
commit it.

## 10. The same walk for an agent

`ava mcp` serves the session API over MCP, on stdin and stdout, so an agent reasons across
your repository by walking it instead of searching it. Add it to Claude Code:

```console no-test
$ claude mcp add avalanche -- ava -C /path/to/your/folder mcp
```

The agent gets four tools, `search`, `ask`, `step` and `why`, with the same arguments and
the same text back as the commands above: it starts a walk, reads the ranked open
questions at each step, and steers with `take` and `prefer`. The store is opened for each
call and closed after it, so you can use `ava` at the same time. One exchange, as the
agent sees it:

```console
$ printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"ask","arguments":{"question":"why is the invoice a cent off?"}}}' | ava mcp
{"id":1,"jsonrpc":"2.0","result":{"content":[{"text":"session s4 at issue:BUG-12, pinned to T2, budget 20\n  token s4.0.2\n","type":"text"}]}}
$ printf '%s\n' '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"step","arguments":{"token":"s4.0.2","prefer":"duplicates=0"}}}' | ava mcp
{"id":2,"jsonrpc":"2.0","result":{"content":[{"text":"step 1  issue:BUG-12 \"A cent off on long invoices\"\n  + <-because- decision:ADR-007  \"Banker's rounding for money amounts\"  0.90\n  + <-fixes- commit:cc746808d1  \"invoice: round totals half-even (ADR-007, BUG-12)\"  0.72\n  open 2 (opened 2, closed 1); next: decision:ADR-007 0.90, commit:cc746808d1 0.72\n  stats: out 2 in 6; held back 0; budget left 17; path use 3; 33 keys in 480µs\n  token s4.1.2\n","type":"text"}]}}
```

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

`ava dream --since 2026-10-01` limits a dream to recent sources.

## Phase two

From the theory, next: measuring a walk against diffusion and running the fire test on the
edges it used (`ava measure`); letting walks bend the graph, reinforcing used paths and
decaying unused ones; splitting crowded nodes into shorter links (REM-1168). From the spec,
later: immutable snapshot files, per-tenant encryption and crypto-shredding, a Postgres
adapter, query languages over the step core, and distribution.

## How this README is tested

`cargo test --test readme` builds `ava`, copies `examples/` to a fresh folder, and runs
every `console` block above in order, comparing each command's output to the block with
only durations and wall-clock times masked. Blocks marked `no-test` are skipped;
`needs-key` blocks run only when `AVALANCHE_MODEL_KEY` is set, and every other block runs
with no key, so `dream` must replay; commands in `fails` blocks must exit non-zero.
`make.sh` builds the example repository with fixed authors and dates, so commit ids match
on every machine. `cargo test --test install` publishes the built binary as a release
would, in a folder, and runs `install.sh` against it, including a tarball whose checksum
is wrong. If the story and the binary disagree, the build fails.
