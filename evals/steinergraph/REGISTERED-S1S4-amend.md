# S1′ and S4′ (an amendment to REGISTERED-S1S4.md, registered before scoring): the most probable tree

*20 Nov 2026, bill, agreed with james (M-20261120-171946-07eb). It is shared with his S2b. $0.*

## Why amend

- On the registered 4 cases, the hop-count T\* is 1–3 passages beyond the seeds, but the ball within its depth holds
  484 to 21,082 passages.
- james's S2 found the same on test: the hop tree is the terminals alone for 90–99% of questions, and a cut never
  changes the hops.
- So hop count is saturated, the same saturation P2 found, in tree form. The original S1/S4 results stand and are
  reported as row 0.

## The amended T*

- **Link cost:** −log p(u→v), where p is the walk's one-step transition from a unit mass on u, as in l1.G.step:
  p(u→v) = h_v · W_uv / Σ_x h_x · W_ux.
  - W_uv = Σ over doors shared by u and v of width^θ1, plus the next/near weight.
  - h_v = (1 + degree_v)^θ2 · F_v.
- **Two references:**
  - **Graph-only (primary):** UNI (θ1 −1, θ2 0) with F = 1. This is the structure that drift and repair change.
  - **Walk-as-used:** L2's LC θ with search scores as F, as in S1.
- **T\*:** the minimum-cost arborescence from the seeds to every gold passage beyond them: directed, oriented away from
  the root, and attachable at any seed. Its cost is −log of the probability that one-step moves trace it.
- **Solver:** exact Dreyfus–Wagner on the directed passage graph (Dijkstra on the reversed links), with no smoothing.
  A link with W = 0 doesn't exist.

## Measures (unchanged except where noted)

- **S1′:** coverage, focus, order and departure, as registered, against the new T\*. Added: T\*'s cost in nats, and the
  cost of its cheapest single hop and of its dearest.
- **S4′:** as registered, against the new T\*'s edges. Added, because the original confounded search with walks: an
  edge counts as walk-shown only if a walk read its far end, rather than having it as a seed.
- **Row 0:** the hop-count results.

## Cases and aggregate

- **Cases:** the same 4 cases.
- **Aggregate:** over all dev, but only if one cards question solves in under a minute. The directed passage graph on
  cards has about 16M links. Otherwise it runs on the first 20 dev questions of each set, and the result says so. The minute and the 20 are a compute budget; no explanation rests on them.
