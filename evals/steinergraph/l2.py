"""L2 (REGISTERED-L2.md), $0: fit L1's link weights with no gold. The reward is the coherence of seeds ∪ top 5 over a
strength-preserving null. Score held-out recall@5 beyond the seeds against Q and L1's gold-fitted LQ.
    uv run --with scipy --with numpy python l2.py SCRATCH SDIR"""
import json, sys, random, os
import numpy as np, scipy.sparse as sp
import l1
from l1 import G, GRID, UNI, recall5, mean_ok, boot, load, load_s, Fmat


def strength(rows, g):
    """w_ij = Σ 1/(df−1) over shared keys (2 ≤ df ≤ 100), + 1 if Beside. Near left out (likeness, not connection)."""
    A = g.A[:, g.ok].tocsr()
    df = np.asarray(A.sum(0)).ravel()
    W = (A @ sp.diags(1.0 / np.maximum(df - 1, 1)) @ A.T).tocsr()
    ri, ci = [], []
    for i, r in enumerate(rows):
        for x in r["next"]:
            j = g.ix.get(x)
            if j is not None and j != i: ri += [i, j]; ci += [j, i]
    B = sp.csr_matrix((np.ones(len(ri)), (ri, ci)), shape=W.shape); B.data[:] = 1; B.sum_duplicates(); B.data[:] = 1
    W = (W + B).tocsr(); W.setdiag(0); W.eliminate_zeros()
    s = np.asarray(W.sum(1)).ravel()
    return W, s, s.sum()


def tops(P, seeds, k=5):
    out = []
    for c, ss in enumerate(seeds):
        p = P[:, c].copy(); p[ss] = -1
        t = np.argpartition(-p, k)[:k]; out.append([int(x) for x in t if p[x] > 0])
    return out


def coherence(W, s, m2, seeds, T):
    R = list(dict.fromkeys(list(seeds) + list(T)))
    if len(R) < 2: return 0.0
    S = [x for x in dict.fromkeys(seeds)]
    pairs = lambda X: (W[X][:, X].sum() / 2, ((s[X].sum() ** 2 - (s[X] ** 2).sum()) / 2) / m2)
    (o, e), (os_, es) = pairs(R), pairs(S)
    obs, exp = o - os_, e - es  # seed–seed pairs dropped: they don't depend on θ (bill's amendment 2)
    return obs / exp if exp > 0 else 0.0


def local(W, seeds, T):
    """LL control (bill's amendment 1): share of T directly linked to a seed, unweighted, no null."""
    if not T or not seeds: return 0.0
    return float((np.asarray(W[T][:, list(seeds)].sum(1)).ravel() > 0).mean())


def fit(scores):
    """scores: θ -> mean reward. argmax, ties to the θ nearest uniform (L1's rule)."""
    return max(scores, key=lambda th: (round(scores[th], 9), -sum(abs(x - y) for x, y in zip(th, UNI))))


def rewards(g, W, s, m2, seeds, F, shuf):
    out = {"C": {}, "H": {}, "Cshuf": {}, "L": {}}
    for th in GRID:
        P, _ = g.run(seeds, th, F=F)
        T = tops(P, seeds)
        out["C"][th] = float(np.mean([coherence(W, s, m2, ss, t) for ss, t in zip(seeds, T)]))
        out["H"][th] = float(np.mean([s[t].mean() if t else 0 for t in T]))
        out["L"][th] = float(np.mean([local(W, ss, t) for ss, t in zip(seeds, T)]))
        out["Cshuf"][th] = float(np.mean([coherence(W, s, m2, seeds[shuf[i]], t) for i, t in enumerate(T)]))
    return out


def main():
    scr, sdir = sys.argv[1], sys.argv[2]
    lq = {c: tuple(v["fit"]["LQ"]) for c, v in json.load(open("out/l1-q.json")).items()}
    res = {}
    for gname, sets in (("p8", ("cards", "prs")), ("mq", ("mq",))):
        rows = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gname}.jsonl")]
        g = G(rows); W, s, m2 = strength(rows, g)
        for c in sets:
            dev, test = load(scr, g, c)
            Sd, St = load_s(sdir, "dev", c, g), load_s(sdir, "test", c, g)
            ds = [s_ for _, s_, *_ in dev]; ts = [s_ for _, s_, *_ in test]
            Fd = Fmat(g, [q for q, *_ in dev], Sd); Ft = Fmat(g, [q for q, *_ in test], St)
            rnd = random.Random(0)
            def derange(n):
                p = list(range(n)); rnd.shuffle(p); r = p[1:] + p[:1]; d = [0] * n
                for a, b in zip(p, r): d[a] = b
                return d
            Rd = rewards(g, W, s, m2, ds, Fd, derange(len(ds)))
            Rt = rewards(g, W, s, m2, ts, Ft, derange(len(ts)))
            th = {"LC": fit(Rd["C"]), "LC-test": fit(Rt["C"]), "LH": fit(Rd["H"]), "LL": fit(Rd["L"]), "LC-shuf": fit(Rd["Cshuf"]), "LQ": lq[c]}
            print(f"{c}: θ (width, doors, α) side by side: " + "; ".join(f"{k} {v}" for k, v in th.items()), flush=True)
            for k, v in th.items():
                if v in Rd["C"]: print(f"  {k}: dev coherence {Rd['C'][v]:.3f} (uniform {Rd['C'][UNI]:.3f}), dev locality {Rd['L'][v]:.3f} (uniform {Rd['L'][UNI]:.3f})", flush=True)
            tq = [(s_, gi) for _, s_, gi, _, _ in test]
            arms = {"Q": recall5(g.run(ts, UNI, F=Ft)[0], tq)}
            for k, v in th.items(): arms[k] = recall5(g.run(ts, v, F=Ft)[0], tq)
            print(f"TEST {c}: " + ", ".join(f"{k} {mean_ok(v):.3f}" for k, v in arms.items()), flush=True)
            out = {}
            for a in ("LC", "LC-test", "LH", "LL", "LC-shuf", "LQ"):
                d, lo, hi = boot(arms[a], arms["Q"]); out[a] = (d, lo, hi)
                print(f"  {a} − Q {d:+.3f} [{lo:+.3f}, {hi:+.3f}]")
            gq = out["LQ"][0]
            if gq > 0: print(f"  share of LQ's gain recovered by LC {out['LC'][0] / gq:.2f}")
            # does dev coherence track dev recall across θ? (diagnostic, uses dev gold)
            from scipy.stats import spearmanr
            dq = [(s_, gi) for _, s_, gi, _, _ in dev]
            dr = {t: mean_ok(recall5(g.run(ds, t, F=Fd)[0], dq)) for t in GRID}
            print(f"  diagnostic: Spearman across the grid of dev coherence vs dev recall@5 {spearmanr([Rd['C'][t] for t in GRID], [dr[t] for t in GRID])[0]:+.3f}; "
                  f"hub reward vs recall {spearmanr([Rd['H'][t] for t in GRID], [dr[t] for t in GRID])[0]:+.3f}; "
                  f"locality vs recall {spearmanr([Rd['L'][t] for t in GRID], [dr[t] for t in GRID])[0]:+.3f}; "
                  f"coherence vs locality {spearmanr([Rd['C'][t] for t in GRID], [Rd['L'][t] for t in GRID])[0]:+.3f}", flush=True)
            res[c] = {"theta": {k: list(v) for k, v in th.items()}, "test": {k: mean_ok(v) for k, v in arms.items()},
                      "diff_vs_Q": {k: list(v) for k, v in out.items()}}
    os.makedirs("out", exist_ok=True)
    json.dump(res, open("out/l2.json", "w"), indent=1)


if __name__ == "__main__":
    main()
