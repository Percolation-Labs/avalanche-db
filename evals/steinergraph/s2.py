"""S2 (REGISTERED-S2.md), $0: cut the one key joining a gold pair, measure T* and the walk; control cut; restore.
    uv run --with scipy --with numpy python s2.py SCRATCH SDIR [--cases-only]"""
import json, sys, os, collections
import numpy as np, scipy.sparse as sp
from scipy.sparse import csgraph
import l1
from l1 import G, UNI, load, load_s, Fmat, recall5, boot, mean_ok
from l3 import family


def links(g):
    Ak = g.A[:, g.ok]
    L = (Ak @ Ak.T).tocsr(); L.setdiag(0)
    O = sp.csr_matrix((np.ones(len(g.Ori)), (g.Ori, g.Oci)), shape=(g.n, g.n))
    L = ((L + O + O.T) > 0).astype(float).tocsr(); L.eliminate_zeros()
    return L


def tstar(L, seeds, gold):
    """KMB shortest-path Steiner tree; terminal 0 is the seed set contracted to a root. Returns (cost, nodes) or (inf, None)."""
    terms = [list(seeds)] + [[x] for x in sorted(gold)]
    D, P = [], []
    for t in terms:
        d, p, _ = csgraph.dijkstra(L, indices=t, unweighted=True, min_only=True, return_predecessors=True)
        D.append(d); P.append(p)
    k = len(terms)
    M = np.array([[min(D[i][x] for x in terms[j]) for j in range(k)] for i in range(k)])
    if not np.isfinite(M).all(): return float("inf"), None
    inT, nodes = {0}, set(seeds)
    while len(inT) < k:  # Prim, ties by terminal order
        i, j = min(((i, j) for i in inT for j in range(k) if j not in inT), key=lambda e: (M[e], e[1], e[0]))
        x = terms[j][0]  # walk back from gold terminal j toward terminal i's source
        while x >= 0 and not (i == 0 and x in seeds) and not (i > 0 and x == terms[i][0]):
            nodes.add(x); x = P[i][x]
        if x >= 0: nodes.add(x)
        inT.add(j)
    return len(nodes - set(seeds) - set(gold)), nodes


def oklinks(g):
    df = np.asarray(g.A.sum(0)).ravel()
    return df


def main():
    scr, sdir = sys.argv[1], sys.argv[2]
    cases_only = "--cases-only" in sys.argv
    out, txt = {}, []
    def say(s): print(s, flush=True); txt.append(s)
    for gname, sets in (("mq", ("mq",)), ("p8", ("cards", "prs"))):
        rows = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gname}.jsonl")]
        g0 = G(rows); L0 = links(g0)
        kix = {}
        for r in rows:
            for k in r["keys"]: kix.setdefault(k, len(kix))
        df = collections.Counter(k for r in rows for k in set(r["keys"]))
        okk = lambda k: 2 <= df[k] <= 100
        def door(a, b):  # Beside or Near either way
            ra, rb = rows[a], rows[b]
            return any(rows[b]["d"] in ra[kd] or rows[a]["d"] in rb[kd] for kd in ("next", "near"))
        for c in sets:
            _, test = load(scr, g0, c)
            S = load_s(sdir, "test", c, g0)
            qual = []
            for qid, seeds, gi, _, _ in sorted(test, key=lambda t: t[0]):
                gl = sorted(x for x in gi if x >= 0)
                for ia, a in enumerate(gl):
                    hit = None
                    for b in gl[ia + 1:]:
                        sh = sorted(k for k in set(rows[a]["keys"]) & set(rows[b]["keys"]) if okk(k))
                        if len(sh) == 1 and not door(a, b): hit = (a, b, sh[0]); break
                    if hit: break
                if not hit: continue
                a, b, key = hit
                sa, sb = a in seeds, b in seeds
                cut = (b if sa and not sb else a if sb and not sa else max(a, b, key=lambda x: rows[x]["d"]))
                other = b if cut == a else a
                gold_keys = set().union(*(set(rows[x]["keys"]) for x in gl if x != cut))
                cands = sorted((abs(df[k] - df[key]), k) for k in set(rows[cut]["keys"])
                               if k != key and okk(k) and family(k) == family(key) and k not in gold_keys)
                ctrl = cands[0][1] if cands else None
                qual.append(dict(qid=qid, seeds=seeds, gi=gi, a=cut, b=other, key=key, ctrl=ctrl))
            say(f"\n== {c}: {len(qual)} test questions with a singly joined gold pair ({sum(q['ctrl'] is None for q in qual)} without a control key)")
            todo = qual[:4] if (cases_only or c == "prs") else qual
            F = Fmat(g0, [q["qid"] for q in todo], S)
            def arm(drop):  # drop: list of (passage, key) per case, or None
                res = []
                for i, q in enumerate(todo):
                    d = drop(q)
                    if d is None: res.append(None); continue
                    rr = list(rows)
                    if d:
                        p, k = d; rr[p] = dict(rows[p], keys=[x for x in rows[p]["keys"] if x != k])
                    g = G(rr) if d else g0; L = links(g) if d else L0
                    cost, nodes = tstar(L, q["seeds"], {x for x in q["gi"] if x >= 0})
                    P, _ = g.run([q["seeds"]], UNI, F=F[:, [i]])
                    rec = recall5(P, [(q["seeds"], q["gi"])])[0]
                    p = P[:, 0].copy(); p[q["seeds"]] = -1
                    rank = int((p > p[q["a"]]).sum()) + 1
                    res.append(dict(cost=cost, rec=rec, rank=rank, tnodes=sorted(rows[x]["d"] for x in nodes) if nodes else None))
                return res
            A = {"built": arm(lambda q: ()), "cut": arm(lambda q: (q["a"], q["key"])),
                 "restored": arm(lambda q: ()), "control": arm(lambda q: (q["a"], q["ctrl"]) if q["ctrl"] else None)}
            agree = 0
            for i, q in enumerate(todo[:4]):
                b_, cu, re_, co = (A[k][i] for k in ("built", "cut", "restored", "control"))
                say(f"case {q['qid']}: cut key '{q['key']}' (width {df[q['key']] - 1}, {family(q['key'])}) from {rows[q['a']]['d']}, which joined it to {rows[q['b']]['d']}")
                for nm, r in (("built", b_), ("cut", cu), ("restored", re_), ("control '" + str(q["ctrl"]) + "'", co)):
                    if r: say(f"   {nm:28s} T* cost {r['cost']}, recall {r['rec'] if r['rec'] is None else round(r['rec'], 3)}, cut passage rank {r['rank']}")
                moved = cu["cost"] > b_["cost"] or cu["rank"] > b_["rank"]
                still = co is not None and co["cost"] <= b_["cost"] and co["rank"] <= b_["rank"]
                ok = moved and still and re_ == b_
                agree += ok
                say(f"   cut moved {moved}; control held {still}; restored equals built {re_ == b_}  -> {'agrees' if ok else 'does not agree'}")
            say(f"{c} gate: {agree}/{min(4, len(todo))} cases agree")
            res = {"cases": [{**{k: v for k, v in q.items() if k in ('qid', 'key', 'ctrl')}, "passage": rows[q['a']]['d'], "partner": rows[q['b']]['d'],
                               **{a: A[a][i] for a in A}} for i, q in enumerate(todo)], "gate": agree}
            if len(todo) > 4:
                pr = [(cu["rec"], co["rec"]) for cu, co in zip(A["cut"], A["control"]) if co is not None and cu["rec"] is not None]
                d, lo, hi = boot([x for x, _ in pr], [y for _, y in pr])
                cost = [(cu["cost"] - b_["cost"], co["cost"] - b_["cost"]) for b_, cu, co in zip(A["built"], A["cut"], A["control"]) if co]
                say(f"{c} aggregate ({len(pr)} pairs): recall cut {np.mean([x for x, _ in pr]):.3f}, control {np.mean([y for _, y in pr]):.3f}, built {mean_ok([b_['rec'] for b_ in A['built']]):.3f}; "
                    f"cut − control {d:+.3f} [{lo:+.3f}, {hi:+.3f}]; T* cost added: cut {np.mean([x for x, _ in cost if np.isfinite(x)]):.2f} (unreachable {sum(not np.isfinite(x) for x, _ in cost)}), control {np.mean([y for _, y in cost if np.isfinite(y)]):.2f}")
                res["aggregate"] = dict(n=len(pr), diff=(d, lo, hi))
            out[c] = res
    os.makedirs("out", exist_ok=True)
    tag = "-cases" if cases_only else ""
    json.dump(out, open(f"out/s2{tag}.json", "w"), indent=1, default=str)
    open(f"out/s2{tag}.txt", "w").write("\n".join(txt) + "\n")


if __name__ == "__main__":
    main()
