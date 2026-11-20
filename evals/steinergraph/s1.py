"""S1 and S4 (REGISTERED-S1S4.md), $0: the exact gold Steiner tree T*, how the walk uses it, and when its edges emerge
from walks pooled over seed sets.
    uv run --with scipy --with numpy python s1.py SCRATCH SDIR OUT [--all]"""
import json, os, sys, random
import numpy as np, scipy.sparse as sp
from scipy.sparse.csgraph import dijkstra

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l1 import G, load_s, Fmat, ITERS, golds  # noqa: E402

EPS = 1e-9          # csgraph drops explicit zeros, so a zero-cost hop into a key is EPS
UNI = (-1, 0, .15)


class PG:
    """passages 0..n-1 and doors n..n+K-1; entering a passage costs 1, entering a door costs 0."""
    def __init__(s, rows, g):
        s.n = g.n; ok = np.where(g.ok)[0]; s.K = len(ok); kpos = {k: s.n + j for j, k in enumerate(ok)}
        A = g.A.tocoo(); r, c = [], []
        for p, k in zip(A.row, A.col):
            if k in kpos: r.append(p); c.append(kpos[k])
        s.key_of = {s.n + j: int(k) for j, k in enumerate(ok)}
        lr, lc = [], []
        for i, row in enumerate(rows):
            for kind in ("next", "near"):
                for x in row[kind]:
                    j = g.ix.get(x)
                    if j is not None and j != i: lr += [i, j]; lc += [j, i]
        s.N = s.n + s.K
        src = np.r_[r, c, lr]; dst = np.r_[c, r, lc]
        w = np.r_[np.full(len(r), EPS), np.ones(len(c)), np.ones(len(lr))]
        M = sp.csr_matrix((w, (src, dst)), shape=(s.N, s.N)); M.sum_duplicates()
        M.data = np.where(M.data > 1, 1.0, M.data)  # a duplicated link costs one hop
        s.M = M; s.cost = np.r_[np.ones(s.n), np.zeros(s.K)]

    def from_vec(s, init):
        """Dijkstra from a virtual source with an edge of weight init[v] to every finite v; returns dist, pred
        (pred == s.N means 'from the source')."""
        f = np.isfinite(init); idx = np.where(f)[0]
        top = sp.csr_matrix((np.maximum(init[idx], EPS), (np.zeros(len(idx), int), idx)), shape=(1, s.N + 1))
        M = sp.vstack([sp.hstack([s.M, sp.csr_matrix((s.N, 1))]), top]).tocsr()
        d, p = dijkstra(M, directed=True, indices=s.N, return_predecessors=True)
        return d[:s.N], p[:s.N]

    def steiner(s, terms):
        """terms: list of passage-index lists (a list of several = one contracted terminal). Exact Dreyfus–Wagner.
        Returns (cost, passages, edges [(a, b, via)])."""
        t = len(terms); F = 1 << t
        dp = np.full((F, s.N), np.inf); pred = [None] * F; split = [None] * F
        for i, T in enumerate(terms):
            init = np.full(s.N, np.inf); init[T] = 1.0
            dp[1 << i], pred[1 << i] = s.from_vec(init); split[1 << i] = None
        for S in range(1, F):
            if S & (S - 1) == 0: continue
            best = np.full(s.N, np.inf); arg = np.full(s.N, -1)
            A = (S - 1) & S
            while A:
                B = S ^ A
                if A < B:
                    v = dp[A] + dp[B] - s.cost
                    m = v < best; best[m] = v[m]; arg[m] = A
                A = (A - 1) & S
            dp[S], pred[S] = s.from_vec(best); split[S] = arg
        full = F - 1; root = int(np.argmin(dp[full])); cost = float(dp[full][root])
        nodes, edges = set(), []

        def build(S, v):
            path = [v]
            while pred[S][path[-1]] != s.N and pred[S][path[-1]] >= 0: path.append(int(pred[S][path[-1]]))
            u = path[-1]
            nodes.update(path)
            for a, b in zip(path, path[1:]): edges.append((a, b))
            if S & (S - 1): A = int(split[S][u]); build(A, u); build(S ^ A, u)
        build(full, root)
        return cost, nodes, edges

    def collapse(s, nodes, edges, dist=None):
        """A tree edge between passages: passage–door–passage becomes (hub, other, key), where a door holding m tree
        passages gives m−1 edges from its hub (the passage nearest the root, by dist), so T* stays a tree. A
        passage–passage hop is a link."""
        adj = {}
        for a, b in edges: adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
        out = set()
        for v in nodes:
            nb = adj.get(v, set())
            if v < s.n:
                out |= {(min(u, v), max(u, v), "link") for u in nb if u < s.n}
            else:
                ps = sorted((u for u in nb if u < s.n), key=lambda u: (dist[u] if dist is not None else 0, u))
                out |= {(min(ps[0], w), max(ps[0], w), s.key_of[v]) for w in ps[1:]}
        return sorted(out, key=lambda e: (e[0], e[1], str(e[2])))

    def sp_tree(s, seeds, gold):
        """james's: the union of shortest paths from the nearest seed to each gold passage."""
        init = np.full(s.N, np.inf); init[seeds] = 1.0
        d, p = s.from_vec(init); nodes, edges = set(), []
        for x in gold:
            if not np.isfinite(d[x]): continue
            path = [x]
            while p[path[-1]] != s.N and p[path[-1]] >= 0: path.append(int(p[path[-1]]))
            nodes.update(path); edges += list(zip(path, path[1:]))
        return nodes, s.collapse(nodes, edges, d), d


def first_rows(scr, c):
    rows = [json.loads(l) for l in open(f"{scr}/dream/dt-{c}.jsonl")]
    if c == "mq":
        want = ("RW:2hop__", "RW:3hop1__", "RW:4hop1__"); out = []
        for w in want: out.append(next(r for r in rows if r["qid"].startswith(w)))
        return out, rows
    return rows[:1], rows


def walk_reads(g, seeds_list, theta, F):
    P, W = g.run(seeds_list, theta, F=F, steps=tuple(range(1, ITERS + 1)))
    out = []
    for c, ss in enumerate(seeds_list):
        per = []
        for i in range(1, ITERS + 1):
            x = W[i][:, c].copy(); x[ss] = -1
            t = np.argpartition(-x, 5)[:5]; per.append([int(v) for v in t if x[v] > 0])
        p = P[:, c].copy(); p[ss] = -1; t = np.argpartition(-p, 5)[:5]
        out.append((per, [int(v) for v in t if p[v] > 0]))
    return out


def main():
    scr, sdir, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
    lc = {c: tuple(v["theta"]["LC"]) for c, v in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out/l2.json"))).items()}
    for gname, c in (("mq", "mq"), ("p8", "cards")):
        rows = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gname}.jsonl")]
        g = G(rows); pg = PG(rows, g)
        print(f"== {c}: {g.n} passages, {pg.K} doors", flush=True)
        cases, allr = first_rows(scr, c)
        ALL = "--all" in sys.argv
        if ALL: cases = allr
        agg = []
        say = (lambda *a, **k: None) if ALL else print
        Sd = load_s(sdir, "dev", c, g)
        tf = open(f"{out}/tstar-{c}.jsonl", "w"); pf = open(f"{out}/pool-{c}.jsonl", "w")
        rng = random.Random(0)
        for r in cases:
            q = r["qid"]; docs = [g.ix[d] for d in r["docs"] if d in g.ix]; seeds = docs[:5]
            gold_all = sorted(golds(r["gold"])); gold = [g.ix[x] for x in gold_all if x in g.ix]
            gold_out = [x for x in gold_all if x not in g.ix]
            tgt = [x for x in gold if x not in seeds]
            _, spe, dist = pg.sp_tree(seeds, gold)
            cut = [g.ids[x] for x in tgt if not np.isfinite(dist[x])]
            reach = [x for x in tgt if np.isfinite(dist[x])]
            say(f"\n-- {q}: gold {len(gold_all)} ({len(gold_out)} not in graph, {len(gold) - len(tgt)} already seeds, "
                  f"{len(cut)} cut off from the seeds)", flush=True)
            if not reach: say("   nothing to connect"); agg.append({"q": q, "reach": 0, "cut": len(cut), "nig": len(gold_out)}); continue
            cost, tn, te_raw = pg.steiner([seeds] + [[x] for x in reach]); te = pg.collapse(tn, te_raw, dist)
            spn, spe2, _ = pg.sp_tree(seeds, reach)
            tp = sorted(v for v in tn if v < g.n); tns = [v for v in tp if v not in seeds]
            hop = np.rint(dist[:g.n]) - 1  # hops from the nearest seed (dist carries EPS per door)
            depth = {v: int(hop[v]) for v in tp}
            say(f"   T*: {len(tp)} passages ({len(tns)} beyond seeds), {len(te)} edges; "
                  f"shortest-path tree {len([v for v in spn if v < g.n])} passages (gap {len([v for v in spn if v < g.n]) - len(tp)})")
            for a, b, via in te:
                kname = via if via == "link" else next((k for k in rows[a]["keys"] if k in rows[b]["keys"]), "?")
                ra = "S" if a in seeds else ("G" if a in reach else "·"); rb = "S" if b in seeds else ("G" if b in reach else "·")
                say(f"     {ra} {g.ids[a][:40]:40s} —[{kname[:30]}]— {rb} {g.ids[b][:40]}")
            tf.write(json.dumps({"qid": q, "root": [g.ids[x] for x in seeds], "gold": [g.ids[x] for x in reach],
                                 "cut": cut, "not_in_graph": gold_out, "nodes": [g.ids[x] for x in tp],
                                 "edges": [[g.ids[a], g.ids[b], "next" if v == "link" else next((k for k in rows[a]['keys'] if k in rows[b]['keys']), '?')] for a, b, v in te]}) + "\n")
            F1 = Fmat(g, [q], Sd)
            tset = set(tns); tedges = {(a, b) for a, b, _ in te}
            rec = {"q": q, "reach": len(reach), "cut": len(cut), "nig": len(gold_out), "size": len(tns), "gap": len([v for v in spn if v < g.n]) - len(tp)}
            for name, th in (("LC", lc[c]), ("U", UNI)):
                (per, av), = walk_reads(g, [seeds], th, F1)
                R = {v for t in per for v in t}
                first = {}
                for i, t in enumerate(per, 1):
                    for v in t: first.setdefault(v, i)
                dep = next((i for i, t in enumerate(per, 1) if not set(t) & tset), None)
                ball = int((hop <= max(depth.values())).sum()) - len(seeds)
                ref = len(tns) / max(ball, 1)
                order = sorted((depth[v], first[v]) for v in tns if v in first)
                rec[name] = (len(R & tset) / len(tset), len(R & tset) / max(len(R), 1), ref)
                say(f"   {name} θ{th}: coverage {len(R & tset)}/{len(tset)}, focus {len(R & tset)}/{len(R)} = {len(R & tset) / max(len(R), 1):.3f} "
                      f"(ball ref {ref:.4f}, ball {ball}); order (depth, first step) {order}; departs at step {dep}; "
                      f"avalanche top5 gold {len(set(av) & set(reach))}/{len(reach)}, on T* {len(set(av) & tset)}/5")
            # S4: pooled walks over seed sets
            ks = list(range(1, len(docs) + 1)); sets = [docs[:k] for k in ks]
            rand = [rng.sample(range(g.n), 5) for _ in range(3)]
            res = walk_reads(g, sets + rand, lc[c], np.repeat(F1, len(sets) + len(rand), 1))
            pools = {}
            for j, ((per, _), ss) in enumerate(zip(res, sets + rand)):
                draw = f"search-{ks[j]}" if j < len(sets) else f"rand-{j - len(sets)}"
                pf.write(json.dumps({"qid": q, "draw": draw, "seeds": [g.ids[x] for x in ss],
                                     "reads": [[g.ids[v], i] for i, t in enumerate(per, 1) for v in t]}) + "\n")
                pools[draw] = set(ss) | {v for t in per for v in t}

            def score(draws):
                shown = set(); pairs = set()
                for d in draws:
                    s_ = sorted(pools[d]); pairs |= {(a, b) for i, a in enumerate(s_) for b in s_[i + 1:]}
                shown = tedges & pairs
                return len(shown), len(tedges), len(shown) / max(len(pairs), 1), len(pairs)
            line = []
            for k in (1, 2, 4, len(docs)):
                a, n_, p_, np_ = score([f"search-{x}" for x in range(1, k + 1)]); line.append(f"k{k} {a}/{n_} (prec {p_:.4f} of {np_})")
            for j in (1, 2, 3):
                a, n_, p_, np_ = score([f"rand-{x}" for x in range(j)]); line.append(f"rand×{j} {a}/{n_}")
            # deviation (labelled): an edge counts as walk-shown only if its far end was read by a walk, not seeded
            readby = {v for (per, _), ss in zip(res[:len(sets)], sets) for t in per for v in t if v not in ss}
            rec["walk_shown"] = sum(1 for a, b in tedges if (a in readby or b in readby) and any({a, b} <= pools[f"search-{k}"] for k in ks))
            rec["edges"] = len(tedges)
            rec["S4"] = {k: score([f"search-{x}" for x in range(1, k + 1)])[0] / max(len(tedges), 1) for k in (1, 2, 4, len(docs))}
            rec["rand"] = score(["rand-0", "rand-1", "rand-2"])[0] / max(len(tedges), 1)
            agg.append(rec)
            emerge = next((k for k in ks if score([f"search-{x}" for x in range(1, k + 1)])[0] == len(tedges)), None)
            say("   S4 T*-edge recall: " + "; ".join(line) + f"; emerges at k = {emerge}", flush=True)
        tf.close(); pf.close()
        if ALL:
            A = [a for a in agg if a["reach"]]
            print(f"   all dev: {len(agg)} questions; {len(A)} with gold beyond the seeds reachable; {sum(a['cut'] > 0 for a in agg)} with gold cut off; {sum(a['nig'] > 0 for a in agg)} with gold not in the graph")
            print(f"   T* passages beyond seeds: mean {np.mean([a['size'] for a in A]):.2f}, max {max(a['size'] for a in A)}; DW smaller than the shortest-path tree on {sum(a['gap'] > 0 for a in A)}")
            for nm in ("LC", "U"):
                cv = [a[nm][0] for a in A]; fo = [a[nm][1] for a in A]; rf = [a[nm][2] for a in A]
                print(f"   {nm}: coverage mean {np.mean(cv):.3f} (any read {sum(x > 0 for x in cv)}/{len(A)}); focus mean {np.mean(fo):.4f} vs ball ref {np.mean(rf):.4f}; focus > ref on {sum(f > r for f, r in zip(fo, rf))}/{len(A)}")
            for k in (1, 2, 4, 10):
                v = [a["S4"].get(k, a["S4"][max(a["S4"])]) for a in A]
                print(f"   S4 search-pooled k{k}: T*-edge recall mean {np.mean(v):.3f}, all edges shown {sum(x == 1 for x in v)}/{len(A)}")
            print(f"   S4 rand×3: mean {np.mean([a['rand'] for a in A]):.3f}; edges shown with the far end walk-read (deviation): {sum(a['walk_shown'] for a in A)}/{sum(a['edges'] for a in A)}", flush=True)


if __name__ == "__main__":
    main()
