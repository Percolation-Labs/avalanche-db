"""L3 (REGISTERED-L3.md), $0: on top of L2's coherence-fitted θ, learn one weight per key family (bill's K1 surface
families) plus Beside, by coordinate ascent on dev coherence (no gold). Score held-out recall@5 against L2's LC.
    uv run --with scipy --with numpy python l3.py SCRATCH SDIR"""
import json, sys, random, os, re
import numpy as np, scipy.sparse as sp
import l1, l2
from l1 import G, UNI, recall5, mean_ok, boot, load, load_s, Fmat

FAMS = ("number", "code", "phrase", "word", "beside")
GRIDB = (-2, -1, 0, 1, 2)


def family(k):  # bill's K1 definition, verbatim
    if re.search(r"\d", k): return "number"
    if re.search(r"[_./]", k): return "code"
    if " " in k.strip(): return "phrase"
    return "word"


class G3(G):
    def __init__(s, rows):
        super().__init__(rows)
        kix = {}
        for r in rows:
            for k in r["keys"]: kix.setdefault(k, len(kix))
        s.kfam = np.empty(len(kix), dtype=object)
        for k, i in kix.items(): s.kfam[i] = family(k)
        kind = []  # replicate G's owned-door order to know which entries are Beside
        for i, r in enumerate(rows):
            for kd in ("next", "near"):
                t = sorted({s.ix[x] for x in r[kd] if x in s.ix and s.ix[x] != i})
                kind += [kd] * len(t)
        s.Okind = np.array(kind)
        assert len(s.Okind) == len(s.Ori)
        s.beta = {f: 0.0 for f in FAMS}

    def set_theta(s, t1, t2):
        mult = np.array([np.exp(s.beta[f]) for f in s.kfam])
        s.kw = np.where(s.ok, s.kwidth ** t1 * mult, 0.0)
        s.Akw = s.A @ s.kw
        ow = s.Owid ** t1 * np.where(s.Okind == "next", np.exp(s.beta["beside"]), 1.0)
        s.Ow = sp.csr_matrix((ow, (s.Ori, s.Oci)), shape=(s.n, s.n))
        s.hdeg = (1 + s.nd) ** t2


def main():
    scr, sdir = sys.argv[1], sys.argv[2]
    l2fit = json.load(open("out/l2.json"))
    lq = {c: tuple(v["fit"]["LQ"]) for c, v in json.load(open("out/l1-q.json")).items()}
    res = {}
    for gname, sets in (("p8", ("cards", "prs")), ("mq", ("mq",))):
        rows = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gname}.jsonl")]
        g = G3(rows); W, s, m2 = l2.strength(rows, g)
        fams_present = [f for f in FAMS if (f == "beside" and (g.Okind == "next").any()) or (f != "beside" and (g.kfam[g.ok] == f).any())]
        for c in sets:
            th = tuple(l2fit[c]["theta"]["LC"])
            dev, test = load(scr, g, c)
            Sd, St = load_s(sdir, "dev", c, g), load_s(sdir, "test", c, g)
            ds = [x for _, x, *_ in dev]; ts = [x for _, x, *_ in test]
            Fd = Fmat(g, [q for q, *_ in dev], Sd); Ft = Fmat(g, [q for q, *_ in test], St)
            rnd = random.Random(0)
            def derange(n):
                p = list(range(n)); rnd.shuffle(p); r = p[1:] + p[:1]; d = [0] * n
                for a, b in zip(p, r): d[a] = b
                return d
            shd = derange(len(ds))
            cache = {}
            def reward(beta, split):
                key = (tuple(beta[f] for f in FAMS), split)
                if key not in cache:
                    g.beta = dict(beta)
                    seeds, F = (ds, Fd) if split == "dev" else (ts, Ft)
                    P, _ = g.run(seeds, th, F=F); T = l2.tops(P, seeds)
                    own = float(np.mean([l2.coherence(W, s, m2, a, b) for a, b in zip(seeds, T)]))
                    shf = float(np.mean([l2.coherence(W, s, m2, seeds[shd[i]], t) for i, t in enumerate(T)])) if split == "dev" else None
                    cache[key] = (own, shf)
                return cache[key]
            def ascend(split, which):
                beta = {f: 0.0 for f in FAMS}
                for rnd_ in range(3):
                    changed = False
                    for f in fams_present:
                        best = (reward(beta, split)[which], beta[f])
                        for v in GRIDB:
                            if v == beta[f]: continue
                            b2 = dict(beta); b2[f] = v
                            r = reward(b2, split)[which]
                            if r > best[0] + 1e-12: best = (r, v)
                        if best[1] != beta[f]: beta[f] = best[1]; changed = True
                    print(f"  {c} {split}/{'own' if which == 0 else 'shuf'} round {rnd_ + 1}: β {beta} coherence {reward(beta, split)[which]:.3f}", flush=True)
                    if not changed: break
                return beta
            fits = {"LC3": ascend("dev", 0), "LC3-shuf": ascend("dev", 1), "LC3-test": ascend("test", 0)}
            base = {f: 0.0 for f in FAMS}
            print(f"{c}: L2 θ {th}; dev coherence at β=0 {reward(base, 'dev')[0]:.3f}, at LC3 {reward(fits['LC3'], 'dev')[0]:.3f}; families present {fams_present}", flush=True)
            for k, b in fits.items():
                edge = [f for f in fams_present if abs(b[f]) == max(GRIDB)]
                print(f"  {k} β: " + ", ".join(f"{f} {b[f]:+.0f}" for f in fams_present) + (f"  (at grid edge: {edge})" if edge else ""), flush=True)
            tq = [(x, gi) for _, x, gi, _, _ in test]
            arms = {}
            g.beta = dict(base); arms["Q"] = recall5(g.run(ts, UNI, F=Ft)[0], tq)
            arms["LQ"] = recall5(g.run(ts, lq[c], F=Ft)[0], tq)
            arms["LC"] = recall5(g.run(ts, th, F=Ft)[0], tq)
            for k, b in fits.items():
                g.beta = dict(b); arms[k] = recall5(g.run(ts, th, F=Ft)[0], tq)
            g.beta = dict(base)
            print(f"TEST {c}: " + ", ".join(f"{k} {mean_ok(v):.3f}" for k, v in arms.items()), flush=True)
            out = {}
            for a in ("LC3", "LC3-shuf", "LC3-test"):
                d, lo, hi = boot(arms[a], arms["LC"]); out[a] = (d, lo, hi)
                print(f"  {a} − LC {d:+.3f} [{lo:+.3f}, {hi:+.3f}]", flush=True)
            res[c] = {"theta": list(th), "beta": fits, "test": {k: mean_ok(v) for k, v in arms.items()}, "diff_vs_LC": out}
    os.makedirs("out", exist_ok=True)
    json.dump(res, open("out/l3.json", "w"), indent=1)


if __name__ == "__main__":
    main()
