# CS: coherence as surprising convergence (registered before any run)

*20 Nov 2026, bill and james, from Sirsh's steer M-20261120-223736-c1af. $0, no Jev, no Claude data, nothing fitted.*

Coherence is things that had no reason to agree converging anyway. Agreement inside a homogeneous cluster isn't
coherence, and neither is convergence through a generic hub. `cs.py` holds the one measure both of us use.

## The measure

- **p_i.** L1's walk from seed i alone, with the question's θ, F and ITERS. The walk is linear in its start mass, so
  the question's walk is the sum of these per-seed walks.
- **q_i.** The same walk from a uniform mass over every passage with seed i's link degree. The link degree counts
  keys of width 2–100, Beside and Near, as in `s2.links`. q_i is the exact mean of p_i over degree-matched random
  seeds. If a degree has no other passage, the class adds the nearest degree that has one.
- **lift_ij(v).** log p_i(v)p_j(v) − log q_i(v)q_j(v). This uses independent draws for i and j.
- **A_ij.** Σ p_i p_j / Σ q_i q_j over the scored set. It says how much the pair agrees everywhere, so it catches twin
  seeds. cs_ij = lift_ij − log A_ij.
- **The scored set.** Non-seed passages that every seed's walk reaches, with no epsilon. The count of dropped
  passages is reported.
- **Pairs.** Each passage is scored both by its mean over pairs and by its max over pairs.
- **A note on A.** Within one question, −log A_ij is a constant for each pair. So cs_mean ranks passages exactly as
  lift_mean does, and A changes only the max arm and any comparison across θ or graphs, which is Q1's use.

## Q2 (bill): does CS line up with gold and T\* in the reference world?

The code is `csq2.py`, and its output goes to `out/csq2.json`.

**Cases.** Four dev questions: the first two qids in `tstarp-mq.jsonl` and the first two in `tstarp-cards.jsonl`
(S1′'s exact most probable trees). Each is run under both refs:
- graph-only, with UNI and no F, scored against the graph-only T\*;
- walk-as-used, with L2's LC θ and F, scored against that ref's T\*.

**The readout.** For each case and ref, over the scored set:
- AUC of each arm for gold beyond the seeds against the rest;
- AUC of each arm for T\*'s non-seed passages against the rest;
- Spearman correlation of each arm with link degree.

Arms: cs_mean, cs_max and lift_max, against these controls: walk mass P (the seed-union walk), L2's per-passage
coherence (links to the seeds ÷ the degree-product expectation, using L2's strength), and degree.

**Directional pass,** under graph-only: cs_mean or cs_max beats walk mass on gold AUC in ≥3 of 4 cases, and on T\* AUC
in ≥3 of 4. The arm that passes is named. If only cs_max passes, the claim is single-pair convergence, not diverse
seeds converging.

**Predictions (bill):**
- On MuSiQue, the second-hop gold is reached from one seed, so cs_mean ≤ walk mass there.
- cs_max may do better.
- On cards, adjacent cards converge from many seeds, so CS may beat P on T\* but not on gold.
- Overall, I expect a FAIL on gold for cs_mean, with the gate decided by cards.

## Q1 and Q3 (james)

These are registered in james's own section or file before they run. In short:
- **Q1:** do L3's β and S3's accepted links raise CS the way they raised loose coherence?
- **Q3:** CS as the reward in the repair loop. This runs only if Q1 and Q2 both pass directionally, and is
  registered jointly first.
