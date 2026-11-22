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

**What a test would ask.** Whether a second entry (the entry request's runner-up, walked one step) recovers the
off-hop questions at less cost than it adds. SR-BE's two-walk selector didn't help on both hops, but A-last is a looser
target: a second walk needs only to touch the answer passage. A $0 look on the cached pass requests can price it
before any registration.

**Scope.** MuSiQue train 2-hop, seen questions.
