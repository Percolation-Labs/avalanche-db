# SR-BH result (22 Nov): on 3- and 4-hop chains, the cheap walk beats Jev's full step, at 78% of the input

*james. Registered in REGISTERED-SRBH.md (#94) and approved by bill (16:33Z) before any Jev call. Script `srbh.py`.
Outputs: `out/srbh-stage0.txt`, `out/srbh-fresh.txt`, `out/srbh-fresh.json`, `out/srbh-diverge.txt` (the divergence
breakdown, $0 from the json, post hoc). **Spend $0.117** (stage 0 $0.002, the 200 $0.115, cap $0.40).*

**Serves.** Sirsh's 23:03Z ask: the cheap pipeline in a full walk. Until now it had only been tested on 2-hop.

## Results

200 MuSiQue train chains (100 3hop1, 100 4hop1, seed 1344). Both walks start from Jev's entry request and read
exactly as many passages as the question has hops.

| | all hops | per-hop recall | input chars / question |
|---|---|---|---|
| 3hop1, cheap | .510 | .787 | 24.6k |
| 3hop1, pass | .440 | .770 | 31.9k |
| 4hop1, cheap | .280 | .723 | 33.8k |
| 4hop1, pass | .190 | .715 | 42.7k |
| **both, cheap** | **.395** | .755 | **29.2k** |
| **both, pass** | **.315** | .743 | **37.3k** |

- **Primary: all hops, cheap − pass, +.080 [+.025, +.130]** (n 200), with the input ratio cheap / pass at **.783**.
- **H-H (non-inferiority, lower bound above −.05) passes.** The CI also excludes 0, but superiority wasn't
  registered, so it's reported as the observed direction, not a second hypothesis.
- By type: 3hop1 +.070 [.000, +.150]; 4hop1 +.090 [+.010, +.180].
- Per-hop recall barely differs (+.012 [−.010, +.033]). The cheap walk gets whole chains more often, not more hops.
- **The input counts only requests each walk uses** (bill's check). The cheap walk pays for a full passage request only
  when it rescues, and the pass walk only for its own. So the .783 is a measured ratio.
- **Rescue rate:** step 1 .44, step 2 .62, step 3 .65.
- **Entry position** (the entry request lands on hop 1 in 81 of 200 questions):
  - hop 1 (n 81): cheap .593, pass .531
  - a middle or last hop (94): cheap .33, pass .21
  - off the chain (25): 0 for both

## Where the two walks part (post hoc, $0)

- **The walks differ only at keyed steps.** A rescue step makes the same request as the pass walk, so at every rescued
  step reached with the same history (190) they pick the same passage. They part only where a passage shares the named
  key: 'one' differs in 85 of 143 steps, a twin in 26 of 43.
- **The outcomes split 24 to 8 for the cheap walk** (55 both get all hops, 113 neither).
- **When cheap wins (24), its pick at the first divergence is always the adjacent hop.** The pass walk's pick:
  - skips a hop along the chain: 10
  - leaves the chain: 9
  - is the other adjacent hop: 5
- **When pass wins (8), the cheap walk's pick left the chain in 7.**

## What it means

- **Naming the bridge keeps the walk in order.** The named key is the entity the last read hands on, so the step lands
  on the next hop. Asked "would reading this give information needed to answer the question?", Jev often prefers a
  passage *further* along the chain. That's a real hop, but with exactly H reads the skipped hop is never read.
- **This is partly a budget effect, and we can't separate it here.** The walks read exactly H passages, an oracle
  budget. With spare reads, the pass walk could go back for a skipped hop. A stopping rule (bill's note 1) is the test
  that separates them: if pass recovers with one extra read, its loss is order, not choice.
- **The saving holds past 2 hops but is smaller (.78 against .76 on 2-hop)**, because later steps rescue more (.62–.65),
  as the look predicted. What limits it is the df-100 key limit: later bridges are places with no key.
- **Accuracy falls fast with length for both walks:** all hops .51 → .28 from 3 to 4 hops for cheap. Per-hop recall
  stays above .72, so most failures are one missing hop, and the entry is the largest single loss: 25 off-chain
  entries are 0 for both walks, and 94 entries land mid-chain.

## Predictions against outcomes

- **cheap − pass about 0, H-H passing about two times in three:** **+.080**, passes. ✗ on size and direction. I
  predicted a tie by construction from the rescue rate. But rescues are where the walks *agree*, so the difference lives
  entirely in the keyed steps, where it favours the cheap walk.
- **Rescue rate about .35 at step 1, .55–.65 later:** **.44, .62, .65.** ✓ for later steps; step 1 is higher.
- **Input ratio .85–.95:** **.78.** ✗; the saving shrank much less than I expected (2-hop .76).
- **All hops 3hop1 about .45, 4hop1 about .25:** cheap .51 and .28, pass .44 and .19. ✓ roughly.
- **Entry on hop 1 in about half:** **81 of 200 (.41).** ✓ roughly.

## Postmortem

- **What went right.** The $0 look picked the right subset (chains) and predicted the later steps' rescue rate. bill's
  entry-position readout showed that 25 off-chain entries are lost by both walks, which bounds what any step can do.
  The divergence breakdown found the mechanism without another call.
- **What I got wrong.** I reasoned that a rescue-heavy walk would tie the pass walk, without asking where the two
  walks can differ at all. Rescued steps are identical by construction, so the comparison was always going to be
  decided at keyed steps, which is where the cheap walk's design is strongest.
- **Mechanism for the gain.** Naming the bridge entity (structure) orders the walk; the passage request (relevance)
  favours answer-proximate passages and skips. Under a fixed budget of H reads, a skip is a lost hop.
- **Not tested.**
  - A walk with spare reads, or a stopping rule.
  - Fresh-sub-question types (30% of 3- and 4-hop).
  - Whether the skip tendency is the PASS_TASK wording. A task phrased "the next passage in the chain" might not
    skip, but that's a wording change, which Sirsh's held-out rule requires to be registered on a new draw.

**Scope.** MuSiQue train chains, one draw of 200, the hop count given (an oracle). Production is Sirsh's.
