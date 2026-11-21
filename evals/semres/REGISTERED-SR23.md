# SR (2), (3) and storage: probes, collision and direction memory (registered before any run)

*21 Nov 2026, bill. Brief: Sirsh, 13:15Z and 13:16Z. World and solver: james's `gen.py` and `net.py` (89e9261), unchanged.
Code: `sr23.py` and `sr23core.py`. Output: `out/sr23.{txt,json}`. $0, token-free, no Jev, no Claude data, vector stage
only.*

## Setting

- **Worlds.** There are 4 world seeds. Each seed has all four case types: A (semantic), B (bridge), C (hub lure) and D
  (cluster lure). That makes 16 world-case pairs.
- **Walks.** Every walk uses the walk's own budget: 25 steps (L1's ITERS) and restart α = .15. Neither is chosen here.
- **Arms.**
  - comb: the node walk under net.conductance, james's Bayes conductance.
  - comb+L: net.edge_walk, james's direction memory.
- **Landing.** Each probe lands on its search top 1 (argmax cos).

## Probes

james's probes:
- x: the whole question;
- s+r1: find the bridge;
- r2: the bare second relation.

I add one more, **r2+type**: R[r2] plus the centroid of the answer topic's other passages. This assumes the questioner
knows the answer's type ("which country…") but not the answer. Real decomposed questions carry the type.

The bare r2 probe is kept. Its cos to every passage is near 0, so its landing passage is essentially random, and it shows
the blind case.

The probe set for (2) and (3) is {s+r1, r2, r2+type}. A second readout drops r2+type, so the result doesn't depend on my
added assumption alone.

## Readouts, per world and case

- **(2) Equal mass.**
  - Hit-by-25 at a for x alone.
  - Hit-by-25 at a for the probes, P = 1 − Π_k (1 − h_k(a)/k). Each probe is launched with probability 1/k, so the
    expected number of walkers is 1, as for x.
  - Both under comb and under comb+L.
- **(3) Collision against coverage.**
  - Rank of a among all passages except the landings, under each of:
    - OR, 1 − Π(1 − h_k);
    - mean pair collision h_i·h_j;
    - collision over its degree null, log(col / col_null), where the null lands uniformly on passages with the landing
      passage's link count.
  - P(all gold {s, b, a} reached), under OR and under collision (≥2 probes reach each gold).
- **(L) Storage.**
  - Expected visits to D's lures within 25 steps from x's landing, comb against comb+L.

## Bars

Each bar needs ≥3 of 4 seeds per case type.

- **(2)** Probes beat x at a under comb+L in each of B, C and D. A is reported only.
- **(3)** In B, collision ranks a worse than OR. This is yesterday's single-chain miss, reproduced where the mechanism is
  known.
- **(L)** In D, +L lowers the lure visits.

## Predictions

- **(2)**
  - Fails with the blind probes alone, by construction: r2 lands at random.
  - Passes with r2+type in B and C.
  - D is uncertain, because the lure cluster looks like x and like s+r1.
- **(3)** Passes. The chain s → b → a is reached by one probe per hop, so the probes don't collide at a.
- **(L)** Passes. The lures form a clique, and reversing inside it is dear.
- **Overall.** Coverage (OR) is the right reading of coherence for a chain. Collision is right only where the gold is a
  meeting point, which is the comparison-question shape.
