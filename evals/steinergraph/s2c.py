"""S2c (REGISTERED-S2c.md), $0: drop the key carrying T*'s cheapest edge into a gold passage; walk rank is the gate.
    uv run --with scipy --with numpy python s2c.py SCRATCH SDIR [--cases-only]"""
import json, sys, os, collections
import numpy as np
from scipy.sparse import csgraph
import l1, s2
from l1 import G, UNI, load, load_s, Fmat, recall5, boot
from s2b import costs


def tree_edges(C, seeds, gold):
    tree, left, total, par = set(seeds), set(gold) - set(seeds), 0.0, {}
    while left:
        d, p, _ = csgraph.dijkstra(C, directed=True, indices=sorted(tree), min_only=True, return_predecessors=True)
        j = min(left, key=lambda x: (d[x], x))
        if not np.isfinite(d[j]): return float("inf"), None
        total += d[j]; x = j
        while x not in tree: par[x] = int(p[x]); tree.add(x); x = p[x]
        left -= tree
    return total, par


def main():
    scr, sdir = sys.argv[1], sys.argv[2]
    cases_only = "--cases-only" in sys.argv
    l2fit = json.load(open("out/l2.json"))
    out, txt = {}, []
    def say(s): print(s, flush=True); txt.append(s)
    for gname, sets in (("mq", ("mq",)), ("p8", ("cards", "prs"))):
        rows = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gname}.jsonl")]
        g0 = G(rows); L0 = s2.links(g0); C0 = costs(g0, UNI)
        df = collections.Counter(k for r in rows for k in set(r["keys"]))
        okk = lambda k: 2 <= df[k] <= 100
        for c in sets:
            LC = tuple(l2fit[c]["theta"]["LC"])
            _, test = load(scr, g0, c)
            S = load_s(sdir, "test", c, g0)
            qual, skipped = [], 0
            for qid, seeds, gi, _, _ in sorted(test, key=lambda t: t[0]):
                gold = {x for x in gi if x >= 0}
                if not gold - set(seeds): continue
                _, par = tree_edges(C0, seeds, gold)
                if par is None: continue
                ins = sorted((C0[u, v], v, u) for v, u in par.items() if v in gold)
                if not ins: continue
                _, v, u = ins[0]
                sh = sorted((df[k], k) for k in set(rows[u]["keys"]) & set(rows[v]["keys"]) if okk(k))
                if not sh: skipped += 1; continue
                key = sh[0][1]
                into_v = [w for x, w in par.items() if x == v]
                onT = set().union(*(set(rows[w]["keys"]) for w in into_v))
                cands = sorted((abs(df[k] - df[key]), k) for k in set(rows[v]["keys"]) if okk(k) and k not in onT)
                qual.append(dict(qid=qid, seeds=seeds, gi=gi, a=v, u=u, key=key, ctrl=cands[0][1] if cands else None))
            say(f"\n== {c}: {len(qual)} qualifying test questions; {skipped} skipped (door-only edge); {sum(q['ctrl'] is None for q in qual)} without a control key")
            todo = qual[:4] if (cases_only or c == "prs") else qual
            F = Fmat(g0, [q["qid"] for q in todo], S)
            def arm(drop):
                res = []
                for i, q in enumerate(todo):
                    d = drop(q)
                    if d is None: res.append(None); continue
                    if d:
                        p, k = d; rr = list(rows); rr[p] = dict(rows[p], keys=[x for x in rows[p]["keys"] if x != k]); g = G(rr); L = s2.links(g)
                    else: g, L = g0, L0
                    gold = {x for x in q["gi"] if x >= 0}
                    hop, _ = s2.tstar(L, q["seeds"], gold)
                    cu = tree_edges(costs(g, UNI), q["seeds"], gold)[0] if d else tree_edges(C0, q["seeds"], gold)[0]
                    cl = tree_edges(costs(g, LC, F[:, i]), q["seeds"], gold)[0]
                    P, _ = g.run([q["seeds"]], UNI, F=F[:, [i]])
                    p_ = P[:, 0].copy(); p_[q["seeds"]] = -1
                    res.append(dict(hop=hop, uni=round(cu, 4), lc=round(cl, 4), rec=recall5(P, [(q["seeds"], q["gi"])])[0], rank=int((p_ > p_[q["a"]]).sum()) + 1))
                return res
            A = {"built": arm(lambda q: ()), "cut": arm(lambda q: (q["a"], q["key"])),
                 "restored": arm(lambda q: ()), "control": arm(lambda q: (q["a"], q["ctrl"]) if q["ctrl"] else None)}
            agree = 0
            for i, q in enumerate(todo[:4]):
                b_, cu, re_, co = (A[k][i] for k in ("built", "cut", "restored", "control"))
                say(f"case {q['qid']}: T* edge {rows[q['u']]['d']} -> {rows[q['a']]['d']}; cut '{q['key']}' (width {df[q['key']] - 1}); control '{q['ctrl']}' (width {df[q['ctrl']] - 1 if q['ctrl'] else '-'})")
                for nm, r in (("built", b_), ("cut", cu), ("restored", re_), ("control", co)):
                    if r: say(f"   {nm:9s} hop T* +{r['hop']}; T* UNI {r['uni']:.2f} nats, LC+F {r['lc']:.2f}; recall {r['rec'] if r['rec'] is None else round(r['rec'], 3)}; rank of v {r['rank']}")
                ok = co is not None and (cu["rank"] - b_["rank"]) > (co["rank"] - b_["rank"]) and re_ == b_
                agree += ok
                say(f"   rank change: cut {cu['rank'] - b_['rank']:+d}, control {co['rank'] - b_['rank'] if co else None}; restored equals built {re_ == b_} -> {'agrees' if ok else 'does not agree'}")
            say(f"{c} gate: {agree}/{min(4, len(todo))} cases agree")
            res = {"cases": [{**{k: v for k, v in q.items() if k in ('qid', 'key', 'ctrl')}, "v": rows[q['a']]['d'], "u": rows[q['u']]['d'], **{a: A[a][i] for a in A}} for i, q in enumerate(todo)], "gate": agree}
            if len(todo) > 4:
                trip = [(b_, cu, co) for b_, cu, co in zip(A["built"], A["cut"], A["control"]) if co]
                lr = [np.log(cu["rank"] / b_["rank"]) for b_, cu, co in trip]; lc = [np.log(co["rank"] / b_["rank"]) for b_, cu, co in trip]
                d, lo, hi = boot(lr, lc)
                rr = [(cu["rec"], co["rec"]) for b_, cu, co in trip if cu["rec"] is not None]
                d2, lo2, hi2 = boot([x for x, _ in rr], [y for _, y in rr])
                say(f"{c} aggregate ({len(trip)}): log rank change cut {np.mean(lr):+.3f}, control {np.mean(lc):+.3f}, cut − control {d:+.3f} [{lo:+.3f}, {hi:+.3f}]; "
                    f"recall cut − control {d2:+.3f} [{lo2:+.3f}, {hi2:+.3f}]; T* UNI added cost cut {np.mean([cu['uni'] - b_['uni'] for b_, cu, _ in trip]):+.2f}, control {np.mean([co['uni'] - b_['uni'] for b_, _, co in trip]):+.2f}")
                res["aggregate"] = dict(n=len(trip), logrank=(d, lo, hi), recall=(d2, lo2, hi2))
            out[c] = res
    os.makedirs("out", exist_ok=True)
    tag = "-cases" if cases_only else ""
    json.dump(out, open(f"out/s2c{tag}.json", "w"), indent=1, default=str)
    open(f"out/s2c{tag}.txt", "w").write("\n".join(txt) + "\n")


if __name__ == "__main__":
    main()
