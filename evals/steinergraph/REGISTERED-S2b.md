# S2b and S3, registered: the oracle tree weighted by the walk's step cost, cut, then repaired without the oracle

*20 Nov 2026, james. Follows RESULT-S2: counted in hops, T\* is the gold itself. Here every link costs what it costs
the walk to take it. $0, no Jev, no Claude data, nothing fitted, no chosen constants. bill's four review points on
e60b0f2 are built in and marked [b1]–[b4].*

## The tree

- **Step cost** (the definition agreed with bill, shared with S1′ and S4′). p(u→v) is the walk's one-step
  transition from u to v: the column of L1's `step()` from a unit mass on u. A link's cost is −log p(u→v) in nats,
  with no smoothing. It is directed, and a link that can't be taken costs ∞. There are two references:
  - **Primary, graph only:** UNI with no question terms, so the h weights are 1. This is the structure that drift and
    repair change.
  - **The walk actually used:** L2's LC θ with the question's search scores F [b2].
- **T\*:** the cheapest directed tree from the seed root to every gold passage. It is built by Takahashi–Matsuyama:
  starting from the seeds, repeatedly add the cheapest path from the tree to the nearest gold passage not yet in it,
  with ties broken by id. Its **cost** is the sum of its link costs, which is −log of the probability that the walk
  takes exactly those steps. TM is the registered tree, chosen before any run. TM gives an upper bound, and bill's
  exact edge-weighted Dreyfus–Wagner (`s1.py`) is reported beside it once it exists, along with any gap.
- **Row 0 of every result:** the hop-counted tree, S2's measure. It is the finding that motivates this change.

## S2b: drift

- **Cuts, cases and control:** the same as S2 (REGISTERED-S2.md).
- **Control fallback:** if no key of the same family misses gold, take the nearest-width key of any family that
  misses gold.
- **Measured:** T\*'s cost in nats, built, cut, restored and control, plus the walk's recall and the cut passage's
  rank, as in S2.
- **Directional gate:** on at least 3 of 4 cases in each of cards and MuSiQue, the cut raises T\*'s cost by more than
  the control cut does. Restoring the key must give back the built values exactly.
- **Aggregate bar:** over all singly joined test pairs, T\*'s added cost, cut minus control, is above 0 with a
  bootstrap 95% interval above 0 on both sets. Recall, cut minus control, is reported against S2's bar.

## S3: repair from walks alone

As REGISTERED-S2.md, with these additions:
- **[b1] Count control:** add the same number of links, taken by co-read count alone. If coherence doesn't beat
  counting, the learning step is counting, and that will be the reported finding.
- **[b3] Trivial co-reads:** a cut pair whose two ends are both seeds of the same walk is co-read without any walk
  finding it. Recovered is reported with and without those pairs.
- **[b4] Collateral:** on the graph as built, the paired difference in recall over all questions (repaired minus
  built) must have a 95% interval that doesn't lie wholly below 0.
- **Scored in tree terms too:** each repair's effect on T\*'s cost for the cut questions. A real repair brings the
  cost back toward the built value.
- **Timing:** one greedy round is timed on one set before the loop, and reported. If a round takes over 10 minutes, I
  will post before going on, not run it. This is a budget line, not a parameter of the method.
- **S3 runs only if S2b passes its gate.** Repairing drift the tree can't see would measure nothing.
