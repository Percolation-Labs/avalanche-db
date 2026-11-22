# SR-BF result (22 Nov): a second entry gets the answer passage in more often, but not to the reader

*bill. Registered in REGISTERED-SRBF.md (#100) before any Jev call. Script `srbf.py`, outputs `out/srbf-dry.txt`,
`out/srbf-stage0.txt`, `out/srbf-fresh.txt`, `out/srbf-fresh.json`, and `out/srbf-diag.txt` (`srbf_diag.py`, from
cache, $0). **Spend $0.078** ($0.002 stage 0, $0.076 the 150; cap $0.30). james was told before the 150 ran; his
review of the registration came after.*

**Serves.** Sirsh's 17:07Z target, the answer in what the walk returns. On 2-hop the entry's hit rate caps A-last
(NOTE-ENTRY-ALAST.md). This tests whether walking the entry request's runner-up too gets more answers to a reader.

## Results

150 fresh MuSiQue train 2-hop questions.

| arm | returned passages | A-last | AC (the reader) |
|---|---|---|---|
| ONE: entry request's argmax, one cheap step | 2.00 | .840 | .693 |
| TWO: plus its runner-up, one cheap step | 2.61 | .887 | .713 |

- **H-F fails. AC(TWO) − AC(ONE): +.020 [−.020, +.060]**; 6 questions gained, 3 lost.
- A-last(TWO) − A-last(ONE): **+.047 [+.013, +.080]**.
- The entry is on a hop in .827 of questions. When it isn't, the runner-up is in 13 of 26.
- The second walk adds only 0.61 passages on average: the runner-up is often the first walk's step, or its step is
  the first entry.

**AC by what ONE returned** (`out/srbf-diag.txt`):

| ONE's set | n | AC |
|---|---|---|
| both hops | 104 | .808 |
| answer passage + another | 22 | .818 |
| hop 1 + another | 11 | .182 |
| neither hop | 13 | .000 |

- The reader behaves as SR-AC found: with the answer passage it picks the answer about 81% of the time, whether or not
  hop 1 is there; without it, rarely.
- **AC is a lower bound here too.** Its failures on both-hop sets include scoring misses: the gold "Salt Lake City
  metropolitan area" isn't contained in a chosen sentence that says "Salt Lake City"; "Wab Kinew" when the chosen
  sentence is about the district.

## What it means

- **The second entry buys A-last, and the reader keeps about half of it.** +.047 A-last becomes +.020 AC, inside the
  noise. The three AC losses are the reader choosing a rival sentence from the extra passage.
- **On 2-hop the walk is near what one entry can give.** With the entry on a hop 83% of the time and the reader at
  about 81% given the answer passage, the remaining loss is half entry, half reader.
- **For the entry work:** more entries aren't worth it at this size. A better single entry would be.

## Predictions against outcomes

- A-last(TWO) − A-last(ONE) about +.05: **+.047** ✓
- AC(TWO) − AC(ONE) about 0 (−.02 to +.03), H-F more likely to fail: **+.020, fails** ✓
- e1 on a hop about .89: **.827** ✗ (lower on this draw)

## Postmortem

- **What went right.** The $0 price (the upper bound and the reader cost from SR-AC) set the prediction, and judging
  by the reader rather than A-last kept a significant A-last gain from being reported as a win. The low AC level was
  diagnosed from cache before the write-up.
- **What I got wrong.** I ran the 150 before james reviewed the registration. Within the rules (registered, capped,
  under $1), but it broke our habit of a second read first. AC's containment check is one-directional; a gold answer
  longer than the reader's sentence fails. That should be fixed before AC is used as anyone's primary.
- **Scope.** MuSiQue train 2-hop, one draw of 150, one reader.
