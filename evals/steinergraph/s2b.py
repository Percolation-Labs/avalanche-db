"""S2b (REGISTERED-S2b.md), $0: S2's cuts, with T* the cheapest directed tree under the walk's step cost -log p(u->v).
    uv run --with scipy --with numpy python s2b.py SCRATCH SDIR [--cases-only]"""
import json, sys, os, collections
import numpy as np, scipy.sparse as sp
from scipy.sparse import csgraph
import l1, s2
from l1 import G, UNI, load, load_s, Fmat, recall5, boot, mean_ok
from l3 import family


def costs(g, theta, f=None):
    """-log of step()'s one-step transition u->v; target weight h_v = hdeg_v * F_v (F omitted = 1)."""
    t1, t2, _ = theta
    g.set_theta(t1, t2)
    W = (g.A.multiply(g.kw[None, :]) @ g.A.T).tocsr()
    W = W - sp.diags(g.Akw) + g.Ow
    W = W.tocsr(); W.data[W.data < 1e-12] = 0; W.eliminate_zeros()
    W = W @ sp.diags(g.hdeg * (f if f is not None else 1.0))
    rs = np.asarray(W.sum(1)).ravel()
    P = sp.diags(1 / np.where(rs > 0, rs, 1)) @ W
    C = P.tocsr(); C.data = -np.log(C.data)
    return C


def tstar(C, seeds, gold):
    """Takahashi-Matsuyama directed Steiner tree from the seed root. Returns (cost in nats, nodes) or (inf, None)."""
    tree, left, total = set(seeds), set(gold) - set(seeds), 0.0
    while left:
        d, p, _ = csgraph.dijkstra(C, directed=True, indices=sorted(tree), min_only=True, return_predecessors=True)
        j = min(left, key=lambda x: (d[x], x))
        if not np.isfinite(d[j]): return float("inf"), None
        total += d[j]; x = j
        while x not in tree: tree.add(x); x = p[x]
        left -= tree
    return total, tree


def main():
    scr, sdir = sys.argv[1], sys.argv[2]
    cases_only = "--cases-only" in sys.argv
    l2fit = json.load(open("out/l2.json"))
    out, txt = {}, []
    def say(s): print(s, flush=True); txt.append(s)
    for gname, sets in (("mq", ("mq",)), ("p8", ("cards", "prs"))):
        rows = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gname}.jsonl")]
        g0 = G(rows)
        df = collections.Counter(k for r in rows for k in set(r["keys"]))
        okk = lambda k: 2 <= df[k] <= 100
        def door(a, b):
            return any(rows[b]["d"] in rows[a][kd] or rows[a]["d"] in rows[b][kd] for kd in ("next", "near"))
        for c in sets:
            thetas = {"UNI": UNI, "LC": tuple(l2fit[c]["theta"]["LC"])}
            L0 = s2.links(g0)
            _, test = load(scr, g0, c)
            S = load_s(sdir, "test", c, g0)
            qual = []
            for qid, seeds, gi, _, _ in sorted(test, key=lambda t: t[0]):
                gl = sorted(x for x in gi if x >= 0)
                hit = None
                for ia, a in enumerate(gl):
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
                pool = [k for k in set(rows[cut]["keys"]) if k != key and okk(k) and k not in gold_keys]
                same = sorted((abs(df[k] - df[key]), k) for k in pool if family(k) == family(key))
                anyf = sorted((abs(df[k] - df[key]), k) for k in pool)
                ctrl = same[0][1] if same else (anyf[0][1] if anyf else None)
                qual.append(dict(qid=qid, seeds=seeds, gi=gi, a=cut, b=other, key=key, ctrl=ctrl, ctrl_fam=bool(same)))
            say(f"\n== {c}: {len(qual)} test questions with a singly joined gold pair ({sum(q['ctrl'] is None for q in qual)} without any control key, {sum(not q['ctrl_fam'] for q in qual)} on the any-family fallback)")
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
                    Cs = {"UNI": costs(g, UNI), "LC": costs(g, thetas["LC"], F[:, i])}
                    gold = {x for x in q["gi"] if x >= 0}
                    hop, _ = s2.tstar(L, q["seeds"], gold)
                    r = {"hop": hop}
                    for nm, th in thetas.items():
                        cost, nodes = tstar(Cs[nm], q["seeds"], gold)
                        P, _ = g.run([q["seeds"]], th, F=F[:, [i]])
                        p_ = P[:, 0].copy(); p_[q["seeds"]] = -1
                        r[nm] = dict(cost=round(cost, 4), rec=recall5(P, [(q["seeds"], q["gi"])])[0], rank=int((p_ > p_[q["a"]]).sum()) + 1,
                                     tsize=len(nodes - set(q["seeds"]) - gold) if nodes else None)
                    res.append(r)
                return res
            A = {"built": arm(lambda q: ()), "cut": arm(lambda q: (q["a"], q["key"])),
                 "restored": arm(lambda q: ()), "control": arm(lambda q: (q["a"], q["ctrl"]) if q["ctrl"] else None)}
            agree = 0
            for i, q in enumerate(todo[:4]):
                b_, cu, re_, co = (A[k][i] for k in ("built", "cut", "restored", "control"))
                say(f"case {q['qid']}: cut '{q['key']}' (width {df[q['key']] - 1}, {family(q['key'])}) from {rows[q['a']]['d']} (joined {rows[q['b']]['d']}); control '{q['ctrl']}' (width {df[q['ctrl']] - 1 if q['ctrl'] else '-'})")
                for nm, r in (("built", b_), ("cut", cu), ("restored", re_), ("control", co)):
                    if r: say(f"   {nm:9s} hop T* +{r['hop']}; " + "; ".join(f"{t}: T* {r[t]['cost']:.2f} nats (+{r[t]['tsize']} passages), recall {r[t]['rec'] if r[t]['rec'] is None else round(r[t]['rec'], 3)}, rank {r[t]['rank']}" for t in thetas))
                dc = cu["UNI"]["cost"] - b_["UNI"]["cost"]; dk = (co["UNI"]["cost"] - b_["UNI"]["cost"]) if co else None
                ok = co is not None and dc > dk and re_ == b_
                agree += ok
                say(f"   UNI added cost: cut {dc:+.2f}, control {dk if dk is None else round(dk, 2)}; restored equals built {re_ == b_} -> {'agrees' if ok else 'does not agree'}")
            say(f"{c} gate: {agree}/{min(4, len(todo))} cases agree")
            res = {"cases": [{**{k: v for k, v in q.items() if k in ('qid', 'key', 'ctrl', 'ctrl_fam')}, "passage": rows[q['a']]['d'], **{a: A[a][i] for a in A}} for i, q in enumerate(todo)], "gate": agree}
            if len(todo) > 4:
                for t in thetas:
                    pr = [(cu[t]["cost"] - b_[t]["cost"], co[t]["cost"] - b_[t]["cost"]) for b_, cu, co in zip(A["built"], A["cut"], A["control"]) if co and np.isfinite(cu[t]["cost"]) and np.isfinite(co[t]["cost"])]
                    d, lo, hi = boot([x for x, _ in pr], [y for _, y in pr])
                    rr = [(cu[t]["rec"], co[t]["rec"]) for cu, co in zip(A["cut"], A["control"]) if co and cu[t]["rec"] is not None]
                    d2, lo2, hi2 = boot([x for x, _ in rr], [y for _, y in rr])
                    say(f"{c} aggregate {t} ({len(pr)} pairs): added T* cost cut {np.mean([x for x, _ in pr]):.3f}, control {np.mean([y for _, y in pr]):.3f}, cut − control {d:+.3f} [{lo:+.3f}, {hi:+.3f}]; recall cut − control {d2:+.3f} [{lo2:+.3f}, {hi2:+.3f}]")
                    res[f"aggregate-{t}"] = dict(n=len(pr), cost=(d, lo, hi), recall=(d2, lo2, hi2))
            out[c] = res
    os.makedirs("out", exist_ok=True)
    tag = "-cases" if cases_only else ""
    json.dump(out, open(f"out/s2b{tag}.json", "w"), indent=1, default=str)
    open(f"out/s2b{tag}.txt", "w").write("\n".join(txt) + "\n")


if __name__ == "__main__":
    main()
