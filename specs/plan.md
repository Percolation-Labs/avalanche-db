# Avalanche DB: the plan

The approved plans for REM-1172, newest first, and what comes next. The lab write-ups and scripts cited here (`lab/…`) are kept in the private `avalanche-lab` repository. The README is the short story; [docs/stories.md](../docs/stories.md) is the full set of stories.

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

**Stage C, measured (30 Oct; `lab/STAGE-C.md`, both parts registered first).** Redundancy carries the imperfect judge
to the evidence. It accepts 63% of routes to a required item, and 131 of 133 items had at least one accepted route, as
independent errors predict up to 8 routes. Two items had 22 and 42 routes and none accepted: the judge turned down
their whole theme (Kappa Proposition 5). The other 8 unread items had 2 to 16 accepted routes each, and the walk never
travelled one, because it ranks routes one by one in a queue of 400 to 1,500. Letting routes vote (convergence order)
did not help: cov@100 −0.005 [−0.026, +0.015]. In the product's own queue, votes rank unread evidence above other
unread documents at only AUC 0.596. The routes that converge are on topic too, so votes count the same topical
judgement again. Redundancy that helps has to be of a kind the judge does not read as topic. The next candidates are
sitting and time, and Kappa's factored predictor.

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


## Phase two

From the theory, next: measuring a walk against diffusion and running the fire test on the
edges it used (`ava measure`); letting walks bend the graph, reinforcing used paths and
decaying unused ones; splitting crowded nodes into shorter links (REM-1168). From the spec,
later: immutable snapshot files, per-tenant encryption and crypto-shredding, a Postgres
adapter, query languages over the step core, and distribution.

