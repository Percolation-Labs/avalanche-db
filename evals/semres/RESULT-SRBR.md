# SR-BR: dreaming that rewards walked bridges improves new questions' walks, by a little

*22 Nov 2026, bill. Registered in `REGISTERED-SRBR.md` (#87, from `DESIGN-BRIDGE-REWARD.md`), reviewed by james before
scoring. $0, no Jev. Script `srbr.py`, outputs `out/srbr.txt` and `out/srbr.json`.*

**Versions.** bge-small-en-v1.5. MuSiQue train 2-hop answerable from james's corpus and graph (#75). The learn half is 652
questions and the test half 459 (SR-BX's 304 excluded), split by sha256(id) parity.

**The method.** The walk is the cosine entry, then the strongest weighted door. Weights are r(passage, key), raised by
1/|S_k| at both ends of every shared key on a learn-half walk whose pair was the gold pair (the feedback stand-in). The
test half is walked with those weights. Nothing about the test questions is used.

## Result (test half, both hops)

| weights from the learn half | both hops | − unweighted |
|---|---|---|
| none (cosdoor) | .401 | |
| **R: rewarded walks** | **.418** | **+.017 [+.007, +.031]** |
| F: failed walks (control) | .401 | |
| RND: count-matched random walked events (control) | .407 | |
| B: all learn-half gold bridges (ceiling, gold) | .431 | |
| R2, R3: R re-walked 2 and 3 passes | .420, .425 | |

- **Primary: R − unweighted = +.017 [+.007, +.031]. H-R passes.** Weights learned from one half's successful walks
  improve walks on the other half's questions.
- **It isn't memorising answers.** In the 453 test questions that share no gold pair with a learn question, the gain is
  +.018 [+.007, +.031]. Only 6 share one, and there it's 0.
- **The outcome signal matters.** R − RND is **+.011 [+.002, +.022]**, so boosting the walked memberships of successful
  walks beats boosting walked memberships at random. R − F is +.017: boosting failed walks' memberships does nothing.
- **There's room above.** B − R is +.013 [+.004, +.024]. Rewarding all bridges (gold) does better than rewarding only
  those the walk found.
- **More passes don't help reliably.** R3 − R is +.007 [−.002, +.017]. Learn-half success goes .463 → .477 → .480.

**The top weights are place-name hubs.** "quebec city", "puerto rico", "santa rosa", "ghana" and "clinton county" lead
R, and R3 triples them (4 → 12). The update re-rewards the same successful walks on every pass, so weights grow linearly
and don't converge. The relative change per pass halves (1.01 → .51) only because the total grows. **That's a flaw in the
update rule, not a convergence result.**

**Predictions against outcomes.**
- R − unweighted +.02 to +.04: +.017, just below the range. H-R was called a coin flip, and it passed.
- R − RND positive and small: right (+.011).
- B − R positive: right (+.013).
- R3 − R about 0: right (+.007, n.s.), but for a worse reason than I gave: the weights don't converge.

## What it means for "define good, let dreaming converge toward it"

- **A reward-driven reweighting of bridges transfers to new questions**, which is the RL loop Sirsh described, in its
  simplest form. It's small (+.017 on .401, about 4% relative) and specific to success (+.011 over random).
- **The sign is what matters, not the size.** MuSiQue reuses single-hop questions, which inflates transfer (65% of test
  questions touch a learn bridge), and the walk is a structural cosdoor with no Jev. In the Jev pipeline the weight
  would act only on tie-breaks and the |S| = 0 fallback, so the gain there is untested.
- **To converge, the update has to stop re-rewarding what it already rewards.** Two knob-free options:
  - reward only walks that *changed* outcome since the last pass;
  - cap r at the reward a membership would get from one pass (tenure, not repetition).
  Either makes "converge" mean something. Untested.
- **Hubs are the risk.** The top weights are broad place names that bridge many questions. They help here, but on a
  corpus where a hub is a lure, they would steer walks wrong. The diminishing 1/|S_k| doesn't stop a hub that wins
  across many different questions.

## Postmortem

- **What went right.** A power check before the design (65% reuse) and a leakage check before registration (6 shared
  pairs). james's RND control isolated the outcome signal, and with F alone the reading would have been ambiguous. The
  whole loop cost $0.
- **What I got wrong.** The multi-pass arm re-rewards identical walks, so it measures accumulation, not convergence. I
  predicted 'about 0' for the right number and the wrong reason. A convergence readout needs an update that can reach a
  fixed point, and I should have checked that in the design rather than in the result.
- **Scope.** MuSiQue train 2-hop, a structural walk, a gold feedback stand-in on the learn half, one update rule, 459
  test questions.
