"""J2 bar: J2's J against J1's J, paired per question.    python j2pair.py SCRATCH J1DIR J2DIR"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l1 import G, load, UNI  # noqa: E402
scr, d1, d2 = sys.argv[1:4]
g = G([json.loads(l) for l in open(f"{scr}/dream/d1/graph-mq.jsonl")])
_, test = load(scr, g, "mq"); order = [q for q, *_ in test]; gold = {q: gi for q, _, gi, _, _ in test}
def tot(d, ch):
    R = {r["qid"]: r for r in map(json.loads, open(f"{d}/j1-{ch}.jsonl"))}
    seeds = [[g.ix[x] for x in R[q]["seeds"] if x in g.ix] for q in order]; P, _ = g.run(seeds, UNI); out = []
    for c, (q, s) in enumerate(zip(order, seeds)):
        p = P[:, c].copy(); p[s] = -1; top = [int(t) for t in np.argsort(-p)[:5] if p[t] > 0]
        out.append(len(gold[q] & (set(s) | set(top))) / len(gold[q]))
    return np.array(out)
a, b = tot(d2, "J"), tot(d1, "J"); d = a - b; r = np.random.default_rng(0)
bs = [d[r.integers(0, len(d), len(d))].mean() for _ in range(2000)]; lo, hi = np.percentile(bs, [2.5, 97.5])
print(f"J2 J {a.mean():.3f} − J1 J {b.mean():.3f}: {d.mean():+.3f} [{lo:+.3f}, {hi:+.3f}]; questions up {int((d > 0).sum())}, down {int((d < 0).sum())}")
print("J2:", "pass" if d.mean() >= .02 and lo > 0 else "fail (J2 − J1 bar)")
