# SR-BC result (22 Nov): the replace update reaches a fixed point in two passes, and that point is SR-BR's R

*bill. Registered in REGISTERED-SRBC.md (#91) before scoring. Script `srbc.py`, output `out/srbc.txt`, `out/srbc.json`.
$0, no Jev. SR-BR's R reproduces exactly (.418).*

**Serves.** Sirsh's "define good, let dreaming converge toward it", and his 15:52Z steer: an update for reward-driven
bridge weighting that can reach a fixed point.

## Results

| learn half (652) | successes | in | out | relative weight change |
|---|---|---|---|---|
| unweighted | 302 (.463) | | | |
| T pass 1 (= SR-BR's R) | 307 (.471) | +5 | 0 | 1.000 |
| T pass 2 | 307 | 0 | 0 | .011 |
| T pass 3 | 307 | 0 | 0 | .000 |

- **H-C1 passes.** T reaches a fixed point after two passes: the 307 successes rebuild exactly the weights that make
  them. U, rewarding each question once, stops at the same 307 questions and the same weights.
- **H-C2 passes. Both hops on the test half, T* − unweighted: +.017 [+.007, +.031]** (n 459), 8 questions gained, 0
  lost.

| test half (459), both hops | | − unweighted | gained / lost |
|---|---|---|---|
| unweighted | .401 | | |
| R (one pass) | .418 | +.017 | 8 / 0 |
| **T*, the fixed point** | **.418** | **+.017 [+.007, +.031]** | **8 / 0** |
| U* | .418 | +.017 | 8 / 0 |
| R3 (SR-BR's accumulating arm) | .425 | | 12 / 1 |

- T* − R and U* − R are exactly 0: the five learn questions gained at pass 1 change no test walk.
- T* − R3 is −.007 [−.015, +.002].

## What it means

- **One pass is the operator.** The fixed point is one pass plus a 1% weight adjustment. So SR-BR's R isn't a chosen
  number of passes: it is (to within five rewarded walks) the state the reward converges to.
- **The update settles because almost nothing moves.** Rewards change the walk on only five learn questions, and no
  walk breaks, so the success set has nowhere to go. A fixed point this close to the start is the expected case for a
  structural walk where the reward only adds to doors that already won.
- **R3's extra +.007 is scale, not learning.** R3 is R's weights tripled; the success sets are near-identical. Its
  edge shows that **the size of a reward relative to the base door strength is an unstated constant**: S_w uses
  (1 + r), so the reward unit is fixed at "one pass = one unit of base strength". T fixes the rewards; it doesn't fix
  their scale.

## Predictions against outcomes

- H-C1 in 2–4 passes: **2**. ✓
- T* − R about 0: **exactly 0**. ✓
- T* − unweighted about +.015 to +.02, H-C2 a coin flip: **+.017, passes.** ✓ (the CI was R's, since T* = R on test)
- U* above R by about +.005: **exactly 0**. ✗ I expected U to keep rewards of walks that later broke; none broke.

## Postmortem

- **What went right.** Registering two updates (replace and first-reward) made the fixed-point claim robust: both
  arrive at the same 307 questions by different routes. The $0 loop reproduced SR-BR exactly, so the comparison is
  clean.
- **What I got wrong.** The design asked "does it converge?" but on this walk that was nearly settled before the run:
  SR-BR's own pass-2 output (+5 successes) showed how little moves. The question that stays open is the scale, and I
  only saw it once R3 beat T*.
- **Mechanism.** The walk's step is an argmax over door strength; a reward only raises doors that already won, so it
  changes the argmax for few walks, and none for the worse. Convergence follows from monotonicity in practice, not by
  construction (T could cycle on another corpus).
- **Not tested.** The reward scale. A knob-free scale would set r so the expected rewarded strength equals the base
  strength (normalising by the mean door strength in the pool) rather than by the unit 1. That's the next design, not
  a run.
- **Scope.** MuSiQue train 2-hop, the structural walk, the gold stand-in for a confirmed answer, 459 test questions.
