# Entry look on A-last (22 Nov, $0, post hoc on SR-BE's cache): the step finds the answer passage; the entry caps it

*bill. Script `entry_alast.py`, output `out/entry-alast.txt`; the walks' A-last ("hop2") is from SR-BE's own
`out/srbe-fresh.txt`. 300 fresh 2-hop questions, already scored in SR-BE, so this prices an idea and isn't a result.
Serves Sirsh's 17:07Z target: the answer passage in what the walk returns (A-last).*

| returned set (2-hop) | passages | A-last |
|---|---|---|
| Jev's entry request, top 1 | 1 | .283 |
| Jev's entry request, top 2 | 2 | .603 |
| Jev's entry request, top 3 | 3 | .737 |
| cosine entry × cheap step | 2 | .837 |
| **Jev's entry × cheap step** | **2** | **.893** |
| Jev's entry × Jev's full step | 2 | .887 |
| *Jev's entry lands on a hop (either)* | | *.893* |

- **Walking beats retrieving.** For the same two passages, the entry plus one step reaches the answer passage .893 of
  the time; the entry request's own top 2 reaches it .603. The entry request ranks the answer passage second (median),
  but it is asked "what should be read first", and the answer passage is often not what it puts second.
- **On 2-hop, A-last equals the entry's hit rate.** Jev's entry is on one of the two hops in .893 of questions, and the
  walk's A-last is .893. Once the entry is on a hop, the step reaches the answer passage essentially always; every
  A-last loss is an entry that missed both hops.
- **So the entry is the lever on 2-hop, and it is capped by entry misses.** The look-2 anatomy (RESULT-ENTRY-LOOK2.md)
  said most misses are a hop's neighbour (21 of 48 for cosine) or a namesake (13). On chains, james's SR-BH reported
  25 of 200 entries off-chain, lost by every arm.

**A second entry, priced ($0).** The entry request's argmax is off both hops in 32 of 300 questions. Its runner-up
is on a hop in 19 of those (its third in 15). So walking the top two entries one step each (four passages) would put an
entry on a hop in .957 of questions against .893: **an upper bound of +.064 on A-last, for twice the passages**.

- The price isn't only input. SR-AC found that extra non-answer passages cost a reader about 7 points (answer passage
  alone .900, with chain-sized noise .827). Doubling the returned set to recover 6% of questions could lose as much at
  the reader as it gains in A-last.
- So a test must score the returned set with the reader (AC) as well as A-last, and compare one entry (2 passages)
  against two (4 passages) on both. A gate that walks the second entry only sometimes would need a signal, and every
  signal tried so far (SR-BE's selectors) is a choice between walks, not a reason to add one.

**Scope.** MuSiQue train 2-hop, seen questions.
