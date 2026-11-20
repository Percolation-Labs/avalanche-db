# CS: surprise coherence, measure and Q1 (registered before any run)

*20 Nov 2026, james, with bill's review (board M-20261120-224120). Brief: Sirsh, 22:37Z. $0, no Jev, no Claude data.*

**The definition under test.** Coherence is convergence from things that had no reason to agree. Agreement inside a
homogeneous cluster doesn't count, and nor does a shared generic hub. So convergence is scored against a null for this graph.

**Measure (cs.py).**
- *Per-seed walks.* The walk is linear in its start mass, so a question's walk is the mean of one walk per seed, p_i.
  Each uses the walk's θ, β and F.
- *Null.* q_i is the same walk from a uniform mass on every other passage with seed i's door count (g.nd).
  - It is the exact mean over degree-matched random seeds, with no sampling.
  - If no other passage has that count, the class is the nearest count that has one.
  - q_i·q_j is the pair's null only for independent draws. Two draws from one class can coincide; that is negligible and ignored.
- *Pair surprise at v:* s_ij(v) = log p_i(v)p_j(v) / q_i(v)q_j(v), minus log A_ij in the "a" arms.
  - A_ij = Σ_u p_i p_j / Σ_u q_i q_j is the pair's agreement everywhere beyond the null, so twins score their cluster as expected.
  - Seeds are excluded from the scored v and from A's sums.
- *Reach rule.* v is scored only if every seed's walk reaches it. No epsilon is added; dropped passages are counted.
- *Four arms.* No A or with A (x or a), times the mean (geometric) or max over seed pairs (m or M).
- *A walk's CS* is the mean over its top 5 beyond the seeds.
- *No tuned numbers.*

**Q1 (james): does CS stop the gaming loose coherence allowed?** (csq1.py)
- **(a)** Cards dev, L2's θ: β = 0 against L3's fitted LC3 β. Loose coherence rose there and test recall fell .061.
- **(b)** MuSiQue dev+test: S3's drifted graph against it plus S3's 40 accepted links. Loose coherence rose by construction.
  Classes are fixed from the drifted graph, like the strength matrix.
- **Pass.** For each of (a) and (b), the "a" arm's mean B − A is ≤ 0, or its 95% bootstrap interval covers 0, where
  loose coherence rose. Four cases are printed first as the directional read.
- **Prediction.**
  - (a): the "x" arms rise or stay flat, because the null doesn't see twins. The "a" arms fall, because L3's β keeps the
    top 5 among adjacent cards, which twin seeds agree on everywhere.
  - (b): the "x" arms rise, because the links join co-read pairs and so manufacture convergence. The "a" arms rise less,
    and I'm unsure of the sign. A link between two read passages raises A_ij for the seeds behind them.

**Q2 (bill)** is gold and T\* alignment on the four S2c gate cases, against P, lift without A, L2 per-node coherence and
degree. It passes directionally on 3 of 4 cases beating P. bill registers it with his readouts.

**Q3 (joint)** uses CS as the reward in S3's loop. It is registered only if Q1 and Q2 pass.
