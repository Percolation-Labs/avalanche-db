# J3 (registered before running): search later hops over the doors of what has been read

*19 Nov 2026, bill. $0: no Jev, no Claude, nothing fitted. Proposed by james (M-20261119-151820-c7f7) after Sirsh
declined beam 2 as a knob (M-20261119-150933-c7bc).*

## Why

J2's diagnostic found that hop 1's search puts its gold passage in the top 5 for .81 of questions, but later hops,
searched with Jev's fill substituted, manage only .45. A wrong or partial fill steers the next search off course, so
errors compound. The walk has a second route to the next hop that needs no fill: the links (doors) out of the
passages already read. If hop j's answer is in what was read, hop j+1's passage is usually one link away (P2: 79% of
MuSiQue gold pairs are directly linked). The hypothesis is that **searching the next sub-question among the
neighbours of what has been read recovers the later hops' search without a fill**.

## Setup (all fixed in advance; no constant is chosen here)

- MuSiQue test, the same 150 questions, MuSiQue's own decomposition, and later hops (j ≥ 2) only (247 sub-questions,
  as in J2).
- **Read set R:** the top 5 hits of every earlier hop. This is the same 5 used in J1, J2 and P2.
- **Doors:** the neighbours of R under L1's graph as it is (a shared key held by 2–100 passages, or next/near either
  way, as in P2's `adjacency`), excluding R itself.
- **Text:** the sub-question with `#k` removed (no fill).
- **Ranker:** Okapi BM25 over title + paragraph, with IDF over the full 21,100-passage corpus, at the textbook k1 1.2,
  b .75, not tuned. Tokens are lower-case alphanumeric runs.

## Arms

| arm | read set from | candidates | query text |
|---|---|---|---|
| **D** | its own chain (hop 1 from the probe's search, then D's hits) | doors of R | unfilled |
| **DO** (bound) | the gold passages of earlier hops | doors of the gold | unfilled |
| **B** (ranker control) | none | the whole corpus | unfilled |
| **F** (reference) | J2's Jev arm, recorded | the probe's search, whole corpus | Jev-filled (J2) |

- B separates the doors from the ranker: D − B is the effect of searching among doors rather than everywhere.
- F is J2's recorded later-hop rank, as already reported (.45 in the top 5).

## Measures

- **Primary:** the later-hop top-5 rate, i.e. the share of the 247 later sub-questions whose own gold passage is in
  that hop's top 5.
- **Secondary:** total recall at 10 reads, with seeds round-robin over the hop hits as in J1 and the uniform
  avalanche's top 5 beyond. This is compared with J2's J (.586) and blind (.504).

## Bars

- **Gate (before scoring D):** DO's later-hop top-5 rate must exceed F's by at least .05. If even gold reads don't
  lift the next hop through the doors, D cannot.
- **Bar:** D's later-hop top-5 rate minus F's is at least +.05, with the 95% paired bootstrap interval (over
  sub-questions, 2000 resamples, seed 0) above 0, and D − B above 0 likewise.
- **Reported, not barred:** total recall at 10 for D against J2 J and blind; D's rate split by whether R holds the
  previous hop's gold.

## Not tested

- Combining doors with a fill. That comes after, only if D passes and only as a mechanism, not a width.
- Any learned weights on doors. That is L1/L2, which is james's.
