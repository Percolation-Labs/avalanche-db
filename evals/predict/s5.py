"""evals/predict/REGISTERED-S5.md: AUC of neighbourhood properties for 'the walk read gold beyond the seeds', and graph means.
    python3 s5.py DIR   (sp-{cards,prs,mq}.jsonl)"""
import json, sys
from statistics import mean, median

SETS = [("cards", "cards"), ("prs", "PR titles"), ("mq", "MuSiQue")]
PROPS = {"spectral gap": 1, "seed coherence": 1, "density (lower)": -1}
KEY = {"spectral gap": "gap", "seed coherence": "coherence", "density (lower)": "density"}


def auc(xs, ys):
    P = [x for x, y in zip(xs, ys) if y]; N = [x for x, y in zip(xs, ys) if not y]
    return sum(1.0 if p > n else .5 if p == n else 0.0 for p in P for n in N) / (len(P) * len(N)) if P and N else float("nan")


def main(d):
    R = {k: [json.loads(l) for l in open(f"{d}/sp-{k}.jsonl")] for k, _ in SETS}
    print(f"{'AUC, walk reads gold beyond the seeds':<40}" + "".join(f"{n:>12}" for _, n in SETS))
    hits = {}
    for p, s in PROPS.items():
        a = {k: auc([s * r[KEY[p]] for r in R[k]], [r["walk_gold_beyond_seeds"] for r in R[k]]) for k, _ in SETS}
        hits[p] = sum(v >= .65 for v in a.values())
        print(f"{p:<40}" + "".join(f"{a[k]:>12.3f}" for k, _ in SETS))
    nq = {k: f"{len(R[k])} ({sum(r['walk_gold_beyond_seeds'] for r in R[k])})" for k, _ in SETS}
    print(f"{'questions (walk found gold beyond seeds)':<40}" + "".join(f"{nq[k]:>12}" for k, _ in SETS))
    print("\ngraph medians (means)")
    single = {}
    for name, key in [("spectral gap", "gap"), ("seed coherence", "coherence"), ("density", "density"), ("H size", "n"),
                      ("gold in H", "gold_in_h"), ("gold conductance", "gold_conductance")]:
        m = {k: [r[key] for r in R[k] if r[key] is not None] for k, _ in SETS}
        mu = {k: mean(v) for k, v in m.items()}
        lo, hi = sorted([mu["cards"], mu["mq"]])
        out = mu["prs"] < lo - (hi - lo) or mu["prs"] > hi + (hi - lo)
        single[name] = out
        print(f"  {name:<18}" + "".join(f"{n} {median(m[k]):.3f} ({mu[k]:.3f})   " for k, n in SETS) + ("  ← PR titles outside" if out else ""))
    pred = [p for p in hits if hits[p] >= 2]
    print(f"\nPREDICTS (AUC ≥ .65 on two graphs): {pred or 'none'}")
    print(f"SINGLES OUT PR TITLES (question-free properties): {[n for n in ('spectral gap', 'seed coherence', 'density') if single[n]] or 'none'}")


if __name__ == "__main__":
    main(sys.argv[1])
