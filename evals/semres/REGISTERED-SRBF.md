# SR-BF (registered 22 Nov, before any Jev call): does walking a second entry get the answer to the reader?

*bill. Follows NOTE-ENTRY-ALAST.md (#100, $0): on 2-hop, A-last equals the entry's hit rate, and a second entry's
upper bound is +.064 for twice the passages. Script `srbf.py`. Cap $0.30. Serves Sirsh's 17:07Z target, measured as
agreed: A-last, with the reader check AC beside it (SR-AC, #99).*

**Data.** MuSiQue train answerable 2-hop, `train-corpus.jsonl` and `graph-train-pc.jsonl`: positions 608 onward of
SR-BX's seed-1341 permutation, minus every 2-hop question SR-BS and SR-AC used. 'fresh' is the first 150; stage 0 the
next 4. No Jev quantity has been computed on these.

**Arms.** Both start from Jev's 20-passage entry request (ENTRY_TASK) and take the cheap step (nt_rescue), as SR-BE.
- **ONE:** the entry request's argmax e1, one step: returns {e1, s1}.
- **TWO:** also its runner-up e2 (ties by position), one step: returns {e1, s1, e2, s2}, deduplicated, in that order.

**Measures on the returned set.**
- **AC:** srac.py's reader request, unchanged (sentences of the set as options, title-prefixed; the chosen sentence holds
  the gold answer or an alias).
- **A-last:** the set contains the gold last-hop passage.
- The returned-set size.

**Primary. H-F: AC(TWO) − AC(ONE), paired bootstrap 95% CI, lower bound above 0.** The reader is the judge here
because the arm's price is extra passages, and SR-AC found extra passages cost a reader about 7 points. A-last alone
can't see that cost.

**Secondary.**
- A-last(TWO) − A-last(ONE).
- e1's hit rate (on either hop), and e2's hits when e1 misses.
- AC flips both ways.
- Input characters per question per arm.

**Predictions.**
- A-last(TWO) − A-last(ONE) about +.05: most of the +.064 upper bound, since a walk from a hop almost always reaches
  the answer passage.
- **AC(TWO) − AC(ONE) about 0** (−.02 to +.03). The A-last gain is offset by rival sentences in the larger set. H-F
  fails more likely than not.
- e1 on a hop about .89, as in SR-BE.

**What follows.** If H-F passes, the walk returns two entries' walks, reported to Sirsh as a hypothesis. If A-last rises
but AC doesn't, the reader cost of a larger set is confirmed, and the entry work turns to a better single entry rather
than more of them.

**Spend.** The dry run (random scores, `out/srbf-dry.txt`) estimates $0.071. Stage 0 (4 questions) first. Cap $0.30.

**Scope.** MuSiQue train 2-hop, one draw of 150, one reader.
