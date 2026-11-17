# Avalanche DB

A lightweight database of a different kind. It has no SQL or Cypher interface, and needs none,
because it is built on **durable walks**.

## Likeness, then connection

There are only two ways to know a thing: by what it is like, and by what it is connected to
([There Are Only Two Ways to Know a Thing](https://drafts4life.substack.com/p/there-are-only-two-ways-to-know-a)).
A durable walk alternates between the two:

1. **Likeness.** A `LIKE` step is a key lookup, a fuzzy key lookup or a semantic lookup. It
   returns a wave of nodes.
2. **Connection.** Each of those nodes has typed links. The agent chooses which to follow,
   and following them returns more keys.
3. Those keys start the next likeness wave, and so on, until the open questions run out.

The alternation of likeness waves and connection waves is the heartbeat of the whole system,
like a heart's systole and diastole. Every question is answered by that rhythm, which is why
there is no graph-pattern language or SQL to learn: a query is a walk, likeness followed by
connection. The walk is durable because every step is kept. It can be paused and resumed
from a token, read back as the plan it followed, and replayed later to see what changed.

Avalanche DB builds the graph from the places your work already lives (git history, notes,
research), and the graph never forgets its own history. Today it is one binary and one file
on disk, and it sits beside your repository and replaces nothing.

## Install

```console no-test
$ curl -fsSL https://raw.githubusercontent.com/Percolation-Labs/avalanche-db/main/install.sh | sh
```

From a clone, `./install.sh --local` builds it instead (it needs a Rust toolchain).

## Your own repository, from Claude

In the repository you want to ask about, register the store with Claude Code:

```console no-test
$ cd ~/code/your-repo
$ midb mcp install
claude mcp add --scope user avalanche -- /Users/you/.local/bin/midb -C /Users/you/code/your-repo mcp
Added stdio MCP server avalanche with command: /Users/you/.local/bin/midb -C /Users/you/code/your-repo mcp to user config
```

`--scope project` writes the registration to the repository's `.mcp.json` instead. Without `claude` on the PATH,
the command prints the JSON config for any other MCP client.

Then open Claude in the repository and ask it to ingest and to answer. Claude calls three tools:
1. `ingest_repo`, once, to read every text, markdown and code file and every commit message into the store.
2. `walk`, with your question, which returns the documents that answer it.
3. `read_document`, on the documents it wants to read.

Here is what Claude gets back when that is run on this repository itself, at `2e71f77`. Ingesting takes half a
second:

```console no-test
ingest_repo
added a documents source for . to avalanche.toml
documents .              700 passages →  62504 facts

walk  "why does a re-ingest retract facts instead of rewriting the store?"
walk: 10 documents, 5 from search then one door a wave; decider jev (jev-1.13.0), kappa K6
   1  src/construct/review.rs#2      search                 "src/construct/review.rs"
   2  src/construct/documents.rs#12  search                 "src/construct/documents.rs"
   …
   6  commit/7636e8d34e              term:ingest compares   "commit 7636e8d: ingest --documents PATH, and a documents re…"
   …
jev: 26 requests (0 replayed, 26 sent), 149910 input tokens, $0.0063
```

**How the walk finds documents.**
- Search finds the first five.
- The walk then follows doors: words, names and ids the documents share, a file's neighbouring parts, and passages
  with close wording.
- Jev picks one door a wave. Here it went from the ingest code to the commit that made re-ingesting a diff, which
  search didn't rank.
- It needs a key, set with `midb key set` or `AVALANCHE_MODEL_KEY`. Without one, the walk ranks doors by search's
  order and says so.
- Every answer is kept in `.avalanche/decisions.jsonl`, so asking the same question again costs nothing.
- The same walk runs from the shell: `midb ingest --documents .`, then `midb walk "…" --budget 10`.

**What it was measured to do** ([evals/e2e/RESULT.md](evals/e2e/RESULT.md)):
- The test ran on 150 questions over this team's own repository, each asking what was done about a board card and why.
- At 10 documents, the walk returned 48% of the commits that did the work. Search returned 29% (+.19, 95% CI
  [+.12, +.25]).
- On a public multi-hop benchmark, MuSiQue, the walk returned 60% of the supporting paragraphs and search 46%.
- It is one repository and one kind of question. At 5 documents the walk is no better than search.

## A cent off

The repository ships an example: a small billing service with its git history, a few notes
and a Percolate research package. Build it and read it all in:

```console
$ cd examples/billing
$ ./make.sh
built repo/: 10 commits
$ midb init
created avalanche.toml and .avalanche/store.redb (tenant "me")
  sources: markdown notes, git repo, percolate percolate.json
  ids: ADR decision, BUG issue, P proposal, SUP issue
$ midb ingest
markdown  notes          5 notes    →  16 facts
git       repo           10 commits  →  53 facts
percolate percolate.json 3 claims   →  28 facts
T1: 97 facts in 33.3ms
```

Ingesting records only what the sources say outright. `midb dream` asks a model what each
mention means: does this commit fix that bug, does this claim support that decision. The
example's model answers are recorded, so it needs no key and bills nothing:

```console
$ midb dream
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
$ midb why "why is the invoice a cent off from the customer's spreadsheet?" --prefer duplicates=0,cites=0
issue:BUG-12                                                  2026-04-09 "A cent off on long invoices"
  led to (dreamed, not stated)  decision:ADR-007              2026-04-11 "Banker's rounding for money amounts"
    rejects (dreamed, not stated)  proposal:P-3               2026-03-02 "Round halves away from zero"
    supported by (dreamed, not stated)  claim:rp-rounding/C1  2026-04-14 "Rounding every line and adding the results lets rounding er…"
      answers  question:q-round-once                          2026-04-14 "Should an invoice total be rounded once, or line by line?"
        answered by  claim:rp-rounding/C3                     2026-04-14 "People judge a total by whether it matches their own sheet,…"
      made by  package:rp-rounding                            2026-04-14 "Rounding money on long invoices: once per invoice, or once…"
        makes  claim:rp-rounding/C2                           2026-04-14 "Sheet formulas round each line with halves away from zero,…"
    decides (dreamed, not stated)  file:src/invoice/round.rs
  fixed by (dreamed, not stated)  commit:cc746808d1           2026-04-12 "invoice: round totals half-even (ADR-007, BUG-12)"
10 steps, 7 link kinds; 203 keys read in 583.0µs
```

Search finds the bug report and stops there, because the reason shares no words with the
question. The walk goes on from the bug to the decision made because of it, ADR-007 (round
the total once, halves to even), and to the proposal ADR-007 turned down, P-3 (halves away
from zero, which is what a spreadsheet does). The cent is by design.

Every link the dream decided is marked `(dreamed, not stated)`, so a reader can tell what a
model judged from what a source says. Read without that mark, a wrong judgement passes for
fact.

## Read more

- [docs/stories.md](docs/stories.md): the ten stories in full, including walking one step
  at a time, asking what the graph knew then, retracting a link, replaying questions, and
  serving the walk to an agent over MCP.
- [docs/waves.md](docs/waves.md): five SQL and Cypher queries rewritten as likeness and
  connection waves, and what the exercise reveals.
- [docs/architecture.md](docs/architecture.md): the three layers (construct, infer, walk)
  and how to point Avalanche at your own history.
- [docs/testing.md](docs/testing.md): how this README and the stories run as tests.
- [specs/engine.md](specs/engine.md): the design principles (Rust and redb, one file,
  append-only, bitemporal quads, typed predicates, durable sessions, tenant isolation) and
  which of them are built.
- [specs/p8ql.md](specs/p8ql.md): P8QL, a durable walk written down: each clause is one
  likeness or connection step, and the plan runs in the order it is written.
- [specs/plan.md](specs/plan.md): the approved plans, what we measured, and what comes next.
