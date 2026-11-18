# Result: the likeness door (REGISTERED-likeness.md), 18 Nov 2026

**The registered test FAILS on L1, the floor, on PR titles: like − search −.015 [−.051, +.020] against a bar of −.01.**
Every other bar passes. The door narrows the PR-title gap to search from −.042 to −.015, but doesn't close it. So
`like` stays off by default.

Test: k=10, the `match` head (chosen on dev), stores e2e-p8i (cards, PR titles B) and e2e-mq3. Baselines are the
recorded test logs. Recall@10, paired bootstrap 95%. Spend: dev $0.836, test $0.703.

| Set (orthogonal share) | search | today's walk | likeness | oracle max(walk, search) | L1 like − search | L2 like − walk | L3 like − coin | losses to search, walk → like |
|---|---|---|---|---|---|---|---|---|
| cards (.51) | .291 | .477 | .508 | .524 | +.217 PASS | +.031 [−.006, +.070] PASS | +.124 PASS | 13 → 12 |
| PR titles (.30) | .514 | .472 | .498 | .539 | **−.015 [−.051, +.020] FAIL** | +.026 [+.004, +.052] (reported) | +.005 [−.017, +.029] PASS | 16 → 11 |
| MuSiQue (.36) | .464 | .598 | .602 | .621 | +.138 PASS | +.004 [−.007, +.017] PASS | +.071 PASS | 10 → 7 |

In see-also terms, the walk's gain over search tracks each set's orthogonal share: +.217 at .51 (cards), +.138 at .36
(MuSiQue), −.015 at .30 (PR titles). The likeness door costs nothing where links pay; cards and MuSiQue are slightly
up. It recovers 62% of the PR-title loss. Across the sets it removes 9 of the 39 losses to search.

## Postmortem: why PR titles still sit below search

The door's membership was never the problem: opened in round 1, it reproduces search exactly (tests/doors.rs). The
problem is Jev's ranking. On all 11 PR-title questions the walk still loses, the likeness door was never opened. In
each, a two-word term door ("term:census beam", "term:sweep moves") scored above it by .03–.18; the median gap was
.11, against .06 on the other questions. Jev opens the door in round 1 on 17/93 PR-title questions, against 7/150 on
cards and MuSiQue, so it does discriminate in the right direction. But on the losing questions its P doesn't separate
a narrow term door with no gold from search's continuation. This is the same calibration fault bill found for merge
doors (P .53 while a gold commit sits on 75% of their pages). Jev's P is the one thing the floor now rests on, and on
PR titles it is the bottleneck.

What this rules out: a fixed tie-break or bonus toward the likeness door. That would be a per-kind prior, which
Sirsh's 10:33 steer excludes. What is left, generically: how the door is described (one dev choice among three heads
was made; the leads are D6's), and what Jev is told in the task.
