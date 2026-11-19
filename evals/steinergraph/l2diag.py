"""L2 diagnostic (bill's suggestion, M-20261119-160437-972f; NOT registered, run after L2 was scored), $0.
At a fixed θ (uniform Q, and L2's LC), does per-question coherence track per-question recall@5 on test?
Positive: coherence is also a per-question confidence signal. Near zero: a corpus-level objective only.
    uv run --with scipy --with numpy python l2diag.py SCRATCH SDIR"""
import json, sys
import numpy as np
from scipy.stats import spearmanr
import l1, l2

scr, sdir = sys.argv[1], sys.argv[2]
fit = json.load(open("out/l2.json"))
for gname, sets in (("p8", ("cards", "prs")), ("mq", ("mq",))):
    rows = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gname}.jsonl")]
    g = l1.G(rows); W, s, m2 = l2.strength(rows, g)
    for c in sets:
        _, test = l1.load(scr, g, c)
        St = l1.load_s(sdir, "test", c, g)
        ts = [x for _, x, *_ in test]; tq = [(x, gi) for _, x, gi, _, _ in test]
        Ft = l1.Fmat(g, [q for q, *_ in test], St)
        for name, th in (("Q", l1.UNI), ("LC", tuple(fit[c]["theta"]["LC"]))):
            P, _ = g.run(ts, th, F=Ft)
            T = l2.tops(P, ts); rec = l1.recall5(P, tq)
            coh = [l2.coherence(W, s, m2, a, b) for a, b in zip(ts, T)]
            loc = [l2.local(W, a, b) for a, b in zip(ts, T)]
            hub = [s[b].mean() if b else 0 for b in T]
            keep = [i for i, r in enumerate(rec) if r is not None]
            r = np.array([rec[i] for i in keep])
            sp = lambda v: spearmanr([v[i] for i in keep], r)[0]
            hit = r > 0
            from p3 import auc
            ch = [coh[i] for i in keep]
            print(f"{c} θ={name} (n {len(keep)}, any gold in top 5 {hit.mean():.2f}): Spearman with recall@5: coherence {sp(coh):+.3f}, "
                  f"locality {sp(loc):+.3f}, hub {sp(hub):+.3f}; coherence AUC for any gold in top 5 "
                  f"{auc([x for x, h in zip(ch, hit) if h], [x for x, h in zip(ch, hit) if not h]):.3f}", flush=True)
