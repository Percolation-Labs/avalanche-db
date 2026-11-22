# SR-BA result (22 Nov): the answer-passage reward helps new questions, almost entirely where the answer passage recurs

*bill. Registered in REGISTERED-SRBA.md (#104) before scoring; reviewed by james (17:40Z), whose stratum readout was
added before the run. Script `srba.py --swap`, output `out/srba-swap.txt`, `out/srba-swap.json`. $0, no Jev.*

**Serves.** Sirsh's 17:07Z decision: optimise the dreaming reward toward the answer being in what the walk returns.

## Results

Learn on half 1 (600 questions), test on half 0 (489, never scored before). SR-BC's structural walk and fixed-point
update.

| reward | fixed point | test A-last | − none | gained / lost |
|---|---|---|---|---|
| none | | .569 | | |
| gold pair (SR-BC's) | 2 passes | .579 | +.010 [+.002, +.020] | 5 / 0 |
| **A-last** | 3 passes | **.581** | **+.012 [+.004, +.022]** | **6 / 0** |

- **H-BA passes. T*alast − none: +.012 [+.004, +.022].**
- T*alast − T*pair: +.002 [+.000, +.006].
- Both hops moves identically, since on 2-hop a walk that gets the answer passage from a hop entry gets both.

**Where the gain is** (james's note 1):
- **136 of 489 test questions** have a last-hop passage that a rewarded learn walk contained. MuSiQue reuses
  single-hop questions, so answer passages recur far more than whole gold pairs (6).
- **Shared last-hop passage: +.037 (n 136), 5 gained.**
- **Not shared: +.003 (n 353), 1 gained.**

**Both directions** (james's note 3; each direction's CI is the test):
- the look, half 0 → half 1: +.022 [+.009, +.037], 10 / 0;
- this test, half 1 → half 0: +.012 [+.004, +.022], 6 / 0;
- pooled over 948 test questions: about +.017, 16 gained, 0 lost.

## What it means

- **The reward works, and it works by recurrence.** Rewarding the doors into an answer passage helps a later question
  whose answer is in that same passage, and almost never anything else. That is useful where questions recur (a user's
  corpus asked about the same things repeatedly), and close to nothing where they don't.
- **It is memory of answer passages, not a learned way to find new ones** (james). Its value in use depends on how
  often real questions land on passages an earlier confirmed walk already reached. MuSiQue train has 136 of 489 by
  construction; a real workload may have more or fewer, and nothing here measures that. The hypothesis for Sirsh:
  *reward walks whose returned set held a confirmed answer; it helps questions that reuse those passages* (+.037),
  and almost no others (+.003).
- **It never breaks a walk** (0 losses in both directions, as for every additive reward so far).
- **The A-last reward is at least as good as the gold-pair reward** and needs only "did the answer passage come back",
  which is closer to a signal a product could observe than the gold pair is.

## Predictions against outcomes

- T*alast − none about +.02, two in three to pass: **+.012, passes** ✓ (smaller than predicted).
- T*alast − T*pair about +.005, n.s.: **+.002** ✓
- No losses: **0** ✓

## Postmortem

- **What went right.** The swap gave a fresh test without new data. james's stratum request turned "it works" into
  "it works by recurrence", which is the honest reading and the one that decides where it's useful.
- **What I got wrong.** I predicted +.02 from the look without asking why the look worked; the stratum would have told
  me that the gain depends on recurrence, and so on the direction's reuse.
- **Mechanism.** The reward raises the doors between a rewarded walk's entry and answer passage. A new question gains
  only if its walk passes through the same memberships, which on MuSiQue means the same answer passage.
- **Scope** (james's note 2). MuSiQue train 2-hop, **the structural walk only**. On A-last, Jev's full step is now the
  better walk (SR-BU2), and whether a door-weight reward changes a Jev-chosen walk is untested. Gold labels stand in
  for an observed answer.
