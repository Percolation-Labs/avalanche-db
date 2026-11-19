# P1: how well can a question's Steiner graph be predicted from the question and its seeds?

*19 Nov 2026, bill. Registered before any run. $0, no Jev. Sirsh's 10:22 framing (M-20261119-102233-4cd7): a
question's Steiner graph is its gold passages and the connections between them that a walk seeded from the question
can reach. The task is to predict which passages the avalanche from the seeds reaches with high probability.*

**Setting:**
- Held-out test questions for cards, PR titles and MuSiQue: the recorded k=10 walks of evals/width, with their gold.
- The seeds are search's top 5, as in the walk.
- Every predictor scores passages that are not seeds.

**Predictors (all fixed, nothing fitted):**
- **S, search:** BM25 order beyond the seeds (ranks 6, 7, …), i.e. what search alone would read next.
- **U, uniform avalanche:** PPR from the seeds (α .15, push to 1e-4) on the walk's uniform step: a door at random,
  then a target at random. This is question-free beyond the seeds.
- **Q, question-aware avalanche:** the same PPR, but a step from u to t through door k has weight
  (1 / width(k)) · (s(t) + .01), where s(t) is t's BM25 score for the question divided by the question's top score
  (0 for passages search doesn't return). The question steers the avalanche toward passages that match it. The .01
  keeps non-matching passages reachable. It is fixed here and not tuned.
- **Q on shuffled links:** Q with each door's targets drawn at random at the same widths (the structure control).

**Measures, on test:**
1. **Primary, recall@5:** the share of a question's gold beyond the seeds that is in the predictor's top 5. Five
   is the walk's budget past its seeds. Mean over questions that have gold beyond the seeds.
2. Recall@20, and the mean rank of the best gold passage.
3. **Reference, not a predictor:** the recorded Jev walk's recall of gold beyond the seeds in its 5 reads past them.
4. **The avalanche, wave by wave:** for U and Q, the walk distribution from the seeds after 1, 2 and 3 steps, without
   restart. At each step: the mass on gold, and the share of questions whose best gold passage is in the top 10.

**Bar:**
- Q predicts the Steiner graph beyond search if its recall@5 beats S by at least .03 on at least two sets, and beats U
  and Q-shuffled on those sets.
- Its comparison with the Jev walk is reported, not barred: the walk chooses with Jev, and Q chooses with no model at
  all.

**Postmortem:** every result gets one.
