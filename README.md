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

## Approved 30 Oct: what we learned, what no longer holds, the plan and the ten stories

Sirsh, M-20261030-094748-d36e and M-20261030-094844-403a. Approved 30 Oct 10:09Z (M-20261030-100911-3ad3), with
stage C reframed from a better judge to redundancy that carries an imperfect one. The 26 Oct proposal follows as the
record; where this one changes it, it says so.

**What changed since 26 Oct.** Four results, and none of them is about the engine.

- *The walk pays only where search buries the evidence* (REM-1244, percolate's walk spec §14). Walk minus search at
  100 reads is +15.6 [+5.2, +27.5] at 1M, +1.1 [−2.5, +4.9] at 500K and +1.2 [−3.1, +6.3] at 100K. Pooled by
  burial, it is +50.0 on evidence at search ranks 51–200 (n = 9) and about zero above rank 50. The share of buried
  questions grows with the history: 1 of 50 at 100K, 7 of 39 at 1M.
- *Judging, not the graph, is the bottleneck* (bill's lab, `bill/walklab` `meta/lab/README.md`). On the same graph
  and budget, a perfect lead judge covers .983 of required items by read 100, the product's recorded Jev verdicts
  .811 and search alone .787. Most of the loss is irrelevant leads accepted: new evidence meets other leads at 1 to
  80, Jev ranks them at AUC 0.84, and so 5% of travels find anything new. Copies are 4% of travels.
- *Jev judges topic, not answer.* Its P on a lead is .515 when the evidence line is in front of it and .508 when it
  is hidden. It responds to how on-topic the shown lines are.
- *Memory shown as "found" works as a topic signal* (the Kappa paper, ld-8473a1528273, §10, and bill's case
  1M:28). An exact memory lowers branching, as Proposition 6 says, but Jev then demotes new items on the same theme
  (P .62 → .29), which is Propositions 3 and 5 observed. The logarithmic memory (Conjecture 1; `kappa_k` = 3 ln reads)
  lowered NEW-versus-copy AUC by 0.12–0.15, three times the noise floor, on 4 walks.

DecisionRAG (arXiv 2610.35868) reports the other half from outside: a language model judging a node's children
*together*, in one pass, so their scores are comparable, navigating broad to narrow with no retriever. It beats
dense retrieval with an 8B reranker by 13.8 R@1 on MultiDoc2Dial and 17.4 Hit@1 on Natural Questions.

**Postmortems: what no longer holds, and why.**

| 26 Oct claim | Verdict | Why |
|---|---|---|
| Each narrow question gets "the evidence, which search alone does not reach" | theory too broad | true only where search buries it below rank 50. On a small history search's top 100 holds most of it (95.8% at 100K). The stories were chosen for being *why* questions, not for being buried, and none was checked |
| A gold-blind temperature says how close the walk is (stage 1) | theory wrong, already reported 26 Oct | Good-Turing needs random draws. A steered walk's sightings scored AUC 0.52–0.60. Stage 1 proved convergence and not the estimator, so story 4 had no mechanism |
| "Jev decides relevance; the graph decides order" (25 Oct) | half wrong | the order half holds (fewest-targets-first, near competing on count). The relevance half is the failure: relevance is *topic*, and at 1 to 80 a topical yes travels mostly waste. This is Kappa's Proposition 3 (relevance is the wrong admission criterion) applied to leads, not memory |
| Learning means the graph keeps its walks and the next walk is warmer (stage 4) | untested, and now at risk | a kept walk shown to the decider is a memory, and memory shown as found demotes new evidence on the same theme. Write-back has to be scoped by event and question class (Kappa Proposition 7 and §9) or it repeats 1M:28 |
| Stage 2's reference is reach.py | superseded | reach.py stays the engine-free baseline. But the reference that is the product is now bill's engine, identical to the product's P walk on 83 of 83 recorded runs |
| Story 8's "every mention" is a walk story | wrong problem | it is breadth, and 25 Oct already set breadth aside as its own mode. The topical judgement that fails narrow questions is the right one for breadth |

**The hard problem, restated.** A narrow question in a long history usually has its answer in search's first fifty,
and then nothing beats search. The hard case is evidence search buries. There, the graph already holds a path a
perfect judge finds in 100 reads 98% of the time, and the decision model loses it by saying yes to anything on
topic. The judge is imperfect by design, as a person is (Sirsh, M-20261030-100911-3ad3), and the design's answer
is not a better judge but redundancy in the graph: several routes to the same evidence, echoes and restatements, so
a judge that turns down one route still meets another. So the hard problem is how much redundancy it takes for an
imperfect judge at a 1-to-80 base rate to reach the answer anyway, and where the graph lacks it. Two questions
follow: what redundancy buys, measured, and a stop signal that says how much is left without knowing the answer.

**The plan.** Each stage is proven before the next. Every stage runs in bill's lab as the harness: its fixture
(288 BEAM questions, DEV and HELD-OUT), its oracle (items, not pieces), its scorecard and its Jev cache. Avalanche
is the second engine, and lessons go both ways (M-20261030-095133-3077 proposes the split to bill).

| Stage | What is shown | Passes when | Cost |
|---|---|---|---|
| A. Avalanche is a lab engine | the lab's fixture walked by Avalanche | the same reads, in the same order, with the same clues as bill's engine on the 83 recorded product runs, given their recorded verdicts. A negative control must diverge | $0 |
| B. A stop signal that works | Kappa §8: the branching ratio (accepted leads per read) and the open frontier as a gold-blind estimate of the items left | it ranks true remaining items better than reads-so-far on DEV, reported once on HELD-OUT, from recorded verdicts | $0 |
| C. Redundancy carries an imperfect judge | for each required item, the routes the graph offers to it (distinct leads whose targets cover it, and restatements by bill's calibrated RESTATES), against whether the walk reached it under Jev's recorded verdicts. Then the lever: add restatement routes to the graph and walk again under the *same* judge | the chance an item is reached rises with its route count as the judge's per-route acceptance predicts (an item with r routes missed about (1 − a)^r of the time), and added routes raise coverage at 100 reads with no change to the judge, on HELD-OUT once. Items with one route are named as the graph's gaps. A cheap judgement change (joint choice across a request's options, as DecisionRAG does) runs only as a side arm, never the main line. Any class built from BEAM's unlabelled material is audited blind first: bill's E1 found 31% of on-topic unlabelled neighbours answer the question and 24% of labelled evidence does not | $0 on recorded verdicts; under $1 of Jev for the walks after routes are added |
| D. Real history, buried questions | p8-subsystems' history (commits, cards, postmortems) and Percolate claims, with REM-1196's known-answer why-questions and more | questions *selected by burial* (best search rank of the answer beyond 50, measured and reported). The walk reads the answer where search does not, scored by items: a decision restated in a commit, a card and a postmortem is one item. Stage B's signal agrees with the truth | Jev only for C's winner |
| E. Learning, scoped | stage D's questions asked again after walks write back event-scoped summaries (Kappa §9) | fewer reads for the same items, a shorter context for the decision model, and no new evidence demoted. A topic-scoped summary is the control that should fail | small |

Stage A replaces 26 Oct's stage 2 as the gate. Stages B and C are new. D and E are 26 Oct's stages 3 and 4,
re-scoped.

**Stage A, built and passed (30 Oct).** `ava lab import` reads the lab's 33 conversation graphs into a store, one
tenant per conversation: each document labelled in the graph's order, its terms as `tagged` values (so the documents
holding a term are that value's incoming edges, and the lab's `post` is never stored; import checks it is the
inverse), and the lab's `beside` and `near` lists as one-way links. That is 35,212 documents and 841,720 facts in 7
seconds. `src/walk/lab.rs` is the lab's engine rule for rule, asking the store for every term, posting and list.
`ava lab serve` runs it over JSON lines and hands each round's judgement back to the caller, and
`lab/avalanche_engine.py` gives it the lab engine's `run`, so walklab's deciders, scorecard and Jev cache drive it
unchanged. `lab/fidelity.py` replays the 79 recorded live 1M P runs with their recorded verdicts. Avalanche matches the
recording and the lab's engine on all 79: the same reads in the same order, the same `via`, clues, P, travels and stop.
It needed no fix: the lab's collation and float4 tie-breaks were ported up front. The control, one travelled verdict
pushed under the gate, diverges at read 14. Avalanche takes 8.1 s for the 79 walks against the lab engine's 3.9 s, the
difference being one process round trip per judgement.

**Stage B, passed directionally (30 Oct; `lab/STAGE-B.md`, registered before any result).** The signal is m, the
accepted leads per read. It says whether required items are still unread at AUC 0.837 on HELD-OUT, where the wave
alone says it at 0.541. Stopping at the first wave with m < 1, the theory's threshold untuned, leaves 8 of 63 items
unread, where a fixed stop at the same reads leaves 13 (DEV: 11 of 70 against 27). It is 40 questions, because only
those have recorded verdicts. Its failure is a theory gap. When the judge accepts nothing, m is 0 at once, while
search reads go on finding items: the walk is a branching process with immigration, and such a process does not die
out. The stop has to price search's own yield as well, and that is the next registered test.

**Ten stories, rewritten.** Each states a hard problem honestly, including when search is enough.

| # | The hard problem | What proves it | Stage |
|---|---|---|---|
| 1 | Install it, ask a buried question, and get an answer search can't give | one real question whose answer is past search's rank 50, measured and printed. The walk reads it within 100 reads | D |
| 2 | Know when not to walk | for a question whose answer is in search's first ten, Avalanche says so and stops. A walk would cost reads and find nothing more | D |
| 3 | An answer three hops away | question to bug to decision to commit, each hop printed with the link and the judgement that took it | D |
| 4 | Nothing there, or stopped looking? | stage B's signal: a question with no answer in the history dies out (branching below 1, empty frontier); one stopped by budget is flagged as still growing | B, D |
| 5 | The judge says no, and the answer arrives anyway | a buried question where the judge turns down the first route to the answer, and the walk reaches it by a second: an echo or a restatement. The routes, and which one carried it, are printed | C |
| 6 | What was known then | as 26 Oct: the relay question as of 26 Oct 06:00Z and now, different answers, both commits on the path | built (story 6) |
| 7 | A wrong link, taken back | as 26 Oct: the retraction changes the path and the stop signal, and stays on record | built (story 7) |
| 8 | Find every mention: breadth, not a walk | "every change to the release train in October" in broad mode: on-topic is the right judgement here, with a count checked by hand | own mode |
| 9 | The second time is cheaper, without forgetting what's new | stage E: fewer reads on repeat questions, and a new event on an old theme still found | E |
| 10 | An agent asks the big question by asking small ones | as 26 Oct, over MCP: each narrow walk returns evidence, the stop signal and leads, and the agent's context is the yes set | D |

The 26 Oct examples (hooksPath, the release catalog, severity) stay as candidates for stories 1 and 3. Each is
kept only if stage D measures its answer as buried.

## Approved 26 Oct: the target, the plan, and ten hard stories (the record)

Sirsh, M-20261026-060505 and M-20261026-062436. Approved 26 Oct 13:33Z (M-20261026-133343-0d35); stage 2 is built
and passes (below).

**The target.** A proof of concept that Avalanche is a query layer with a decision model in it, not a reasoner. The
caller, an agent or a person, breaks a large question into narrow ones, and each narrow question gets three things:

- the evidence, which search alone does not reach;
- a coverage estimate, so the caller can tell "nothing there" from "stopped looking";
- leads: the specific terms and links near what was found, for the next question.

**The plan, four stages, each proven before the next.**

| Stage | What is shown | Data | Passes when |
|---|---|---|---|
| 1 | The walk converges in the limit, and a gold-blind temperature says how close it is | p8-subsystems `meta/spikes/2026-10-25-reachability`: synthetic worlds where every piece of evidence and every path to it is known by construction | all evidence read in the limit whenever the three conditions hold, and stalls where one is broken; the temperature ranks the true share left |
| 2 | Avalanche walks those worlds the same way | the same worlds, imported (facts.jsonl, vectors.npy, ids.json, questions.jsonl) | the same reads in the same order as the reference walk, with the decider replayed. Any gap is an implementation fault and is fixed before stage 3 |
| 3 | Real questions with known answers | p8-subsystems history: 7,736 commits on main, the board's cards, and postmortems whose `fixes:` name the cards. Percolate claims through the second adapter | for at least 20 "why did we…" questions, the walk reads the known evidence by 50 reads where search does not, and the coverage estimate agrees with the truth |
| 4 | Learning: repeat walks get warmer faster, and the line between Avalanche and the LLM moves | stage 3's questions, asked again after the graph has kept its own walks | the same evidence in fewer reads, a shorter context handed to the LLM, or a smaller model reaching the same answer |

Every failure along the way is given one of three verdicts before anything is tuned: the data is wrong, the theory
is wrong, or the implementation is wrong.

**Stage 2, built and passed (26 Oct).** `ava world import <dir>` reads a reach.py world into a store beside it:
items in creation order, terms and sittings as values (`tagged`, `inSitting`), vectors in a table of their own, and
each item's three nearest in meaning computed once at import (`near`). `src/walk/world.rs` answers the seven
questions reach.py's walk asks of a store from the indexes, and `ava world walk` runs stage 1's exploring walk
(`src/walk/explore.rs`) with each clue's P replayed from the reference's recording and its draws from a coin both
engines share (SplitMix64 seeded by SHA-256). On four 5,000-document worlds (13,000 items, 113,000 facts each),
600 walks in five modes, accepted only to a third of travel exploring with near misses first, read the same items
in the same order as the reference, with the same frontier and specific frontier after every read: 600 of 600.
Avalanche walks a world's 30 questions in about 5 seconds; the reference takes 30 to 50. Getting there needed two
fixes in the reference, both to orders Python happened to produce rather than orders the walk chose: a clue's
targets were read in the order the facts were written (and, for nearest meaning, in numpy's partition order), and
an exploring draw listed open clues in the order they were opened. Both are now creation order and name order in
both engines, and stage 1's numbers hold under them (instruction questions 38% read accepted only, 65% to 71% with
near misses first, by draw). A negative control shows the comparison can fail: one recorded P moved under the bar
moves the walk from read 188 on.

**Ten stories, each a hard retrieval problem solved on real data.** The examples below are real questions from this
team's own history, and the answers are known. Stage 3 checks that each one is as hard as it looks: search must
miss what the walk finds.

| # | The hard problem | The real example | What proves it |
|---|---|---|---|
| 1 | Install, point it at a repository, and in a minute get an answer search can't give | "Why does every push from here pass `-c core.hooksPath=dev/githooks`?" Answer: REM-1015 (c78b719e). Claude Code's worktree creation rewrites the shared hooksPath as an absolute path | the walk reads the gate's commit and the card; search's top 10 hold neither |
| 2 | An answer three hops away: question to bug to decision to commit | "Why does a release apply its own catalog?" Answer: postmortem 2026-10-18 "A release was five steps" to REM-873 and REM-947 to their commits | each hop is printed with the link it travelled and its P |
| 3 | An answer that shares no words with the question | "Why did the board stop sorting by severity?" Answer: postmortem 2026-10-20, "severity never meant priority", and REM-1092 | the decision shares no word with the question, and it is still read |
| 4 | Nothing there, or stopped looking? | A question whose answer is not in the history, asked beside one where the walk stopped early | coverage near 1 with nothing found for the first; low coverage, flagged, for the second |
| 5 | A vague question becomes a good one | "What went wrong with the board on 23 Oct?" returns leads (REM-1147, waiter, relay); the question asked again with a lead is answered | the second walk reads the evidence the first could only point at |
| 6 | What was known then | "Does the relay forward a message sent to all?" asked as of 26 Oct 06:00Z, and again now | as of 06:00Z the answer is yes, by 40264585, which made the relay spin on old broadcasts. Now it is no, by 72913ee8. Both commits are on the path |
| 7 | A wrong link, taken back | a dreamed link that sends story 2's walk the wrong way; retract it | the walk's path and its coverage both change, and the retraction is on record |
| 8 | Find every mention, with a count you can trust | "every change to the release train in October" | all mentions in time order from the graph, with a coverage estimate checked against a hand count |
| 9 | The second time is cheaper | the 20 stage-3 questions asked again after the graph has kept its walks | fewer reads for the same evidence, measured per question; a rebuild replays them as a regression test |
| 10 | An agent asks the big question by asking small ones | "How did releases change in October?" over MCP: the agent breaks it into narrow questions, and each walk returns its evidence, coverage and leads | the agent's answer cites every walk, and the LLM's context is the yes set, not the history |

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

From a clone of this repository, one command builds `ava`, packs it as a release would,
checks it against its checksum and puts it in `~/.local/bin`:

```console no-test
$ ./install.sh --local
installed ava 0.1.0 at /Users/you/.local/bin/ava
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
on every machine. `cargo test --test install` runs `install.sh --local`, and publishes the built binary as a
release would, in a folder, and runs `install.sh` against it, including a tarball whose
checksum is wrong. If the story and the binary disagree, the build fails.
