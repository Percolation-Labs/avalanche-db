# R-stop replay check (22 Nov): stopping when the reader finds an answer sentence beats the knowledge stop, and fails non-inferiority to the oracle narrowly

*james, on bill's suggestion. Registered in REGISTERED-RSTOP.md (#105) and amended at bill's review before the run.
Script `reader_stop.py`. Outputs `out/rstop.txt`, `out/rstop.json`. **Spend $0.050** (cap $0.15). A replay on SR-BS3's
cached trajectories, the questions where the idea came from, so **a pass would still need a fresh draw**.*

**Serves.** Sirsh's 17:07Z goal: the answer in what the walk returns, with the reader (AC) as primary, since the rule
changes set size (bill's 17:43Z rule).

## Results

300 chains (SR-BS3's), Jev's full step. After each read, the reader request plus NONE; stop when a real sentence wins.

| stop | AC (standard request) | A-last | returned |
|---|---|---|---|
| oracle H | .783 | .857 | 3.00 |
| **R-stop** | **.760** | .840 | **2.63** |
| S-check (SR-BS3) | .710 | .777 | 2.59 |

- **Primary, like for like: AC R-stop − oracle H: −.023 [−.057, +.007].** **H-R fails, narrowly.** Per the
  registration, that's "not shown within .05, cost within about .06", not evidence of harm.
- **Sensitivity (bill's note 1).** 30 of 300 walks (10%) never stopped. Their cut point depends on the oracle H.
  Excluding them gives −.011 [−.041, +.019], which would pass. **At 10%, above "a few percent", this replay can't settle
  non-inferiority**, as registered.
- **R-stop − S-check: +.050 [+.020, +.083].** The reader-tied stop beats the knowledge stop at about the same set size
  (2.63 against 2.59).
- AC of the NONE-request's own choice: −.033 [−.063, −.003]. The standard request on the stopped set does a little
  better than the stop request's own pick.
- By type, AC R-stop against oracle H: 2-hop .770 against .780; 3hop1 .720 against .770; 4hop1 .760 against .800.
- Stops after one read: 90, against S-check's 98.
- **The never-stopped 30 are hard questions, not missing passages.** The answer passage was in the set in 26 of 30,
  but the standard reader found the answer in only 8. NONE kept winning because the reader couldn't find it.

## What it means

- **Tying the stop to a sentence the reader can use removes most of the knowledge-stop cost.** S-check's −.073 becomes
  −.023, at the same set size.
- **It isn't shown within .05 of the oracle on this replay, and the replay can't fully decide.** The 10% that never
  stop are cut at an H-dependent length. Excluding them, the gap is −.011.
- **The next test is a live walk on a fresh draw**, where the reader-stop walk keeps walking until it stops or the pool
  runs out. That removes the oracle from the never-stopped cases.

## Predictions against outcomes

- **About 2.8 passages:** **2.63.** ✗ slightly fewer.
- **AC − oracle H about −.02, H-R passing about half the time:** **−.023, fails narrowly.** ✓ on the size.
- **R-stop − S-check about +.05:** **+.050.** ✓
- **Never stopped under 10%:** **10.0%.** ✗, just.

## Postmortem

- **What went right.** All three of bill's amendments mattered.
  - Like-for-like scoring moved the primary from −.033 to −.023.
  - The sensitivity row showed that the replay can't decide.
  - Calling it a replay check keeps it from being claimed.
  - Sequential waves cost $0.05, against an all-prefix worst case near $0.08.
- **What I got wrong.** I estimated never-stopped walks as rare. They're the hardest 10%, where the reader can't find
  the answer even with the answer passage present. A live walk will read many passages for these, and that cost needs
  watching.
- **Mechanism.** NONE wins until a sentence the reader takes as the answer appears. That happens on arrival for most
  questions, and never for the reader's hardest ones. The knowledge stop fired on what Jev knew. This one fires on what
  the set shows.
- **Not tested.** A live walk with a fresh draw. A cap on reads for the never-stopping walks would be a constant; the
  pool (20) is the only physical bound.

**Scope.** SR-BS3's 300 chains (seen), a replay, and the pass step. Production is Sirsh's.
