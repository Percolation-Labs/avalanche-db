# S3 result: FAIL. Walks don't read the missing link, so walk-driven repair can't propose it

*20 Nov 2026, james. Registered in REGISTERED-S2.md (S3), amended in REGISTERED-S2b.md and REGISTERED-S2c.md (99937f2)
before any S3 run. $0, no Jev, no Claude data, nothing fitted. Code `s3.py`; output `out/s3-{mq,cards}.{txt,json,log}`.
It runs on S2c's cuts, every test cut applied at once.*

## Result (rerun with the float-error stop, bill's #54 review; run 1 is in `out/s3-*-run1.log`)

| | MuSiQue | cards |
|---|---|---|
| cut pairs (test) | 133 | 133 |
| **cut pairs that are candidates at all** (co-read by ≥2 walks) | **7** (6 trivially, both ends seeds of one walk) | **4** (1 trivially) |
| cut pairs recovered by the loop | 0 | 0 |
| their rank among round-1 candidates by coherence gain | 139–477 of 835 | 108–227 of 237 |
| links accepted (gain above float error) | 40 | 5 |
| recall on cut questions: built / drifted / repaired | .145 / .073 / .073 | .223 / .200 / .200 |
| repaired − drifted, recall | +.000 | +.000 |
| **cut questions whose top 5 changed: repaired / random / hub / count** | **24** / 4 / 2 / 6 | 1 / 0 / 0 / 1 |
| of those, with a new gold entry | 0 in every arm | 0 in every arm |
| T\* cost (UNI nats): built / drifted / repaired | 9.64 / 10.50 / 10.50 | 7.27 / 8.10 / 8.10 |
| collateral on the graph as built: links added; recall change | 41; −.013 [−.032, +.000] | 7; +.000 |

**Verdict: FAIL on the gate and the bar, on both sets.** The gate needed 2 of 4 cut pairs recovered per set. The loop
recovers none, wins back none of the recall the cut cost (.072 and .023), and leaves the tree's cost where the cut
put it. Run 1 stopped at gain ≤ 0 and accepted float-noise ties (207 and 36 links). The verdict is the same, but it
recovered 1 MuSiQue pair by such a tie, and that recovery doesn't survive the proper stop. Collateral passes narrowly
on MuSiQue: the interval touches 0.

## Why

1. **The candidate source fails first, as bill's S4 predicted.** After the cut, the gold passage sits at a median walk
   rank of 32–56, outside every walk's top 5, and other questions' walks don't reach it either. So the cut link is
   almost never co-read, and a repair drawn from what walks read can't propose it. The few cut pairs that are
   candidates are mostly pairs of seeds, which search supplied, not the walk.
2. **Coherence moves the walk, but not toward the answer.** By construction, every candidate joins passages that walks
   already read.
   - On MuSiQue, the 40 coherence-chosen links change the top 5 of 24 cut questions, against 2–6 for the random, hub
     and count controls. So the reward really steers the walk.
   - None of the new entries is gold, in any arm.
   - The reward pulls the walk toward passages that tie tightly to what it already read, and on these graphs those
     aren't the answer. That is L3's failure again, now seen in the reads themselves, and not inferred from a flat
     recall.
3. **Nothing separates coherence from counting on the outcome.** Every arm wins back 0 recall. Coherence differs from
   the controls only in how much it moves the walk.

## Postmortem

1. **Predicted by data in hand, again.** bill's S4 (edges whose far end a walk read: 23% and 49%, upper bounds) and S2c
   (the cut pushes the passage to rank 30–60) together imply that walks won't co-read the cut link. I registered S3
   before either existed, and once they did, the candidate check ran first. It is the first line of the result.
2. **What the story can and can't claim.** We know what good looks like: the most probable tree (bill's S1′). We can
   measure drift: tree cost in nats, and S2c passed. We **can't yet** bring it back from walks alone. The structure the
   walk would need is exactly what the walk stops reading once it is damaged. A repair needs a candidate source that
   doesn't depend on the damaged walk reaching the far end.
3. **Candidate sources for that, each to be registered before use:**
   - (a) Passages that share text but no narrow key: the graph's own Near links, used as candidates rather than doors.
   - (b) The search scores of other questions, without gold. A passage that search ranks highly for many questions
     but that is reached only through wide links is a likely missing entry hop. This is bill's entry-hop finding
     turned into a candidate rule.
   - (c) Walks at more than 5 reads, to see how far the budget must grow before the cut pair is co-read. That
     measures the walk data a repair needs, which is S4's question.
   - None of these is a knob. The reward question, whether coherence or counting, stays open until some source
     proposes the true link.
4. **Run cost:** the lazy greedy loop rescores only candidates whose walks changed, which brought rounds from 107 s
   to 0–5 s. Run 1 on MuSiQue took 426 rounds in about 25 minutes; the rerun stops far sooner.
