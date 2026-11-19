"""K1 (REGISTERED-K1.md), $0: per key family, its share of a walk's coherence and its own ratio over the null; AUC of
found (gold in the top 5 beyond the seeds) against not found, on dev, at L2's fitted θ.
    uv run --with scipy --with numpy python k1.py SCRATCH SDIR"""
import json, os, re, sys
from collections import defaultdict
import numpy as np, scipy.sparse as sp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l1 import G, load, load_s, Fmat  # noqa: E402
from l2 import tops  # noqa: E402

FAM = ("number", "code", "phrase", "word", "beside")


def family(k):
    if re.search(r"\d", k): return "number"
    if re.search(r"[_./]", k): return "code"
    if " " in k.strip(): return "phrase"
    return "word"


def fam_strength(rows, g):
    """{family: W_f} with W_f = Σ 1/(df−1) over shared keys of f (2 ≤ df ≤ 100), Beside = 1 per next link."""
    mem = defaultdict(list)
    for i, r in enumerate(rows):
        for k in r["keys"]: mem[k].append(i)
    Ws = {}
    keys_by_f = defaultdict(list)
    for k, m in mem.items():
        if 2 <= len(m) <= 100: keys_by_f[family(k)].append(m)
    for f, ms in keys_by_f.items():
        ri = [i for m in ms for i in m]; ci = [j for j, m in enumerate(ms) for _ in m]
        A = sp.csr_matrix((np.ones(len(ri)), (ri, ci)), shape=(g.n, len(ms)))
        df = np.array([len(m) for m in ms], float)
        W = (A @ sp.diags(1.0 / (df - 1)) @ A.T).tocsr(); W.setdiag(0); W.eliminate_zeros(); Ws[f] = W
    ri, ci = [], []
    for i, r in enumerate(rows):
        for x in r["next"]:
            j = g.ix.get(x)
            if j is not None and j != i: ri += [i, j]; ci += [j, i]
    B = sp.csr_matrix((np.ones(len(ri)), (ri, ci)), shape=(g.n, g.n)); B.data[:] = 1; B.sum_duplicates(); B.data[:] = 1
    B.setdiag(0); B.eliminate_zeros(); Ws["beside"] = B.tocsr()
    return {f: (W, np.asarray(W.sum(1)).ravel()) for f, W in Ws.items()}


def obs_exp(W, s, seeds, T):
    R = list(dict.fromkeys(list(seeds) + list(T))); S = list(dict.fromkeys(seeds)); m2 = s.sum()
    if m2 == 0 or len(R) < 2: return 0.0, 0.0
    f = lambda X: (W[X][:, X].sum() / 2, ((s[X].sum() ** 2 - (s[X] ** 2).sum()) / 2) / m2)
    (o, e), (o2, e2) = f(R), f(S)
    return o - o2, e - e2


def auc(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if not len(x) or not len(y): return float("nan")
    return float(((x[:, None] > y[None]).sum() + .5 * (x[:, None] == y[None]).sum()) / (len(x) * len(y)))


def boot_auc(v, found, n=2000, seed=0):
    r = np.random.default_rng(seed); v = np.asarray(v); found = np.asarray(found); out = []
    for _ in range(n):
        ix = r.integers(0, len(v), len(v)); out.append(auc(v[ix][found[ix]], v[ix][~found[ix]]))
    return np.nanpercentile(out, [2.5, 97.5])


def main():
    scr, sdir = sys.argv[1:3]
    lc = {c: tuple(v["theta"]["LC"]) for c, v in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out/l2.json"))).items()}
    for gname, sets in (("p8", ("cards", "prs")), ("mq", ("mq",))):
        rows = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gname}.jsonl")]
        g = G(rows); Wf = fam_strength(rows, g)
        Wt = sum(W for W, _ in Wf.values()).tocsr(); st = np.asarray(Wt.sum(1)).ravel()
        nk = defaultdict(int)
        for r in rows:
            for k in r["keys"]: nk[family(k)] += 1
        print(f"{gname}: key occurrences by family " + ", ".join(f"{f} {nk[f]}" for f in FAM[:4]), flush=True)
        for c in sets:
            dev, _ = load(scr, g, c)
            Sd = load_s(sdir, "dev", c, g); ds = [s_ for _, s_, *_ in dev]
            P, _ = g.run(ds, lc[c], F=Fmat(g, [q for q, *_ in dev], Sd)); T = tops(P, ds)
            found = np.array([bool(set(t) & gi) for t, (_, _, gi, _, _) in zip(T, dev)])
            tot = [obs_exp(Wt, st, ss, t) for ss, t in zip(ds, T)]
            coh = [o / e if e > 0 else 0 for o, e in tot]
            lo, hi = boot_auc(coh, found)
            print(f"{c} (dev {len(dev)}, found {found.sum()}), θ {lc[c]}: total coherence AUC {auc(np.array(coh)[found], np.array(coh)[~found]):.3f} [{lo:.3f}, {hi:.3f}]", flush=True)
            for f in [f for f in FAM if f in Wf]:
                W, s = Wf[f]
                oe = [obs_exp(W, s, ss, t) for ss, t in zip(ds, T)]
                share = [o / to if to > 0 else 0 for (o, _), (to, _) in zip(oe, tot)]
                ratio = [o / e if e > 0 else 0 for o, e in oe]
                a1 = auc(np.array(share)[found], np.array(share)[~found]); l1_, h1 = boot_auc(share, found)
                a2 = auc(np.array(ratio)[found], np.array(ratio)[~found]); l2_, h2 = boot_auc(ratio, found)
                sep = lambda lo_, hi_: " *" if lo_ > .5 or hi_ < .5 else ""
                print(f"  {f:7s} mean share {np.mean(share):.3f}  share AUC {a1:.3f} [{l1_:.3f}, {h1:.3f}]{sep(l1_, h1)}  "
                      f"ratio AUC {a2:.3f} [{l2_:.3f}, {h2:.3f}]{sep(l2_, h2)}", flush=True)


if __name__ == "__main__":
    main()
