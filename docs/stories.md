# The ten stories

Each story is shown as commands with their real output, run against the billing example. This file is an acceptance test: `cargo test --test readme` runs every `console` block in order (see [testing.md](testing.md)).

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
| 11 | Query with P8QL: find by likeness, follow by connection, and read the plan first | [11](#11-query-with-p8ql) |

## 1. Install one binary

From a clone of this repository, one command builds `ava`, packs it as a release would,
checks it against its checksum and puts it in `~/.local/bin`:

```console no-test
$ ./install.sh --local
installed ava 0.1.1 at /Users/you/.local/bin/ava
```

There is no server, daemon or account: `ava` is one 6 MB binary, and a store is one file
in the folder you run it in. `--local` needs a Rust toolchain and no network. Once
releases are published, the same script downloads the build for your machine (macOS or
Linux, on Apple silicon, Intel or ARM) instead:

```console no-test
$ curl -fsSL https://raw.githubusercontent.com/Percolation-Labs/avalanche-db/main/install.sh | sh
```

```console
$ ava --version
ava 0.1.1
```

## 2. Ingest a Git history

The repository ships an example: a small billing service, its git history, its notes (a
decision record, a proposal, two bugs and a support ticket) and a Percolate research
package about it. The rest of this story uses it, and every output below is what you will
see.

```console
$ cd examples/billing
$ ./make.sh
built repo/: 10 commits
$ ava init
created avalanche.toml and .avalanche/store.redb (tenant "me")
  sources: markdown notes, git repo, percolate percolate.json
  ids: ADR decision, BUG issue, P proposal, SUP issue
$ ava ingest repo
git       repo           10 commits  →  53 facts
T1: 53 facts in 32.9ms
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
T2: 44 facts in 19.9ms
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
  issue:BUG-12          "A cent off on long invoices"                                   6.96
  issue:SUP-88          "Invoice total differs from customer spreadsheet"               6.11
  commit:b9adc7af54     "export: invoices to a spreadsheet"                             3.46
  issue:BUG-3           "Spreadsheet export drops the currency symbol"                  2.17
  claim:rp-rounding/C3  "People judge a total by whether it matches their own sheet,…"  1.36
13 records share a word with the question; the best 5 shown
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
  stats: out 2 in 7; held back 0; budget left 16; path use 0; 32 keys in 161µs
  token s1.1.3
$ ava step s1.1.3
step 2  decision:ADR-007 "Banker's rounding for money amounts"
  + -rejects-> proposal:P-3  "Round halves away from zero"  0.73
  + <-supports- claim:rp-rounding/C1  "Rounding every line and adding the results lets rounding er…"  0.57
  + -decides-> file:src/invoice/round.rs  0.49
    -because-> issue:BUG-12  (visited)
    <-implements- commit:cc746808d1  (already open)
  open 5 (opened 3, closed 1); next: proposal:P-3 0.73, commit:cc746808d1 0.72, claim:rp-rounding/C1 0.57
  stats: out 9 in 6; held back 0; budget left 13; path use 0; 37 keys in 148µs
  token s1.2.3
$ ava step s1.2.3
step 3  proposal:P-3 "Round halves away from zero"
    <-rejects- decision:ADR-007  (visited)
  open 4 (opened 0, closed 1); next: commit:cc746808d1 0.72, claim:rp-rounding/C1 0.57, file:src/invoice/round.rs 0.49
  stats: out 3 in 3; held back 0; budget left 13; path use 0; 15 keys in 142µs
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
  stats: out 0 in 6; held back 0; budget left 13; path use 0; 15 keys in 135µs
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
14 steps, 9 link kinds; 249 keys read in 1.8ms
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
10 steps, 7 link kinds; 219 keys read in 1.0ms
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
2 steps, 1 link kind; 30 keys read in 141.0µs
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
14 steps, 9 link kinds; 296 keys read in 2.8ms
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
13 steps, 8 link kinds; 311 keys read in 2.5ms
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
T1  2026-11-08 13:25Z  53 facts
T2  2026-11-08 13:25Z  44 facts
T3  2026-11-08 13:25Z  8 facts
T4  2026-11-08 13:25Z  3 facts
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
git       repo           10 commits  →  53 facts
percolate percolate.json 3 claims   →  28 facts
reviews   reviews.jsonl  1 review   →  2 facts
T1: 99 facts in 45.6ms
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

The agent gets seven tools: `search`, `ask`, `step` and `why`, and the three P8QL tools of story 11, `p8ql_schema`, `p8ql_explain` and `p8ql_run`. The first four take with the same arguments and
the same text back as the commands above: it starts a walk, reads the ranked open
questions at each step, and steers with `take` and `prefer`. The store is opened for each
call and closed after it, so you can use `ava` at the same time. One exchange, as the
agent sees it:

```console
$ printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"ask","arguments":{"question":"why is the invoice a cent off?"}}}' | ava mcp
{"id":1,"jsonrpc":"2.0","result":{"content":[{"text":"session s4 at issue:BUG-12, pinned to T2, budget 20\n  token s4.0.2\n","type":"text"}]}}
$ printf '%s\n' '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"step","arguments":{"token":"s4.0.2","prefer":"duplicates=0"}}}' | ava mcp
{"id":2,"jsonrpc":"2.0","result":{"content":[{"text":"step 1  issue:BUG-12 \"A cent off on long invoices\"\n  + <-because- decision:ADR-007  \"Banker's rounding for money amounts\"  0.90\n  + <-fixes- commit:cc746808d1  \"invoice: round totals half-even (ADR-007, BUG-12)\"  0.72\n  open 2 (opened 2, closed 1); next: decision:ADR-007 0.90, commit:cc746808d1 0.72\n  stats: out 2 in 6; held back 0; budget left 17; path use 3; 33 keys in 181µs\n  token s4.1.2\n","type":"text"}]}}
```

## 11. Query with P8QL

Some questions have a known shape. "Who works with Bob?" is one likeness step, to find Bob,
and one connection step, to follow "works with". P8QL ([specs/p8ql.md](../specs/p8ql.md))
writes that shape as a SQL-like statement in which every clause is one step. The plan comes
back before anything runs:

```console
$ ava schema
kinds at T2
  claim      3
  commit     10
  decision   1
  file       5
  issue      3
  package    1
  person     3
  proposal   1
  question   1
  source     3
links
  parent       commit -> commit  (9)
  authoredBy   commit -> person  (10)
  touches      commit -> file  (10)
  mentions     most kinds -> most kinds  (14)
  answers      claim|item -> question  (2)
  makes        package|item -> claim|item  (3)
  cites        claim -> source  (3)
  because      decision|card -> issue|card  (1)
  rejects      decision -> proposal  (1)
  decides      decision -> file  (1)
  fixes        commit|pr -> issue  (2)
  implements   commit|pr -> decision|card  (1)
  supports     claim -> decision|card|proposal  (1)
paths
  works_with   <-authoredBy- commit -touches-> file <-touches- commit -authoredBy->
$ ava query --explain "SELECT colleague, count(DISTINCT file) AS shared_files FROM person LIKE 'bob' AS b WALK b -[works_with]- person AS colleague WHERE colleague <> b GROUP BY colleague ORDER BY shared_files DESC"
plan  T2
  1  like     person 'bob'                       names and labels of kind person, fuzzy
  2  hop      <-authoredBy- commit               ospg prefix scan per row  (path works_with)
  3  hop      -touches-> file                    spog prefix scan per row  (path works_with)
  4  hop      <-touches- commit                  ospg prefix scan per row  (path works_with)
  5  hop      -authoredBy-> person               spog prefix scan per row  (path works_with)
  6  filter   colleague <> b
  7  group    colleague, count(distinct file)
  8  order    shared_files desc
```

`works_with` is a named path from `avalanche.toml`, so the plan shows the four hops it
expands to: Bob's commits, the files they touched, the other commits on those files, and
their authors. Each hop is one prefix scan. Run it, and each step reports its rows and the
keys it read:

```console
$ ava query "SELECT colleague, count(DISTINCT file) AS shared_files FROM person LIKE 'bob' AS b WALK b -[works_with]- person AS colleague WHERE colleague <> b GROUP BY colleague ORDER BY shared_files DESC"
plan  T2
  1  like     person 'bob'                       names and labels of kind person, fuzzy
  2  hop      <-authoredBy- commit               ospg prefix scan per row  (path works_with)
  3  hop      -touches-> file                    spog prefix scan per row  (path works_with)
  4  hop      <-touches- commit                  ospg prefix scan per row  (path works_with)
  5  hop      -authoredBy-> person               spog prefix scan per row  (path works_with)
  6  filter   colleague <> b
  7  group    colleague, count(distinct file)
  8  order    shared_files desc
ran
  1  like     'bob' → person:Bob 1.00
  2  hop      <-authoredBy- commit               2 rows, 2 keys
  3  hop      -touches-> file                    2 rows, 10 keys
  4  hop      <-touches- commit                  7 rows, 10 keys
  5  hop      -authoredBy-> person               7 rows, 41 keys
  6  filter   colleague <> b: 5 of 7 kept
  7  group    2 groups
colleague    shared_files
person:Ana   2
person:Chen  1
2 rows; 68 keys read in 228.2µs
```

Likeness never picks a winner silently. One word is matched fuzzily against names and
labels, so `bobby` still finds Bob. A word that many records are equally like pauses the
query and lists the candidates, and you choose one by name:

```console
$ ava query "SELECT p FROM person LIKE 'bobby' AS p"
plan  T2
  1  like     person 'bobby'                     names and labels of kind person, fuzzy
ran
  1  like     'bobby' → person:Bob 0.60
p
person:Bob
1 row; 5 keys read in 97.5µs
$ ava query "SELECT r FROM record LIKE 'invoice' AS r"
plan  T2
  1  like     record 'invoice'                   names and labels of kind record, fuzzy
paused at step 1: 'invoice' is like 11 records about equally; choose one with record = '<name>' and run again
  commit:56bf3a3b56            1.00  "invoice: round each line half-up"
  commit:5b17c0bfa2            1.00  "invoice: compute totals"
  commit:984a051ce9            1.00  "tests: forty-line invoice totals"
  commit:cc746808d1            1.00  "invoice: round totals half-even (ADR-007, BUG-12)"
  commit:cee444c6a5            1.00  "invoice: say why totals round half-even"
```

A record select is a lookup and its links, each with the transaction it was learned in. `AS
OF` pins the whole query to an earlier transaction: ADR-007's rejection of P-3 was learned
when the example dreamed, at T2 since story 9's rebuild, so at T1 it is not there yet:

```console
$ ava query "SELECT p FROM decision = 'ADR-007' AS d WALK d -rejects-> proposal AS p"
plan  T2
  1  lookup   decision:ADR-007                   dict, one key
  2  hop      -rejects-> proposal                spog prefix scan per row
ran
  1  lookup   decision:ADR-007
  2  hop      -rejects-> proposal                1 row, 9 keys
p
proposal:P-3
1 row; 18 keys read in 56.3µs
$ ava query "SELECT p FROM decision = 'ADR-007' AS d WALK d -rejects-> proposal AS p AS OF T1"
plan  T1 of T2
  1  lookup   decision:ADR-007                   dict, one key
  2  hop      -rejects-> proposal                spog prefix scan per row
ran
  1  lookup   decision:ADR-007
  2  hop      -rejects-> proposal                0 rows, 9 keys
p
0 rows; 18 keys read in 38.1µs
```

A hop that cannot exist is refused before anything runs, with the kinds the link does join:

```console fails
$ ava query "SELECT f FROM person = 'Bob' AS b WALK b -touches-> file AS f"
```

A question without a known shape is the native walk. `WALK FROM` starts where likeness is
strongest and runs the walk of story 5, with `FOLLOW` as its policy:

```console
$ ava query "WALK FROM (SELECT r FROM record LIKE 'invoice a cent off from the spreadsheet' AS r) FOLLOW because 1.0, rejects 0.9, implements 0.8, fixes 0.8, supports 0.7 BUDGET 20 RETURN PATH"
plan  T2
  1  like     record 'invoice a cent off from…'  label search (BM25) → the top record
  2  frontier budget 20                          follow because 1, rejects 0.9, implements 0.8, fixes 0.8, supports 0.7; others 0
  3  step…    best open question each step       until the frontier is empty or the budget runs out
ran
  1  like     'invoice a cent off from the spreadsheet' → issue:BUG-12 1.00 (next commit:b9adc7af54 0.50)
  2  walk     session s5, 5 steps
issue:BUG-12                            2026-04-09 "A cent off on long invoices"
  led to  decision:ADR-007              2026-04-11 "Banker's rounding for money amounts"
    rejects  proposal:P-3               2026-03-02 "Round halves away from zero"
    supported by  claim:rp-rounding/C1  2026-04-14 "Rounding every line and adding the results lets rounding er…"
  fixed by  commit:cc746808d1           2026-04-12 "invoice: round totals half-even (ADR-007, BUG-12)"
5 steps, 4 link kinds; 138 keys read in 294.0µs
```

