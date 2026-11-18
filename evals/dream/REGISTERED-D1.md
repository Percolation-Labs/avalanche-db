# Registered: D1, does dreaming that writes hubs close the encoding gap? (james, 18 Nov 2026, before spend)

Sirsh's ruling (M-20261118-200827-fd14): dreaming's job is only ever structural. It adds edges and their
attributes, and possibly hubs. What it learns, it learns from its own walks and expresses as structure. Nothing is
set by hand, there are no per-kind weights, and no text is reworded. The split with bill (M-20261118-200923-3d3e):
bill measures which structural properties predict a cheap Steiner walk (evals/structural). D1 is the operator that
writes structure, and the test of whether it moves bill's measures and the encoding gap (b) on held-out questions.

**Why hubs, and why a rule.** Test gold is almost never dev gold (cards 19/294 passages, PR titles 0/266,
MuSiQue 60/331; `bound1.py`). Neither are the misleading doors (TRANSFER.md). So no list of edges learned on dev
passages can reach test. The operator has to be a rule over structure, applied to the whole graph and learned from
walks.

## The edit

A **hub** is a new key that the dream writes onto a set of passages: one `tagged` literal per member. The walk then
raises it like any shared key, as a door over its unread members. It uses the same D6 lines, the same cap (100) and
no new door kind. Members: 2–20 passages. An edge is a hub with two members. The hub's **label** (its attribute) is
written by the loop from structure: the existing key held by the most members, with ties broken by fewest postings.
It is never the question's words and never gold. A neutral-label arm (`h<n>`) checks how much the label matters.

## The loop

1. **Candidates, question-free and graph-wide.** For every passage d: personalized PageRank from d over the
   passage–key graph (keys under the cap, plus `next`/`near`), then a sweep cut at the least conductance, of size
   2–20. Duplicates are merged. Candidates that equal an existing key's postings are dropped.
2. **Walks.** The training questions are walked on the current graph G_r: dev for every corpus, plus the 265 pool
   cards for cards. These are search-order walks at k=10 with no key ($0), and they are logged.
3. **Reward, from those walks.** A candidate earns credit on a training wave when it would have been raised there
   (it has a read member) and holds unread gold that the wave's opened door did not reach. Gold is used here only as
   the training reward, and only on training questions.
4. **Learned function.** A logistic model over the candidate's structural features: size, conductance, cohesion,
   convergence, local PPR mass, and the postings of its label. Bill's door-level features are added as they land.
   Kind is not a feature. The model is fit on the round's rewards, on 80% of the training questions.
5. **Write.** The top N candidates by the model's score are written to G_{r+1}, where N is 1% of passages per
   round.
6. **Accept.** A round is kept only if the training objective, measured on the 20% of training questions left out
   of the fit, rises. Otherwise the loop stops at G_r. There are at most 4 rounds.

**Convergence argument.** Writes only add structure, from a finite candidate set. Each kept round raises a bounded
objective, so the loop terminates. Per round, the loop reports the objective, the overlap (Jaccard) between the sets
written in successive rounds, and how far the model's coefficients moved. It has converged when the written set
stops changing. A loop that stops on the first round counts as a null, not as convergence.

**Objective.** Both measures, as Sirsh asked: (a) the walk-feasible oracle recall@10 and share@5 (bill,
evals/steiner), and gold door first per wave (bill's (b)), here approximated at $0 by the gold door's rank under
bill's best structural door feature. Jev is not called in training.

## Held out

The test sets (cards 150, PR titles 93, MuSiQue 150) are scored once, on the final graph. No choice in D1 is made on
test.

**Arms.**
- **G0:** the graph as built.
- **G_D1:** the learned loop.
- **Random hubs:** the same number of candidates, drawn at random from the same candidate pool. This is the key
  control: does learning matter, or does adding hubs do the work?
- **Neutral label:** G_D1's hubs, labelled `h<n>`.
- **Oracle hubs:** one hub over each test question's gold. This is the ceiling for legibility and can never ship.
- **Search order:** the floor.

**Read-outs, on test.**
- **$0:** (a) share@5 and the oracle's recall@10, and bill's structural gold-door separation (AUC).
- **Jev:** (b) gold door first and MRR on the waves that have a gold door, plus recall@10 against search (the floor).

**Pass.** G_D1 beats both G0 and random hubs on (b) gold-door-first by at least .05 on at least two of the three
sets. Its recall@10 must be no worse than G0 and no lower than search on any set. If G_D1 doesn't beat random hubs
on the $0 measures, the Jev stage is not run, and that is the result.

## Spend

- The $0 stage comes first: candidates, the loop and the test structure measures.
- Jev only then: test walks on G_D1, random hubs and neutral label, plus the oracle hubs on 20 questions a set.
- Cap: $1.00, probed with one request first. Each arm stops at $0.30.

## Postmortem

Whatever comes back is postmortemed.
