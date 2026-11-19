"""Steiner fixtures (Sirsh 12:34Z, M-20261119-123441-6d0b, item 1), $0. Per test question, one JSON file holding:
the question, search's seeds and the gold; the actual connectivity (an approximate Steiner tree over gold plus the
entry from the nearest seed, each link with the doors that make it); the potential connectivity (what the graph
reaches within 1 and 2 doors of the seeds, and the uniform spread's top 20); where each seed lands; what the Jev walk
read; and the top 5 under search, U, Q and LQ (L1's learned weights).

    uv run --with scipy --with numpy python fixtures.py SCRATCH SDIR [SETS...]
Writes fixtures/<set>/<qid>.json and fixtures/<set>/index.jsonl (one summary row per question)."""
import json, sys, gzip, subprocess, os, re
import numpy as np, scipy.sparse as sp
from scipy.sparse.csgraph import shortest_path, minimum_spanning_tree
import l1

REPO = os.path.dirname(os.path.abspath(__file__)) + "/../.."
MAXD = 6  # a gold passage further than this from every other terminal is reported as detached


def git_gz(ref, path):
    out = subprocess.run(["git", "-C", REPO, "show", f"{ref}:{path}"], capture_output=True).stdout
    return [json.loads(l) for l in gzip.decompress(out).decode().splitlines() if l.strip()]


class Doors:
    """undirected passage adjacency (shared key under the cap, Beside, Near), and what joins a pair."""
    def __init__(s, rows, g):
        s.rows, s.g = rows, g
        A = g.A[:, g.ok].tocsr()
        s.A = A
        df = np.asarray(A.sum(0)).ravel()
        W = (A @ sp.diags(1.0 / np.maximum(df - 1, 1)) @ A.T).tocsr()  # strength: sum of 1/width over shared keys
        ri, ci = [], []
        for i, r in enumerate(rows):
            for kind in ("next", "near"):
                for x in r[kind]:
                    j = g.ix.get(x)
                    if j is not None and j != i: ri += [i, j]; ci += [j, i]
        W = (W + sp.csr_matrix((np.ones(len(ri)), (ri, ci)), shape=W.shape)).tocsr()
        W.setdiag(0); W.eliminate_zeros()
        s.N = W.copy(); s.N.data[:] = 1          # hops
        s.C = W.copy(); s.C.data = 1 + .5 / (1 + 50 * W.data)  # fewest doors first; among equal, the narrowest
        s.keys_of = [set(r["keys"]) for r in rows]
        s.df = {}
        for ks in s.keys_of:
            for k in ks: s.df[k] = s.df.get(k, 0) + 1

    def via(s, a, b):
        ra, rb = s.rows[a], s.rows[b]
        out = []
        ida, idb = ra["d"], rb["d"]
        if idb in ra["next"] or ida in rb["next"]: out.append({"kind": "beside"})
        if idb in ra["near"] or ida in rb["near"]: out.append({"kind": "near", "width": len(ra["near"] if idb in ra["near"] else rb["near"])})
        shared = sorted(s.keys_of[a] & s.keys_of[b], key=lambda k: s.df[k])
        out += [{"kind": "term", "key": k, "width": s.df[k]} for k in shared if 2 <= s.df[k] <= 100][:5]
        return out


def path(pred, src_row, t):
    p = [t]
    while p[-1] != src_row and pred[p[-1]] >= 0: p.append(pred[p[-1]])
    return p[::-1] if p[-1] == src_row else None


def steiner(D, terminals, entry_seeds):
    """Kou-style: BFS from each terminal, MST over terminal distances, expand the tree's edges into paths; then join
    the nearest seed. Returns nodes, edges (pairs), detached terminals, pairwise gold distances."""
    T = sorted(terminals)
    if not T: return set(), set(), [], {}, None
    dist, pred = shortest_path(D.C, directed=False, indices=T, return_predecessors=True)
    hops = shortest_path(D.N, unweighted=True, indices=T)
    k = len(T)
    M = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            if i != j: M[i, j] = dist[i, T[j]] if np.isfinite(dist[i, T[j]]) and hops[i, T[j]] <= MAXD else 0
    tree = minimum_spanning_tree(sp.csr_matrix(M)).tocoo()
    nodes, edges = set(T), set()
    linked = set()
    for i, j in zip(tree.row, tree.col):
        p = path(pred[i], T[i], T[j])
        if p:
            nodes |= set(p); edges |= {tuple(sorted(e)) for e in zip(p, p[1:])}; linked |= {T[i], T[j]}
    detached = [t for t in T if k > 1 and t not in linked]
    pair = {f"{T[i]}|{T[j]}": (int(hops[i, T[j]]) if np.isfinite(hops[i, T[j]]) else None) for i in range(k) for j in range(i + 1, k)}
    # entry: the seed nearest to any terminal, and its path in
    best = None
    for i in range(k):
        for s_ in entry_seeds:
            d = dist[i, s_]
            if np.isfinite(d) and (best is None or d < best[0]): best = (d, i, s_)
    entry = None
    if best is not None:
        d, i, s_ = best
        p = path(pred[i], T[i], s_)
        if p:
            nodes |= set(p); edges |= {tuple(sorted(e)) for e in zip(p, p[1:])}
            entry = {"seed": s_, "gold": T[i], "doors": int(hops[i, s_])}
    return nodes, edges, detached, pair, (hops, entry)


def main():
    scr, sdir = sys.argv[1], sys.argv[2]
    sets = sys.argv[3:] or ["cards", "prs", "mq"]
    fit = {c: tuple(v["fit"]["LQ"]) for c, v in json.load(open("out/l1-q.json")).items()}
    for gname, gsets in (("p8", ("cards", "prs")), ("mq", ("mq",))):
        gsets = [c for c in gsets if c in sets]
        if not gsets: continue
        rows = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gname}.jsonl")]
        labels = {r["d"]: r["label"] for r in map(json.loads, open(f"{scr}/dream/d1/labels-{gname}.jsonl"))}
        g = l1.G(rows); D = Doors(rows, g)
        print(f"{gname}: adjacency nnz {D.N.nnz}", flush=True)
        for c in gsets:
            dev, test = l1.load(scr, g, c)
            St = l1.load_s(sdir, "test", c, g)
            qids = [q for q, *_ in test]
            seeds = [s_ for _, s_, _, _, _ in test]
            Ft = l1.Fmat(g, qids, St)
            P = {"U": g.run(seeds, l1.UNI)[0], "Q": g.run(seeds, l1.UNI, F=Ft)[0], "LQ": g.run(seeds, fit[c], F=Ft)[0]}
            Ps = np.zeros((g.n, len(test)))
            for ci, q in enumerate(qids):
                for i, x in St.get(q, {}).items(): Ps[i, ci] = x
            P["S"] = Ps
            traces = {t["qid"]: t for t in map(json.loads, open(f"{scr}/floor/" + {"cards": "trace-cards", "prs": "trace-pr", "mq": "trace-mq"}[c] + ".jsonl"))}
            os.makedirs(f"fixtures/{c}", exist_ok=True)
            idx = open(f"fixtures/{c}/index.jsonl", "w")
            for ci, (qid, s_, gi, walk, gs) in enumerate(test):
                L = lambda i: {"id": g.ids[i], "label": labels.get(g.ids[i])}
                gold_in = sorted(x for x in gi if x >= 0)
                missing = sorted(x for x in gs if x not in g.ix)
                nodes, edges, detached, pair, extra = steiner(D, gold_in, s_)
                dist, entry = extra if extra else (None, None)
                seed_rows = []
                for r_, x in enumerate(s_):
                    d = None if dist is None else min((dist[i, x] for i in range(len(gold_in))), default=np.inf)
                    seed_rows.append(L(x) | {"rank": r_ + 1, "gold": x in gi, "doors_to_gold": (int(d) if d is not None and np.isfinite(d) else None)})
                sd = shortest_path(D.N, unweighted=True, indices=s_).min(0) if s_ else np.full(g.n, np.inf)
                tops = {}
                for arm, M in P.items():
                    p = M[:, ci].copy(); p[s_] = -1
                    top = [int(t) for t in np.argsort(-p)[:5] if p[t] > 0]
                    tops[arm] = [L(t) | {"gold": t in gi} for t in top]
                tgt = set(gold_in) - set(s_)
                rec = {arm: (sum(t["gold"] for t in v) / (len(tgt) + len([m for m in missing])) if (tgt or missing) else None) for arm, v in tops.items()}
                pu = P["U"][:, ci].copy(); pu[s_] = -1
                tr = traces.get(qid, {})
                gold_pairs = [v for v in pair.values()]
                fx = {
                    "qid": qid, "set": c, "question": tr.get("question"),
                    "gold": [L(x) | {"seed": x in s_} for x in gold_in] + [{"id": m, "label": None, "not_in_graph": True} for m in missing],
                    "seeds": seed_rows,
                    "steiner": {
                        "nodes": [L(x) | {"role": "gold" if x in gi else ("seed" if x in s_ else "connector")} for x in sorted(nodes)],
                        "links": [{"a": g.ids[a], "b": g.ids[b], "via": D.via(a, b)} for a, b in sorted(edges)],
                        "cost": len(edges), "detached_gold": [g.ids[x] for x in detached],
                        "gold_pair_doors": gold_pairs, "entry": (entry and {"seed": g.ids[entry["seed"]], "gold": g.ids[entry["gold"]], "doors": entry["doors"]}),
                    },
                    "potential": {"within_1_door": int((sd == 1).sum()), "within_2_doors": int((sd == 2).sum()),
                                  "gold_within_1": int(sum(sd[x] == 1 for x in gold_in)), "gold_within_2": int(sum(sd[x] == 2 for x in gold_in)),
                                  "top_U": [L(int(t)) | {"p": float(pu[t]), "gold": int(t) in gi} for t in np.argsort(-pu)[:20] if pu[t] > 0]},
                    "walk_reads": [{"id": d["id"], "label": d.get("label"), "wave": d["wave"], "via": d.get("via"), "gold": d["id"] in gs} for d in tr.get("documents", [])],
                    "top5": tops, "recall5": rec,
                }
                fn = re.sub(r"[^A-Za-z0-9_.-]", "_", qid)
                json.dump(fx, open(f"fixtures/{c}/{fn}.json", "w"), indent=1)
                idx.write(json.dumps({"qid": qid, "file": f"{fn}.json", "n_gold": len(gold_in) + len(missing), "seeds_on_gold": sum(r["gold"] for r in seed_rows),
                                      "nearest_seed_doors": entry["doors"] if entry else None, "steiner_cost": len(edges), "steiner_nodes": len(nodes),
                                      "detached": len(detached), "max_gold_pair_doors": max([v for v in gold_pairs if v is not None], default=None),
                                      "recall5": rec, "walk_recall": (len(tgt & walk) / len(tgt) if tgt else None)}) + "\n")
            idx.close()
            print(f"{c}: {len(test)} fixtures", flush=True)


if __name__ == "__main__":
    main()
