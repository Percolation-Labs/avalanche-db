# S2c and S3, registered: cut the tree's own link

*20 Nov 2026, james. Follows RESULT-S2b. There the cut gold–gold link was never on the seed-rooted tree. $0, no Jev, no
Claude data, nothing fitted. The tree, the step cost (UNI with no F as primary; LC with F beside it), row 0 and
the walk are as in REGISTERED-S2b.md.*

## The cut

1. For each test question, compute T\* on the graph as built.
2. Among T\*'s edges u → v where v is a gold passage that isn't a seed, take the cheapest one. Ties go to the
   smaller v id.
3. The **cut key** is the shared key of u and v (2–100 holders) with the largest weight kw at UNI, that is the
   narrowest. Ties are broken by key text. It is dropped from v.
4. If u and v share no key (the edge is only a Beside or Near door), the question is skipped and counted.

The edge may survive through other shared keys, as it would when an extractor misses one entity.

## The control

Drop from v the key whose width is nearest the cut key's, among v's keys not shared with any passage that has an
edge into v on T\*. Ties are broken by key text.

## Directional gate (on the walk, since T\*'s cost rises by construction)

On the first 4 qualifying test questions by qid in each of cards and MuSiQue, the cut must raise v's rank in the
walk (L1's UNI walk with search F, as in S2) by more than the control raises it. That must hold on at least 3 of 4
cases per set. Restoring the key must give back the built values exactly. PR titles is reported only.

## Aggregate bar

Over all qualifying test questions, compute log(rank after the cut / rank as built), minus the same for the control.
The paired bootstrap 95% interval must be above 0 on both sets. Recall@5, cut minus control, is reported. T\*'s added
cost, cut and control, is reported too.

## S3

S3 runs on these cuts, unchanged from REGISTERED-S2b.md, only if this gate passes.

## S3 amendment (before any S3 run)

Three points that S2c's cuts force, fixed before S3 runs:

1. **Candidates are co-read pairs with no Beside door between them, not "unlinked" pairs.** An S2c cut often leaves u
   and v joined through wider keys. A repair is a Beside link, the graph's narrowest direct door. So a pair already
   joined by keys can still be repaired, and one already joined by Beside can't.
2. **A candidate's gain is scored by rerunning only the walks whose R holds either end.** Other walks would change
   only by second-order mass. The strength matrix stays fixed at the drifted graph, so an added link can't raise its
   own observed coherence. Only the walks it moves can.
3. **Recovered means a repair link was added on the cut pair (u, v).** Its effect is scored as v's rank, recall, T\*'s
   cost and T\*'s dearest hop (bill: the tree fails at its dearest hop). These are compared across drifted, repaired,
   the random, hub and count controls, and built. Before any ranking, S3 reports how many cut pairs are candidates at
   all. bill's S4 found that walks rarely read both ends of a tree edge.
