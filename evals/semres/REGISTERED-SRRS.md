# SR-RS (registered 22 Nov, before scoring): does a unit-free reward (a door's success rate) beat SR-BC's fixed point?

*bill. Design DESIGN-REWARD-SCALE.md, revised after james's review. Script `srrs.py`. $0, no Jev.*

**Serves.** Sirsh's "define good, measure it, let dreaming converge toward it", with no magic constants. SR-BC's
weighting (1 + r) fixes one pass's reward at one unit of base door strength; this replaces the unit with a measured rate.

**Data, split, walk.** SR-BC's, unchanged: MuSiQue train 2-hop, learn half 652, test half 459, the structural walk,
the gold-pair stand-in on the learn half only.

**Weight.** For each membership (passage, key): n = learn walks that used it (both ends of every shared key the step
crossed), w = how many of those succeeded, ρ = W/N, the learn success rate of the current walks.

    m(p, k) = (w + 2ρ) / ((n + 2)ρ)          S_m[e, v] = Σ_k m(e, k) · m(v, k) / (df_k − 1)

n = 0 gives 1. The prior strength 2 is Laplace's convention.

**Arms.** unweighted; **T*** (SR-BC's fixed point, must reproduce .418); **RATE** (successes and failures); **RATE-W**
(successes only, n = w, so a door can only rise). Each RATE arm iterates: weights from all learn questions' current
walks, re-walk, until the tuple of walks repeats. Period 1 is a fixed point; a cycle's test arm is the mean of its
multipliers.

**Primary.** Both hops on the test half, **RATE − T***, paired bootstrap 95% CI. H-RS passes if the lower bound is
above 0. **Lost walks are the main readout**: flips against unweighted and against T*, both ways.

**Secondary.** RATE − unweighted; RATE-W − T*; RATE-W − unweighted; RATE − RATE-W (do failures as evidence help?);
the iteration's passes, period, and per-pass counts of memberships with m below and above 1.

**Predictions.**
- RATE − T* about 0 to +.01; H-RS is unlikely to pass. Most memberships have n = 1, so RATE is close to "boost
  successes about 1.4×, cut failures to .67×", and the boost side is T*'s with a different scale.
- RATE loses a few test walks (1–4) that T* kept, through down-weighted failure memberships shared with test pools.
- RATE-W ≈ T*.
- RATE reaches a fixed point in 2–3 passes; a cycle wouldn't surprise me (the update is no longer monotone).

**What follows.** If RATE ≥ T* without losses, the success rate replaces (1 + r) as the reward: same result, no unit.
If RATE loses walks, failures should not lower doors, and RATE-W is the unit-free form. Either way nothing goes to
production.

**Scope.** As SR-BC.
