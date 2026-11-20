# CS Q2: does surprise coherence line up with gold and T\*? (registered before any run)

*20 Nov 2026, bill. Measure: `cs.py`, as in REGISTERED-CS.md (james, 1a56609). Code: `csq2.py`. Output:
`out/csq2.json`. $0, no Jev, no Claude data, nothing fitted.*

## Cases

There are four dev questions:
- the first two qids in `tstarp-mq.jsonl`;
- the first two qids in `tstarp-cards.jsonl`.

These have S1′'s exact most probable trees, which `tstarp-*.jsonl` holds for every dev question. That's why they
replace the four S2c gate cases named in REGISTERED-CS.md. The S2c cases are test questions, and no exact tree has been
built for test. A directional slice also shouldn't touch test.

Each case runs under two refs:
- graph-only: UNI, no F, scored against the graph-only T\*;
- walk-as-used: L2's LC θ with F, scored against that ref's T\*.

## Readout

Each case and ref is scored over the passages CS scores (the reach set):
- the AUC of each arm for gold beyond the seeds against the rest;
- the AUC of each arm for T\*'s non-seed passages against the rest;
- the Spearman correlation of each arm with degree (g.nd).

The arms are am, aM and xM; xm is listed as am because within one question −log A_ij is a constant per pair, so xm and am
rank passages identically. They're compared against:
- walk mass P, the seed-union walk;
- L2's per-passage coherence: L2-strength links to the seeds ÷ the degree-product expectation;
- degree.

Every case prints its count of unreached passages and the range of A_ij.

## Directional pass

The pass is judged under graph-only. am or aM must beat walk mass:
- on gold AUC in ≥3 of 4 cases;
- on T\* AUC in ≥3 of 4 cases.

The result names which arm passes. If only aM passes, the claim is single-pair convergence, not diverse seeds
converging. walk-as-used is reported and doesn't gate.

## Predictions (bill)

- **MuSiQue:** the second-hop gold is reached from one seed, so am ≤ P on gold there. aM may do better.
- **Cards:** adjacent cards converge from many seeds, so CS may beat P on T\* and not on gold.
- **Overall:** a FAIL on gold for am, with the gate decided by cards.
