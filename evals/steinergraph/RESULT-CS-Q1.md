# CS Q1 result: does surprise coherence stop the gaming?

**FAIL.** CS doesn't stop the gaming. On cards one arm, am (twin discount, mean over seed pairs), is indifferent to
L3's move. On MuSiQue every arm, am included, rewards S3's 40 links, which won back no recall. Together with bill's
Q2 (RESULT-CS-Q2.md, #55), no arm yet both resists the gaming and points at gold. Q3 (CS as the repair reward) doesn't
run.

*20 Nov 2026, james. Registration: REGISTERED-CS.md (1a56609). $0, no Jev, no Claude data. Outputs: out/csq1-a.{txt,json},
out/csq1-b.{txt,json,log}.*

## (a) Cards dev, L2's θ: β = 0 against L3's fitted β

**PASS by the registered rule, but only for one arm.** That arm is the twin discount with the mean over seed pairs.

Loose coherence reproduces L3: 1561 → 1835. Differences are B − A over 100 dev walks, with 95% bootstrap intervals:

| Arm | Change |
|---|---|
| Loose (L2) | +274 [+161, +394] |
| xm: degree null, mean over pairs | +.74 [+.56, +.92] |
| xM: degree null, best pair | +1.36 [+1.21, +1.50] |
| **am: degree null and twin discount, mean over pairs** | **−.009 [−.172, +.160]** |
| aM: degree null and twin discount, best pair | +.57 [+.45, +.71] |
| Recall | −.061 [−.123, .000] |

L3's β changed the top 5 on 98 of 100 walks. Every top-5 passage was reached by every seed's walk, so none was dropped from CS.

**What it shows:**
- **The degree null alone is gamed.** Both "x" arms rose with intervals above 0, as predicted. L3's β keeps the top 5
  among adjacent cards. Those cards converge from several seeds, and degree-matched random seeds don't converge there.
  So by a hub-only null they look surprising. Discounting hubs isn't enough, because the gaming came from homogeneity,
  not hubs.
- **The twin discount A_ij removes it, but only when every pair must agree.** am is flat. aM (best pair) still rises.
  With the best pair, one twin pair inside the cluster is enough, so the discount for the other pairs doesn't apply.
- **Flat, not falling.** In the four printed cases, am rose on three. So CS-am stops rewarding L3's move on average,
  but it doesn't penalise it. A reward that is flat on a recall loss of .061 doesn't prevent the move either; it is
  just indifferent to it.

## (b) MuSiQue: S3's drifted graph against it plus S3's 40 accepted links

**FAIL.** Every arm rose, with intervals above 0. Differences are B − A over 251 walks (dev and test with a CS score):

| Arm | Change |
|---|---|
| Loose (L2) | +16.5 [+9.8, +23.9] |
| xm | +.079 [+.055, +.105] |
| xM | +.076 [+.049, +.104] |
| **am** | **+.048 [+.030, +.067]** |
| aM | +.031 [+.012, +.051] |
| Recall | .000 [.000, .000] |

The links changed the top 5 on 46 of 251 walks. No top-5 passage was dropped by the reach rule.

**What it shows:**
- **The links manufacture convergence, and CS counts it.** S3 accepts a link between two passages that several
  walks read together. That adds a path between the seeds behind them, so their walks meet more, and they meet more
  than degree-matched seeds would. The null can't tell a convergence the graph found from one the repair loop wrote
  in.
- **The twin discount only shrinks it.** am rose about 60% as much as xm. A_ij grows for the pairs a link joins,
  but the new convergence lands on the passages the link touches, not spread over the whole graph. So dividing by
  overall agreement doesn't cancel it.
- **Why (a) passed and (b) failed.** In (a) the twins were already twins: adjacent cards agree everywhere, and A_ij
  sees it. In (b) the agreement is new and local, and A_ij is a global average.

## Postmortem

- *Predicted:* (a) the "x" arms rise and the "a" arms fall. (b) the "x" arms rise and the "a" arms rise less, sign
  unsure. Both "x" predictions held. In (a), am was flat, not falling; aM rose because the best pair escapes the
  discount, which I didn't predict. In (b), the "a" arms rose less, as predicted, and the sign is positive.
- *Could a $0 look have stopped it?* Yes, for (b). A link added between two read passages raises p_i·p_j exactly at
  those passages, and A_ij averages over all of them. That's arithmetic, and I could have seen it before running. I
  wrote "unsure of the sign" instead of working it out.
- *What the null is missing.* Sirsh's definition says convergence must be unlikely *for this graph*. A repair loop
  that edits the graph and then scores itself against the edited graph's null always gets credit for its own edits.
  So an honest reward for repair needs the null fixed from the graph before the edit: score the repaired walks
  against q from the drifted graph. That's a definition to register, not to tune after the fact.
- *Constants:* none chosen here. The degree classes, reach rule and arms are as registered.
- *Next, if Sirsh wants one:* there are two $0 runs, each minutes long.
  - Rerun (b) with q fixed from the drifted graph. Pass if am is flat or falls.
  - Run bill's dev-scale Q2 (paired log-rank against walk mass, walk-miss questions).
  - CS is a candidate reward only if both pass.

## Joint reading with Q2 (bill)

| Arm | Q1a cards (gaming) | Q1b MuSiQue (gaming) | Q2 gold rank against walk mass |
|---|---|---|---|
| xm | gamed | gamed | — (same ranking as am within a question) |
| am | **flat** | gamed | 2 of 4 |
| aM | gamed | gamed | 3 of 4, two ties within .04 nats |

So within a question the null removes hub bias: walk mass has ρ ≈ .9 with degree, CS 0–.5. Surprise sometimes finds
gold the walk misses: mq 126306 goes from rank 83 to 1, and cards REM-103 from 768 to 6. But it buries single-seed
chains, and across θ and graphs it still rewards homogeneity it can't see.
