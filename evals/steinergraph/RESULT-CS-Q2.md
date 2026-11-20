# CS Q2 result: the bar is met by the letter, not in substance. One real win, one loss and two ties

*20 Nov 2026, bill. Registered in REGISTERED-CS-Q2.md, with amendment 1 made before the rerun. Measure: james's `cs.py`
(1a56609). Output: `out/csq2.{txt,json}`; run 1 is in `out/csq2-run1.*`. $0, no Jev, no Claude data, nothing fitted,
about 1 min of CPU.*

## Result

These are the four walk-miss dev cases. Each cell is the mean log rank of the gold beyond the seeds among the passages
every seed reaches (21–47k); lower is better, and 0 means rank 1.

| case | ref | am (all seed pairs) | aM (best pair) | walk mass P | L2 node coherence |
|---|---|---|---|---|---|
| mq 2hop 126306 | graph-only | 2.77 (rank 16) | **0.00 (rank 1)** | 1.10 (rank 3) | 1.79 |
| | walk-as-used | 1.39 (rank 4) | **0.00 (rank 1)** | 4.42 (rank 83) | 1.79 |
| mq 2hop 130508 | graph-only | **7.38** | 7.98 | 7.87 | 9.35 |
| | walk-as-used | 7.50 | 7.81 | **5.69** | 9.35 |
| cards REM-1001 (6 gold) | graph-only | 4.22 | **4.036** | 4.041 | 4.24 |
| | walk-as-used | 3.90 | 3.85 | **3.64** | 4.24 |
| cards REM-103 (2 gold) | graph-only | **1.59** | 2.61 | 2.65 | 2.33 |
| | walk-as-used | **1.24** | 3.43 | 3.67 | 2.33 |

**The registered gate.** Under graph-only, aM beats P in 3 of 4 cases, so the letter is met. But two of those three wins
are within .04 nats of P, which are ties: 4.036 against 4.041, and 2.61 against 2.65. Substantively, that is one real
win (126306), one loss (130508) and two ties. am, the diverse-seeds arm, beats P in 2 of 4. Under walk-as-used, every
CS arm wins 2 of 4.

**I'm not calling this a pass.** By the registration's own rule, if only aM passes, the claim is single-pair convergence.
Here even that rests on one case.

## What it shows

1. **The null does its job on hubs.** Under graph-only, walk mass correlates with degree at ρ = .86–.96. The CS arms sit
   at −.07 to +.50, and aM at −.03 to +.34. Small-world reach and hubs are discounted, as the definition asks.
2. **Surprise sometimes finds what mass buries, and that is the interesting part.**
   - On mq 126306 under walk-as-used, the walk ranks the gold 83rd, and the best pair's convergence ranks it 1st.
   - On cards REM-103, walk-as-used, P puts one gold at 768 and am puts it at 6.
   - These are exactly the cases where the walk misses.
3. **It can also bury what mass finds.** On mq 130508 under walk-as-used, P ranks the gold about 300th, and every CS arm
   ranks it about 1,800th–2,700th. The second-hop gold there is reached through one seed, so no pair converges on it.
   That is the predicted MuSiQue failure: "diverse seeds converging" says nothing about a chain that only one seed
   starts.
4. **The A_ij twin discount barely changes the max arm.** aM and xM differ by under .1 nats everywhere. Within one
   question, A only shifts each pair by a constant, so it can't reorder a pair's own top. It belongs to Q1, which
   compares θ and graphs, not here.

## Postmortem

- **Predicted:**
  - "am ≤ P on MuSiQue gold": half right. It is worse on 130508 and better than P under walk-as-used on 126306.
  - "aM may do better": true on 126306.
  - "CS beats P on T\* but not gold on cards": untestable, because T\*'s non-seed passages are the gold in three of the
    four cases.
  - "FAIL on gold for am": yes.
- **Run 1 was wasted, and a $0 look would have caught it.**
  - AUC over every reached passage saturates near 1 for any score that knows "near the seeds". I should have checked
    one case's AUC for the plain walk before registering.
  - Amendment 1 moved to absolute rank. It also added walk-miss cases, but by the rule's file order, 3 of the 4 miss
    cases are the run-1 cases. That's legitimate (cards' gold is never all in the top 5, since REM-1001 has 6), but it
    means the miss set is not new questions.
- **"Lower in 3 of 4" with no tie margin is a bar that ties can clear.** A strictly-lower count needs a declared
  resolution. Next time, register a tie band from the data's own scale, such as rank differences under one position,
  rather than leave it to judgement afterwards.
- **Four cases are too few to separate a 1-in-4 effect from noise,** and that was the brief: directional only. The
  directional reading is "sometimes strikingly right where the walk misses, sometimes strikingly wrong, no consistent
  edge".

## Next

- I wouldn't move CS into Q3 on this. Q2 doesn't show that high-surprise convergence lines up with gold in general.
- What would settle it cheaply: a registered dev run over the walk-miss questions (all of dev, $0, a few minutes). The
  measure is the paired log-rank difference aM − P and am − P, with a bootstrap interval. That gives Sirsh's "emergence
  across seeds" an honest number.
- Whether to run it is Sirsh's call, together with james's Q1.
