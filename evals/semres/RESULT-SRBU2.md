# SR-BU2 result (22 Nov): at about equal spend, the cheap walk ties Jev's full step on answer arrival, but needs one more passage to do it

*james. Registered in REGISTERED-SRBU2.md (#98) before the run; bill said yes (17:16Z). Scripts `srbh.py --nocap
--spare` and `srbu2.py`. Outputs `out/srbu2-fresh.txt`, `out/srbu2.txt`. **Spend $0.015** (cap $0.10). Stage 0 was
skipped, as in SR-BU.*

**Serves.** Sirsh's 17:07Z goal (A-last: the answer passage is in what the walk returns), and the cheap walk's case,
which on his measure is cost.

| arm | A-last | returned set | input chars | A-last per 10k chars |
|---|---|---|---|---|
| cheap, no ceiling, H | .800 | 3.5 | 25.3k | **.316** |
| **cheap, no ceiling, H + 1** | **.835** | 4.5 | 32.7k | .256 |
| **pass, H** | **.835** | 3.5 | 37.3k | .224 |
| pass, H + 1 | .890 | 4.5 | 46.8k | .190 |

- **Primary, at equal spend (not equal outcome for the reader):** cheap(H + 1) − pass(H) is **+.000 [−.055, +.060]**.
  **H-U3 fails, narrowly**: the lower bound is −.055 against the −.05 margin. The point estimate is a tie, at 88% of
  pass's input.
- **The read factor alone:** pass(H + 1) − pass(H) is +.055 [+.025, +.090].
- **At equal reads:** cheap(H + 1) − pass(H + 1) is **−.055 [−.110, −.005]**. Given the same number of passages, Jev's
  full step reaches the answer passage more often, significantly.

## What it means

- **On Sirsh's measure, Jev's full step is the better step rule per passage returned.** The cheap walk matches it only
  by returning one more passage, for 12% less input. SR-AC found a noise passage costs a reader about −.07. So for the
  reader, pass at H is the better set: the same arrival with fewer passages.
- **The cheap walk's remaining case is input, not answers.** Per character it reaches the answer passage most often
  (.316 at H), but it returns the answer about .035–.055 less often than pass at the same number of passages.
- **The no-ceiling graph didn't help at H + 1 either.** Today's graph gave the cheap walk .86 at H + 1 (SR-BH2); no
  ceiling gives .835. The difference is unpaired across runs but not in the graph's favour. Better keys improve the
  step's naming and input, not the arrival.
- **Where answer arrival is decided:** the full step reaches the answer passage by skipping, and every read added
  helps it (+.055). For Sirsh's goal, the open levers are the stop rule (how many passages to return) and the entry
  (25 off-chain entries are lost by every arm). The cheap step's in-order reading isn't the lever.

## Predictions against outcomes

- **cheap(H + 1) about .86, H-U3 passes at about +.025:** **.835, +.000, fails narrowly.** ✗
- **At equal reads, cheap − pass about −.03:** **−.055.** ✗ larger.

## Postmortem

- **What went right.** bill's note to report pass at H + 1 isolated the read factor. Without it, "equal spend, tie"
  would have hidden that pass gains as much from a read as the cheap walk does. Labelling the primary "equal spend, not
  equal outcome" kept the extra passage visible.
- **What I got wrong.** I expected the no-ceiling cheap walk to match today's graph at H + 1 (.86) and so beat pass at
  H. It came out lower. My predictions today have assumed better steps mean better arrival, and three runs (SR-BH under
  A-last, SR-BU, SR-BU2) say otherwise. I should predict arrival from where the walk *enters* and whether it *skips*,
  not from step accuracy.
- **Mechanism.** Arrival at the answer passage within a fixed number of reads is helped by skipping toward the answer.
  The cheap step, by naming the link from the last read, doesn't skip, and better links make it follow the chain more
  faithfully, not arrive sooner.
- **Scope.** SR-BH's 200 chains, the hop count given. Production is Sirsh's.
