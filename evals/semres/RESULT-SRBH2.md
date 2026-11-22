# SR-BH2 result (22 Nov): with one spare read the gap mostly closes, but "order" isn't shown by the registered rule

*james. Registered in REGISTERED-SRBH2.md (#94), with H-O amended at bill's review before the run. Scripts `srbh.py
--spare` and `srbh2_did.py`. Outputs `out/srbh2-fresh.txt`, `out/srbh2-did.txt`, `out/srbh-fresh-spare.json`.
**Spend $0.038** (cap $0.10).*

**Serves.** The check bill asked for before SR-BH's result goes to Sirsh: is the cheap walk's +.080 on chains about
reading the chain in order, or about choosing better passages?

## Results

The same 200 chains as SR-BH, with H + 1 reads for both walks. Paired bootstrap 95% CI.

| all hops | H reads (SR-BH) | H + 1 reads |
|---|---|---|
| cheap | .395 | .550 |
| pass | .315 | .525 |
| cheap − pass | +.080 [+.025, +.130] | **+.025 [−.030, +.085]** |

- **pass(H+1) − pass(H): +.210 [+.155, +.270].** The spare read helps the pass walk a lot.
- cheap(H+1) − cheap(H): +.155 [+.105, +.205].
- **The DiD, [(cheap − pass) at H+1] − [(cheap − pass) at H], is −.055 [−.105, +.000].**
- **H-O fails, at the boundary.** The first condition holds; the DiD's upper bound is at 0, not below it. By the rule
  bill and I fixed before the run, order is **not shown**.
- **Input with the spare read:** cheap 37.8k, pass 46.8k, ratio **.807**.
- **Per unit of input** (bill's readout, `out/srbh2-per-char.txt`, $0), all hops per 10k input chars:
  - cheap at H: .135
  - pass at H: .084
  - **cheap at H + 1: .146**
  - pass at H + 1: .112

  The spare read pays for itself: cheap at H + 1 is the best per character as well as the best overall.
- **SR-BH's cheap wins:** with the spare read, the pass walk completes 4 of the 10 where it had skipped a hop, and 3 of
  the 9 where it had left the chain.

## What it means

- **With one spare read, the cheap walk ties Jev's full step and still uses 19% less input.** That's the claim that
  holds under either reading. The cheap walk's case on chains is input, as on 2-hop, plus an accuracy edge under an
  exact budget.
- **Order explains part of the gap, not provably all of it.** The gap shrinks by .055, most of SR-BH's .080, and the
  CI just reaches 0. Skips recover more often than chain-leaves (4 of 10 against 3 of 9), but these counts are too small
  to separate the two.
- **The spare read is worth more than either step rule.** +.155 to +.210 on all hops, against +.080 between the rules.
  On chains, and with H given as an oracle (the walk was told it could have one more read), reading one past the hop
  count matters more than which step is used, and it is the best per character. So stopping is the next lever, and it
  has to be measured without the oracle. That points
  the next test at stopping, not at the step.

## Predictions against outcomes

- **pass(H+1) − pass(H) about +.06:** **+.21.** ✗, far larger. I counted only the recoverable skips, but a spare read
  also rescues walks whose entry or a mid-chain step was off by one.
- **cheap(H+1) − cheap(H) about +.03:** **+.155.** ✗, for the same reason.
- **cheap − pass at H+1 about +.04:** **+.025.** ✓ roughly.
- **H-O passes:** **fails at the boundary.** ✗
- **About 6 of 10 skips and 2 of 9 leaves recover:** **4 and 3.** ✗ on both; the difference between them is smaller than
  predicted.

## Postmortem

- **What went right.** bill's insistence on a DiD with a CI stopped a point-estimate reading ("the gap shrank from .080
  to .025, so it was order") that the data don't support at the registered bar. Holding the Sirsh note until this was
  in avoided sending "order beats choice".
- **What I got wrong.** I predicted the spare read's value from the 19 divergence questions alone. Most of its value is
  elsewhere: off-by-one walks that neither SR-BH breakdown counted. The size of that effect is the result I'd have
  missed.
- **Mechanism.** One extra read recovers a missed hop for either walk, because both walks' options include every unread
  passage, and the missing hop shares entities with what has been read. The cheap walk misses less under an exact
  budget, so it gains less from the spare read.
- **Not tested.**
  - A stopping rule (how many reads without the oracle).
  - Whether a second spare read keeps paying.
  - A fresh draw for the H+1 tie.

**Scope.** SR-BH's 200 chains (the same questions), with H + 1 given as an oracle. Production is Sirsh's.
