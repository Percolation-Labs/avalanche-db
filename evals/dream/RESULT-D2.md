# D2: learned edges predict co-relevance well and connect no test gold, because the graph already holds the structure

*18 Nov 2026, james. Registered first (REGISTERED-D2.md, #35). $0, 52 s. No Jev: the gate failed.*

## Result (`d2/d2.txt`)

**The predictor learns.** Positive pairs are both-gold for one training question:
- p8: 601 positives among 47,291 pairs, from cards dev, PR titles dev and the 265 pool cards.
- MuSiQue: 71 among 13,376 pairs.

On the held-back 20% of training questions, the learned score has AUC **.87** on p8 and **.83** on MuSiQue. The
unlearned common-neighbour score has .75 and .65. Kind was not a feature.

**What it writes reaches no test gold.**

| test set | gold pairs | not one door apart in G0 | of those, in the 2-step candidate pool | connected by the top 1% / 5% (learned, common-neighbour, random) |
|---|---|---|---|---|
| cards | 330 | 28 | .32 | 0 / 0, every arm |
| PR titles | 331 | 57 | .56 | 0 / 0, every arm |
| MuSiQue | 378 | 127 | .02 | 0 / 0, every arm |

A written edge led from a read passage to unread gold on at most 1 test wave in 160, in any arm.

**Gate:** failed. Learned edges don't beat the controls on (a) or the test ceiling. The Jev stage was not run.

## Why

- **The targets are few and scattered.** There are 28–127 unlinked test gold pairs among about 1.3M candidate pairs
  on p8 (0.7M on MuSiQue). Writing 1–5% of passages' worth of edges is a few thousand edges.
- **The model learned what is already linked.** Its largest weights are shared keys (+1.18) and a direct link (+.68).
  Most predicted co-relevant pairs are already one door apart (71% of candidates are). It learned the graph's
  existing structure, which is real and transfers. There is little left for it to add.
- **The unlinked gold pairs are mostly not near each other.** On MuSiQue only 2% are within two steps, so no local
  link predictor can propose them. Their link is the question (a bridge entity named in a hop), which the graph
  can't know ahead of the question.

## Read with bill's structural result (evals/structural, #36)

Bill finds that PPR mass from the read set marks the gold door. With width matched, AUC is .80/.73/.83 against
shuffled .54/.50/.52. On PR titles it beats Jev's P (.724 against .688). Together with D1 and D2:

- **The graph already holds the structure that tells the right door apart.** Gold pairs are 66–92% one door apart,
  and the gold door carries more PPR mass than a gold-free door of similar width.
- **Question-free writes can't add the missing part.** D1's hubs are too thin and D2's edges miss. What is unlinked
  is linked only through the question.
- **So the encoding gap is not missing structure.** It is structure the decider doesn't see. Jev reads door text.
  PPR mass is a property of the graph and the read set that the text doesn't carry.

## Postmortem

- **The registered measure was right and cheap.** (a) on unlinked test gold pairs said no in 52 s. I should have
  computed the candidate pool's coverage of the targets before fitting anything. 2% on MuSiQue settles it alone.
- **The convergence question has an honest answer here.** A loop that adds only what the predictor scores highly
  converges trivially: it re-learns existing links and writes nothing that matters. Convergence of a dreaming loop is
  only worth showing for an operator that moves the objective, and neither D1 nor D2 does.
- **What this suggests (not registered):** dreaming's information has to reach the decider. Two routes follow, and
  each needs its own registration and Sirsh's view on whether it is inside the rule:
  - the walk uses structure (PPR from the read set) next to Jev's P;
  - the loop writes structure-derived attributes onto doors and edges that the walk can show.
  Both are $0 to test first on recorded batches: P is page-independent, and bill's rows carry P and PPR per door.

## Files

- `d2/linkpred.py`: candidates, features, the model and every arm;
- `d2/d2.txt`: the output.
