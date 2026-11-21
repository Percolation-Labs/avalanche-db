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

## Amendment 1 (after run 1, before any rerun)

**Run 1 saturated, and nothing in it is a result.** It is kept as `out/csq2-run1.{txt,json}`.
- Every arm, plain walk mass P included, scored AUC .996–1.000 for gold and T\* on all four cases.
- The reach set has 21–47k passages, and nearly all of them are far from the seeds. AUC against them measures "near the
  seeds", and every arm knows that.
- In all four cases, T\*'s non-seed passages are exactly the gold, because the gold hangs directly off a seed. So these
  first cases are also the easy ones.

**The readout is replaced by absolute rank.** For each gold passage beyond the seeds, its rank under each arm among the
reach set (1 is best). S2c and S3 read the walk the same way.
- Per case, the summary is the mean log rank over that case's gold.
- The same is reported for T\*'s non-gold passages, where any exist.

**Cases are added where the walk misses.** The four run-1 cases stay, reported only. Four miss cases are added: for
each set, the first two qids in `tstarp-{c}.jsonl` (file order) where some gold beyond the seeds is outside the
walk-as-used P's top 5 beyond the seeds. These are the questions where a coherence signal could add something the walk
lacks.

**The directional pass is now judged on the four miss cases, under graph-only.** am or aM must give a lower mean log
gold rank than walk mass P in ≥3 of 4. The arm is named, and the walk-as-used ref is reported beside it.
