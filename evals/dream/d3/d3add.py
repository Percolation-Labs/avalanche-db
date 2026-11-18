"""D3's add arm (REGISTERED-D3.md): hubs over passages that vote for each other strongly (mutual top 5 of the vote)
but share no door; pairs merged into connected sets of at most 20. Scored as D3, against random hubs of the same
count and sizes. $0."""
import sys
exec(open(__file__.replace("d3add.py", "d3.py")).read().split("TESTF = ")[0])
TESTF = {"cards": ("../../floor/trace-cards.jsonl", "../../floor/q-cards.jsonl"), "prs": ("../../floor/trace-pr.jsonl", "../../floor/q-prs-test.jsonl"), "mq": ("../../floor/trace-mq.jsonl", "../../floor/q-musique-questions.jsonl")}

def mutual_hubs(g, top=5, cap=20):
    A, k = g.A, g.k
    Wk = (A.multiply(k).tocsr() @ A.T).tocsr()
    ri, ci = [], []
    for d in g.owned:
        for v in g.own[d]: ri += [d[1], v]; ci += [v, d[1]]
    L = sp.csr_matrix((np.ones(len(ri)), (ri, ci)), shape=(g.n, g.n))
    W = (Wk + L).tocsr(); W.setdiag(0); W.eliminate_zeros()
    deg = np.asarray(W.sum(1)).ravel()
    Wn = (sp.diags(1 / np.maximum(deg, 1e-9)) @ W).tocsr()
    r_, c_, v_ = [], [], []
    for u in range(g.n):
        s0, e0 = Wn.indptr[u], Wn.indptr[u + 1]; t = np.argsort(-Wn.data[s0:e0])[:30]
        r_ += [u] * len(t); c_ += Wn.indices[s0:e0][t].tolist(); v_ += Wn.data[s0:e0][t].tolist()
    Wt = sp.csr_matrix((v_, (r_, c_)), shape=(g.n, g.n))
    V = (Wt @ Wt).tocsr(); V.setdiag(0); V.eliminate_zeros()  # two-step vote: reaches passages not one door away
    tops = {}
    for u in range(g.n):
        s0, e0 = V.indptr[u], V.indptr[u + 1]
        tops[u] = set(V.indices[s0:e0][np.argsort(-V.data[s0:e0])[:top]].tolist())
    pairs = [(u, v) for u in tops for v in tops[u] if u < v and u in tops.get(v, ()) and W[u, v] == 0]
    parent = list(range(g.n))
    def f(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    size = collections.Counter()
    for u, v in pairs:
        a, b = f(u), f(v)
        if a != b and size.get(a, 1) + size.get(b, 1) <= cap:
            parent[a] = b; size[b] = size.get(a, 1) + size.get(b, 1)
    comp = collections.defaultdict(list)
    for u in {x for p in pairs for x in p}: comp[f(u)].append(u)
    return [m for m in comp.values() if len(m) >= 2], len(pairs)

def with_hubs(g, hubs, tag):
    rows_m = list(g.mem)
    for h, mem in enumerate(hubs):
        j = g.kix.setdefault(f"{tag}{h}", len(g.kix))
        rows_m += [(u, j) for u in mem]
    g.mem = np.array(rows_m); g.build(np.ones(len(g.mem), bool), set(g.own))


def plus(waves, hl, tag, g):
    by = collections.defaultdict(list)
    for h, mem in enumerate(hl):
        for u in mem: by[u].append(h)
    out = []
    for R, keys, gold in waves:
        ex = sorted({f"term:{tag}{h}" for d in R if d in g.ix for h in by.get(g.ix[d], [])})
        out.append((R, keys + ex, gold))
    return out

for gname, sets in [("p8", ["cards", "prs"]), ("mq", ["mq"])]:
    rows = [json.loads(l) for l in open(f"graph-{gname}.jsonl")]
    g = G(rows)
    dev = {c: dev_waves(c) for c in sets}; test = {c: test_waves(c, *TESTF[c]) for c in sets}
    hubs, npairs = mutual_hubs(g)
    sizes = [len(h) for h in hubs]
    print(f"{gname}: {npairs} mutual pairs sharing no door -> {len(hubs)} hubs, sizes median {np.median(sizes):.0f}, max {max(sizes)}, passages covered {sum(sizes)}", flush=True)
    for c in sets:
        g0 = G(rows); a0 = score(g0, dev[c]); t0 = score(g0, test[c])
        gh = G(rows); with_hubs(gh, hubs, "dreamhub:"); ah = score(gh, plus(dev[c], hubs, "dreamhub:", g))
        rng = np.random.default_rng(1); rh = [rng.choice(g.n, s, replace=False).tolist() for s in sizes]
        gr = G(rows); with_hubs(gr, rh, "randhub:")
        th = score(gh, plus(test[c], hubs, "dreamhub:", g)); tr = score(gr, plus(test[c], rh, "randhub:", g))
        print(f"  {c}: dev G0 {a0[0]:.3f} -> hubs {ah[0]:.3f} | TEST G0 {t0[0]:.3f} (gold door {t0[1]:.2f}) | hubs {th[0]:.3f} ({th[1]:.2f}) | random hubs {tr[0]:.3f} ({tr[1]:.2f})", flush=True)
