# SR-BS3 (registered 22 Nov, before any Jev call): does the answerability stop hold at the reader on a fresh draw?

*james. Confirms SR-BS2 (#101, #103) before anything is claimed, as bill and I agreed (17:38Z). Scripts `srbs3.py`
(srbs2.py with S-check only, a new seed and a larger draw) and `srbs2_ac.py` (bill's reader and judge, verbatim).
Caps: $0.40 for the walks, $0.15 for the AC scoring.*

**Question.** On SR-BS2's 180, the knob-free check ("`question` can be answered from these passages", argmax after
each read) returned 2.4 passages against the oracle hop count's 3.0, at a reader cost that wasn't distinguishable from
zero: AC −.028 [−.072, +.022] with the judge, −.044 [−.089, +.000] string only. Does that hold on fresh questions?

**Data.** 300 fresh answerable chains (100 each of 2-hop, 3hop1, 4hop1) from the full MuSiQue train file, SEED 1348.
Excluded, and asserted: every question SR-BX, SR-BE, SR-BH, SR-BS, SR-AC, SR-BF and SR-BS2 used. SR-BS2's draw is
rebuilt as it drew, and the dry run's overlap with SR-BS2's questions is 0. Stage 0 is positions 80–81 per type.

**Walk and stop.** SR-BS2's, unchanged: Jev's entry request, then the pass step. S-check after each read, over the
full text of every read passage. Oracle H and oracle H + 1 as references. S-state is dropped, since SR-BS2 found no
difference.

**Primary. AC (string or judge; bill's #102), S-check − oracle(H), paired bootstrap 95% CI over the 300, with
returned passages beside it.**
- **H-S3 (non-inferiority):** the lower bound is above −.05, the margin carried since SR-BH.

**Secondary.**
- AC string only (no judge), the same contrast.
- The judge's yes count per arm.
- A-last, S-check − oracle(H).
- S-check's stops against the first arrival at the answer passage (before, at, after, never). Stops after one read.
- By hop type.

**Predictions.**
- AC, S-check − oracle H, is about −.03, with a half-width of about .035 at n = 300. So the lower bound is near −.065,
  and **H-S3 more likely fails than passes** (about one time in three). The point estimate should match SR-BS2's
  within its CI.
- Returned passages are about 2.4 against 3.0. Stops at arrival are about two times in three.

**What follows.**
- **If H-S3 passes:** "a knob-free stop costs less than .05 of reader accuracy, at about 20% fewer passages" is
  offered to Sirsh as a hypothesis.
- **If it fails with the point estimate near −.03:** the honest claim is "about 3 points of reader accuracy for 20%
  fewer passages", and the trade is Sirsh's to judge.
- **If the point estimate is much worse:** SR-BS2's reading was optimistic, and the postmortem says why.
- Production is Sirsh's.

**Spend.** The dry runs estimate $0.16 for the walks and $0.05 for the AC scoring. Stage 0 first.

**Scope.** MuSiQue train chains, one draw of 300, the pass step, H hidden from the walk.
