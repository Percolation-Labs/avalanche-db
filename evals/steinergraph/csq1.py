"""CS Q1, $0: does surprise coherence stop the gaming that loose (L2) coherence allowed?
(a) cards dev, L2's θ: β = 0 against L3's fitted LC3 β. Loose coherence rose, recall fell.
(b) MuSiQue, S3's drifted graph against it plus S3's 40 accepted links. Loose coherence rose by construction.
Pass: CS falls or stays flat where loose coherence rose. Four cases printed, then the mean difference with a 95% bootstrap.
    uv run --with scipy --with numpy python csq1.py SCRATCH SDIR [a|b] [--cases]"""
import json, sys, collections, copy
import numpy as np
import l1, l2, cs
from l1 import UNI, load, load_s, Fmat, recall5, boot
from l3 import G3
from s3 import add_beside

ARMS = ("xm", "xM", "am", "aM")  # (no A | A) x (mean | max over pairs)


def readout(g, qs, seeds, theta, F, W, s, m2, cls):
    P, _ = g.run(seeds, theta, F=F)
    T = l2.tops(P, seeds)
    loose = [l2.coherence(W, s, m2, ss, t) for ss, t in zip(seeds, T)]
    rec = recall5(P, [(ss, gi) for ss, gi in zip(seeds, [q[2] for q in qs])])
    out = dict(T=T, loose=loose, rec=rec, **{m: [] for m in ARMS}, drop=[])
    for (ss, p, q), t in zip(cs.per_seed(g, seeds, theta, F, cls), T):
        sc = cs.scores(p, q, ss)
        for m in ARMS: out[m].append(cs.walk_score(sc[m], t)[0])
        out["drop"].append(cs.walk_score(sc["xm"], t)[1])
    return out


def compare(say, name, A, B, qs, ncase=4):
    say(f"== {name}: per case (A → B)")
    for i in range(min(ncase, len(qs))):
        say(f"  {qs[i][0]}: loose {A['loose'][i]:.3f} → {B['loose'][i]:.3f}; " + "; ".join(f"{m} {A[m][i]:+.3f} → {B[m][i]:+.3f}" for m in ARMS)
            + f"; recall {A['rec'][i]} → {B['rec'][i]}; top5 changed {set(A['T'][i]) != set(B['T'][i])}; dropped {A['drop'][i]} → {B['drop'][i]}")
    out = {}
    for m in ("loose",) + ARMS + ("rec",):
        a = [x for x in A[m]]; b = [x for x in B[m]]
        ok = [(x, y) for x, y in zip(a, b) if x is not None and y is not None and np.isfinite(x) and np.isfinite(y)]
        d, lo, hi = boot([y for _, y in ok], [x for x, _ in ok])
        out[m] = (d, lo, hi, len(ok)); say(f"  mean B − A, {m}: {d:+.4f} [{lo:+.4f}, {hi:+.4f}] (n {len(ok)})")
    ch = sum(set(x) != set(y) for x, y in zip(A["T"], B["T"])); say(f"  top 5 changed on {ch}/{len(qs)}")
    out["changed"] = ch; out["dropped"] = (int(sum(A["drop"])), int(sum(B["drop"])))
    say(f"  top-5 passages not reached by every seed (dropped from CS): A {out['dropped'][0]}, B {out['dropped'][1]} of {5 * len(qs)}")
    return out


def main():
    scr, sdir, part = sys.argv[1], sys.argv[2], sys.argv[3]
    txt = []
    def say(x): print(x, flush=True); txt.append(x)
    res = {}
    if part == "a":
        rows = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-p8.jsonl")]
        g = G3(rows); W, s, m2 = l2.strength(rows, g)
        th = tuple(json.load(open("out/l2.json"))["cards"]["theta"]["LC"])
        b3 = json.load(open("out/l3.json"))["cards"]["beta"]["LC3"]
        dev, _ = load(scr, g, "cards"); Sd = load_s(sdir, "dev", "cards", g)
        seeds = [x for _, x, *_ in dev]; F = Fmat(g, [q for q, *_ in dev], Sd)
        cls = cs.degree_classes(cs.link_degree(g))
        base = dict(g.beta)
        A = readout(g, dev, seeds, th, F, W, s, m2, cls)
        g.beta = dict(b3); B = readout(g, dev, seeds, th, F, W, s, m2, cls); g.beta = base
        say(f"cards dev, L2 θ {th}: A = β 0, B = LC3 β {b3}; loose mean {np.mean(A['loose']):.3f} → {np.mean(B['loose']):.3f}")
        res["a"] = compare(say, "Q1a cards L3", A, B, dev)
    else:
        rows = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-mq.jsonl")]
        g0 = l1.G(rows)
        s2c = json.load(open("out/s2c.json"))["mq"]["cases"]
        cuts = collections.defaultdict(set)
        for q in s2c: cuts[g0.ix[q["v"]]].add(q["key"])
        rd = list(rows)
        for v, ks in cuts.items(): rd[v] = dict(rows[v], keys=[k for k in rows[v]["keys"] if k not in ks])
        gd = l1.G(rd); W, s, m2 = l2.strength(rd, gd)
        added = [(g0.ix[a], g0.ix[b]) for a, b in json.load(open("out/s3-mq.json"))["added"]]
        dev, test = load(scr, g0, "mq")
        Sd, St = load_s(sdir, "dev", "mq", g0), load_s(sdir, "test", "mq", g0)
        qs = list(dev) + list(test)
        seeds = [x for _, x, *_ in qs]
        F = np.hstack([Fmat(g0, [q for q, *_ in dev], Sd), Fmat(g0, [q for q, *_ in test], St)])
        cls = cs.degree_classes(cs.link_degree(gd))  # degree fixed from the drifted graph, like the strength matrix
        A = readout(gd, qs, seeds, UNI, F, W, s, m2, cls)
        gr = copy.copy(gd); gr.nd = gd.nd.copy(); add_beside(gr, added)
        B = readout(gr, qs, seeds, UNI, F, W, s, m2, cls)
        say(f"MuSiQue S3: A = drifted, B = drifted + {len(added)} accepted links; loose mean {np.mean(A['loose']):.4f} → {np.mean(B['loose']):.4f}")
        res["b"] = compare(say, "Q1b MuSiQue S3", A, B, qs)
    open(f"out/csq1-{part}.txt", "w").write("\n".join(txt) + "\n")
    json.dump(res, open(f"out/csq1-{part}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
