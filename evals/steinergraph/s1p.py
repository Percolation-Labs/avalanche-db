"""S1′/S4′ (REGISTERED-S1S4-amend.md), $0: T* as the walk's most probable tree. Link cost −log p(u→v), p the walk's
one-step transition (l1.G.step); exact directed Dreyfus–Wagner from the seeds (any seed) to every gold beyond them.
Shared with james's S2b: `trans(g, theta, hcol)` and `tree(C, seeds, gold)`.
    uv run --with scipy --with numpy python s1p.py SCRATCH SDIR OUT [--all]"""
import json, os, sys, time, random
import numpy as np, scipy.sparse as sp
from scipy.sparse.csgraph import dijkstra

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l1 import G, load_s, Fmat, ITERS, golds  # noqa: E402
from s1 import first_rows, walk_reads, UNI  # noqa: E402


def link_matrix(g, theta):
    """W_uv = Σ shared doors width^θ1 + next/near weight, zero diagonal (l1.G.step's kernel)."""
    g.set_theta(theta[0], theta[1])
    W = (g.A @ sp.diags(g.kw) @ g.A.T).tocsr() + g.Ow
    W = W.tocsr(); W.setdiag(0); W.eliminate_zeros(); return W


def trans(W, h):
    """p(u→v) = h_v W_uv / Σ_x h_x W_ux, as a CSR matrix."""
    P = (W @ sp.diags(h)).tocsr(); z = np.asarray(P.sum(1)).ravel()
    return (sp.diags(np.divide(1.0, z, out=np.zeros_like(z), where=z > 0)) @ P).tocsr()


def cost_matrix(P):
    C = P.copy(); C.data = -np.log(C.data); C.data = np.maximum(C.data, 1e-12); return C


def _from_vec(CT, init):
    """Dijkstra over the reversed links from a virtual source: d[u] = min_v init[v] + cost(u→…→v)."""
    n = CT.shape[0]; idx = np.where(np.isfinite(init))[0]
    top = sp.csr_matrix((np.maximum(init[idx], 1e-12), (np.zeros(len(idx), int), idx)), shape=(1, n + 1))
    M = sp.vstack([sp.hstack([CT, sp.csr_matrix((n, 1))]), top]).tocsr()
    d, p = dijkstra(M, directed=True, indices=n, return_predecessors=True)
    return d[:n], p[:n]


def tree(C, seeds, gold):
    """Exact min-cost arborescence from any seed to all gold. Returns (cost, edges [(u, v, cost)]), oriented
    root → leaf."""
    n = C.shape[0]; CT = C.T.tocsr(); t = len(gold); F = 1 << t
    dp = np.full((F, n), np.inf); pred = [None] * F; split = [None] * F
    for i, x in enumerate(gold):
        init = np.full(n, np.inf); init[x] = 0.0
        dp[1 << i], pred[1 << i] = _from_vec(CT, init)
    for S in range(1, F):
        if S & (S - 1) == 0: continue
        best = np.full(n, np.inf); arg = np.full(n, -1); A = (S - 1) & S
        while A:
            B = S ^ A
            if A < B:
                v = dp[A] + dp[B]; m = v < best; best[m] = v[m]; arg[m] = A
            A = (A - 1) & S
        dp[S], pred[S] = _from_vec(CT, best); split[S] = arg
    full = F - 1; r = min(seeds, key=lambda s_: dp[full][s_]); cost = float(dp[full][r])
    if not np.isfinite(cost): return cost, []
    edges = []

    def build(S, v):
        u = v
        while pred[S][u] != n and pred[S][u] >= 0:
            w = int(pred[S][u]); edges.append((u, w, float(C[u, w]))); u = w
        if S & (S - 1): A = int(split[S][u]); build(A, u); build(S ^ A, u)
    build(full, r)
    return cost, sorted(set(edges))


def main():
    scr, sdir, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True); ALL = "--all" in sys.argv
    lc = {c: tuple(v["theta"]["LC"]) for c, v in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out/l2.json"))).items()}
    for gname, c in (("mq", "mq"), ("p8", "cards")):
        rows = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gname}.jsonl")]
        g = G(rows); cases, allr = first_rows(scr, c); Sd = load_s(sdir, "dev", c, g)
        Wu = link_matrix(g, UNI); Wl = link_matrix(g, lc[c])
        Cu = cost_matrix(trans(Wu, np.ones(g.n)))
        g.set_theta(*lc[c][:2]); hdeg_l = g.hdeg.copy()
        print(f"== {c}: {g.n} passages, {Wu.nnz} directed links", flush=True)
        tf = open(f"{out}/tstarp-{c}.jsonl", "w"); agg = []; cap = None
        for qi, r in enumerate(allr if ALL else cases):
            if cap is not None and qi >= cap: break
            q = r["qid"]; docs = [g.ix[d] for d in r["docs"] if d in g.ix]; seeds = docs[:5]
            gold = [g.ix[x] for x in sorted(golds(r["gold"])) if x in g.ix]; reach = [x for x in gold if x not in seeds]
            if not reach: agg.append(None); (None if ALL else print(f"\n-- {q}: nothing beyond the seeds")); continue
            F1 = Fmat(g, [q], Sd)
            Cl = cost_matrix(trans(Wl, hdeg_l * F1[:, 0]))
            rec = {"q": q}
            for ref, C, th in (("graph-only", Cu, UNI), ("walk-as-used", Cl, lc[c])):
                t0 = time.time(); cost, E = tree(C, seeds, reach); dt = time.time() - t0
                nodes = {v for e in E for v in e[:2]}; tns = nodes - set(seeds)
                if not E:
                    rec[ref] = None; (None if ALL else print(f"   {ref}: no tree ({dt:.1f}s)")); continue
                (per, av), = walk_reads(g, [seeds], th, F1 if ref == "walk-as-used" else None)
                R = {v for t in per for v in t}; first = {}
                for i, t in enumerate(per, 1):
                    for v in t: first.setdefault(v, i)
                dep = next((i for i, t in enumerate(per, 1) if not set(t) & tns), None)
                hops = sorted(e[2] for e in E)
                rec[ref] = dict(cost=cost, n=len(tns), cov=len(R & tns) / len(tns), focus=len(R & tns) / max(len(R), 1),
                                inter=len(tns - set(reach)), cheap=hops[0], dear=hops[-1], dt=dt)
                if not ALL:
                    if ref == "graph-only": print(f"\n-- {q}: gold beyond seeds {len(reach)}")
                    print(f"   {ref} T*: {len(tns)} passages beyond seeds ({len(tns - set(reach))} non-gold), cost {cost:.2f} nats "
                          f"(p = {np.exp(-cost):.2e}), hops {[round(x, 2) for x in hops]}, solved {dt:.1f}s")
                    for u, v, w in E:
                        lab = lambda x: "S" if x in seeds else ("G" if x in reach else "·")
                        print(f"     {lab(u)} {g.ids[u][:38]:38s} → {lab(v)} {g.ids[v][:38]:38s} {w:.2f}")
                    print(f"   walk {th}: coverage {len(R & tns)}/{len(tns)}, focus {len(R & tns)}/{len(R)}, departs at step {dep}, "
                          f"order {sorted((first[v], g.ids[v][:20]) for v in tns if v in first)}", flush=True)
                tf.write(json.dumps({"qid": q, "ref": ref, "cost": cost, "seeds": [g.ids[x] for x in seeds],
                                     "gold": [g.ids[x] for x in reach], "edges": [[g.ids[u], g.ids[v], w] for u, v, w in E]}) + "\n")
            agg.append(rec)
            if ALL and len([a for a in agg if a]) == 1 and rec.get("graph-only") and rec["graph-only"]["dt"] > 60:
                print(f"   one question took {rec['graph-only']['dt']:.0f}s: aggregate cut to the first 20 (registered budget)", flush=True)
                cap = 20
        tf.close()
        if ALL:
            A = [a for a in agg if a]
            json.dump(A, open(f"{out}/s1p-agg-{c}.json", "w"))
            for ref in ("graph-only", "walk-as-used"):
                B = [a[ref] for a in A if a.get(ref)]
                if not B: continue
                print(f"   {ref}: {len(B)} trees; cost mean {np.mean([b['cost'] for b in B]):.2f} nats; passages beyond seeds mean "
                      f"{np.mean([b['n'] for b in B]):.2f}, non-gold mean {np.mean([b['inter'] for b in B]):.2f}; dearest hop mean {np.mean([b['dear'] for b in B]):.2f}; "
                      f"coverage mean {np.mean([b['cov'] for b in B]):.3f} (any {sum(b['cov'] > 0 for b in B)}/{len(B)}); focus mean {np.mean([b['focus'] for b in B]):.3f}", flush=True)


if __name__ == "__main__":
    main()
