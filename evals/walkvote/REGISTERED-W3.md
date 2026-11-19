# W3: the vote compared only against doors of similar width, fused with P; variant chosen on dev

*19 Nov 2026, bill. Registered before any run. $0. Stage 1 (live Jev, ≤$1) only on a pass.*

W1 (summed vote) rewarded width. W2 (vote per target) rewarded narrowness. V1 measured the vote within similar widths,
which is the comparison that works (.73–.83). W3 makes that comparison the statistic.

**Within-width vote:** doors are put in width classes by ⌊log2 width⌋ (unread targets). A door's X is the share of the
batch's doors in its class whose summed vote is lower (ties count half). A door alone in its class gets .5.

**Variants:** X ∈ {summed vote (W1's), per-target vote (W2's), within-width vote}, each fused with P by reciprocal rank
(60), uniform θ (−1, 0). Ties go by P.

**Selection on dev:** for each graph, the variant with the highest gold-first on the dev waves (the first door of
recorded dev waves with a gold door, V1's dev rows). A variant is not eligible if its read-weighted (b) on dev falls
below P's by more than .02. If none is eligible, P stands and that set counts as no gain. Test is then scored once.

**Test arms:**
- P;
- P ⊕ chosen variant;
- P ⊕ the chosen variant on shuffled links;
- P ⊕ within-width vote, whatever dev chose (reported);
- vote alone, within-width (reported).

**Pass:**
- On test, the chosen variant beats P on gold-first by at least .03 on at least two sets.
- No set falls by more than .02 on gold-first or on read-weighted (b).
- Where it gains, it beats its shuffled arm by at least .02.

**Postmortem:** every result gets one. This is the third fusion variant, so the result says so, and a pass is read
with that in mind.
