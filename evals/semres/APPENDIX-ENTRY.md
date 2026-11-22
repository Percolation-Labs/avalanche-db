# Appendix: where to start

*bill, 22 Nov 2026. Appendix to WRITEUP-WALK.md. Sources: RESULT-SRBX.md (entry arms), RESULT-ENTRY-LOOK2.md,
RESULT-SRBE.md, NOTE-ENTRY-ALAST.md, RESULT-SRBF.md. Spend: SR-BE $0.127, SR-BF $0.078 (Jev); the looks were $0.*

**Tested on.** MuSiQue train 2-hop questions, fresh draws of 300 (SR-BE) and 150 (SR-BF), each with its pool of 20
passages. percolate-core 0.2.15 (Jev), bge-small-en-v1.5.

## A wrong start is fatal

On two-hop questions, a walk whose first passage is on neither hop recovers both hops in **0** cases: the step can't
come back. Why the first passage misses, for the closest-vector start (48 misses in 300):

| the wrong first passage is… | count |
|---|---|
| a neighbour of a hop, linked by a door key | 21 |
| a namesake (same title, different passage) | 13 |
| linked to neither hop | 14 |

So a fix for namesakes alone can't close the gap.

## Three ways to choose the first passage

| first passage chosen by | then the cheap step: both hops | input per question |
|---|---|---|
| closest by vector | .700 | 5.2k chars |
| Jev over the 20 titles only | .690 | |
| **Jev reading all 20 passages** | **.750** | 15.6k chars |
| Jev reading all 20, then Jev's full step | .743 | 20.6k chars |

- **Jev reading the pool picks a better first passage**: about +.05 over the vector start, borderline
  (+.050 [+.003, +.100]). It costs three times the input.
- **Titles alone are worse.** Asked "which passage should be read first", Jev often picks the one that holds the
  answer, which the unordered both-hops measure still credits when the step goes back to hop 1.
- **With Jev's start, the cheap step matches Jev's full step**, at 24% less input.

## Choosing between two starts doesn't help

On seen questions, walking from both the vector start and Jev's title start, then letting Jev's 20-passage request
keep one, chose right in 39 of the 50 questions where the two walks split. On a fresh draw (SR-BE, registered), that
beat the vector walk (+.043 [+.003, +.083]). But **walking from Jev's own pick did as well** (−.007 against it), with
less input. A second candidate gives the request nothing it doesn't already see in the pool.

## On the answer measure, the start is the cap

With the goal set to the answer passage being returned:

| returned set (2-hop) | passages | answer passage present |
|---|---|---|
| Jev's top 2 from the pool, no walk | 2 | .603 |
| vector start + cheap step | 2 | .837 |
| **Jev's start + cheap step** | **2** | **.893** |
| *Jev's start lands on either hop* | | *.893* |

- **Walking beats retrieving**: for the same two passages, a start and one step find the answer passage far more
  often than Jev's own top two.
- **Once the start is on a hop, the step reaches the answer passage essentially always.** Every loss is a start that
  missed both hops.

## A second start: more answer passages, not more answers

Walking Jev's runner-up as well as its first pick (SR-BF, registered):

| | passages returned | answer passage present | reader's check |
|---|---|---|---|
| one start | 2.00 | .840 | .693 |
| two starts | 2.61 | .887 | .713 |

- The answer passage arrives more often: **+.047 [+.013, +.080]**.
- **The reader keeps under half of that: +.020 [−.020, +.060]**, not significant. Three questions were lost to a rival
  sentence in the extra passages.
- With the start on a hop about 83% of the time and the reader right about 81% of the time given the answer passage,
  the remaining loss is half start, half reader.

## What's open

**A better single start**, not more starts. The misses are mostly a hop's neighbours and namesakes, which a request
reading the passages separates better than vectors do, but not always. On longer chains (SR-BH), 25 of 200 starts
were off the chain, and every walk lost them.

## Limits

MuSiQue 2-hop, pools of 20. In an open corpus the start is chosen from far more than 20 passages, and Jev can't read
them all, so the vector start's share of the work would grow.
