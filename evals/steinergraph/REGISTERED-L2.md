# L2: coherence as a gold-free reward for the link weights (REM-1341)

*19 Nov 2026, james. Registered before the run. $0, no Jev. Follows Sirsh's 12:45Z note on REM-1341.*

L1 learned the link weights (θ1 width, θ2 doors, α restart) from dev gold. It passed on cards and PR titles.
In the product there's no gold: the reward has to come from what walks do. L2 asks whether a reward that needs no
gold recovers L1's gain. That reward is the seeds joining up with what they reach more tightly than chance.

**Reward (no gold, no chosen constant):** for question q under θ, let T be the top 5 beyond the seeds of the Q
spread (L1's Q: bill's search scores as target weight). Take R = seeds ∪ T. Link strength between two passages is
Σ 1/(df−1) over the keys they share (2 ≤ df ≤ 100, the graph as stored), plus 1 if they are Beside. Near is left
out: it's a wording door, which is likeness, not connection (Sirsh, 12:34Z, item 3). Let s_i be a passage's total
strength over the whole graph, and 2M = Σ s_i. Then:

**coherence(q, θ) = Σ_{i<j in R} w_ij / Σ_{i<j in R} s_i s_j / 2M**

That's the observed strength among R over its expectation under the strength-preserving null. Generic hubs have
large s_i, so they raise the expectation and can't fake coherence (Sirsh, 12:40Z). There's no width cap, unlike
P3b's ≤5. The θ grid is L1's, unchanged, so the arms compare.

**Arms, all scored on test recall@5 beyond the seeds (gold used only here):**
- **Q:** uniform θ with search target weights (L1's baseline).
- **LQ:** L1's gold-fitted θ, from out/l1-q.json.
- **LC:** θ maximising mean dev coherence. Ties go to the θ nearest uniform, as in L1.
- **LC-test:** θ maximising mean coherence on the test questions themselves. That's legitimate because the reward
  uses no gold, and it's the product's setting. Secondary.
- **LH (hub control):** θ maximising the mean strength s of T. If LH matches LC, the reward is only buying hubs.
- **LC-shuf (join control):** coherence with each question's T scored against another question's seeds (a fixed
  derangement). If LC-shuf matches LC, the reward isn't about joining this question's seeds.

**Bar.** PASS needs both of these:
1. LC − Q > 0 with its 95% bootstrap interval above 0 on at least one of cards and PR titles, the sets where LQ won.
2. LC − Q's interval isn't wholly below 0 on any set.

The controls are reported for the mechanism and don't gate the result. Also reported: the share of LQ's gain that
LC recovers.

**Prediction:** P3b's narrow coherence separated found from not-found on MuSiQue (.739) and PR (.653), but not on
cards (.535). So I expect LC to help on PR titles, and the 64 of 77 PR hits Beside a seed reward it directly. I
expect little on cards. On MuSiQue, L1 harmed, so I expect LC to land near Q.

**Postmortem:** every result gets one.
