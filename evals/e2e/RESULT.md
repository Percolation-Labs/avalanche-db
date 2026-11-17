# End to end: results

This file follows [REGISTERED.md](REGISTERED.md), which was merged as #8 before any full score.

## G0 and G1, at $0 (17 Nov 2026, bill)

**Setup.**
- Both stores were built by `midb ingest` through the `documents` adapter (#6, #7, #9).
- `probe/` reads them through the library:
  - search ranks every passage by full-text BM25;
  - G0 raises the doors of search's top 3 and labels them with D6;
  - the walks no model decides (oracle, width-only, coin, search-order) run `lab::run` with 3 seeds, waves of 10,
    and no search filler after the seeds. Each is cut at its first 20 reads.
- `score0.py` scores the rows; the full output is in `score0.txt`. No model was called.
- A 5-question smoke run of the probe came before the full run, after the registration was pushed.

| | A: MuSiQue, 150 questions | B: p8-subsystems, 150 cards |
|---|---|---|
| Doors per question, from 3 seeds | 73 | 40 |
| **G0**, AUC of question–door overlap, gold door vs the rest | **.738** (needs ≥ .55) | **.707** |
| G0, AUC of width | .575 | .612 |
| search recall@10 | .464 | .291 |
| **G1**, oracle − search, recall@10 | **+.139 [+.092, +.186]** | **+.147 [+.078, +.218]** |
| width-only − search | −.110 [−.143, −.078] | −.197 [−.251, −.147] |
| coin − search | −.092 [−.127, −.057] | −.143 [−.196, −.095] |
| search-order − search | −.054 [−.088, −.022] | −.106 [−.155, −.059] |
| full support @10, search / oracle | .140 / .387 | .187 / .327 |

**Both gates pass on both corpora.** The graph this ingester builds carries the answer, and its D6 doors say which
door leads to it. On MuSiQue the overlap AUC is higher than the lab graph's .569, though the ingester and the door
both differ from the lab's, so the two are not a controlled comparison.

**Every walk that doesn't read its doors loses to search at the same budget.** This is the bar the Jev walk faces.
A walk's reads after the three seeds go through doors, so it gives up search's ranks 4–10. Search's ranks 4–10 are
good: on A, recall rises from .409 at 5 to .464 at 10. A decider must pick doors well enough to make up that loss
before it can gain.

## Postmortem

**Where the oracle's gain comes from.** On A the oracle finds 69 gold passages that search's top 10 misses, and 58 of
them are not in search's top 20 at all. It loses 23 that search's top 10 held. On B it finds 54 and loses 23, and
43 of the 54 are beyond search's top 20. The walk's value is reaching documents search doesn't rank, not reordering
search's own list. The hop from a card to the commits that name its id (term door `rem NNNN`) is exactly that.

**What it means for the walk under test.** Width-only is below coin on both corpora. On these graphs, wide doors are
the worst bet, the opposite of the lab's reference worlds, where width was a strong control. Search-order is the
best of the controls, so a ranking from the question's words alone already closes half the gap. Jev has to beat
search-order to show it reads the text. The registered W2 compares the walk with width-only, and search-order is
reported beside it.

**A design question for the walk, not settled here.** The oracle's 23 losses per corpus are search's own reads that
the walk gave up. A walk that keeps more of search's list, through more seeds or search reads in each wave, raises
the floor and may lower the ceiling. That is james's call for the walk. Any change is chosen on questions outside
these 300, because REGISTERED.md fixes the questions.

**Product findings on the way.** Each was fixed and merged, with a test.
- Deep paths overflowed the 120-character stored pointer (#7).
- Full-text search on p8 took 240 s, because the reader ran one `git show` per commit (#9, now 10 s).
- A re-ingest rewrote every fact and never retracted any (#11).

Ingesting p8-subsystems whole takes 101 s and a 2.2 GB store. Size is the next thing to cut.
