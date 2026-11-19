"""L1 diagnostic (not registered; reported as such): dev and test recall@5 of LQ at every grid point, so the chosen
θ's test rank among all 60 says whether dev selection learned or any θ would do; and which links carry LQ's PR hits.
    uv run --with scipy --with numpy python l1diag.py SCRATCH SDIR"""
import json, sys
import numpy as np
import l1
scr, sdir = sys.argv[1], sys.argv[2]
chosen = {c: tuple(v["fit"]["LQ"]) for c, v in json.load(open("out/l1-q.json")).items()}
for gname, sets in (("p8", ("cards", "prs")), ("mq", ("mq",))):
    rows = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gname}.jsonl")]
    g = l1.G(rows)
    for c in sets:
        dev, test = l1.load(scr, g, c)
        Fd = l1.Fmat(g, [q for q, *_ in dev], l1.load_s(sdir, "dev", c, g)); Ft = l1.Fmat(g, [q for q, *_ in test], l1.load_s(sdir, "test", c, g))
        dq = [(s, gi) for _, s, gi, _, _ in dev]; tq = [(s, gi) for _, s, gi, _, _ in test]
        res = []
        for th in l1.GRID:
            d = l1.mean_ok(l1.recall5(g.run([s for s, _ in dq], th, F=Fd)[0], dq))
            P = g.run([s for s, _ in tq], th, F=Ft)[0]; t = l1.mean_ok(l1.recall5(P, tq))
            res.append((th, d, t))
            if th == chosen[c]: Pc = P
        ts = sorted(r[2] for r in res); ct = [r for r in res if r[0] == chosen[c]][0]
        q = [r for r in res if r[0] == l1.UNI][0]
        rho = np.corrcoef([r[1] for r in res], [r[2] for r in res])[0, 1]
        print(f"{c}: chosen {chosen[c]} dev {ct[1]:.3f} test {ct[2]:.3f}; Q(uniform θ) dev {q[1]:.3f} test {q[2]:.3f}; "
              f"test over 60 θ: median {np.median(ts):.3f}, max {ts[-1]:.3f}, chosen ranks {60 - ts[::-1].index(ct[2]) if False else sum(x > ct[2] for x in ts) + 1}/60; dev–test corr {rho:.2f}", flush=True)
        best = sorted(res, key=lambda r: -r[2])[:3]
        print("   best on test: " + "; ".join(f"{r[0]} dev {r[1]:.3f} test {r[2]:.3f}" for r in best))
        if c == "prs":
            # how chosen-θ LQ's gold hits relate to the seeds: an owned next/near link of a seed, a shared key, or neither
            kinds = {"next": 0, "near": 0, "key only": 0, "2+ hops": 0}
            for ci, (s, gi) in enumerate(tq):
                p = Pc[:, ci].copy(); p[s] = -1; top = set(np.argpartition(-p, 5)[:5])
                for x in (gi - set(s)) & top:
                    tid = g.ids[x]
                    if any(tid in rows[u]["next"] for u in s): kinds["next"] += 1
                    elif any(tid in rows[u]["near"] for u in s): kinds["near"] += 1
                    elif set(rows[x]["keys"]) & set().union(*(rows[u]["keys"] for u in s)): kinds["key only"] += 1
                    else: kinds["2+ hops"] += 1
            print(f"   PR LQ gold hits by link to a seed: {kinds}")
