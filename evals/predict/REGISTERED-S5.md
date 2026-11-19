# S5: does a spectral property of the seeds' neighbourhood predict the walk, or single out PR titles?

*19 Nov 2026, bill. Registered before any run. $0. Stage 2 of S4 (REGISTERED.md): S4 left the PR-titles gap unexplained.*

**Neighbourhood H, per test question:** search's 5 seeds and every target of their doors (one door away), up to 3,000
passages. Its edges are door co-membership (u lists t through some door), symmetrized and unweighted.

**Properties, all question-free except the last, which uses gold and is a diagnostic, not a predictor:**
1. **Spectral gap:** λ2 of H's normalized Laplacian, by deflated power iteration on the lazy walk (1,000 steps). Low
   means H splits into loosely joined parts.
2. **Seed coherence:** the share of the lazy walk's stationary mass after 3 steps from the seeds that stays in the seeds'
   own doors. High means the seeds point the same way.
3. **Density:** edges per node in H.
4. **Gold conductance:** the edges leaving the gold set (within H) divided by its volume (diagnostic only).

**Outcome:** whether the recorded k=10 walk read any gold beyond the seeds.

**Read-outs:**
- Per graph, the AUC of properties 1–3 for the outcome. Directions are fixed now: higher gap, higher coherence and
  lower density are easier.
- The graph means of 1–4.

**Bar:**
- A property predicts if its AUC is at least .65 on two graphs.
- It singles out PR titles if PR titles' mean lies outside the range of the other two graphs' means by more than the
  gap between those two.
- Neither bar is met → structure, spectral included, doesn't explain the PR-titles gap, and the structure line reports
  that to Sirsh as its finding.

**Postmortem:** every result gets one.
