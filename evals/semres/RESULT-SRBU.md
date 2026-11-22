# SR-BU result (22 Nov): the knob-free graph fixes the cheap walk's keys, not its arrival at the answer

*james. Registered in REGISTERED-SRBU.md (#98); bill said yes (17:06Z, 17:13Z). Script `srbh.py --nocap`. Outputs:
`out/srbu-today.txt` (the today arm re-scored from cache, $0), `out/srbu-fresh.txt`, `out/srbu-h1.txt`,
`out/srbh-fresh-nocap.json`. **Spend $0.030** (cap $0.20).*

**Deviation.** Stage 0 was skipped. The script and questions are SR-BH's, which ran clean through stage 0; only the key
file changed; the today arm reproduced SR-BH exactly; and the dry run priced it at $0.03. bill accepted this.

**Serves.** Sirsh's 17:07Z goal: the answer is contained in what the walk returns (A-last, checked).

## Results

SR-BH's 200 chains. The hop count H is an oracle, so every arm returns exactly H passages: the returned-set size is
3.5 on average for all three arms (bill's 17:13Z readout). A walk can't buy A-last here by returning more.

| | A-last | all hops | input chars | A-last per 10k chars |
|---|---|---|---|---|
| cheap, today's graph | .790 | .395 | 29.2k | .270 |
| **cheap, no ceiling** | **.800** | .390 | **25.3k** | **.316** |
| pass (Jev's full step) | .835 | .315 | 37.3k | .224 |

- **H-U1 fails.** cheap(no ceiling) − cheap(today) on A-last is +.010 [−.040, +.065]. 16 questions gained and 14 lost.
- **H-U2 fails.** cheap(no ceiling) − pass is −.035 [−.090, +.025]. The lower bound is below −.05.
- **The mechanism worked as designed.**
  - The rescue rate fell from .44 / .62 / .65 to **.21 / .38 / .46**.
  - Naming accuracy at on-chain keyed steps *rose*: the next hop shares the named key .575, against .399 (uniquely
    .392 against .356).
  - Input fell 13%, to a cheap / pass ratio of **.678**.
- By type: 3hop1 cheap .82 against pass .89; 4hop1 .78 against .78.
- Per character, the no-ceiling cheap walk is the best at reaching the answer passage: .316 against pass .224.

## What it means

- **Better keys made the cheap walk cheaper and more accurate per step, but not more likely to reach the answer.**
  With exactly H reads, the cheap walk reads the chain in order, and a walk that enters mid-chain or misses one link
  runs out of reads before the last hop. Jev's full step heads for the answer passage and skips. So on Sirsh's measure,
  under an exact budget, pass still leads by about .035, and the graph change doesn't close it.
- **The cheap walk's case on Sirsh's measure is cost per answer passage reached.** It's 41% more A-last per character
  than pass (.316 against .224), at about .035 lower A-last.
- **The real lever for A-last is the budget and the stop rule, not the step.** SR-BH2's spare read lifted both walks
  to .86–.89 A-last. The step rule moves A-last by a few points either way.

## Predictions against outcomes

- **Rescue rate at later steps about .35:** .38 and .46. ✓ roughly.
- **Naming accuracy falls to about .35:** **rose to .575.** ✗, in the right direction for the walk. With the bridge now
  a key, Jev names it more often, not less, despite twice the options.
- **A-last about .83, H-U1 borderline at about +.04:** **.800, +.010.** ✗
- **Input ratio about .70:** **.678.** ✓

## Postmortem

- **What went right.** bill's four readouts separated the mechanism from the outcome. Without the rescue rate and
  naming accuracy, the null would read as "uncapped keys don't help". In fact they help the step and not the arrival.
  Re-scoring the cached today arm at $0 made the comparison exactly paired.
- **What I got wrong.** I predicted A-last from keyed reachability. But reachability and naming are per step, and
  A-last under an exact budget is decided by whether the walk is still on course at its last read. The cheap walk's
  in-order reading is what limits it, and better keys don't change the order.
- **Mechanism for the null.** The keyed step moves to the next hop in order. Under an exact read budget, arrival at the
  last hop needs either an on-chain entry at hop 1 or a skip. The full step skips, and the cheap walk doesn't.
- **Not tested.**
  - The no-ceiling graph with a spare read. Since the walk is now cheaper per read, H + 1 on the no-ceiling graph may
    cost about what pass costs at H.
  - A fresh draw.
  - Bill's dreaming side: which high-df memberships are real bridges, if an open corpus makes |S| large.

**Scope.** SR-BH's 200 chains, H given, A-last as the measure. Production is Sirsh's.
