# SR-BE result (22 Nov): Jev's entry request chooses well, but walking from its own pick is as good and cheaper

*bill. Registered in REGISTERED-SRBE.md (#92) with amendment 1 before the 300 were run; reviewed by james. Script
`srbe.py`, outputs `out/srbe-stage0.txt`, `out/srbe-fresh.txt`, `out/srbe-fresh.json`, `out/srbe-extra.txt` (three
contrasts computed afterwards from the json, $0). **Spend $0.127** (stage 0 $0.0013, the 300 $0.1253, cap $0.40).*

**Serves.** Sirsh's 15:52Z steer, the entry look: the walk's largest loss is a wrong first passage.

## Results

Fresh draw, 300 MuSiQue train 2-hop questions (positions 304–603), both hops, paired bootstrap 95% CI.

| walk | both hops | input chars / question |
|---|---|---|
| cosine entry × cheap step (`e_cos×nt_rescue`) | .700 | 12.0k |
| title entry × cheap step | .690 | |
| **SE: both walks, Jev's entry request keeps one** | **.743** | **28.6k** |
| SEP: the same, by entry p × step p | .770 | 28.6k |
| **Jev's entry request's own pick × cheap step (`e_pass×nt_rescue`)** | **.750** | **22.1k** (upper bound) |
| Jev's entry request × Jev's full step (`e_pass×pass`) | .743 | 20.6k |
| *oracle between the cosine and title walks* | *.797* | |

- **H-E passes. SE − e_cos×nt_rescue: +.043 [+.003, +.083].** SE is right on 45 of the 61 questions where the two
  walks split (SEP 53).
- **But the second walk adds nothing. SE − e_pass×nt_rescue: −.007 [−.037, +.027]; SE − e_pass×pass: +.000
  [−.043, +.040].** Once the entry request is paid for, walking from its own argmax does as well, for less input.
- SEP − e_pass×nt_rescue +.020 [−.020, +.060]; SEP − e_pass×pass +.027 [−.020, +.073]. Neither is significant.
- **e_pass×nt_rescue − e_cos×nt_rescue: +.050 [+.003, +.100].** With Jev's entry, the cheap step matches Jev's full
  step: e_pass×nt_rescue − e_pass×pass is +.007 [−.023, +.037].
- The input figure for e_pass×nt_rescue counts the rescue pass request on every question. It's needed only when no
  other passage shares the named key (about 28% in SR-BX), so the real figure is lower than e_pass×pass's.
- One different-entry exact tie in p went to cosine's walk.

## What it means

- **The lever is the entry request, not the second proposal.** Jev's 20-passage entry request, read once, gives a
  better first passage than cosine (+.050). Using it to choose between two proposals is no better than taking its own
  pick.
- **The cheap walk's best form is now Jev's entry, then the cheap step**: .750 on both hops against .700 for cosine's
  entry. That equals Jev on both steps (.743), at about the same or lower input. The price is roughly double the
  cosine-entry walk's input (12k), for +.05.
- **SEP's +.070 over cosine** is the best number here, but it was the best of six rules on the seen set, and it isn't
  separable from e_pass×nt_rescue on this draw. It's not a lead.

## Predictions against outcomes

- SE − e_cos about +.03, H-E a coin flip: **+.043, passes.** ✓ (the look's +.057 shrank, as predicted)
- SE − e_pass×nt_rescue about +.02, n.s.: **−.007, n.s.** ✗ in direction. The second walk doesn't help.
- SEP ≥ SE by under .01: **+.027.** ✗ larger, but SEP isn't separable from the single walk.

## Postmortem

- **What went right.** james's cost readout (1) and the single-walk control turned a passing primary into the right
  conclusion: without them, "SE passes" would have been the headline. Stage 0 was clean; spend was a third of the cap.
- **What I got wrong.** The look's line that the entry request "picks hop 1 only 61% of the time" judged it against hop
  1, but both hops is unordered: an entry on hop 2 also works. Its pick is on a hop 89% of the time (cosine's 84%). I
  argued from the wrong denominator that its argmax was weak, and so predicted the second walk would help.
- **Mechanism.** Most entry misses are neighbours of a hop (21 of 48 in the look). The 20-passage request reads every
  passage's content against the question, so it separates a hop from its neighbour better than cosine does. A second
  candidate gives it nothing it doesn't see in the full pool already.
- **Scope.** MuSiQue train 2-hop, one fresh draw of 300, the cheap walk. Production is Sirsh's.
