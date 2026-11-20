"""CS Q2 (REGISTERED-CS-Q2.md), $0: in the reference world, do high-surprise convergences line up with gold and T*?
Four dev cases: the first two qids of tstarp-mq.jsonl and of tstarp-cards.jsonl (bill's S1′ most probable trees).
    uv run --with scipy --with numpy python csq2.py SCRATCH SDIR TREES"""
import json, os, sys
import numpy as np
from scipy.stats import rankdata, spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l1 import G, load_s, Fmat, UNI  # noqa: E402
import l2, cs  # noqa: E402


def auc(x, pos):
    """P(score of a positive > a negative), ties half; nan if a class is empty."""
    pos = np.asarray(pos, bool)
    if pos.sum() == 0 or (~pos).sum() == 0: return float("nan")
    r = rankdata(x)
    return float((r[pos].sum() - pos.sum() * (pos.sum() + 1) / 2) / (pos.sum() * (~pos).sum()))


def main():
    scr, sdir, trees = sys.argv[1:4]
    here = os.path.dirname(os.path.abspath(__file__))
    lc = {c: tuple(v["theta"]["LC"]) for c, v in json.load(open(f"{here}/out/l2.json")).items()}
    out = []
    for gname, c in (("mq", "mq"), ("p8", "cards")):
        rows = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gname}.jsonl")]
        g = G(rows); deg = cs.link_degree(g); cls = cs.degree_classes(deg)
        W, s, m2 = l2.strength(rows, g); Sd = load_s(sdir, "dev", c, g)
        recs = [json.loads(l) for l in open(f"{trees}/tstarp-{c}.jsonl")]
        qids = list(dict.fromkeys(r["qid"] for r in recs))[:2]
        for q in qids:
            for ref, th in (("graph-only", UNI), ("walk-as-used", lc[c])):
                t = next((r for r in recs if r["qid"] == q and r["ref"] == ref), None)
                if t is None: print(f"-- {c} {q} {ref}: no tree"); continue
                seeds = [g.ix[x] for x in t["seeds"]]; gold = {g.ix[x] for x in t["gold"]}
                tn = {g.ix[x] for e in t["edges"] for x in e[:2]} - set(seeds)
                F = Fmat(g, [q], Sd) if ref == "walk-as-used" else None
                (_, p, qn), = cs.per_seed(g, [seeds], th, F, cls)
                sc = cs.scores(p, qn, seeds); ok = sc["reach"]
                A = {f"{i}{j}": float((p[ok0, i] * p[ok0, j]).sum() / (qn[ok0, i] * qn[ok0, j]).sum())
                     for i in range(len(seeds)) for j in range(i + 1, len(seeds))
                     for ok0 in [np.isin(np.arange(g.n), seeds, invert=True)]}
                Pu, _ = g.run([seeds], th, F=F); Pu = Pu[:, 0]
                l2n = np.asarray(W[:, seeds].sum(1)).ravel() / np.maximum(s * s[seeds].sum() / m2, 1e-300)
                idx = np.where(ok)[0]
                arms = {"am (= xm in rank)": sc["am"], "aM": sc["aM"], "xM": sc["xM"],
                        "walk mass P": Pu, "L2 node coherence": l2n, "degree": deg.astype(float)}
                gpos = np.isin(idx, list(gold)); tpos = np.isin(idx, list(tn))
                res = {"c": c, "q": q, "ref": ref, "scored": int(ok.sum()), "gold": len(gold), "gold_scored": int(gpos.sum()),
                       "tstar": len(tn), "tstar_scored": int(tpos.sum()),
                       "A": A, "unreached": int((~ok).sum() - len(seeds)),
                       "auc_gold": {k: auc(v[idx], gpos) for k, v in arms.items()},
                       "auc_tstar": {k: auc(v[idx], tpos) for k, v in arms.items()},
                       "rho_deg": {k: float(spearmanr(v[idx], deg[idx])[0]) for k, v in arms.items() if k != "degree"}}
                out.append(res)
                print(f"\n-- {c} {q[:40]} [{ref}]: scored {res['scored']} passages; gold {res['gold_scored']}/{res['gold']}, "
                      f"T* non-seed {res['tstar_scored']}/{res['tstar']}; {res['unreached']} unreached; A_ij range {min(A.values()):.3g}–{max(A.values()):.3g}")
                for k in arms:
                    print(f"   {k:24s} AUC gold {res['auc_gold'][k]:.3f}  AUC T* {res['auc_tstar'][k]:.3f}"
                          + (f"  ρ(deg) {res['rho_deg'][k]:+.2f}" if k in res["rho_deg"] else ""), flush=True)
    json.dump(out, open(f"{here}/out/csq2.json", "w"), indent=1)
    for ref in ("graph-only", "walk-as-used"):
        R = [r for r in out if r["ref"] == ref]
        for tgt in ("auc_gold", "auc_tstar"):
            for k in ("am (= xm in rank)", "aM"):
                w = sum(r[tgt][k] > r[tgt]["walk mass P"] for r in R)
                print(f"{ref} {tgt}: {k} beats walk mass in {w}/{len(R)}")


if __name__ == "__main__":
    main()
