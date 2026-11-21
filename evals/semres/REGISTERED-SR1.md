# SR1: reach probability under one structure-and-semantics conductance (registered before the readout)

*21 Nov 2026, james, with bill's review (board M-20261121-131714). Brief: Sirsh, 13:15Z and 13:16Z. $0, token-free
generator, no Jev, no Claude data. Vector stage only; the Jev carry-over is a later registration.*

**Theory (net.py).** The walk is a resistor network.
- *Conductance.* A link u–v of type e has c_uv = w_e · g_e · g(u) · g(v).
  - The step is ∝ w_e · g_e · g(v).
  - c is symmetric, so the walk is reversible.
  - Stopping is a leak to ground, with α = .15 (L1's restart).
- *Reach.* h_v(a) is the voltage at a with v held at 1 V. It's exact: h = G / diag(G), with G = (I − (1−α)P)⁻¹.
- *Semantics.* The Bayes decider for the generator: log g = DIM · μ · cos, the equal-variance likelihood ratio.
  - For nodes, μ is the gap in mean cos between the landing passage's topic and the rest.
  - For edges, μ is the gap between the best relation and the others.
  - Both are measured on the world. w_e = 1 for every edge type.
- *Inductance (edge walk).* The state is the link just taken. The step v → w is weighted P[v, w] · exp(DIM · μ_nn · cos(v − u, w − v)).
  - The walker keeps the direction of its semantic displacement.
  - Reversing the direction is dear.
  - μ_nn is the same Bayes unit, measured on the world.

**World (gen.py).** The parameters in the file header are fixed before the readout. There are 4 seeds, each with all
four case types: A semantic, B bridge, C hub lure, D cluster lure.

**Gate.** The exact h must match 20,000 Monte Carlo walkers within 3 binomial s.d. on b, a and the top 10, on seed 1
case B, both for structure only and for the combined conductance.
- It passed: max 1.41 and 1.61 s.d.
- It can fail: walkers run at α = .20 miss b by 20 s.d.

**Seen before registering.** The gate's case shows h(b) = .85 and h(a) = .0005 under comb. The walker returns from b to
s, because s looks like the question, so the answer is rarely hit. I disclose it because it changes the prediction.

**Readout (sr1.py).** The landing passage is s. For each of the 16 world-case pairs, the rank of a (and of b) among
all other passages under:
- struct
- sem (cos only, no graph)
- comb (h)
- comb@25 (hit by the walk's 25-step budget)
- comb+L@25

It also reports hit-by-25 at a and τ (steps to reach 1 − 1/e of the hit-by-25 value).

**Pass (one formula, no per-case setting).** comb, or comb+L, ranks a in the top 5 (the walk's read budget) in at least
3 of 4 seeds for every case type.

**Predictions.**
- sem gets A and fails B–D.
- struct fails C.
- comb gets A and probably fails B–D, because the back-current to s keeps the walker off the second hop.
- comb+L raises hit-by-25 at a in B–D, because reversal is dear, and helps less in A.
- If comb fails and comb+L passes, the theory's content is this: a reversible conductance network can't price a
  multi-hop chain, and the inductance term (direction memory) is what does.
