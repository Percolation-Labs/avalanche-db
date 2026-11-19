# L1: can dreaming learn, from past walks, a structure on which the avalanche reaches a question's Steiner graph?

*19 Nov 2026, james. Registered before any run. $0, no Jev. Builds on P1 (REGISTERED-P1.md, bill) and Sirsh's
10:22Z and 10:25Z messages (M-20261119-102233-4cd7, M-20261119-102537-f47f).*

**The online computation this stands in for.** Given unlimited time, a walk for one question would score every
passage reachable from its seeds against the question, and spread probability from the seeds along the links that
lead to matching passages. That is P1's Q: PPR from search's top 5, where each step to t through door k weighs
(1/width(k))·(s(t)+.01). Q is the online prior. Dreaming can't see the question. It can only learn, from past
questions' attempts and outcomes, which structure the avalanche should favour, and store that as per-link weights
(attributes on memberships and owned doors). L1 asks whether those learned weights raise the probability of reaching
held-out questions' Steiner graphs, used alone or under Q.

**Setting:** P1's, unchanged.
- The graphs are p8 (cards, PR titles) and MuSiQue.
- Seeds are search's top 5.
- Splits come from evals/width's recorded k=10 walks. Dev is 100 / 65 / 101 questions; test is 150 / 93 / 150.
- Gold beyond the seeds is the target.
- The history is the dev questions only: seeds, and gold as the outcome. Test is never seen by any fit.

**Learned weights (structure only; never kind, never text).** A step from u through door k to target t has weight
exp(θ1·ln width(k) + θ2·ln(1+doors(t))), normalised over u's doors and then over k's targets, and teleports with
probability α.
- This is bill's V1 weight form plus α.
- The fit chooses θ1 ∈ {−3, −2, −1, 0}, θ2 ∈ {−1.5, −1, −.5, 0, .5} and α ∈ {.15, .3, .5}: 60 points per graph.
- The reward is dev's mean recall@5 of gold beyond the seeds, P1's primary measure. Ties go to the point nearest
  uniform (θ = (−1, 0), α = .15).
- Fitting with reach as the reward, not the gold-door AUC, is the one change from V1. It scores what the walk
  reaches, so cutting a gold door can't score well (D3's lesson).

**Arms on test:**
- S (search ranks 6+), U (uniform PPR) and Q, all as P1 defines them.
- **L:** U's avalanche with learned θ, α; question-blind beyond the seeds.
- **LQ:** Q with learned θ, α (the target weight becomes (s(t)+.01)·exp(θ2·ln(1+doors(t)))). θ is fitted separately
  for LQ on dev under Q.
- **H, history prior (reported, not barred):** each passage's count of dev questions it was gold for, as a node
  attribute, multiplied into LQ's target weight as (1+count). This is the plainest "remember what past questions
  needed". Test gold that was dev gold (19/294 cards, 0/266 PR, 60/331 MuSiQue) is stated beside it.

**Controls:**
- **Shuffled reward:** L and LQ fitted with each dev question's gold swapped for another dev question's gold on the
  same graph. If shuffled fits match, the weights learn the graph, not the outcomes.
- **Shuffled links:** P1's, for Q and LQ.

**Measures on test:** P1's.
- Recall@5 of gold beyond the seeds is primary. Recall@20 and best-gold rank are secondary.
- Each gold node's reach mass after 1, 2 and 3 steps for U, L, Q and LQ. This is the avalanche, and shows where the
  learned weights move mass.
- 95% paired bootstrap over questions for each difference.

**Bar.** Dreaming's learned structure recovers a benefit if either holds:
- (i) LQ − Q ≥ +.03 recall@5 on at least two sets, with the bootstrap interval above 0, and LQ beats LQ-shuffled-
  reward on those sets.
- (ii) L closes at least half of the Q − U gap on at least two sets (the question-blind pre-computation recovers the
  online computation's benefit), and beats L-shuffled-reward there.

If both fail, the learned weights are a null for the Steiner reach, as they were for the door AUC on cards and
MuSiQue. Next is the history prior, if H shows a gain beyond its overlap.

**Postmortem:** every result gets one. If a gain shows on one set only, it is reported as corpus-specific, not
claimed.
