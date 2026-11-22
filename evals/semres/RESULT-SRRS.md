# SR-RS result (22 Nov): a unit-free success-rate reward learns the learn half and transfers less than SR-BC's

*bill. Registered in REGISTERED-SRRS.md (#93) after james's review, before scoring. Script `srrs.py`, output
`out/srrs.txt`, `out/srrs.json`. $0, no Jev. T* reproduces SR-BC's .418.*

**Serves.** Sirsh's "define good, measure it, let dreaming converge toward it", with no magic constants: replace SR-BC's
reward unit with a measured rate.

## Results

| arm | learn success at the end | iteration | test both hops | − unweighted | gained / lost |
|---|---|---|---|---|---|
| unweighted | .463 | | .401 | | |
| T* (SR-BC, unit reward) | .471 | fixed point, 2 passes | **.418** | +.017 | 8 / 0 |
| **RATE** (successes and failures) | .51–.52 | **cycle of period 2** | .412 | +.011 [+.000, +.022] | 6 / 1 |
| RATE-W (successes only) | .472 | fixed point, 2 passes | .412 | +.011 [+.002, +.022] | 5 / 0 |

- **H-RS fails. RATE − T*: −.007 [−.017, +.002].** Against T*, RATE gains 1 test walk and loses 4.
- RATE − RATE-W: +.000 [−.007, +.007]. Failures as evidence add nothing on new questions.
- RATE-W − T*: −.007 [−.015, +.000].
- **RATE cycles.** Its learn success alternates between .521 and .506 (passes 2–5): cutting a failed door redirects
  some walks, which then fail elsewhere, which restores the door. The test arm is the mean of the two states.

## What it means

- **Failures teach the learn half, not new questions.** RATE lifts learn success from .463 to about .51, six times
  T*'s gain there, but its test gain is smaller. A door cut because one question's walk failed through it is a fact
  about that question; on a new question the same door is as likely to be the bridge. This is SR-BR's reuse finding
  again (6 of 459 test questions share a learn pair), now on the penalty side.
- **Consistent with the unit mattering, not significant.** RATE-W is T* with a measured scale instead of a unit, and
  it transfers less (+.011 against +.017; RATE-W − T* −.007 [−.015, +.000]). In S_w, T*'s factor (1 + r) applies at both ends, so a typical
  rewarded door gets about 2× from each (T*'s total reward 1,154 over about 1,156 memberships, so mean r ≈ 1), against
  about 1.39× here. On this data, larger boosts to successful
  doors lean toward transferring better, so the unit may not be arbitrary in effect, even if it is in form.
- **For dreaming.** The reward that converges and transfers best here is still SR-BC's T*: successes only, one pass.
  Its scale is a convention I can now name rather than defend: one success = one unit of base door strength. The
  rate form removes the unit, and its point estimate is about a third of the gain lower (a lean, not a measurement).

## Predictions against outcomes

- RATE − T* about 0 to +.01, H-RS unlikely: **−.007, fails.** ✓ direction roughly, sign wrong.
- RATE loses 1–4 test walks T* kept: **4.** ✓
- RATE-W ≈ T*: **−.007**, borderline below. ✗ I thought the scale wouldn't matter.
- RATE reaches a fixed point in 2–3 passes, a cycle wouldn't surprise: **cycle of period 2.** Half right.

## Postmortem

- **What went right.** james's review fixed a real error before it could run: my prior pulled every unwalked door to
  1.08, which would have mixed a corpus-wide boost into the comparison. RATE-W separated "failures as evidence" from
  "a different scale", and the two answers differ.
- **What I got wrong.** I argued in the design that the rate form "has no unit" as if that settled it. The test
  leans toward the unit's size mattering to transfer, so removing it may be a cost, not a cleanup. The design should have registered a
  check on scale alone first (RATE-W against T*), which is the cheaper question.
- **Mechanism.** Penalties are question-specific and don't transfer; boosts transfer weakly, more so when larger.
  Larger boosts were not tested beyond SR-BR's R3 (+.007 over R, n.s.).
- **Not tested.** A scale fixed by a held-out criterion (choose the boost that maximises learn-half success under
  cross-validation). That is a fitted constant, which Sirsh's rule allows only if it's registered and held out.
- **Scope.** MuSiQue train 2-hop, the structural walk, the gold stand-in, 459 test questions.
