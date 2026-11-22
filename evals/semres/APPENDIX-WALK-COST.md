# Appendix: the cheap walk against Jev reading everything

Part of the walk write-up (WRITEUP-WALK.md). All of it is MuSiQue, inside the question's own pool of 20
passages. Cost is **input characters per question** (what Jev is sent), measured from the run caches unless the
row says it's estimated. No file measures tokens.

## The two steps

- **The cheap step (`nt_rescue`).** Jev is shown only the passage just read and asked to name the link to the next
  one (the bridge key). A lexical match on that name finds the candidates. If one passage matches, it's read. If
  several match, Jev picks among just those. If none match, Jev picks from everything unread (the rescue).
- **Jev's full step (`pass`).** Every step, Jev picks the next passage from everything unread. In effect, Jev reads
  the whole pool at each step.

Both walks start from the same entry passage, so any difference comes from the step.

## Two-hop questions

| Walk (entry × step) | Both hops found | Input | Source |
|---|---|---|---|
| Jev entry × cheap step | **.750** | **15.6k** | SR-BE |
| Jev entry × full step | .743 | 20.6k | SR-BE |
| cosine entry × cheap step | .700 | 5.2k | SR-BE |
| cosine entry × full step | .743 | — | SR-BX (another fresh draw) |

The first three rows are one draw of 300 fresh train questions (SR-BE). The last row is SR-BX's own fresh draw,
where the cosine-entry cheap walk scored .723. The same arm scores .700 here, so the two draws differ by a few points.

- **From the same Jev entry, the cheap step ties Jev's full step:** +.007 [−.023, +.037], n 300 fresh, using 24%
  less input (SR-BE).
- **From a cosine entry, the cheap step comes within about .05 of the full step** (−.020 [−.053, +.013], post hoc in
  SR-BX). On SR-BE's draw the same cheap walk sends roughly a quarter of the input of the full walk from Jev's
  entry (5.2k against 20.6k). That ratio is our own arithmetic, not a registered comparison.
- **The rescue is what makes it work.** Without it, naming alone trails the full step by .10–.16:
  - SR-BW: −.104 [−.164, −.045]
  - SR-BN: −.163
  - SR-BT: −.116
  
  The rescue adds +.107 [+.070, +.147] (SR-BX). It's needed on about a third of questions (34–37%, SR-BE).

## Longer chains (3 and 4 hops)

Here the walk is told the hop count H, as an oracle. Appendix STEP-STOP covers what happens without it.

| Comparison | Reading the whole chain | Answer passage returned (A-last) | Input ratio cheap / full |
|---|---|---|---|
| at H (SR-BH) | cheap **+.080** [+.025, +.130] | cheap −.045 [−.095, +.000] | .783 |
| at H+1 (SR-BH2) | +.025 [−.030, +.085] | −.030 [−.075, +.010] | .807 |
| uncapped key graph, at H (SR-BU) | — | −.035 [−.090, +.025] | .678 |
| cheap at H+1 vs full at H (SR-BU2) | — | **+.000** [−.055, +.060] | .877 (32.7k / 37.3k) |
| equal reads, H+1 each (SR-BU2) | — | −.055 [−.110, −.005] | — |

**Why the two measures disagree.** The cheap walk reads the chain in order: each step names the next link. Jev's
full step sees every unread passage, so it often skips ahead straight to the answer passage, leaving the middle of
the chain unread. That loses on "read the whole chain" but wins on "the answer is in what was returned". Since the
goal is the answer, the second measure is the one that counts.

**What's left in the cheap walk's favour is input, not answers.** For the same number of passages returned, Jev's
full step gets the answer in more often (−.055 at equal reads). Given one extra read, the cheap walk ties it
(+.000; the registered test fell just short of its −.05 margin) with 12% less input. Per 10k characters, the cheap walk reaches the answer passage more often: .316 against
.224 on the uncapped graph (SR-BU).

## Limits

- **In-pool only.** Every walk runs inside a 20-passage pool. On a whole corpus, the full step would cost in
  proportion to the corpus; the cheap step would not. That's the argument for the cheap step, but it's untested.
- **The hop count is given as an oracle on chains.** A real walk has to decide when to stop (APPENDIX-STEP-STOP).
- **MuSiQue only.** No cheap-walk test exists on BEAM or any other set.
- **Mixed cost units.** SR-BX's "about 40% of the input" was an estimate in requests. SR-BE's measured characters
  replace it.
