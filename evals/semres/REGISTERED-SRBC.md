# SR-BC (registered 22 Nov, before scoring): can reward-driven bridge weighting reach a fixed point, and does that point help?

*bill. Follows SR-BR (#87). Script `srbc.py`. $0, no Jev. Sirsh at 15:52Z: carry on with the update for reward-driven
bridge weighting that can reach a fixed point.*

**Why.** SR-BR's update added each rewarded walk's events again on every pass. A walk that succeeded on pass 1 was
rewarded again on pass 2 and 3, so the weights only grew (R3's top weight was 3× R's). That measures accumulation, and
it has no fixed point. "Dreaming converges toward good" needs an update whose weights stop moving.

**Two updates, no new constants.** Everything else is SR-BR unchanged: the data, the split, the walk, the event
(1/|S_k| to both ends of each shared key), and the gold-pair reward stand-in on the learn half only.

- **T (replace).** r_{p+1} = T(r_p), where T(r) is the sum of the events of every learn walk that succeeds *under r*.
  Each pass rebuilds the weights from scratch, so a walk's reward counts once, at the walk it makes now.
  - T(0) is SR-BR's R.
  - A fixed point is r* = T(r*): the weights reproduce exactly the successes that made them.
  - The iteration runs until a weight state repeats, which must happen since there are finitely many success sets.
  - A repeat of the previous state is a fixed point. An earlier repeat is a cycle, and the test arm is then the mean of
    the cycle's states.
- **U (first reward only).** Q_{p+1} = Q_p ∪ {learn questions that succeed under r(Q_p)}. r(Q) sums, for each question
  in Q, the events of the walk it made when it first succeeded.
  - Each question is rewarded at most once, so this is SR-BR's "reward only walks that changed outcome".
  - Q only grows, so U stops within 652 passes, when a pass adds no question.

**Primary.** Both hops on the test half (459 questions), **T* − unweighted**, paired bootstrap 95% CI.
- **H-C1:** T reaches a fixed point (period 1), not a cycle.
- **H-C2:** the lower bound of T* − unweighted is above 0.

**Secondary.**
- T* − R (pass 1) and U* − R: does iterating add anything over one pass?
- U* − unweighted.
- T* − R3 (SR-BR's accumulating arm).
- Per pass: learn-half success, the size of the success set, the questions entering and leaving it, and the relative
  weight change.
- Flips against unweighted (gained and lost) for T*, U* and R, as in SR-BR's readout.

**Predictions.**
- **H-C1 passes in 2–4 passes.** R lifted learn success only from .463 to .477, so few walks change, and each change
  only adds or drops a few memberships.
- T* is close to R: T* − R about 0, T* − unweighted about +.015 to +.02. H-C2 is about a coin flip, since R's +.017 had a
  lower bound of +.007, and T* should keep most of it.
- U* is slightly above R (it keeps the rewards of walks that later broke), about +.005, not significant.

**What follows.** If H-C1 and H-C2 pass, the fixed-point update replaces SR-BR's R as the dreaming-reward proposal: one
pass is then justified as the operator, rather than chosen. If T cycles, the postmortem says which walks flip and why,
and U (monotone) is the fallback. Nothing goes to production; any switch-on is Sirsh's.

**Scope.** MuSiQue train 2-hop, the structural walk, the gold stand-in for a confirmed answer, two update rules, 459
test questions.
