"""P3 (REGISTERED-P3.md), $0: percolation signals of a walk's read set (seeds joined, component, coherence over a
degree null, raw links, mean degree) as evidence that gold beyond the seeds was found.
    uv run --with scipy --with numpy python p3.py SCRATCH SDIR"""
import json, sys, random
import numpy as np
from scipy.sparse.csgraph import connected_components
import l1, fixtures

SIGS = ("joined", "component", "coherence", "raw links", "mean degree")


def signals(N, deg, m2, R, seeds):
    R = list(dict.fromkeys(R))
    sub = N[R][:, R]
    links = sub.nnz / 2
    d = deg[R].astype(float)
    exp = ((d.sum() ** 2 - (d ** 2).sum()) / 2) / m2
    _, lab = connected_components(sub, directed=False)
    pos = {x: i for i, x in enumerate(R)}
    sl = [lab[pos[s]] for s in seeds if s in pos]
    best = max(set(sl), key=lambda c: (sl.count(c), (lab == c).sum())) if sl else None
    return {"joined": (sl.count(best) / len(seeds)) if sl else 0.0, "component": int((lab == best).sum()) if sl else 0,
            "coherence": links / exp if exp > 0 else 0.0, "raw links": links, "mean degree": float(d.mean())}


def auc(pos, neg):
    if not pos or not neg: return float("nan")
    p, n = np.array(pos), np.array(neg)
    return float(((p[:, None] > n[None, :]).sum() + .5 * (p[:, None] == n[None, :]).sum()) / (len(p) * len(n)))


def auc_ci(x, y, n=2000, seed=0):
    x, y = np.array(x), np.array(y); r = np.random.default_rng(seed); out = []
    for _ in range(n):
        i = r.integers(0, len(x), len(x)); out.append(auc(list(x[i][y[i]]), list(x[i][~y[i]])))
    out = [v for v in out if v == v]
    if not out: return float("nan"), float("nan"), float("nan")
    return auc(list(x[y]), list(x[~y])), np.percentile(out, 2.5), np.percentile(out, 97.5)


def narrow(rows, g, w):
    """P3b: Beside, or a shared key held by at most w passages (2 ≤ df ≤ w); Near excluded."""
    import scipy.sparse as sp
    A = g.A.tocsc()
    df = np.asarray(A.sum(0)).ravel()
    A = A[:, np.where((df >= 2) & (df <= w))[0]].tocsr()
    M = (A @ A.T).tocsr()
    ri, ci = [], []
    for i, r in enumerate(rows):
        for x in r["next"]:
            j = g.ix.get(x)
            if j is not None and j != i: ri += [i, j]; ci += [j, i]
    M = (M + sp.csr_matrix((np.ones(len(ri)), (ri, ci)), shape=M.shape)).tocsr()
    M.setdiag(0); M.eliminate_zeros(); M.data[:] = 1
    return M


def main():
    scr, sdir = sys.argv[1], sys.argv[2]; rnd = random.Random(0)
    W_ = int(sys.argv[sys.argv.index("--narrow") + 1]) if "--narrow" in sys.argv else None
    tf = {"cards": "trace-cards", "prs": "trace-pr", "mq": "trace-mq"}
    for gname, gsets in (("p8", ("cards", "prs")), ("mq", ("mq",))):
        rows = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gname}.jsonl")]
        g = l1.G(rows)
        N = narrow(rows, g, W_) if W_ else fixtures.Doors(rows, g).N.tocsr()
        deg = np.diff(N.indptr); m2 = N.nnz  # 2m
        for c in gsets:
            _, test = l1.load(scr, g, c)
            St = l1.load_s(sdir, "test", c, g)
            traces = {t["qid"]: t for t in map(json.loads, open(f"{scr}/floor/{tf[c]}.jsonl"))}
            fin = {k: [] for k in SIGS}; srch = {k: [] for k in SIGS}; shuf = {k: [] for k in SIGS}
            y, ys, yr, rec = [], [], [], []
            waves = {}  # wave -> [joined==1, found so far]
            dj_gold, dj_none = [], []
            for qid, seeds, gi, walk, gs in test:
                if not (gi - set(seeds)): continue
                t = traces[qid]
                by_w = {}
                for d in t["documents"]:
                    if d["id"] in g.ix: by_w.setdefault(d["wave"], []).append(g.ix[d["id"]])
                W = sorted(by_w)
                R = []; found = False; prev = None
                for w in W:
                    new = by_w[w]; R += new
                    s = signals(N, deg, m2, R, seeds)
                    gnew = any(x in gi and x not in seeds for x in new)
                    if w > 0 and prev is not None:
                        (dj_gold if gnew and not found else dj_none).append(s["joined"] - prev)
                    found = found or (w > 0 and gnew)
                    waves.setdefault(w, []).append((s["joined"] == 1.0, found))
                    prev = s["joined"]
                for k in SIGS: fin[k].append(s[k])
                y.append(found); rec.append(len((gi - set(seeds)) & set(R)) / len(gi - set(seeds)))
                # search's top 10 as the read set
                order = [i for i, _ in sorted(St.get(qid, {}).items(), key=lambda kv: -kv[1])][:10]
                ss = signals(N, deg, m2, seeds + [i for i in order if i not in seeds][:5], seeds)
                for k in SIGS: srch[k].append(ss[k])
                ys.append(any(i in gi for i in order if i not in seeds))
                # shuffled reads: random passages one door from the seeds, as many as the walk read
                nb = set()
                for s_ in seeds: nb |= set(N.indices[N.indptr[s_]:N.indptr[s_ + 1]].tolist())
                nb -= set(seeds); nb = sorted(nb)
                k_ = len(R) - len(seeds)
                rr = rnd.sample(nb, min(k_, len(nb)))
                sr = signals(N, deg, m2, seeds + rr, seeds)
                for k in SIGS: shuf[k].append(sr[k])
                yr.append(any(i in gi for i in rr))
            y, ys, yr = np.array(y), np.array(ys), np.array(yr)
            print(f"\n{c}: {len(y)} walks with gold beyond the seeds; gold found by the walk {y.mean():.2f}, by search 6-10 {ys.mean():.2f}, by shuffled reads {yr.mean():.2f}")
            for name, S, Y in (("walk, final wave", fin, y), ("search top 10", srch, ys), ("shuffled reads", shuf, yr)):
                print(f"  {name}: " + "; ".join("{} AUC {:.3f} [{:.3f}, {:.3f}]".format(k, *auc_ci(S[k], Y)) for k in SIGS))
            from scipy.stats import spearmanr
            print("  added (bill, REM-1341): Spearman with the walk's recall beyond the seeds: " + "; ".join(f"{k} {spearmanr(fin[k], rec)[0]:+.3f}" for k in SIGS))
            print("  by wave (share joined=1, share found so far): " + ", ".join(f"w{w} {np.mean([a for a, _ in v]):.2f}/{np.mean([b for _, b in v]):.2f}" for w, v in sorted(waves.items())))
            print(f"  Δjoined at the wave gold is first read {np.mean(dj_gold):+.3f} (n {len(dj_gold)}), other waves {np.mean(dj_none):+.3f} (n {len(dj_none)})")


if __name__ == "__main__":
    main()
