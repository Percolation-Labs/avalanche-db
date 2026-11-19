# P2: under the Steiner picture, what limits retrieval: where the seeds land (likeness) or moving between nodes (connection)?

*19 Nov 2026, bill. Registered before any scoring. $0, no Jev, nothing fitted. Sirsh's 12:34 and 12:36 notes
(M-20261119-123441-6d0b, M-20261119-123655-2e56). james takes the fixtures (1) and joins these rows on qid.*

**Setting.**
- The held-out test questions of P1 and L1: cards, PR titles, MuSiQue, with their recorded k=10 Jev walks
  (`floor/trace-*`) and gold.
- The graph is the one L1 used (`dream/d1/graph-{p8,mq}.jsonl`). Two passages are **linked** if they share a key held
  by 2–100 passages, or one lists the other as next or near.
- The seeds are search's top 5 (wave 0 of the recorded walk).
- **S** is the question's gold set. All gold counts here, including gold that is already a seed.
- d(a, b) is the fewest links from a to b, treated as undirected and capped at 6.

**Likeness: how the seeds land.**
- **Entry points:** the number of seeds in S.
- **Near seeds:** the number of seeds within one link of S.
- **Seed distance:** the median over S of the distance to the nearest seed.
- **Coverage:** the share of S within one link of some seed, i.e. seed spread over S.
- **Question to gold:** each gold passage's search rank and normalised BM25 score (P1's s), and the same for the
  oracle seeds below.

**Connection: moving once there.**
- **Compactness:** the mean d over pairs in S (|S| ≥ 2), and the share of pairs that are directly linked.
- **In-S step:** for each g in S, the probability that one uniform step (a door, then a target, as in P1's U) lands on
  another member of S. Averaged over S.
- **Control:** the same two measures on the target-shuffled graph (each key and each next/near list keeps its size,
  members drawn at random).

**Recall against budget.** The share of S read with k reads past the seeds, k ∈ {1, 3, 5, 10, 20}, when the reads
are U's top-ranked non-seeds. The recorded walk's recall (5 reads past the seeds) is the reference.

**Seed sets (MuSiQue only, which ships sub-questions).** Each set is 5 seeds, filled round-robin over sub-question
searches with duplicates skipped.
- **Single:** search's top 5 for the question, as recorded.
- **Decomposed, blind:** MuSiQue's sub-questions with each `#k` placeholder removed, which a decomposer could produce.
- **Decomposed, filled:** `#k` replaced by hop k's gold answer, an upper bound.
- **Oracle:** 5 of search's top 50 for the question, chosen greedily to cover the most of S within one link.

For each set: coverage, entry points, and **total recall at 10 reads**, which is the 5 seeds plus U's top 5 beyond
them.

**Percolation** (Sirsh's 12:36 point 3, and coherence against chance from 12:40) moved to james before any scoring
(amended 12:45, M-20261119-123837-a58a). He scores it on the same rows.

**Bars (test; 95% paired bootstrap, 2000 resamples).**
1. **Compactness:** among questions with |S| ≥ 2 and at least one near seed, U's recall@5 is at least .10 higher in
   the most compact third (by mean d) than in the least compact third, with its interval above 0, on at least two
   sets.
2. **Entry points:** U's recall@5 rises with the number of near seeds (0, 1–2, ≥3). Reported, not barred.
3. **Likeness against connection, per set:** the counterfactuals are reported, not barred.
   - Perfect likeness: the mean recall of questions with at least one entry point.
   - Perfect connection: the share of questions with at least one entry point.
   - Each question gets a label: likeness-limited (no near seed), connection-limited (a near seed, but recall@5 < .5)
     or reached.
4. **Decomposition:** blind-decomposed seeds beat single seeds by at least .03 in total recall at 10, with the
   interval above 0. Filled and oracle seeds are reported as bounds.

**Postmortem:** every result gets one.
