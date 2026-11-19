"""evals/steinergraph/REGISTERED-P2.md, $0: likeness (where the seeds land) against connection (moving inside the gold
set), recall against budget by compactness and entry points, and MuSiQue's decomposed seeds.

    uv run --with scipy --with numpy python p2.py SCRATCH SEARCHDIR SUBQ OUTDIR
SCRATCH: james's L1 scratch (dream/d1/graph-*.jsonl, floor/*). SEARCHDIR: P1's search-test-*.jsonl.gz.
SUBQ: search hits for MuSiQue's sub-questions (qid|blind|i, qid|filled|i). Uses L1's graph class (l1.py, james)."""
import gzip, json, os, random, sys
from collections import defaultdict
import numpy as np, scipy.sparse as sp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l1 import G, load, UNI  # noqa: E402

CAP = 6
KS = (1, 3, 5, 10, 20)


def adjacency(g):
    """Undirected 'linked': a shared key held by 2–100 passages, or a next/near link either way."""
    Ak = g.A[:, np.where(g.ok)[0]]
    N = (Ak @ Ak.T).tocsr()
    O = sp.csr_matrix((np.ones(len(g.Ori)), (g.Ori, g.Oci)), shape=(g.n, g.n))
    N = ((N + O + O.T) > 0).astype(np.int8).tolil()
    N.setdiag(0)
    return N.tocsr()


def dist_from(N, src):
    """Hop distance (capped at CAP) from the set src to every passage."""
    d = np.full(N.shape[0], CAP, dtype=np.int8)
    fr = np.zeros(N.shape[0], bool)
    src = [s for s in src if s >= 0]
    if not src:
        return d
    fr[src] = True; d[src] = 0; seen = fr.copy()
    for h in range(1, CAP):
        nx = (N[np.where(fr)[0]].sum(0).A1 > 0) & ~seen
        if not nx.any():
            break
        d[nx] = h; seen |= nx; fr = nx
    return d


def shuffled_rows(rows, seed=0):
    """Each key keeps its size and each next/near list its length; members drawn at random."""
    rnd = random.Random(seed)
    ids = [r["d"] for r in rows]
    mem = defaultdict(list)
    for r in rows:
        for k in r["keys"]:
            mem[k].append(r["d"])
    keys = defaultdict(list)
    for k, m in mem.items():
        for d in rnd.sample(ids, len(m)):
            keys[d].append(k)
    return [{"d": r["d"], "keys": keys[r["d"]], "next": rnd.sample(ids, len(r["next"])),
             "near": rnd.sample(ids, len(r["near"]))} for r in rows]


def instep(g, S):
    """Mean over g in S of P(one uniform step from g lands on S minus g)."""
    S = [x for x in S if x >= 0]
    if len(S) < 2:
        return None
    _, W = g.run([[x] for x in S], UNI, steps=(1,))
    X = W[1]
    return float(np.mean([sum(X[y, c] for y in S if y != x) for c, x in enumerate(S)]))


def topk(P, c, seeds, k):
    p = P[:, c].copy(); p[seeds] = -1
    o = np.argsort(-p)[:k]
    return [int(t) for t in o if p[t] > 0]


def boot_diff(a, b, n=2000, seed=0, paired=True):
    r = np.random.default_rng(seed); a, b = np.array(a, float), np.array(b, float)
    if paired:
        d = a - b; bs = [d[r.integers(0, len(d), len(d))].mean() for _ in range(n)]; m = d.mean()
    else:
        bs = [a[r.integers(0, len(a), len(a))].mean() - b[r.integers(0, len(b), len(b))].mean() for _ in range(n)]
        m = a.mean() - b.mean()
    return m, np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def rr(gold, got):
    return len(gold & set(got)) / len(gold) if gold else None


def per_set(c, g, gs, N, Ns, test, srch, subq, out):
    qids = [q for q, *_ in test]
    P, _ = g.run([s for _, s, *_ in test], UNI)
    rows = []
    for col, (q, seeds, gold, walk, graw) in enumerate(test):
        Sg = {x for x in gold if x >= 0}
        dS = dist_from(N, list(Sg))
        dSs = dist_from(Ns, list(Sg))
        beyond = gold - set(seeds)
        ranked = topk(P, col, seeds, max(KS))
        hits = srch.get(q, [])
        rank = {d: i + 1 for i, (d, _) in enumerate(hits)}
        sc = dict(hits)
        pairs = [(a, b) for a in Sg for b in Sg if a < b]
        dist_pairs, dist_pairs_s = [], []
        for a in Sg:
            da, das = dist_from(N, [a]), dist_from(Ns, [a])
            dist_pairs += [int(da[b]) for b in Sg if b > a]
            dist_pairs_s += [int(das[b]) for b in Sg if b > a]
        # oracle: greedy over search's top 50, covering the most gold within one link
        cand = [gs.ix[d] for d, _ in hits[:50] if d in gs.ix]
        cov = {x: {y for y in Sg if y == x or N[x, y]} for x in cand}
        orc, have = [], set()
        for _ in range(5):
            best = max((x for x in cand if x not in orc), key=lambda x: (len(cov[x] - have), -cand.index(x)), default=None)
            if best is None:
                break
            orc.append(best); have |= cov[best]
        dseed = [dist_from(N, [x]) for x in seeds]
        dall = dist_from(N, seeds)
        row = {"qid": q, "n_gold": len(gold), "n_gold_in_graph": len(Sg), "seeds": [gs.ids[x] for x in seeds],
               "gold": sorted(graw),
               "likeness": {"entry": sum(1 for s in seeds if s in Sg), "near": int(sum(dS[s] <= 1 for s in seeds)),
                            "seed_dist_median": float(np.median([dall[x] for x in Sg])) if Sg else None,
                            "coverage": sum(1 for x in Sg if dall[x] <= 1) / len(gold),
                            "gold_search_rank": {d: rank.get(d) for d in sorted(graw)},
                            "gold_s": {d: sc.get(d, 0.0) for d in sorted(graw)}},
               "connection": {"mean_pair_dist": float(np.mean(dist_pairs)) if pairs else None,
                              "direct_share": float(np.mean([x == 1 for x in dist_pairs])) if pairs else None,
                              "mean_pair_dist_shuffled": float(np.mean(dist_pairs_s)) if pairs else None,
                              "direct_share_shuffled": float(np.mean([x == 1 for x in dist_pairs_s])) if pairs else None},
               "recall_beyond_U": {str(k): rr(beyond, ranked[:k]) for k in KS},
               "recall_beyond_walk": rr(beyond, walk),
               "oracle_seeds": [gs.ids[x] for x in orc]}
        rows.append(row)
    # in-S step, batched per question (real and shuffled)
    for row, (q, seeds, gold, *_) in zip(rows, test):
        row["connection"]["instep"] = instep(g, gold)
    return rows, P


def seed_sets(g, test, srch, subq, rows):
    """MuSiQue: single, blind-decomposed, filled-decomposed and oracle seeds; total recall at 10 reads."""
    variants = {"single": [s for _, s, *_ in test]}
    for v in ("blind", "filled"):
        vs = []
        for q, *_ in test:
            lists = [[g.ix[d] for d, _ in subq[f"{q}|{v}|{i}"] if d in g.ix] for i in range(10) if f"{q}|{v}|{i}" in subq]
            out, j = [], 0
            while len(out) < 5 and any(j < len(L) for L in lists):
                for L in lists:
                    if j < len(L) and L[j] not in out and len(out) < 5:
                        out.append(L[j])
                j += 1
            vs.append(out)
        variants[v] = vs
    variants["oracle"] = [[g.ix[d] for d in r["oracle_seeds"]] for r in rows]
    N = None
    res = {}
    for v, seeds in variants.items():
        P, _ = g.run(seeds, UNI)
        tot, cov, ent = [], [], []
        for col, ((q, _, gold, *_), s) in enumerate(zip(test, seeds)):
            got = set(s) | set(topk(P, col, s, 5))
            tot.append(rr(gold, got)); ent.append(sum(1 for x in s if x in gold))
        res[v] = {"total10": tot, "entry": ent}
    return res


def main():
    scr, sdir, subqf, od = sys.argv[1:5]
    os.makedirs(od, exist_ok=True)
    subq = {}
    for l in open(subqf):
        r = json.loads(l); subq[r["qid"]] = r["S"]
    summ = {}
    for gname, sets in (("p8", ("cards", "prs")), ("mq", ("mq",))):
        raw = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gname}.jsonl")]
        g = G(raw); gsh = G(shuffled_rows(raw)); assert gsh.ids == g.ids
        N, Ns = adjacency(g), adjacency(gsh)
        print(f"{gname}: n {g.n}, links {N.nnz // 2}, shuffled {Ns.nnz // 2}", flush=True)
        for c in sets:
            _, test = load(scr, g, c)
            srch = {}
            for l in gzip.open(f"{sdir}/search-test-{c}.jsonl.gz", "rt"):
                r = json.loads(l); srch[r["qid"]] = r["S"]
            rows, _ = per_set(c, g, g, N, Ns, test, srch, subq, od)
            # shuffled in-S step
            for row, (q, seeds, gold, *_) in zip(rows, test):
                row["connection"]["instep_shuffled"] = instep(gsh, gold)
            if c == "mq":
                ss = seed_sets(g, test, srch, subq, rows)
                for i, row in enumerate(rows):
                    row["seed_sets"] = {v: {"total10": ss[v]["total10"][i], "entry": ss[v]["entry"][i]} for v in ss}
                summ["seed_sets"] = ss
            with open(f"{od}/p2-{c}.jsonl", "w") as f:
                for row in rows:
                    f.write(json.dumps(row) + "\n")
            print(f"  {c}: {len(rows)} rows", flush=True)


if __name__ == "__main__":
    main()
