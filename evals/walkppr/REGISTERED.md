# Registered: W1, does the walk choose better when it sees the structure? (james, 18 Nov 2026, before running)

D1 and D2 (evals/dream) find nothing for question-free writes to add. Bill (evals/structural, #36) finds that the
graph already marks the gold door: PPR mass from the read set, summed over a door's targets, has width-matched AUC
.80/.73/.83. On PR titles it beats Jev's P (.724 against .688). So the gap may be that the decider doesn't see that
structure. W1 asks, on recorded batches only and at $0, whether combining it with P puts the gold door first more
often.

**Data:** bill's held-out test rows, `evals/structural/out/ft-{cards,prs,mq}.jsonl.gz`. They give, per door per
wave: P, Jev's rank, width, gold, and real and shuffled PPR. P is page-independent (#847), so re-ranking a recorded
batch is valid for the first door of that wave. Later waves would differ in a real walk; that is not measured here.

**Arms.** One fixed combination, with no tuning: reciprocal rank fusion, score = 1/(60 + rank_P) +
1/(60 + rank_PPR), ties broken by P. The constant 60 is the standard one, not fitted. Arms:
- **P:** today.
- **P+PPR**.
- **Controls:**
  - **P+shuffled PPR:** the same widths over random links, which is the width effect;
  - **P+width:** rank by width;
  - **PPR alone;**
  - **search order.**

**Read-outs,** per set, on waves with a gold door:
- gold door first;
- MRR of the best gold door;
- the expected gold from the first door as a share of the best gold door's (bill's read-weighted (b)).

**Pass.** P+PPR beats P on gold-first by at least .05 on at least two of the three sets, and beats P+shuffled PPR
by at least .03 on those same sets (structure beyond width). It must not drop gold-first by more than .03 on any set.

**Scope.** This tests the walk using structure, not dreaming writing it. Whether that is inside Sirsh's rule is his
call. A fixed fusion is one combination, not a per-kind weight. A pass here leads to a registered full-walk stage
with Jev (≤$1), not to a default change.

**Postmortem:** every result gets one.
