"""L1 (REGISTERED-L1.md), $0: fit link weights (θ1, θ2, α) on dev questions' outcomes so the avalanche from search's
top 5 reaches gold beyond the seeds; score recall@5 on held-out test against U, Q and a shuffled-reward fit.

    uv run --with scipy --with numpy python l1.py SCRATCH [--q SDIR]
SCRATCH holds dream/d1/graph-{p8,mq}.jsonl, dream/dt-*.jsonl (dev) and floor/{trace,q}-*.jsonl (test).
--q SDIR: per-question search scores s(t) from P1 (enables Q, LQ, H)."""
import json, sys, itertools, random, os
import numpy as np, scipy.sparse as sp

ITERS = 25
GRID = list(itertools.product((-3, -2, -1, 0), (-1.5, -1, -.5, 0, .5), (.15, .3, .5)))
UNI = (-1, 0, .15)
def golds(g): return set(g.keys()) if isinstance(g, dict) else set(g)


class G:
    def __init__(s, rows):
        s.ids = [r["d"] for r in rows]; s.ix = {d: i for i, d in enumerate(s.ids)}; s.n = len(s.ids)
        kix = {}; mem = []
        for i, r in enumerate(rows):
            for k in r["keys"]: mem.append((i, kix.setdefault(k, len(kix))))
        m = np.array(mem)
        s.A = sp.csr_matrix((np.ones(len(m)), (m[:, 0], m[:, 1])), shape=(s.n, len(kix)))
        df = np.asarray(s.A.sum(0)).ravel()
        s.ok = (df >= 2) & (df <= 100); s.kwidth = np.maximum(df - 1, 1)
        ri, ci, wid, nown = [], [], [], np.zeros(s.n)
        for i, r in enumerate(rows):
            for kind in ("next", "near"):
                t = sorted({s.ix[x] for x in r[kind] if x in s.ix and s.ix[x] != i})
                if t:
                    nown[i] += 1; ri += [i] * len(t); ci += t; wid += [len(t)] * len(t)
        s.Ori, s.Oci, s.Owid = np.array(ri), np.array(ci), np.array(wid, float)
        s.nd = np.asarray(s.A[:, s.ok].sum(1)).ravel() + nown

    def set_theta(s, t1, t2):
        s.kw = np.where(s.ok, s.kwidth ** t1, 0.0)
        s.Akw = s.A @ s.kw
        # duplicates (same target in two owned doors of u) sum, as two doors would
        s.Ow = sp.csr_matrix((s.Owid ** t1, (s.Ori, s.Oci)), shape=(s.n, s.n))
        s.hdeg = (1 + s.nd) ** t2

    def step(s, X, h):
        """one walk step of mass X (n x m); h: n x m target weights (already including deg term)."""
        Z = s.A @ (s.kw[:, None] * (s.A.T @ h)) - s.Akw[:, None] * h + s.Ow @ h
        Y = np.divide(X, Z, out=np.zeros_like(X), where=Z > 0)
        return h * (s.A @ (s.kw[:, None] * (s.A.T @ Y)) - s.Akw[:, None] * Y + s.Ow.T @ Y)

    def run(s, seeds, theta, F=None, steps=()):
        t1, t2, a = theta
        s.set_theta(t1, t2)
        m = len(seeds)
        h = s.hdeg[:, None] * (F if F is not None else np.ones((s.n, 1)))
        if h.shape[1] == 1: h = np.repeat(h, m, 1)
        R = np.zeros((s.n, m))
        for c, ss in enumerate(seeds):
            if ss: R[ss, c] = 1.0 / len(ss)
        P = a * R; X = R; W = {}
        Xn = R  # no-restart walk for the avalanche
        for i in range(1, ITERS + 1):
            X = (1 - a) * s.step(X, h); P = P + a * X
            if i <= max(steps, default=0):
                Xn = s.step(Xn, h)
                if i in steps: W[i] = Xn
        return P, W


def recall5(P, qs, k=5):
    out = []
    for c, (seeds, gold) in enumerate(qs):
        tgt = gold - set(seeds)
        if not tgt: out.append(None); continue
        p = P[:, c].copy(); p[seeds] = -1
        top = np.argpartition(-p, k)[:k]; top = [t for t in top if p[t] > 0]
        out.append(len(tgt & set(top)) / len(tgt))
    return out


def mean_ok(v): v = [x for x in v if x is not None]; return float(np.mean(v)) if v else float("nan")


def boot(a, b, n=2000, seed=0):
    d = np.array([x - y for x, y in zip(a, b) if x is not None and y is not None])
    r = np.random.default_rng(seed); bs = [d[r.integers(0, len(d), len(d))].mean() for _ in range(n)]
    return d.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def load(scr, g, c):
    gold_raw = None
    dev = []
    for r in map(json.loads, open(f"{scr}/dream/dt-{c}.jsonl")):
        dev.append((r["qid"], [g.ix[d] for d in r["docs"][:5] if d in g.ix], {g.ix.get(x, -1) for x in golds(r["gold"])} - {-1},
                    {g.ix[d] for d in r["docs"][5:10] if d in g.ix}, golds(r["gold"])))
    tf = {"cards": "trace-cards", "prs": "trace-pr", "mq": "trace-mq"}[c]
    qf = {"cards": "q-cards", "prs": "q-prs-test", "mq": "q-musique-questions"}[c]
    gold = {r["qid"]: golds(r["gold"]) for r in map(json.loads, open(f"{scr}/floor/{qf}.jsonl"))}
    test = []
    for t in map(json.loads, open(f"{scr}/floor/{tf}.jsonl")):
        gs = gold[t["qid"]]
        seeds = [g.ix[d["id"]] for d in t["documents"] if d["wave"] == 0 and d["id"] in g.ix]
        walk = {g.ix[d["id"]] for d in t["documents"] if d["wave"] >= 1 and d["id"] in g.ix}
        # gold not in the graph stays a miss: keep its count via a sentinel
        gi = {g.ix[x] for x in gs if x in g.ix} | {-(i + 2) for i, x in enumerate(sorted(gs)) if x not in g.ix}
        test.append((t["qid"], seeds, gi, walk, gs))
    for i, (q, s_, gi, w, gs) in enumerate(dev):
        miss = {-(j + 2) for j, x in enumerate(sorted(gs)) if x not in g.ix}
        dev[i] = (q, s_, gi | miss, w, gs)
    return dev, test


def walk_recall(qs):
    out = []
    for _, seeds, gold, walk, _ in qs:
        tgt = gold - set(seeds)
        out.append(len(tgt & walk) / len(tgt) if tgt else None)
    return out


def main():
    scr = sys.argv[1]; random.seed(0)
    res = {}
    for gname, sets in (("p8", ("cards", "prs")), ("mq", ("mq",))):
        g = G([json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gname}.jsonl")])
        for c in sets:
            dev, test = load(scr, g, c)
            dq = [(s_, gi) for _, s_, gi, _, _ in dev]; tq = [(s_, gi) for _, s_, gi, _, _ in test]
            # shuffled reward: each dev question's gold swapped for another's (derangement by rotation of a shuffle)
            perm = list(range(len(dq))); random.shuffle(perm); rot = perm[1:] + perm[:1]
            sh = [None] * len(dq)
            for a_, b_ in zip(perm, rot): sh[a_] = (dq[a_][0], dq[b_][1])
            fit = {}
            for name, qs in (("L", dq), ("L-shuf", sh)):
                best = None
                for th in GRID:
                    P, _ = g.run([s_ for s_, _ in qs], th)
                    r = mean_ok(recall5(P, qs))
                    key = (round(r, 6), -sum(abs(x - y) for x, y in zip(th, UNI)))
                    if best is None or key > best[0]: best = (key, th)
                fit[name] = best[1]
                print(f"{c}: {name} fit θ1,θ2,α = {best[1]} (dev recall@5 {best[0][0]:.3f})", flush=True)
            Pu, Wu = g.run([s_ for s_, _ in tq], UNI, steps=(1, 2, 3))
            arms = {"U": recall5(Pu, tq)}
            for name in ("L", "L-shuf"):
                P, W = g.run([s_ for s_, _ in tq], fit[name], steps=(1, 2, 3))
                arms[name] = recall5(P, tq)
                if name == "L": WL = W
            arms["walk (Jev, reference)"] = walk_recall(test)
            print(f"TEST {c}: " + ", ".join(f"{k} {mean_ok(v):.3f}" for k, v in arms.items()), flush=True)
            for k in ("L", "L-shuf"):
                d, lo, hi = boot(arms[k], arms["U"]); print(f"  {k} − U {d:+.3f} [{lo:+.3f}, {hi:+.3f}]")
            for st in (1, 2, 3):
                gm = lambda W: np.mean([W[st][[x for x in gi - set(s_) if x >= 0], ci].sum() for ci, (s_, gi) in enumerate(tq) if gi - set(s_)])
                print(f"  avalanche step {st}: gold mass U {gm(Wu):.4f}, L {gm(WL):.4f}")
            res[c] = {"fit": fit, "test": {k: mean_ok(v) for k, v in arms.items()}}
    os.makedirs("out", exist_ok=True)
    json.dump(res, open("out/l1-blind.json", "w"), indent=1)




# ---- question-aware half: Q, LQ (learned θ under Q), LQ fitted on shuffled reward, H (dev-gold history prior) ----
def load_s(sdir, split, c, g):
    import gzip
    out = {}
    for l in gzip.open(f"{sdir}/search-{split}-{c}.jsonl.gz", "rt"):
        r = json.loads(l)
        out[r["qid"]] = {g.ix[d]: x for d, x in r["S"] if d in g.ix}
    return out


def Fmat(g, qids, S, hist=None):
    F = np.full((g.n, len(qids)), .01)
    for c, q in enumerate(qids):
        for i, x in S.get(q, {}).items(): F[i, c] += x
    if hist is not None: F *= (1 + hist)[:, None]
    return F


def main_q():
    scr = sys.argv[1]; sdir = sys.argv[sys.argv.index("--q") + 1]; random.seed(0)
    res = {}
    for gname, sets in (("p8", ("cards", "prs")), ("mq", ("mq",))):
        g = G([json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gname}.jsonl")])
        for c in sets:
            dev, test = load(scr, g, c)
            Sd, St = load_s(sdir, "dev", c, g), load_s(sdir, "test", c, g)
            print(f"{c}: search dump covers dev {sum(q in Sd for q, *_ in dev)}/{len(dev)}, test {sum(q in St for q, *_ in test)}/{len(test)}", flush=True)
            dq = [(s_, gi) for _, s_, gi, _, _ in dev]; tq = [(s_, gi) for _, s_, gi, _, _ in test]
            Fd = Fmat(g, [q for q, *_ in dev], Sd); Ft = Fmat(g, [q for q, *_ in test], St)
            perm = list(range(len(dq))); random.shuffle(perm); rot = perm[1:] + perm[:1]
            sh = [None] * len(dq)
            for a_, b_ in zip(perm, rot): sh[a_] = (dq[a_][0], dq[b_][1])
            fit = {}
            for name, qs in (("LQ", dq), ("LQ-shuf", sh)):
                best = None
                for th in GRID:
                    P, _ = g.run([s_ for s_, _ in qs], th, F=Fd)
                    r = mean_ok(recall5(P, qs))
                    key = (round(r, 6), -sum(abs(x - y) for x, y in zip(th, UNI)))
                    if best is None or key > best[0]: best = (key, th)
                fit[name] = best[1]
                print(f"{c}: {name} fit θ1,θ2,α = {best[1]} (dev recall@5 {best[0][0]:.3f})", flush=True)
            hist = np.zeros(g.n)
            for _, _, gi, _, _ in dev:
                for x in gi:
                    if x >= 0: hist[x] += 1
            tgold = [gi - set(s_) for s_, gi in tq]
            overlap = sum(len({x for x in t if x >= 0 and hist[x] > 0}) for t in tgold), sum(len(t) for t in tgold)
            arms = {}
            P, Wq = g.run([s_ for s_, _ in tq], UNI, F=Ft, steps=(1, 2, 3)); arms["Q"] = recall5(P, tq)
            P, Wlq = g.run([s_ for s_, _ in tq], fit["LQ"], F=Ft, steps=(1, 2, 3)); arms["LQ"] = recall5(P, tq)
            P, _ = g.run([s_ for s_, _ in tq], fit["LQ-shuf"], F=Ft); arms["LQ-shuf"] = recall5(P, tq)
            P, _ = g.run([s_ for s_, _ in tq], fit["LQ"], F=Fmat(g, [q for q, *_ in test], St, hist)); arms["H"] = recall5(P, tq)
            # S: search ranks 6+ as a ranking (P1's S), from the dump
            Ps = np.zeros((g.n, len(test)))
            for ci, (q, *_) in enumerate(test):
                for i, x in St.get(q, {}).items(): Ps[i, ci] = x
            arms["S"] = recall5(Ps, tq)
            arms["walk (Jev, reference)"] = walk_recall(test)
            print(f"TEST {c}: " + ", ".join(f"{k} {mean_ok(v):.3f}" for k, v in arms.items())
                  + f" | test gold beyond seeds that was dev gold: {overlap[0]}/{overlap[1]}", flush=True)
            for a_, b_ in (("LQ", "Q"), ("LQ-shuf", "Q"), ("LQ", "LQ-shuf"), ("H", "LQ"), ("Q", "S")):
                d, lo, hi = boot(arms[a_], arms[b_]); print(f"  {a_} − {b_} {d:+.3f} [{lo:+.3f}, {hi:+.3f}]")
            for st in (1, 2, 3):
                gm = lambda W: np.mean([W[st][[x for x in gi - set(s_) if x >= 0], ci].sum() for ci, (s_, gi) in enumerate(tq) if gi - set(s_)])
                print(f"  avalanche step {st}: gold mass Q {gm(Wq):.4f}, LQ {gm(Wlq):.4f}")
            res[c] = {"fit": fit, "test": {k: mean_ok(v) for k, v in arms.items()}, "overlap": overlap}
    os.makedirs("out", exist_ok=True)
    json.dump(res, open("out/l1-q.json", "w"), indent=1)


if __name__ == "__main__":
    main_q() if "--q" in sys.argv else main()
